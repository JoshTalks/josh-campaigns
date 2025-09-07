#!/usr/bin/env python3
"""
Test MSG91 service through Django application context
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joshCampaigns.settings')
django.setup()

from outreach.msg91_service import MSG91EmailService

def test_msg91_through_django():
    """Test MSG91 service through Django"""
    
    print("🚀 Testing MSG91 Service Through Django Application")
    print("=" * 60)
    
    try:
        # Create service instance
        service = MSG91EmailService()
        
        print(f"🔑 Auth Key: {service.auth_key[:8]}...{service.auth_key[-4:]}")
        print(f"📤 From: {service.from_name} <{service.from_email}>")
        print(f"🌐 Domain: joshjobs.joshtalks.com")
        print()
        
        # Test 1: Connection test
        print("📧 Test 1: MSG91 Connection Test")
        print("-" * 40)
        
        success, message = service.test_connection()
        if success:
            print(f"✅ Connection successful: {message}")
        else:
            print(f"❌ Connection failed: {message}")
            return
        
        print()
        
        # Test 2: Send template email
        print("📧 Test 2: Send Template Email")
        print("-" * 40)
        
        success, message = service.send_template_email(
            to_email="avivish000@gmail.com",
            customer_name="Django Test User",
            template_id="global_otp",
            variables={
                "company_name": "Josh Talks",
                "otp": "123456"
            }
        )
        
        if success:
            print(f"✅ Template email sent successfully: {message}")
        else:
            print(f"❌ Template email failed: {message}")
        
        print()
        
        # Test 3: Send bulk template emails
        print("📧 Test 3: Send Bulk Template Emails")
        print("-" * 40)
        
        success, message = service.send_bulk_template_emails([
            {
                'name': 'Django Test User 1',
                'email': 'avivish000@gmail.com',
                'variables': {
                    'company_name': 'Josh Talks',
                    'otp': '123456'
                },
                'template_id': 'global_otp'
            },
            {
                'name': 'Django Test User 2',
                'email': 'avikumar@joshtalks.com',
                'variables': {
                    'company_name': 'Josh Jobs',
                    'otp': '654321'
                },
                'template_id': 'global_otp'
            }
        ])
        
        if success:
            print(f"✅ Bulk template emails sent successfully: {message}")
        else:
            print(f"❌ Bulk template emails failed: {message}")
        
        print()
        print("=" * 60)
        print("🎯 Django MSG91 Service Test Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"💥 Error testing MSG91 service: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_msg91_through_django()
