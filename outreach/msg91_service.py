import requests
import json
import logging
from django.conf import settings
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MSG91EmailService:
    """
    Service class for sending emails through MSG91 API
    """
    
    def __init__(self):
        self.auth_key = settings.MSG91_AUTH_KEY
        self.base_url = settings.MSG91_EMAIL_ENDPOINT
        # Use the working configuration values from test_msg91_simple.py
        self.from_email = "developers@joshtalks.com"  # Working email
        self.from_name = "Josh2"  # Working name
        self.headers = {
            'accept': "application/json",
            'authkey': self.auth_key,
            'content-type': "application/JSON"
        }
    
    def send_email(self, to_email: str, subject: str, content: str, 
                   customer_name: str = None, is_html: bool = True, 
                   template_id: str = None, variables: dict = None) -> Tuple[bool, str]:
        """
        Send a single email through MSG91 using the working configuration
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (HTML or plain text)
            customer_name: Customer name for personalization
            is_html: Whether content is HTML format
            template_id: MSG91 template ID (required for MSG91)
            variables: Template variables (required when using template_id)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # MSG91 requires template_id for all emails
            if not template_id:
                return False, "MSG91 requires template_id for all emails. Please use send_template_email() or provide a template_id."
            
            if not variables:
                return False, "Template variables are required when using template_id. Please provide variables."
            
            # Use the working payload structure from test_msg91_simple.py
            payload = {
                "recipients": [
                    {
                        "to": [
                            {
                                "name": customer_name or "Customer",
                                "email": to_email
                            }
                        ],
                        "variables": variables
                    }
                ],
                "from": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "domain": "joshjobs.joshtalks.com",  # Working domain
                "template_id": template_id
            }
            
            # Send email using the working configuration
            response = requests.post(
                "https://control.msg91.com/api/v5/email/send",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' or result.get('hasError') == False:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True, "Email sent successfully"
                else:
                    error_msg = result.get('message', 'Unknown error from MSG91')
                    logger.error(f"MSG91 API error: {error_msg}")
                    return False, f"MSG91 API error: {error_msg}"
            else:
                logger.error(f"MSG91 API request failed with status {response.status_code}")
                return False, f"API request failed with status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending email to {to_email}: {str(e)}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"
    
    def send_bulk_emails(self, emails_data: List[Dict]) -> Dict:
        """
        Send bulk emails through MSG91 in a single API call (like test_msg91_simple.py)
        
        Args:
            emails_data: List of dictionaries with email details
                [{'to_email': 'email@example.com', 'subject': 'Subject', 'content': 'Content', 
                  'customer_name': 'Name', 'template_id': 'template_id', 'variables': {}}]
        
        Returns:
            Dictionary with results summary
        """
        try:
            if not emails_data:
                return {'total': 0, 'success': 0, 'failed': 0, 'errors': []}
            
            # Check if all emails use the same template
            template_id = emails_data[0].get('template_id')
            use_template = all(email.get('template_id') == template_id for email in emails_data)
            
            if template_id and use_template:
                # For template emails, use the working structure from test_msg91_simple.py
                recipients = []
                for email_data in emails_data:
                    recipient = {
                        "to": [
                            {
                                "name": email_data.get('customer_name', 'Customer'),
                                "email": email_data['to_email']
                            }
                        ],
                        "variables": email_data.get('variables', {})
                    }
                    recipients.append(recipient)
                
                payload = {
                    "recipients": recipients,
                    "from": {
                        "name": self.from_name,
                        "email": self.from_email
                    },
                    "domain": "joshjobs.joshtalks.com",  # Working domain
                    "template_id": template_id
                }
            else:
                # For regular emails, MSG91 doesn't support individual content per recipient in bulk
                # So we'll send them individually
                logger.info(f"Mixed or regular emails detected, sending individually to {len(emails_data)} recipients")
                
                results = {
                    'total': len(emails_data),
                    'success': 0,
                    'failed': 0,
                    'errors': []
                }
                
                for email_data in emails_data:
                    success, message = self.send_email(
                        to_email=email_data['to_email'],
                        subject=email_data['subject'],
                        content=email_data['content'],
                        customer_name=email_data.get('customer_name'),
                        is_html=email_data.get('is_html', True)
                    )
                    
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'email': email_data['to_email'],
                            'error': message
                        })
                
                logger.info(f"Individual bulk email sending completed: {results['success']} success, {results['failed']} failed")
                return results
            
            logger.info(f"Sending bulk template email to {len(emails_data)} recipients")
            
            # Send bulk template email using the working configuration
            response = requests.post(
                "https://control.msg91.com/api/v5/email/send",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' or result.get('hasError') == False:
                    logger.info(f"Bulk template email sent successfully to {len(emails_data)} recipients")
                    return {
                        'total': len(emails_data),
                        'success': len(emails_data),
                        'failed': 0,
                        'errors': []
                    }
                else:
                    error_msg = result.get('message', 'Unknown error from MSG91')
                    logger.error(f"MSG91 bulk template API error: {error_msg}")
                    return {
                        'total': len(emails_data),
                        'success': 0,
                        'failed': len(emails_data),
                        'errors': [{'email': 'bulk_request', 'error': error_msg}]
                    }
            else:
                logger.error(f"MSG91 bulk template API request failed with status {response.status_code}")
                return {
                    'total': len(emails_data),
                    'success': 0,
                    'failed': len(emails_data),
                    'errors': [{'email': 'bulk_request', 'error': f'API failed with status {response.status_code}'}]
                }
                
        except Exception as e:
            logger.error(f"Unexpected error sending bulk emails: {str(e)}")
            return {
                'total': len(emails_data),
                'success': 0,
                'failed': len(emails_data),
                'errors': [{'email': 'bulk_request', 'error': str(e)}]
            }
    
    def send_template_email(self, to_email: str, customer_name: str, 
                           template_id: str, variables: dict) -> Tuple[bool, str]:
        """
        Send email using MSG91 template (based on working test configuration)
        
        Args:
            to_email: Recipient email address
            customer_name: Customer name for personalization
            template_id: MSG91 template ID
            variables: Template variables dictionary
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Use the exact working payload structure from test_msg91_simple.py
            payload = {
                "recipients": [
                    {
                        "to": [
                            {
                                "name": customer_name or "Customer",
                                "email": to_email
                            }
                        ],
                        "variables": variables
                    }
                ],
                "from": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "domain": "joshjobs.joshtalks.com",  # Working domain
                "template_id": template_id
            }
            
            print(f"Sending template email to {to_email} using template {template_id}")
            print(f"MSG91 API Request URL: https://control.msg91.com/api/v5/email/send")
            print(f"MSG91 API Request Headers: {self.headers}")
            print(f"MSG91 API Request Body: {json.dumps(payload, indent=2)}")
            
            # Send email using the working configuration
            response = requests.post(
                "https://control.msg91.com/api/v5/email/send",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"MSG91 API Response Status: {response.status_code}")
            print(f"MSG91 API Response Body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' or result.get('hasError') == False:
                    logger.info(f"Template email sent successfully to {to_email}")
                    return True, "Template email sent successfully"
                else:
                    error_msg = result.get('message', 'Unknown error from MSG91')
                    logger.error(f"MSG91 template API error: {error_msg}")
                    return False, f"MSG91 template API error: {error_msg}"
            else:
                logger.error(f"MSG91 template API request failed with status {response.status_code}")
                return False, f"Template API request failed with status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending template email to {to_email}: {str(e)}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error sending template email to {to_email}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"
    
    def send_bulk_template_emails(self, recipients_data: List[Dict]) -> Tuple[bool, str]:
        """
        Send bulk template emails through MSG91 (exactly like test_msg91_simple.py)
        
        Args:
            recipients_data: List of dictionaries with recipient details
                [{'name': 'Customer Name', 'email': 'email@example.com', 'variables': {}}]
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not recipients_data:
                return False, "No recipients provided"
            
            # Use the exact working payload structure from test_msg91_simple.py
            recipients = []
            for recipient_data in recipients_data:
                recipient = {
                    "to": [
                        {
                            "name": recipient_data.get('name', 'Customer'),
                            "email": recipient_data['email']
                        }
                    ],
                    "variables": recipient_data.get('variables', {})
                }
                recipients.append(recipient)
            
            payload = {
                "recipients": recipients,
                "from": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "domain": "joshjobs.joshtalks.com",  # Working domain
                "template_id": recipients_data[0].get('template_id')  # All should use same template
            }
            
            logger.info(f"Sending bulk template email to {len(recipients_data)} recipients")
            
            # Send email using the working configuration
            response = requests.post(
                "https://control.msg91.com/api/v5/email/send",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' or result.get('hasError') == False:
                    logger.info(f"Bulk template email sent successfully to {len(recipients_data)} recipients")
                    return True, f"Bulk template email sent successfully to {len(recipients_data)} recipients"
                else:
                    error_msg = result.get('message', 'Unknown error from MSG91')
                    logger.error(f"MSG91 bulk template API error: {error_msg}")
                    return False, f"MSG91 bulk template API error: {error_msg}"
            else:
                logger.error(f"MSG91 bulk template API request failed with status {response.status_code}")
                return False, f"Bulk template API request failed with status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending bulk template emails: {str(e)}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error sending bulk template emails: {str(e)}")
            return False, f"Unexpected error: {str(e)}"
    
    def get_templates(self, page: int = 1, per_page: int = 25) -> Tuple[bool, List[Dict]]:
        """
        Get email templates from MSG91
        
        Args:
            page: Page number for pagination
            per_page: Number of templates per page
            
        Returns:
            Tuple of (success: bool, templates: List[Dict])
        """
        try:
            params = {
                'page': page,
                'per_page': per_page,
                'with': 'versions',
                'keyword': '',
                'search_in': 'name',
                'status_id': 2  # Active templates
            }
            
            response = requests.get(
                f"{self.base_url}/templates",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':  # Changed from 'type' to 'status'
                    templates = result.get('data', {}).get('data', [])  # Changed from 'templates' to 'data'
                    logger.info(f"Retrieved {len(templates)} email templates from MSG91")
                    return True, templates
                else:
                    error_msg = result.get('message', 'Unknown error from MSG91')
                    logger.error(f"MSG91 API error getting templates: {error_msg}")
                    return False, []
            else:
                logger.error(f"MSG91 API request failed with status {response.status_code}")
                return False, []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting templates: {str(e)}")
            return False, []
        except Exception as e:
            logger.error(f"Unexpected error getting templates: {str(e)}")
            return False, []
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test MSG91 API connection by getting templates
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, templates = self.get_templates(page=1, per_page=1)
        if success:
            return True, "MSG91 API connection successful"
        else:
            return False, "MSG91 API connection failed"
