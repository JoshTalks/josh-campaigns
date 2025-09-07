#!/usr/bin/env python3
"""
Debug script for regular email sending to see exact error responses
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
import json

def debug_regular_email():
    """Debug regular email sending to see exact error responses"""
    
    print("🔍 Debugging Regular Email Sending")
    print("=" * 50)
    
    # Create service instance
    service = MSG91EmailService()
    
    # Test regular email payload
    print("\n📧 Testing Regular Email Payload")
    print("-" * 40)
    
    payload = {
        "recipients": [
            {
                "to": [
                    {
                        "name": "Avi",
                        "email": "avivish000@gmail.com"
                    }
                ]
            }
        ],
        "from": {
            "name": "Josh2",
            "email": "developers@joshtalks.com"
        },
        "domain": "joshjobs.joshtalks.com",
        "subject": "Test Regular Email",
        "body": {
            "data": "<h1>Test Regular Email</h1><p>This is a test regular email.</p>",
            "type": "text/html"
        }
    }
    
    headers = {
        'accept': "application/json",
        'authkey': service.auth_key,
        'content-type': "application/JSON"
    }
    
    print(f"🔑 Auth Key: {service.auth_key[:8]}...{service.auth_key[-4:]}")
    print(f"📤 From: {service.from_name} <{service.from_email}>")
    print(f"🌐 Domain: joshjobs.joshtalks.com")
    print(f"📋 Subject: Test Regular Email")
    
    print("\n📤 Sending regular email request...")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
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
    debug_regular_email()
