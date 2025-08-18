from django.contrib import admin
from .models import Customer, MessageTemplate, Campaign, CampaignCustomer, Message, VendorTemplate

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
