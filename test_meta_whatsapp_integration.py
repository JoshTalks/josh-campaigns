#!/usr/bin/env python3
"""
Test script for Meta WhatsApp Cloud API integration
Tests the two core functionalities: sending messages and listing templates
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

def test_list_templates():
    """Test listing WhatsApp message templates"""
    print("\n" + "="*60)
    print("TESTING: List WhatsApp Message Templates")
    print("="*60)
    
    service = MetaWhatsAppService()
    
    # Test 1: Get all approved templates
    print("\n1. Fetching approved templates...")
    success, templates, message = service.get_message_templates(limit=10, status='APPROVED')
    
    if success:
        print(f"✅ Success: {message}")
        print(f"📊 Found {len(templates)} approved templates")
        
        if templates:
            print("\n📋 Template Details:")
            for i, template in enumerate(templates[:3], 1):  # Show first 3
                print(f"\n{i}. Template: {template.get('name', 'N/A')}")
                print(f"   ID: {template.get('id', 'N/A')}")
                print(f"   Status: {template.get('status', 'N/A')}")
                print(f"   Category: {template.get('category', 'N/A')}")
                print(f"   Language: {template.get('language', 'N/A')}")
                
                # Show components
                components = template.get('components', [])
                if components:
                    print(f"   Components:")
                    for comp in components:
                        comp_type = comp.get('type', 'N/A')
                        comp_text = comp.get('text', 'N/A')
                        print(f"     - {comp_type}: {comp_text[:50]}{'...' if len(comp_text) > 50 else ''}")
        else:
            print("⚠️  No templates found")
    else:
        print(f"❌ Failed: {message}")
    
    # Test 2: Get all templates (any status)
    print("\n2. Fetching all templates (any status)...")
    success, templates, message = service.get_message_templates(limit=10, status='ALL')
    
    if success:
        print(f"✅ Success: {message}")
        print(f"📊 Found {len(templates)} total templates")
        
        # Group by status
        status_counts = {}
        for template in templates:
            status = template.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\n📊 Templates by Status:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
    else:
        print(f"❌ Failed: {message}")

def test_send_message():
    """Test sending a WhatsApp message"""
    print("\n" + "="*60)
    print("TESTING: Send WhatsApp Message")
    print("="*60)
    
    service = MetaWhatsAppService()
    
    # Test phone number (replace with a valid number for testing)
    test_phone = "+916205321307"  # Your recipient number
    template_name = "hello_world"  # Use a simple template
    
    print(f"\n📱 Sending test message to: {test_phone}")
    print(f"📝 Using template: {template_name}")
    
    # Test 1: Send message without parameters
    print("\n1. Sending message without parameters...")
    success, message, response_data = service.send_message(
        to_phone=test_phone,
        template_name=template_name,
        language_code='en_US',
        parameters=None
    )
    
    if success:
        print(f"✅ Success: {message}")
        if response_data:
            print(f"📊 Response data: {json.dumps(response_data, indent=2)}")
    else:
        print(f"❌ Failed: {message}")
    
    # Test 2: Send message with parameters
    print("\n2. Sending message with parameters...")
    test_params = ["John", "25%", "SAVE25", "2024-12-31"]
    
    success, message, response_data = service.send_message(
        to_phone=test_phone,
        template_name="seasonal_promotion_text_only",  # Use a template that accepts parameters
        language_code='en_US',
        parameters=test_params
    )
    
    if success:
        print(f"✅ Success: {message}")
        if response_data:
            print(f"📊 Response data: {json.dumps(response_data, indent=2)}")
    else:
        print(f"❌ Failed: {message}")

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "="*60)
    print("TESTING: Error Handling")
    print("="*60)
    
    service = MetaWhatsAppService()
    
    # Test 1: Invalid phone number
    print("\n1. Testing invalid phone number...")
    success, message, response_data = service.send_message(
        to_phone="invalid_phone",
        template_name="hello_world",
        language_code='en_US'
    )
    
    if not success:
        print(f"✅ Correctly handled invalid phone: {message}")
    else:
        print(f"⚠️  Unexpected success with invalid phone: {message}")
    
    # Test 2: Non-existent template
    print("\n2. Testing non-existent template...")
    success, message, response_data = service.send_message(
        to_phone="+1234567890",
        template_name="non_existent_template",
        language_code='en_US'
    )
    
    if not success:
        print(f"✅ Correctly handled non-existent template: {message}")
    else:
        print(f"⚠️  Unexpected success with non-existent template: {message}")

def main():
    """Main test function"""
    print("🚀 Meta WhatsApp Cloud API Integration Test")
    print("Based on: https://developers.facebook.com/docs/whatsapp/cloud-api")
    
    try:
        # Test 1: List templates
        test_list_templates()
        
        # Test 2: Send messages
        test_send_message()
        
        # Test 3: Error handling
        test_error_handling()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
