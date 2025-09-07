#!/usr/bin/env python3
"""
Test script for the updated MSG91 service using the working configuration

This script demonstrates how to use the updated send_email and send_template_email methods
that now use the same working configuration as test_msg91_simple.py
"""

import os
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joshCampaigns.settings')

import django
django.setup()

from outreach.msg91_service import MSG91EmailService

def test_updated_service():
    """Test the updated MSG91 service methods"""
    
    print("🚀 Testing Updated MSG91 Service")
    print("=" * 50)
    
    # Create service instance
    service = MSG91EmailService()
    
    # Test 1: Send regular email
    print("\n📧 Test 1: Sending Regular Email")
    print("-" * 30)
    
    success, message = service.send_email(
        to_email="avivish000@gmail.com",
        subject="Test from Updated Service",
        content="<h1>Hello from Updated Service!</h1><p>This email was sent using the updated MSG91 service.</p>",
        customer_name="Avi",
        is_html=True
    )
    
    if success:
        print("✅ Regular email sent successfully!")
    else:
        print(f"❌ Regular email failed: {message}")
    
    # Test 2: Send template email
    print("\n📧 Test 2: Sending Template Email")
    print("-" * 30)
    
    success, message = service.send_template_email(
        to_email="avivish000@gmail.com",
        customer_name="Avi",
        template_id="global_otp",
        variables={
            "company_name": "Josh Talks",
            "otp": "123456"
        }
    )
    
    if success:
        print("✅ Template email sent successfully!")
    else:
        print(f"❌ Template email failed: {message}")
    
    # Test 3: Send bulk emails (single API call)
    print("\n📧 Test 3: Sending Bulk Emails (Single API Call)")
    print("-" * 50)
    
    bulk_emails = [
        {
            'to_email': 'avivish000@gmail.com',
            'subject': 'Bulk Test 1',
            'content': '<h1>Bulk Test 1</h1><p>First bulk email test.</p>',
            'customer_name': 'Avi',
            'is_html': True
        },
        {
            'to_email': 'avikumar@joshtalks.com',
            'subject': 'Bulk Test 2',
            'content': '<h1>Bulk Test 2</h1><p>Second bulk email test.</p>',
            'customer_name': 'Avi Kumar',
            'is_html': True
        }
    ]
    
    results = service.send_bulk_emails(bulk_emails)
    print(f"📊 Bulk email results: {results['success']} success, {results['failed']} failed")
    
    if results['errors']:
        print("❌ Errors encountered:")
        for error in results['errors']:
            print(f"   - {error['email']}: {error['error']}")
    
    # Test 4: Send bulk template emails (exactly like test_msg91_simple.py)
    print("\n📧 Test 4: Sending Bulk Template Emails (Like Working Test)")
    print("-" * 60)
    
    bulk_template_recipients = [
        {
            'name': 'Avi',
            'email': 'avivish000@gmail.com',
            'variables': {
                'company_name': 'Josh Talks',
                'otp': '123456'
            },
            'template_id': 'global_otp'
        },
        {
            'name': 'Avi Kumar',
            'email': 'avikumar@joshtalks.com',
            'variables': {
                'company_name': 'Josh Jobs',
                'otp': '654321'
            },
            'template_id': 'global_otp'
        }
    ]
    
    success, message = service.send_bulk_template_emails(bulk_template_recipients)
    if success:
        print("✅ Bulk template emails sent successfully!")
        print(f"   📧 Sent to: {len(bulk_template_recipients)} recipients")
    else:
        print(f"❌ Bulk template emails failed: {message}")
    
    print("\n" + "=" * 50)
    print("🎯 Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_updated_service()
