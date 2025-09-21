#!/usr/bin/env python3
"""
WhatsApp Setup Diagnostic Tool
Helps troubleshoot why messages aren't being received
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

from django.conf import settings
import requests
import json

def check_configuration():
    """Check current configuration status"""
    print("🔍 WhatsApp Configuration Diagnostic")
    print("=" * 50)
    
    config = {
        'Access Token': getattr(settings, 'META_WHATSAPP_ACCESS_TOKEN', ''),
        'Business Account ID': getattr(settings, 'META_WHATSAPP_BUSINESS_ACCOUNT_ID', ''),
        'Phone Number ID': getattr(settings, 'META_WHATSAPP_PHONE_NUMBER_ID', ''),
        'API Version': getattr(settings, 'META_WHATSAPP_API_VERSION', ''),
    }
    
    print("\n📋 Current Configuration:")
    for key, value in config.items():
        if value:
            if 'your_' in str(value) or value == '':
                print(f"  ❌ {key}: {value} (PLACEHOLDER - NEEDS REAL VALUE)")
            else:
                print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: Not set")
    
    return config

def test_api_connection(access_token, business_account_id):
    """Test if the API credentials work"""
    print(f"\n🌐 Testing API Connection...")
    
    if not access_token or 'your_' in str(access_token):
        print("  ❌ Cannot test - Access token is placeholder")
        return False
    
    try:
        # Test with a simple API call
        url = f"https://graph.facebook.com/v23.0/{business_account_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("  ✅ API connection successful!")
            data = response.json()
            print(f"  📊 Business Account: {data.get('name', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print("  ❌ API connection failed - Invalid access token")
            return False
        else:
            print(f"  ❌ API connection failed - Status: {response.status_code}")
            print(f"  📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ API connection failed - Error: {str(e)}")
        return False

def test_phone_number_access(access_token, phone_number_id):
    """Test if we can access the phone number"""
    print(f"\n📱 Testing Phone Number Access...")
    
    if not phone_number_id or 'your_' in str(phone_number_id):
        print("  ❌ Cannot test - Phone number ID is placeholder")
        return False
    
    try:
        url = f"https://graph.facebook.com/v23.0/{phone_number_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("  ✅ Phone number access successful!")
            data = response.json()
            print(f"  📊 Phone Number: {data.get('display_phone_number', 'Unknown')}")
            print(f"  📊 Status: {data.get('status', 'Unknown')}")
            return True
        else:
            print(f"  ❌ Phone number access failed - Status: {response.status_code}")
            print(f"  📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Phone number access failed - Error: {str(e)}")
        return False

def test_send_message(access_token, phone_number_id, recipient_phone):
    """Test sending a message"""
    print(f"\n📤 Testing Message Send...")
    print(f"  📱 To: {recipient_phone}")
    
    if not phone_number_id or 'your_' in str(phone_number_id):
        print("  ❌ Cannot test - Phone number ID is placeholder")
        return False
    
    try:
        url = f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Use hello_world template (most basic)
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_phone.replace('+', ''),
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {
                    "code": "en_US"
                }
            }
        }
        
        print(f"  📝 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("  ✅ Message sent successfully!")
            data = response.json()
            print(f"  📊 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"  ❌ Message send failed - Status: {response.status_code}")
            print(f"  📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Message send failed - Error: {str(e)}")
        return False

def get_setup_instructions():
    """Provide setup instructions"""
    print(f"\n📚 Setup Instructions")
    print("=" * 50)
    print("""
To get WhatsApp working, you need to:

1. 🌐 Go to https://business.facebook.com/
2. 📱 Create a WhatsApp Business Account
3. 🔑 Get your credentials:
   - Access Token (from WhatsApp API)
   - Business Account ID (from your business account)
   - Phone Number ID (for +1 555 191 6249)

4. 📝 Update your .env file with REAL values:
   META_WHATSAPP_ACCESS_TOKEN=your_real_access_token
   META_WHATSAPP_BUSINESS_ACCOUNT_ID=your_real_business_account_id  
   META_WHATSAPP_PHONE_NUMBER_ID=your_real_phone_number_id

5. 📋 Create message templates in your WhatsApp Business account
   - Go to WhatsApp Manager
   - Create templates like "hello_world"
   - Wait for approval

6. 🧪 Test again with this script
""")

def main():
    """Main diagnostic function"""
    print("🚀 WhatsApp Setup Diagnostic Tool")
    print("This will help you troubleshoot why messages aren't being received")
    
    # Check configuration
    config = check_configuration()
    
    # Test API connection
    if config['Access Token'] and config['Business Account ID']:
        api_works = test_api_connection(config['Access Token'], config['Business Account ID'])
        
        if api_works and config['Phone Number ID']:
            phone_works = test_phone_number_access(config['Access Token'], config['Phone Number ID'])
            
            if phone_works:
                # Try to send a test message
                test_send_message(config['Access Token'], config['Phone Number ID'], "+916205321307")
    
    # Show setup instructions
    get_setup_instructions()
    
    print(f"\n💡 Quick Fix:")
    print("The main issue is that you're using placeholder credentials.")
    print("You need to get real credentials from your WhatsApp Business account.")
    print("Once you have them, update the .env file and run this script again.")

if __name__ == "__main__":
    main()

