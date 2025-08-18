import logging
from django.conf import settings
from django.core.mail import EmailMessage
from .models import Campaign, Message, Customer
from datetime import datetime
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
                    message.sent_at = datetime.now()
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
        
        campaign.sent_at = datetime.now()
        campaign.completed_at = datetime.now()
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
    Send email message using SendGrid
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
        
        logger.info(f"Email sent successfully to {customer.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {customer.email}: {str(e)}")
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
