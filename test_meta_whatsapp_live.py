#!/usr/bin/env python3
"""
Live test script for Meta WhatsApp Cloud API integration
Using actual phone numbers: +1 555 191 6249 (sender) and +91 6205321307 (recipient)
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joshCampaigns.settings')
django.setup()

from outreach.meta_whatsapp_service import MetaWhatsAppService
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_live_integration():
    """Test Meta WhatsApp integration with live phone numbers"""
    print("🚀 Meta WhatsApp Live Integration Test")
    print("="*60)
    print("Sender Number: +1 555 191 6249")
    print("Recipient Number: +91 6205321307")
    print("="*60)
    
    service = MetaWhatsAppService()
    
    # Test 1: List Templates
    print("\n1. 📋 Fetching Available Templates...")
    success, templates, message = service.get_message_templates(limit=10, status='APPROVED')
    
    if success:
        print(f"✅ Success: {message}")
        print(f"📊 Found {len(templates)} approved templates")
        
        if templates:
            print("\n📋 Available Templates:")
            for i, template in enumerate(templates[:5], 1):  # Show first 5
                print(f"  {i}. {template.get('name', 'N/A')} ({template.get('status', 'N/A')})")
                print(f"     Category: {template.get('category', 'N/A')}")
                print(f"     Language: {template.get('language', 'N/A')}")
                
                # Show body component if available
                components = template.get('components', [])
                for comp in components:
                    if comp.get('type') == 'BODY':
                        body_text = comp.get('text', '')
                        print(f"     Body: {body_text[:100]}{'...' if len(body_text) > 100 else ''}")
                print()
        else:
            print("⚠️  No approved templates found")
    else:
        print(f"❌ Failed to fetch templates: {message}")
        return
    
    # Test 2: Send Test Message
    print("\n2. 📱 Sending Test Message...")
    recipient_phone = "+916205321307"  # Your recipient number
    
    # Try to send with the first available template
    if templates:
        template_name = templates[0].get('name')
        print(f"Using template: {template_name}")
        
        # Prepare parameters based on template
        parameters = []
        components = templates[0].get('components', [])
        for comp in components:
            if comp.get('type') == 'BODY':
                body_text = comp.get('text', '')
                # Extract variables from template
                import re
                variables = re.findall(r'\{\{(\w+)\}\}', body_text)
                for var in variables:
                    if var == 'name':
                        parameters.append('Test User')
                    elif var == 'company_name':
                        parameters.append('Josh Campaigns')
                    elif var == 'otp':
                        parameters.append('123456')
                    elif var == 'discount':
                        parameters.append('25%')
                    elif var == 'coupon_code':
                        parameters.append('TEST123')
                    elif var == 'expiry_date':
                        parameters.append('2024-12-31')
                    else:
                        parameters.append(f'Test {var}')
                break
        
        print(f"Template parameters: {parameters}")
        
        success, response_msg, response_data = service.send_message(
            to_phone=recipient_phone,
            template_name=template_name,
            language_code='en_US',
            parameters=parameters if parameters else None
        )
        
        if success:
            print(f"✅ Message sent successfully!")
            print(f"📊 Response: {response_msg}")
            if response_data:
                print(f"📋 Response Data:")
                print(json.dumps(response_data, indent=2))
        else:
            print(f"❌ Failed to send message: {response_msg}")
    else:
        print("⚠️  No templates available for testing")
    
    # Test 3: Send Simple Message (if hello_world template exists)
    print("\n3. 📱 Sending Simple Test Message...")
    simple_templates = [t for t in templates if t.get('name') == 'hello_world']
    
    if simple_templates:
        success, response_msg, response_data = service.send_message(
            to_phone=recipient_phone,
            template_name='hello_world',
            language_code='en_US',
            parameters=None
        )
        
        if success:
            print(f"✅ Simple message sent successfully!")
            print(f"📊 Response: {response_msg}")
        else:
            print(f"❌ Failed to send simple message: {response_msg}")
    else:
        print("⚠️  hello_world template not found, skipping simple test")

def check_configuration():
    """Check if Meta WhatsApp is properly configured"""
    print("🔧 Checking Configuration...")
    
    from django.conf import settings
    
    config_status = {
        'Access Token': bool(settings.META_WHATSAPP_ACCESS_TOKEN),
        'Business Account ID': bool(settings.META_WHATSAPP_BUSINESS_ACCOUNT_ID),
        'Phone Number ID': bool(settings.META_WHATSAPP_PHONE_NUMBER_ID),
        'API Version': settings.META_WHATSAPP_API_VERSION
    }
    
    print("\nConfiguration Status:")
    for key, value in config_status.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")
    
    if not all([config_status['Access Token'], config_status['Business Account ID']]):
        print("\n⚠️  Warning: Missing required configuration!")
        print("Please update your .env file with:")
        print("  META_WHATSAPP_ACCESS_TOKEN=your_access_token")
        print("  META_WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id")
        print("  META_WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id")
        return False
    
    return True

def main():
    """Main test function"""
    try:
        # Check configuration first
        if not check_configuration():
            print("\n❌ Configuration check failed. Please fix the issues above.")
            return
        
        # Run live integration test
        test_live_integration()
        
        print("\n" + "="*60)
        print("✅ LIVE TEST COMPLETED")
        print("="*60)
        print("Check your phone (+91 6205321307) for WhatsApp messages!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

