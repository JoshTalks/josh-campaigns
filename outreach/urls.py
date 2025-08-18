from django.urls import path
from . import views

app_name = 'outreach'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-customers/', views.add_customers, name='add_customers'),
    path('create-campaign/', views.create_campaign, name='create_campaign'),
    path('campaign/<uuid:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaign-overview/', views.campaign_overview, name='campaign_overview'),
    path('campaign/<uuid:campaign_id>/messages/', views.campaign_messages, name='campaign_messages'),
    path('message/<uuid:message_id>/', views.message_detail, name='message_detail'),
    path('templates/', views.manage_templates, name='manage_templates'),
    path('template/<uuid:template_id>/', views.template_detail, name='template_detail'),
    path('template/<uuid:template_id>/delete/', views.delete_template, name='delete_template'),
    path('csv-processing-status/', views.csv_processing_status, name='csv_processing_status'),
    path('api/providers/', views.get_providers, name='get_providers'),
    path('api/vendor-templates/', views.get_vendor_templates, name='get_vendor_templates'),
]
