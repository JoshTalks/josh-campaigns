#!/usr/bin/env python3
"""
Debug script for MSG91 service to see exact error responses
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
import requests

def debug_msg91_service():
    """Debug the MSG91 service to see exact error responses"""
    
    print("🔍 Debugging MSG91 Service")
    print("=" * 50)
    
    # Create service instance
    service = MSG91EmailService()
    
    # Test the exact working payload from test_msg91_simple.py
    print("\n📧 Testing with exact working payload structure")
    print("-" * 50)
    
    payload = {
        "recipients": [
            {
                "to": [
                    {
                        "name": "Avi",
                        "email": "avivish000@gmail.com"
                    }
                ],
                "variables": {
                    "company_name": "Avu",
                    "otp": "1234"
                }
            }
        ],
        "from": {
            "name": "Josh2",
            "email": "developers@joshtalks.com"
        },
        "domain": "joshjobs.joshtalks.com",
        "template_id": "global_otp"
    }
    
    headers = {
        'accept': "application/json",
        'authkey': service.auth_key,
        'content-type': "application/JSON"
    }
    
    print(f"🔑 Auth Key: {service.auth_key[:8]}...{service.auth_key[-4:]}")
    print(f"📤 From: {service.from_name} <{service.from_email}>")
    print(f"🌐 Domain: {getattr(service, 'domain', 'Not set')}")
    print(f"📋 Template ID: global_otp")
    
    print("\n📤 Sending request...")
    
    try:
        response = requests.post(
            "https://control.msg91.com/api/v5/email/send",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Result: {result}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"💥 Exception: {str(e)}")

if __name__ == "__main__":
    debug_msg91_service()
