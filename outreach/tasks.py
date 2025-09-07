import logging
import json
import http.client
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from io import BytesIO
import base64
from .models import Campaign, Message, Customer
from .csv_processor import BulkCSVProcessor
from django.utils import timezone
import time

logger = logging.getLogger(__name__)

@shared_task
def send_campaign_messages(campaign_id):
    """
    Send messages for a specific campaign to all customers
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
    Send email message using configured provider (SendGrid or MSG91)
    """
    try:
        # Prepare email content with customer variables
        content = campaign.content
        if campaign.subject:
            subject = campaign.subject
        else:
            subject = f"Message from {campaign.name}"
        
        # Replace variables in content
        # First, use custom placeholders if available
        if hasattr(campaign, 'custom_placeholders') and campaign.custom_placeholders:
            logger.info(f"   for campaign {campaign.id}: {campaign.custom_placeholders}")
            for placeholder, value in campaign.custom_placeholders.items():
                content = content.replace('{{' + placeholder + '}}', value)
                logger.info(f"Replaced {{{{{placeholder}}}}} with '{value}'")
        else:
            logger.info(f"No custom placeholders found for campaign {campaign.id}")
        
        # Then replace remaining customer-specific variables
        content = content.replace('{{name}}', customer.name or '')
        content = content.replace('{{email}}', customer.email or '')
        content = content.replace('{{phone}}', customer.phone or '')
        content = content.replace('{{address}}', customer.address or '')
        content = content.replace('{{job_link}}', customer.job_link or '')
        
        # Check provider and send accordingly
        if campaign.provider == 'msg91-email':
            # Use MSG91 API for email sending
            logger.info(f"Using MSG91 API to send email to {customer.email}")
            logger.info(f"Campaign provider: {campaign.provider}, Template: {campaign.template}")
            if campaign.template:
                logger.info(f"Template external_id: {campaign.template.external_id}")
            
            # Check if campaign has a template with external_id
            if not campaign.template or not campaign.template.external_id:
                message.error_message = "MSG91 requires template_id for all emails. Please select a template with external_id."
                logger.error(f"MSG91 email sending failed to {customer.email}: No template_id provided")
                return False
            
            return send_email_via_msg91(campaign, customer, message, content, subject)
        else:
            # Use Django's email backend (SendGrid) for other providers
            logger.info(f"Using Django email backend to send email to {customer.email}")
            return send_email_via_django(campaign, customer, message, content, subject)
        
    except Exception as e:
        logger.error(f"Error sending email to {customer.email}: {str(e)}")
        message.error_message = str(e)
        return False

def send_email_via_msg91(campaign, customer, message, content, subject):
    """
    Send email via MSG91 API using the updated service
    """
    try:
        from .msg91_service import MSG91EmailService
        
        # Create MSG91 service instance
        msg91_service = MSG91EmailService()
        
        # We already checked for template existence in the calling function
        template_id = campaign.template.external_id
        logger.info(f"Using MSG91 template ID: {template_id}")
        
        # Prepare variables for template
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
        
        # Send template email
        success, msg = msg91_service.send_template_email(
            to_email=customer.email,
            customer_name=customer.name or "Customer",
            template_id=template_id,
            variables=variables
        )
        
        if success:
            logger.info(f"Template email sent successfully via MSG91 to {customer.email}")
            return True
        else:
            logger.error(f"Template email failed via MSG91 to {customer.email}: {msg}")
            message.error_message = f"MSG91 template email error: {msg}"
            return False
            
    except Exception as e:
        logger.error(f"Error sending email via MSG91 to {customer.email}: {str(e)}")
        message.error_message = str(e)
        return False

def send_email_via_django(campaign, customer, message, content, subject):
    """
    Send email using Django's email backend (SendGrid)
    """
    try:
        # Send email using Django's email backend (SendGrid)
        email = EmailMessage(
            subject=subject,
            body=content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer.email]
        )
        
        # Check if content contains HTML
        if '<' in content and '>' in content:
            email.content_subtype = 'html'
        
        email.send()
        
        logger.info(f"Email sent successfully via Django backend to {customer.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email via Django backend to {customer.email}: {str(e)}")
        message.error_message = str(e)
        return False

def send_sms_message(campaign, customer, message):
    """
    Send SMS message (placeholder for future SMS provider integration)
    """
    try:
        # TODO: Implement SMS sending logic for different providers
        # For now, just log and mark as failed
        logger.info(f"SMS sending not yet implemented for provider: {campaign.provider}")
        message.error_message = "SMS sending not yet implemented"
        return False
        
    except Exception as e:
        logger.error(f"Error sending SMS to {customer.phone}: {str(e)}")
        message.error_message = str(e)
        return False

def send_whatsapp_message(campaign, customer, message):
    """
    Send WhatsApp message (placeholder for future WhatsApp provider integration)
    """
    try:
        # TODO: Implement WhatsApp sending logic for different providers
        # For now, just log and mark as failed
        logger.info(f"WhatsApp sending not yet implemented for provider: {campaign.provider}")
        message.error_message = "WhatsApp sending not yet implemented"
        return False
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp to {customer.phone}: {str(e)}")
        message.error_message = str(e)
        return False

@shared_task
def process_pending_campaigns():
    """
    Process all campaigns that are in 'draft' status and ready to be sent
    """
    try:
        # Find campaigns that are ready to be sent
        pending_campaigns = Campaign.objects.filter(
            status='draft',
            customers__isnull=False
        ).distinct()
        
        for campaign in pending_campaigns:
            # Check if campaign has customers
            if campaign.customers.count() > 0:
                logger.info(f"Processing pending campaign: {campaign.name}")
                # Trigger the send campaign task
                send_campaign_messages(campaign.id)
        
        return f"Processed {pending_campaigns.count()} pending campaigns"
        
    except Exception as e:
        logger.error(f"Error processing pending campaigns: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def process_customers_csv_task(file_b64: str, user_id: int) -> dict:
    """Process uploaded CSV content (base64) and return stats including affected_ids."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = None

    try:
        csv_bytes = base64.b64decode(file_b64.encode('ascii'))
        csv_file = BytesIO(csv_bytes)
        processor = BulkCSVProcessor(batch_size=1000)
        stats = processor.process_csv_file(csv_file, user)
        return stats
    except Exception as e:
        logger.error(f"CSV processing task failed: {str(e)}")
        raise
