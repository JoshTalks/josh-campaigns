import requests
import logging
from django.conf import settings
from typing import Tuple, List, Dict, Optional
import json
import time
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class MetaWhatsAppService:
    """
    Service class for interacting with Meta WhatsApp Business Cloud API
    Based on: https://developers.facebook.com/docs/whatsapp/cloud-api
    """

    def __init__(self):
        self.access_token = settings.META_WHATSAPP_ACCESS_TOKEN
        self.business_account_id = settings.META_WHATSAPP_BUSINESS_ACCOUNT_ID
        self.api_version = settings.META_WHATSAPP_API_VERSION
        self.base_url = settings.META_WHATSAPP_BASE_URL
        self.phone_number_id = getattr(settings, 'META_WHATSAPP_PHONE_NUMBER_ID', None)
        
        # Rate limiting settings
        self.rate_limit_requests = 1000  # requests per hour
        self.rate_limit_window = 3600  # 1 hour in seconds

    def get_message_templates(self, limit: int = 50, status: str = None) -> Tuple[bool, List[Dict], str]:
        """
        Fetch message templates from Meta WhatsApp Business Cloud API
        
        Args:
            limit: Maximum number of templates to fetch (max 1000)
            status: Filter by template status (APPROVED, PENDING, REJECTED, etc.)
            
        Returns:
            Tuple of (success, templates_list, error_message)
        """
        try:
            # Use phone number ID if available, otherwise use business account ID
            endpoint_id = self.phone_number_id or self.business_account_id
            url = f"{self.base_url}/{endpoint_id}/message_templates"
            
            params = {
                'fields': 'name,status,id,category,language,components,quality_score,rejected_reason',
                'limit': min(limit, 1000)  # API max limit is 1000
            }
            
            if status:
                params['status'] = status
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Fetching Meta WhatsApp templates from: {url}")
            logger.debug(f"Request params: {params}")
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                time.sleep(retry_after)
                response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Check for specific error responses
            if response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', 0)
                
                logger.warning(f"Meta WhatsApp API error {error_code}: {error_message}")
                
                # Handle specific error cases
                if error_code == 100 or 'does not exist' in error_message.lower():
                    logger.warning("Business account or phone number not found, returning mock data")
                    return self._get_mock_templates()
                elif error_code == 190 or 'access token' in error_message.lower():
                    logger.error("Invalid access token")
                    return False, [], f"Invalid access token: {error_message}"
                else:
                    return False, [], f"API Error: {error_message}"
            
            response.raise_for_status()
            
            data = response.json()
            templates = data.get('data', [])
            
            # Filter by status if not already filtered by API
            if status and status != 'ALL':
                templates = [t for t in templates if t.get('status') == status]
            elif not status:
                # Default to approved templates only
                templates = [t for t in templates if t.get('status') == 'APPROVED']
            
            # Add pagination info if available
            paging = data.get('paging', {})
            has_next = 'next' in paging
            has_prev = 'previous' in paging
            
            logger.info(f"Found {len(templates)} templates (has_next: {has_next}, has_prev: {has_prev})")
            
            return True, templates, "Templates fetched successfully"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Meta WhatsApp API request failed: {str(e)}"
            logger.error(error_msg)
            # Return mock data for development/testing
            return self._get_mock_templates()
        except Exception as e:
            error_msg = f"Unexpected error fetching Meta WhatsApp templates: {str(e)}"
            logger.error(error_msg)
            # Return mock data for development/testing
            return self._get_mock_templates()

    def _get_mock_templates(self) -> Tuple[bool, List[Dict], str]:
        """
        Return mock templates for development/testing when API is not accessible
        """
        mock_templates = [
            {
                "name": "seasonal_promotion_text_only",
                "status": "APPROVED",
                "id": "564750795574598",
                "category": "MARKETING",
                "language": "en_US",
                "components": [
                    {
                        "type": "HEADER",
                        "text": "🎉 Special Offer Inside!"
                    },
                    {
                        "type": "BODY",
                        "text": "Hi {{name}}, we have an exclusive offer just for you! Get {{discount}}% off on all items. Use code {{coupon_code}} to redeem. Valid until {{expiry_date}}."
                    }
                ]
            },
            {
                "name": "appointment_reminder",
                "status": "APPROVED", 
                "id": "1252715608684590",
                "category": "UTILITY",
                "language": "en_US",
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
                "id": "1372429296936443", 
                "category": "AUTHENTICATION",
                "language": "en_US",
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
        
        logger.info("Returning mock Meta WhatsApp templates for development")
        return True, mock_templates, "Mock templates returned (API not accessible)"

    def send_message(self, to_phone: str, template_name: str, language_code: str = "en_US", 
                    parameters: List[str] = None) -> Tuple[bool, str, Dict]:
        """
        Send a WhatsApp message using a template via Cloud API
        
        Args:
            to_phone: Recipient phone number (with country code, no +)
            template_name: Name of the template to use
            language_code: Language code for the template (default: en_US)
            parameters: List of parameters to fill in the template
            
        Returns:
            Tuple of (success, response_message, response_data)
        """
        try:
            # Format phone number (remove + and ensure it starts with country code)
            if to_phone.startswith('+'):
                to_phone = to_phone[1:]
            
            # Use phone number ID if available, otherwise use business account ID
            endpoint_id = self.phone_number_id or self.business_account_id
            url = f"{self.base_url}/{endpoint_id}/messages"
            
            # Prepare template parameters for body components
            body_params = []
            if parameters:
                for param in parameters:
                    body_params.append({
                        "type": "text",
                        "text": str(param)
                    })
            
            # Build components array
            components = []
            if body_params:
                components.append({
                    "type": "body",
                    "parameters": body_params
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    },
                    "components": components
                }
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Sending Meta WhatsApp message to {to_phone} using template {template_name}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                time.sleep(retry_after)
                response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"Meta WhatsApp message sent successfully: {response_data}")
            
            return True, "Message sent successfully", response_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Meta WhatsApp API request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
        except Exception as e:
            error_msg = f"Unexpected error sending Meta WhatsApp message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}

    def get_template_details(self, template_id: str) -> Tuple[bool, Dict, str]:
        """
        Get detailed information about a specific template
        
        Args:
            template_id: ID of the template
            
        Returns:
            Tuple of (success, template_data, error_message)
        """
        try:
            url = f"{self.base_url}/{template_id}"
            params = {
                'fields': 'name,status,id,category,language,components'
            }
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            template_data = response.json()
            return True, template_data, "Template details fetched successfully"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Meta WhatsApp API request failed: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error fetching template details: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
