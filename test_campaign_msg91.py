#!/usr/bin/env python3
"""
Test MSG91 integration through the actual campaign system
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joshCampaigns.settings')
django.setup()

from outreach.models import Campaign, Customer, Message, MessageTemplate
from django.contrib.auth.models import User
from outreach.tasks import send_campaign_messages

def test_campaign_msg91():
    """Test MSG91 integration through campaign system"""
    
    print("🚀 Testing MSG91 Integration Through Campaign System")
    print("=" * 60)
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='testuser_msg91',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Get or create test customer
        customer, created = Customer.objects.get_or_create(
            email='avivish000@gmail.com',
            defaults={
                'name': 'MSG91 Test Customer',
                'phone': '+1234567890'
            }
        )
        
        if created:
            print(f"✅ Created test customer: {customer.name}")
        else:
            print(f"✅ Using existing test customer: {customer.name}")
        
        # Get or create test template
        template, created = MessageTemplate.objects.get_or_create(
            external_id='global_otp',
            defaults={
                'name': 'Global OTP Template',
                'channel': 'email',
                'provider': 'msg91-email',
                'subject': 'Your OTP Code',
                'content': 'Hello {{name}}, your OTP is {{otp}} from {{company_name}}.',
                'created_by': user
            }
        )
        
        if created:
            print(f"✅ Created test template: {template.name}")
        else:
            print(f"✅ Using existing test template: {template.name}")
        
        # Create test campaign
        campaign = Campaign.objects.create(
            name='MSG91 Integration Test Campaign',
            channel='email',
            provider='msg91-email',
            subject='MSG91 Integration Test',
            content='Hello {{name}}, this is a test campaign via MSG91.',
            template=template,
            created_by=user
        )
        
        # Add customer to campaign
        campaign.customers.add(customer)
        
        print(f"✅ Created test campaign: {campaign.name}")
        print(f"   📧 Channel: {campaign.channel}")
        print(f"   🔧 Provider: {campaign.provider}")
        print(f"   👥 Customers: {campaign.customers.count()}")
        print(f"   📋 Template: {campaign.template.name if campaign.template else 'None'}")
        
        print()
        print("📤 Sending campaign messages...")
        
        # Send campaign messages
        result = send_campaign_messages(str(campaign.id))
        
        print(f"📊 Campaign Result: {result}")
        
        if result.get('success'):
            print("✅ Campaign sent successfully!")
            print(f"   📧 Success: {result.get('success_count', 0)}")
            print(f"   ❌ Failures: {result.get('failure_count', 0)}")
            
            # Check message status
            messages = Message.objects.filter(campaign=campaign)
            for msg in messages:
                print(f"   📨 Message to {msg.customer.email}: {msg.status}")
                if msg.error_message:
                    print(f"      Error: {msg.error_message}")
        else:
            print(f"❌ Campaign failed: {result.get('error', 'Unknown error')}")
        
        print()
        print("=" * 60)
        print("🎯 Campaign MSG91 Integration Test Complete!")
        print("=" * 60)
        
        # Cleanup (optional)
        # campaign.delete()
        # template.delete()
        # customer.delete()
        # user.delete()
        
    except Exception as e:
        print(f"💥 Error testing campaign MSG91 integration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_campaign_msg91()
