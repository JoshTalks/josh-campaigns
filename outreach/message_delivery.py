import logging
from django.conf import settings
from django.core.mail import EmailMessage
from .models import Campaign, Message, Customer
from .msg91_service import MSG91EmailService
from django.utils import timezone
import time

logger = logging.getLogger(__name__)

def send_campaign_messages_sync(campaign_id):
    """
    Send messages for a specific campaign to all customers (synchronous version)
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        customers = campaign.customers.all()
        
        logger.info(f"Starting to send campaign {campaign.name} to {customers.count()} customers")
        
        # Update campaign status to sending
        campaign.status = 'sending'
        campaign.save()
        
        success_count = 0
        failure_count = 0
        
        for customer in customers:
            try:
                # Create message record
                message = Message.objects.create(
                    campaign=campaign,
                    customer=customer,
                    status='pending'
                )
                
                # Send message based on channel and provider
                if campaign.channel == 'email':
                    success = send_email_message(campaign, customer, message)
                elif campaign.channel == 'sms':
                    success = send_sms_message(campaign, customer, message)
                elif campaign.channel == 'whatsapp':
                    success = send_whatsapp_message(campaign, customer, message)
                else:
                    logger.error(f"Unknown channel: {campaign.channel}")
                    success = False
                
                if success:
                    message.status = 'sent'
                    message.sent_at = timezone.now()
                    success_count += 1
                    logger.info(f"Message sent successfully to {customer.email or customer.phone}")
                else:
                    message.status = 'failed'
                    message.error_message = "Failed to send message"
                    failure_count += 1
                    logger.error(f"Failed to send message to {customer.email or customer.phone}")
                
                message.save()
                
                # Small delay to avoid overwhelming the provider
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error sending message to customer {customer.id}: {str(e)}")
                failure_count += 1
                continue
        
        # Update campaign status
        if failure_count == 0:
            campaign.status = 'completed'
        else:
            campaign.status = 'completed'  # Still mark as completed even with some failures
        
        campaign.sent_at = timezone.now()
        campaign.completed_at = timezone.now()
        campaign.save()
        
        logger.info(f"Campaign {campaign.name} completed. Success: {success_count}, Failures: {failure_count}")
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'success_count': success_count,
            'failure_count': failure_count
        }
        
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return {'success': False, 'error': 'Campaign not found'}
    except Exception as e:
        logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

def send_email_message(campaign, customer, message):
    """
    Send email message using the configured provider (SendGrid or MSG91)
    """
    try:
        # Prepare email content with customer variables
        content = campaign.content
        if campaign.subject:
            subject = campaign.subject
        else:
            subject = f"Message from {campaign.name}"
        
        # Replace variables in content
        content = content.replace('{{name}}', customer.name or '')
        content = content.replace('{{email}}', customer.email or '')
        content = content.replace('{{phone}}', customer.phone or '')
        content = content.replace('{{address}}', customer.address or '')
        content = content.replace('{{job_link}}', customer.job_link or '')
        
        # Check if content contains HTML
        is_html = '<' in content and '>' in content
        
        # Send email based on provider
        if campaign.provider == 'msg91-email':
            # Use MSG91 for email sending
            msg91_service = MSG91EmailService()
            
            # Check if campaign has a template with external_id
            if campaign.template and campaign.template.external_id:
                # Use template-based sending
                # Map customer data to template variables
                variables = {
                    "name": customer.name or "Customer",
                    "email": customer.email,
                    "phone": customer.phone or "",
                    "address": customer.address or "",
                    "job_link": customer.job_link or "",
                    # Add common template variables
                    "company_name": "JoshTalks",  # Default company name
                    "otp": "123456",  # Default OTP - should be generated dynamically
                }
                
                # Add custom placeholders from campaign if available
                if hasattr(campaign, 'custom_placeholders') and campaign.custom_placeholders:
                    # Clean up malformed placeholders
                    clean_placeholders = {}
                    for key, value in campaign.custom_placeholders.items():
                        # Skip malformed keys like ' + variable + '
                        if isinstance(key, str) and not (' + ' in key and ' + ' in key):
                            clean_placeholders[key] = value
                    variables.update(clean_placeholders)
                
                success, msg = msg91_service.send_template_email(
                    to_email=customer.email,
                    customer_name=customer.name or "Customer",
                    template_id=campaign.template.external_id,
                    variables=variables
                )
            else:
                # MSG91 requires template_id for all emails
                message.error_message = "MSG91 requires template_id for all emails. Please select a template with external_id."
                logger.error(f"MSG91 email sending failed to {customer.email}: No template_id provided")
                return False
            
            if not success:
                message.error_message = msg
                logger.error(f"MSG91 email sending failed to {customer.email}: {msg}")
                return False
                
        else:
            # Use Django's email backend (SendGrid) as fallback
            email = EmailMessage(
                subject=subject,
                body=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer.email]
            )
            
            if is_html:
                email.content_subtype = 'html'
            
            email.send()
        
        logger.info(f"Email sent successfully to {customer.email} using {campaign.provider}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {customer.email}: {str(e)}")
        message.error_message = str(e)
        return False

def send_sms_message(campaign, customer, message):
    """
    Send SMS message
    """
    try:
        if not customer.phone:
            message.error_message = "Customer phone missing"
            return False

        # Clean and format phone number for Gupshup
        phone = clean_phone_number(customer.phone)
        if not phone:
            message.error_message = "Invalid phone number format"
            return False

        sms_text = campaign.content or ''
        # Basic placeholder replacement for common fields
        sms_text = sms_text.replace('{{name}}', customer.name or '')
        sms_text = sms_text.replace('{{phone}}', phone or '')
        sms_text = sms_text.replace('{{email}}', customer.email or '')
        sms_text = sms_text.replace('{{address}}', customer.address or '')
        sms_text = sms_text.replace('{{job_link}}', customer.job_link or '')

        if campaign.provider == 'gupshup-sms':
            from .gupshup_service import GupshupSMSService
            gs = GupshupSMSService()
            # Choose type based on campaign.subject (optional) defaults to TRANSACTIONAL
            msg_type = (campaign.subject or 'TRANSACTIONAL').upper()
            ok, info = gs.send_sms(phone, sms_text, msg_type=msg_type)
            if not ok:
                message.error_message = info
                message.status = 'failed'
                message.save()
                return False
            else:
                # Update message status to sent
                message.status = 'sent'
                message.sent_at = timezone.now()
                message.error_message = ''
                message.save()
                return True
        else:
            logger.info(f"SMS provider not supported yet: {campaign.provider}")
            message.error_message = f"Unsupported SMS provider: {campaign.provider}"
            return False
        
    except Exception as e:
        logger.error(f"Error sending SMS to {customer.phone}: {str(e)}")
        message.error_message = str(e)
        return False


def clean_phone_number(phone):
    """
    Clean and format phone number for Gupshup SMS
    Gupshup expects 10-digit Indian mobile numbers or international format
    """
    if not phone:
        return None
    
    # Remove all non-digit characters except +
    import re
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Handle different formats
    if cleaned.startswith('+'):
        # International format - remove + and check length
        digits = cleaned[1:]
        if len(digits) == 10 and digits.startswith(('6', '7', '8', '9')):
            # Indian mobile number with country code
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            # US number with country code
            return digits[1:]  # Remove country code for now
        else:
            # Other international - try to extract last 10 digits
            if len(digits) >= 10:
                return digits[-10:]
    else:
        # Local format
        if len(cleaned) == 10 and cleaned.startswith(('6', '7', '8', '9')):
            return cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            return cleaned[1:]
    
    # If we can't format it properly, return as is and let Gupshup handle it
    return cleaned

def send_whatsapp_message(campaign, customer, message):
    """
    Send WhatsApp message using the configured provider (Meta WhatsApp)
    """
    try:
        # Create message object if it doesn't exist
        if message is None:
            from .models import Message
            message = Message.objects.create(
                campaign=campaign,
                customer=customer,
                status='pending'
            )
        
        if not customer.phone:
            message.error_message = "Customer phone missing"
            message.status = 'failed'
            message.save()
            return False

        # Clean and format phone number for WhatsApp
        phone = clean_phone_number(customer.phone)
        if not phone:
            message.error_message = "Invalid phone number format"
            message.status = 'failed'
            message.save()
            return False

        if campaign.provider == 'meta-whatsapp':
            from .meta_whatsapp_service import MetaWhatsAppService
            
            # Get template name from campaign template
            template_name = campaign.template.name if campaign.template else 'hello_world'
            
            # Prepare template parameters from campaign content and custom placeholders
            parameters = []
            if campaign.content:
                # Extract parameters from template content
                import re
                template_vars = re.findall(r'\{\{(\w+)\}\}', campaign.content)
                
                for var in template_vars:
                    if var == 'name':
                        parameters.append(customer.name or 'Customer')
                    elif var == 'phone':
                        parameters.append(phone)
                    elif var == 'email':
                        parameters.append(customer.email or '')
                    elif var == 'address':
                        parameters.append(customer.address or '')
                    elif var == 'job_link':
                        parameters.append(customer.job_link or '')
                    elif hasattr(campaign, 'custom_placeholders') and campaign.custom_placeholders:
                        # Get from custom placeholders
                        parameters.append(campaign.custom_placeholders.get(var, ''))
                    else:
                        # Default value for unknown variables
                        parameters.append('')
            
            meta_service = MetaWhatsAppService()
            success, response_msg, response_data = meta_service.send_message(
                to_phone=phone,
                template_name=template_name,
                language_code='en_US',
                parameters=parameters
            )
            
            if not success:
                message.error_message = response_msg
                message.status = 'failed'
                message.save()
                return False
            else:
                # Update message status to sent and store message ID if available
                message.status = 'sent'
                message.sent_at = timezone.now()
                if response_data and 'messages' in response_data:
                    # Store the WhatsApp message ID for tracking
                    whatsapp_msg_id = response_data['messages'][0].get('id')
                    if whatsapp_msg_id:
                        message.external_id = whatsapp_msg_id
                message.error_message = ''
                message.save()
                return True
                
        elif campaign.provider == 'gupshup-whatsapp':
            from .gupshup_whatsapp_service import GupshupWhatsAppService
            
            # Prepare message content with variable replacement
            message_content = campaign.content or ''
            if message_content:
                # Replace variables in the message content
                message_content = message_content.replace('{{name}}', customer.name or 'Customer')
                message_content = message_content.replace('{{phone}}', phone)
                message_content = message_content.replace('{{email}}', customer.email or '')
                message_content = message_content.replace('{{address}}', customer.address or '')
                message_content = message_content.replace('{{job_link}}', customer.job_link or '')
                
                # Replace custom placeholders
                if hasattr(campaign, 'custom_placeholders') and campaign.custom_placeholders:
                    for key, value in campaign.custom_placeholders.items():
                        message_content = message_content.replace(f'{{{{{key}}}}}', str(value))
            
            # Get header from campaign subject
            header = campaign.subject or ''
            
            gupshup_service = GupshupWhatsAppService()
            success, response_msg = gupshup_service.send_message(
                to_phone=phone,
                message=message_content,
                header=header,
                is_template=True
            )
            
            if not success:
                message.error_message = response_msg
                message.status = 'failed'
                message.save()
                return False
            else:
                # Update message status to sent
                message.status = 'sent'
                message.sent_at = timezone.now()
                message.error_message = ''
                message.save()
                return True
        else:
            logger.info(f"WhatsApp provider not supported yet: {campaign.provider}")
            message.error_message = f"Unsupported WhatsApp provider: {campaign.provider}"
            message.status = 'failed'
            message.save()
            return False
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp to {customer.phone}: {str(e)}")
        message.error_message = str(e)
        message.status = 'failed'
        message.save()
        return False
