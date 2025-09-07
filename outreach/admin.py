from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.contrib import messages
from .models import Customer, MessageTemplate, Campaign, CampaignCustomer, Message, VendorTemplate
from .msg91_service import MSG91EmailService

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['id', 'created_at']

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'created_by', 'created_at']
    list_filter = ['channel', 'created_at']
    search_fields = ['name', 'content']
    readonly_fields = ['id', 'created_at']

@admin.register(VendorTemplate)
class VendorTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'provider', 'status', 'is_approved', 'created_at']
    list_filter = ['channel', 'provider', 'status', 'is_approved', 'created_at']
    search_fields = ['name', 'external_id', 'content']
    readonly_fields = ['id', 'created_at']

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'provider', 'status', 'created_by', 'created_at']
    list_filter = ['channel', 'provider', 'status', 'created_at']
    search_fields = ['name', 'content']
    readonly_fields = ['id', 'created_at']
    filter_horizontal = ['customers']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:campaign_id>/test-msg91/',
                self.admin_site.admin_view(self.test_msg91_integration),
                name='outreach_campaign_test_msg91',
            ),
        ]
        return custom_urls + urls
    
    actions = ['test_msg91_integration_bulk']
    
    def test_msg91_integration_bulk(self, request, queryset):
        """Test MSG91 integration for selected campaigns"""
        msg91_campaigns = queryset.filter(provider='msg91-email', channel='email')
        
        if not msg91_campaigns.exists():
            messages.warning(request, 'No MSG91 email campaigns selected for testing')
            return
        
        msg91_service = MSG91EmailService()
        success, message = msg91_service.test_connection()
        
        if success:
            messages.success(request, f'MSG91 integration test successful: {message}')
        else:
            messages.error(request, f'MSG91 integration test failed: {message}')
    
    test_msg91_integration_bulk.short_description = "Test MSG91 integration for selected campaigns"
    
    def test_msg91_integration(self, request, campaign_id):
        """Test MSG91 integration for a specific campaign"""
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            
            if campaign.provider != 'msg91-email':
                messages.error(request, f'Campaign {campaign.name} is not using MSG91 Email provider')
                return HttpResponseRedirect('../')
            
            if campaign.channel != 'email':
                messages.error(request, f'Campaign {campaign.name} is not an email campaign')
                return HttpResponseRedirect('../')
            
            # Test MSG91 service
            msg91_service = MSG91EmailService()
            success, message = msg91_service.test_connection()
            
            if success:
                messages.success(request, f'MSG91 integration test successful: {message}')
            else:
                messages.error(request, f'MSG91 integration test failed: {message}')
                
        except Campaign.DoesNotExist:
            messages.error(request, f'Campaign with ID {campaign_id} not found')
        except Exception as e:
            messages.error(request, f'Error testing MSG91 integration: {str(e)}')
        
        return HttpResponseRedirect('../')

@admin.register(CampaignCustomer)
class CampaignCustomerAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'customer', 'added_at']
    list_filter = ['added_at']
    search_fields = ['campaign__name', 'customer__name']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'customer', 'status', 'sent_at', 'delivered_at', 'read_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['campaign__name', 'customer__name', 'customer__email', 'customer__phone']
    readonly_fields = ['id', 'created_at']
