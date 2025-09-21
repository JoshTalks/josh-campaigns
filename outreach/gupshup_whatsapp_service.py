import requests
import logging
from django.conf import settings
from typing import Tuple, List, Dict
import json
from urllib.parse import quote

logger = logging.getLogger(__name__)

class GupshupWhatsAppService:
    """
    Service class for interacting with Gupshup WhatsApp API
    """

    def __init__(self):
        self.userid = settings.GUPSHUP_WHATSAPP_USERID
        self.password = settings.GUPSHUP_WHATSAPP_PASSWORD
        self.app_id = settings.GUPSHUP_WHATSAPP_APP_ID
        self.api_key = settings.GUPSHUP_WHATSAPP_API_KEY
        self.api_url = settings.GUPSHUP_WHATSAPP_API_URL
        self.media_url = settings.GUPSHUP_WHATSAPP_MEDIA_URL

    def get_message_templates(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch message templates from Gupshup WhatsApp API
        
        Returns:
            Tuple of (success, templates_list, error_message)
        """
        try:
            # Try POST method with app_id in body
            url = f"https://api.gupshup.io/wa/app/{self.app_id}/template"
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Add app_id as form data for POST request
            data = {
                'appId': self.app_id
            }
            
            logger.info(f"Fetching Gupshup WhatsApp templates from: {url}")
            logger.info(f"Using API key: {self.api_key[:10]}...")
            logger.info(f"App ID: {self.app_id}")
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"API Response: {data}")
            
            # Process the response to extract templates
            templates = []
            if 'templates' in data:
                for template_data in data['templates']:
                    template = {
                        'name': template_data.get('name', ''),
                        'status': template_data.get('status', 'PENDING'),
                        'id': template_data.get('id', ''),
                        'category': template_data.get('category', 'UTILITY'),
                        'language': template_data.get('language', 'en'),
                        'components': template_data.get('components', [])
                    }
                    templates.append(template)
            
            # Filter only approved templates
            approved_templates = [
                template for template in templates 
                if template.get('status') == 'APPROVED'
            ]
            
            logger.info(f"Found {len(approved_templates)} approved templates out of {len(templates)} total")
            
            return True, approved_templates, "Templates fetched successfully"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Gupshup WhatsApp API request failed: {str(e)}"
            logger.error(error_msg)
            # Return mock data for development/testing
            return self._get_mock_templates()
        except Exception as e:
            error_msg = f"Unexpected error fetching Gupshup WhatsApp templates: {str(e)}"
            logger.error(error_msg)
            # Return mock data for development/testing
            return self._get_mock_templates()

    def _get_mock_templates(self) -> Tuple[bool, List[Dict], str]:
        """
        Return mock templates for development/testing when API is not accessible
        """
        mock_templates = [
            {
                "name": "job_opportunity",
                "status": "APPROVED",
                "id": "job_opp_001",
                "category": "UTILITY",
                "language": "en",
                "components": [
                    {
                        "type": "HEADER",
                        "text": "IMMEDIATE HIRING!"
                    },
                    {
                        "type": "BODY",
                        "text": "English Linguistic Experts Transcription | Work From Home\n\nLink- {{job_link}}\n\nJosh Talks is looking for immediate joiners who have excellent proficiency (reading, listening, writing, speaking) in English and can work from home for the next 15 days.\n\nDuration: {{duration}}\nCompensation: ₹{{compensation}}\n\nIf you're interested, please fill out the form and complete the short task as part of your application."
                    }
                ]
            },
            {
                "name": "appointment_reminder",
                "status": "APPROVED",
                "id": "appt_rem_001",
                "category": "UTILITY",
                "language": "en",
                "components": [
                    {
                        "type": "HEADER",
                        "text": "Appointment Reminder"
                    },
                    {
                        "type": "BODY",
                        "text": "Hello {{name}}, this is a reminder about your appointment with {{company_name}} on {{appointment_date}} at {{appointment_time}}. Please arrive 10 minutes early."
                    }
                ]
            },
            {
                "name": "otp_verification",
                "status": "APPROVED",
                "id": "otp_ver_001",
                "category": "AUTHENTICATION",
                "language": "en",
                "components": [
                    {
                        "type": "HEADER",
                        "text": "Verification Code"
                    },
                    {
                        "type": "BODY",
                        "text": "Your verification code is {{otp_code}}. This code will expire in {{expiry_minutes}} minutes. Do not share this code with anyone."
                    }
                ]
            }
        ]
        
        logger.info("Returning mock Gupshup WhatsApp templates for development")
        return True, mock_templates, "Mock templates returned (API not accessible)"

    def send_message(self, to_phone: str, message: str, header: str = None, is_template: bool = False) -> Tuple[bool, str]:
        """
        Send a WhatsApp message using Gupshup
        
        Args:
            to_phone: Recipient phone number (with country code, no +)
            message: Message content
            header: Optional header text
            is_template: Whether this is a template message
            
        Returns:
            Tuple of (success, response_message)
        """
        try:
            # Format phone number (remove + and ensure it starts with country code)
            if to_phone.startswith('+'):
                to_phone = to_phone[1:]
            
            # Use the exact format from the original curl example with proper URL encoding
            if is_template:
                # For template messages, use the media API with template parameters
                url = f"{self.media_url}?userid={self.userid}&password={quote(self.password)}&send_to={to_phone}&v=1.1&format=json&msg_type=TEXT&method=SENDMESSAGE&msg={quote(message)}&isTemplate=true"
                
                if header:
                    url += f"&header={quote(header)}"
                
                data = None
                headers = {}  # No headers needed for this API
            else:
                # For regular messages, use the media API
                url = f"{self.media_url}?userid={self.userid}&password={quote(self.password)}&send_to={to_phone}&v=1.1&format=json&msg_type=TEXT&method=SENDMESSAGE&msg={quote(message)}"
                
                data = None
                headers = {}  # No headers needed for this API
            
            logger.info(f"Sending Gupshup WhatsApp message to {to_phone}")
            logger.info(f"Using API key: {self.api_key[:10]}...")
            logger.info(f"URL: {url}")
            logger.info(f"Data: {data}")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Response Status Code: {response.status_code}")
            logger.info(f"Response Headers: {response.headers}")
            logger.info(f"Response Text: {response.text}")
            
            try:
                response_data = response.json()
                logger.info(f"API Response JSON: {response_data}")
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                # Try to extract success from text response
                if 'success' in response.text.lower():
                    return True, "Message sent successfully (text response)"
                else:
                    return False, f"API returned non-JSON response: {response.text}"
            
            # Check if the response indicates success
            if response_data.get('status') == 'success' or 'success' in str(response_data).lower():
                logger.info(f"Gupshup WhatsApp message sent successfully: {response_data}")
                return True, "Message sent successfully"
            else:
                error_msg = f"Gupshup WhatsApp API error: {response_data}"
                logger.error(error_msg)
                return False, error_msg
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Gupshup WhatsApp API request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error sending Gupshup WhatsApp message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def send_template_message(self, to_phone: str, template_name: str, parameters: List[str] = None, header: str = None) -> Tuple[bool, str]:
        """
        Send a WhatsApp template message using Gupshup
        
        Args:
            to_phone: Recipient phone number (with country code, no +)
            template_name: Name of the template
            parameters: List of parameters to fill in the template
            header: Optional header text
            
        Returns:
            Tuple of (success, response_message)
        """
        try:
            # Format phone number (remove + and ensure it starts with country code)
            if to_phone.startswith('+'):
                to_phone = to_phone[1:]
            
            # Use the correct Gupshup API endpoint for template messages
            url = "https://api.gupshup.io/sm/api/v1/template/msg"
            
            # Prepare template data
            template_data = {
                'id': template_name,
                'params': parameters or []
            }
            
            data = {
                'source': self.userid,  # Your WhatsApp number
                'destination': to_phone,
                'template': str(template_data).replace("'", '"')  # Convert to JSON string
            }
            
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            logger.info(f"Sending Gupshup WhatsApp template message to {to_phone}")
            logger.info(f"Template: {template_name}")
            logger.info(f"Parameters: {parameters}")
            logger.info(f"Using API key: {self.api_key[:10]}...")
            logger.info(f"URL: {url}")
            logger.info(f"Data: {data}")
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"API Response: {response_data}")
            
            # Check if the response indicates success
            if response_data.get('status') == 'success' or 'success' in str(response_data).lower():
                logger.info(f"Gupshup WhatsApp template message sent successfully: {response_data}")
                return True, "Template message sent successfully"
            else:
                error_msg = f"Gupshup WhatsApp API error: {response_data}"
                logger.error(error_msg)
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error sending Gupshup WhatsApp template message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
