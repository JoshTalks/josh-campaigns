from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from .models import Customer, Campaign, Message, MessageTemplate, VendorTemplate
from .forms import CustomerUploadForm, CustomerManualForm, CampaignForm, MessageTemplateForm, CampaignSearchForm
import csv
import logging

logger = logging.getLogger(__name__)
import io
from .message_delivery import send_campaign_messages_sync
from .csv_processor import process_csv_upload_sync
from .tasks import process_customers_csv_task, send_campaign_messages as send_campaign_messages_task
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests

@login_required
def dashboard(request):
    """Simplified dashboard view"""
    # Get recent campaigns
    recent_campaigns = Campaign.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    
    # Get recent messages
    recent_messages = Message.objects.filter(campaign__created_by=request.user).order_by('-created_at')[:10]
    
    context = {
        'recent_campaigns': recent_campaigns,
        'recent_messages': recent_messages,
    }
    return render(request, 'outreach/dashboard.html', context)

@login_required
def create_campaign(request):
    """Create a new outreach campaign"""
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            
            # Set content from template or POST data
            if form.cleaned_data.get('template'):
                template = form.cleaned_data['template']
                campaign.content = template.content
                campaign.subject = getattr(template, 'subject', '') or ''
                
                # Store custom placeholder values if provided
                custom_placeholders = {}
                for key, value in request.POST.items():
                    if key.startswith('placeholder_') and value.strip():
                        placeholder_name = key.replace('placeholder_', '')
                        custom_placeholders[placeholder_name] = value.strip()
                
                if custom_placeholders:
                    # Store custom placeholders in campaign data
                    campaign.custom_placeholders = custom_placeholders
                    print(f"Stored custom placeholders: {custom_placeholders}")
                else:
                    print("No custom placeholders found in request")
                
                # Debug: Print all POST data
                print("All POST data received:")
                for key, value in request.POST.items():
                    print(f"  {key}: {value}")
            else:
                # Fallback to POST data if no template
                campaign.content = request.POST.get('content', '')
                campaign.subject = request.POST.get('subject', '')
            
            campaign.save()
            
            # Get customers from session
            customer_ids = request.session.get('campaign_customers', [])
            print(f"Customer IDs from session: {customer_ids}")
            
            if customer_ids:
                customers = Customer.objects.filter(id__in=customer_ids)
                print(f"Found {customers.count()} customers in database")
                campaign.customers.set(customers)
                # Clear session
                del request.session['campaign_customers']
                
                # Trigger message delivery asynchronously
                if customers.exists():
                    print(f"Triggering message delivery for campaign {campaign.id}")
                    
                    # For local development, send synchronously if Celery is not running
                    # try:
                    #     send_campaign_messages_task.delay(str(campaign.id))
                    #     messages.success(request, f'Campaign "{campaign.name}" created. Messages are being sent in the background.')
                    # except Exception as e:
                    print(f"Celery task failed, trying synchronous execution:")
                    # Fallback to synchronous execution for local testing
                    from .tasks import send_campaign_messages
                    result = send_campaign_messages(str(campaign.id))
                    if result.get('success'):
                        messages.success(request, f'Campaign "{campaign.name}" created and messages sent successfully!')
                    else:
                        messages.warning(request, f'Campaign "{campaign.name}" created but message sending failed: {result.get("error", "Unknown error")}')
                else:
                    print("No customers found in database")
                    messages.warning(request, f'Campaign "{campaign.name}" created but no customers were found to send messages to.')
            else:
                print("No customer IDs found in session")
                messages.warning(request, f'Campaign "{campaign.name}" created but no customers were added. Please add customers first.')
            
            return redirect('outreach:campaign_overview')
        else:
            print("Form errors:", form.errors)
            return JsonResponse({'success': False, 'error': 'Form validation failed: ' + str(form.errors)})
    else:
        form = CampaignForm()
    
    # Check if there are customers in session
    customer_ids = request.session.get('campaign_customers', [])
    customers_count = len(customer_ids)
    
    if customers_count == 0:
        messages.warning(request, 'Please add customers to your campaign before creating it.')
        return redirect('outreach:add_customers')
    
    context = {
        'form': form,
        'customers_count': customers_count,
    }
    return render(request, 'outreach/create_campaign.html', context)

@login_required
def add_customers(request):
    """Add customers to campaign - CSV upload or manual entry"""
    if request.method == 'POST':
        if 'csv_upload' in request.POST:
            form = CustomerUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                
                try:
                    # Check file size to decide processing method
                    csv_file.seek(0, 2)  # Seek to end
                    file_size = csv_file.tell()
                    csv_file.seek(0)  # Reset to beginning
                    
                    # Queue Celery task for CSV processing (both small/large files)
                    import base64
                    b64 = base64.b64encode(csv_file.read()).decode('ascii')
                    async_result = process_customers_csv_task.delay(b64, request.user.id)
                    request.session['csv_processing_task_id'] = async_result.id
                    messages.info(request, 'CSV processing started in background.')
                    return redirect('outreach:csv_processing_status')
                    
                except Exception as e:
                    messages.error(request, f'Error processing CSV: {str(e)}')
                    return redirect('outreach:add_customers')
        elif 'manual_entry' in request.POST:
            # Handle manual customer entry
            customers = process_manual_customers(request.POST)
            request.session['campaign_customers'] = [str(c.id) for c in customers]
            messages.success(request, f'{len(customers)} customers processed!')
            return redirect('outreach:create_campaign')
    else:
        form = CustomerUploadForm()
    
    context = {
        'form': form,
        'manual_form': CustomerManualForm(),
    }
    return render(request, 'outreach/add_customers.html', context)

def _get_customers_for_session(result, csv_file, user):
    """
    Helper method to get customer objects for session after CSV processing
    """
    # Reset file pointer
    csv_file.seek(0)
    
    # Read CSV again to get the actual data for session
    csv_data = csv_file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    customers = []
    for row in csv_reader:
        # Clean the row data
        cleaned_data = {
            'name': row.get('name', '').strip(),
            'email': row.get('email', '').strip() or None,
            'phone': row.get('phone', '').strip() or None,
            'address': row.get('address', '').strip() or None,
            'job_link': row.get('job_link', '').strip() or None,
        }
        
        # Skip invalid rows
        if not cleaned_data['name'] or (not cleaned_data['email'] and not cleaned_data['phone']):
            continue
        
        # Get or create customer for session
        customer = get_or_create_customer(cleaned_data)
        customers.append(customer)
    
    return customers

def process_manual_customers(post_data):
    """Process manually entered customer data"""
    customers = []
    if post_data.get('name'):
        customer_data = {
            'name': post_data['name'],
            'email': post_data.get('email'),
            'phone': post_data.get('phone'),
            'address': post_data.get('address'),
            'job_link': post_data.get('job_link'),
        }
        customer = get_or_create_customer(customer_data)
        customers.append(customer)
    
    return customers

def get_or_create_customer(customer_data):
    """Get existing customer or create new one, updating fields if needed"""
    email = customer_data.get('email')
    phone = customer_data.get('phone')
    
    # Try to find existing customer by email AND phone combination
    customer = None
    if email and phone:
        try:
            customer = Customer.objects.get(email=email, phone=phone)
        except Customer.DoesNotExist:
            pass
    
    # If not found by combination, try to find by email only (for backward compatibility)
    if not customer and email:
        try:
            customer = Customer.objects.get(email=email)
            # If found by email only, update the phone if it's different
            if customer.phone != phone:
                # Create a new customer with the new phone number
                customer = None
        except Customer.DoesNotExist:
            pass
    
    # If not found by email, try to find by phone only (for backward compatibility)
    if not customer and phone:
        try:
            customer = Customer.objects.get(phone=phone)
            # If found by phone only, update the email if it's different
            if customer.email != email:
                # Create a new customer with the new email
                customer = None
        except Customer.DoesNotExist:
            pass
    
    if customer:
        # Update existing customer fields (including email/phone if they match)
        customer.name = customer_data.get('name', customer.name)
        customer.address = customer_data.get('address', customer.address)
        customer.job_link = customer_data.get('job_link', customer.job_link)
        customer.save()
    else:
        # Create new customer
        try:
            customer = Customer.objects.create(**customer_data)
        except Exception as e:
            # If creation fails due to unique constraint, try to find existing customer
            if email and phone:
                try:
                    customer = Customer.objects.get(email=email, phone=phone)
                except Customer.DoesNotExist:
                    raise e
    
    return customer

@login_required
def campaign_detail(request, campaign_id):
    """View campaign details and send messages"""
    campaign = get_object_or_404(Campaign, id=campaign_id, created_by=request.user)
    
    if request.method == 'POST' and 'send_campaign' in request.POST:
        # Send campaign to all customers
        success_count = send_campaign_messages_sync(campaign)
        messages.success(request, f'Campaign sent to {success_count} customers!')
        return redirect('outreach:campaign_overview')
    
    context = {
        'campaign': campaign,
        'customers': campaign.customers.all(),
    }
    return render(request, 'outreach/campaign_detail.html', context)

def send_campaign_messages(campaign):
    """Send campaign messages to all customers"""
    success_count = 0
    
    for customer in campaign.customers.all():
        message, created = Message.objects.get_or_create(
            campaign=campaign,
            customer=customer,
            defaults={'status': 'pending'}
        )
        
        try:
            # Here you would integrate with actual providers (AWS SES, Twilio, etc.)
            # For now, we'll just mark as sent
            message.status = 'sent'
            message.sent_at = timezone.now()
            message.save()
            success_count += 1
            
        except Exception as e:
            message.status = 'failed'
            message.error_message = str(e)
            message.save()
    
    # Update campaign status
    campaign.status = 'completed'
    campaign.sent_at = timezone.now()
    campaign.completed_at = timezone.now()
    campaign.save()
    
    return success_count

@login_required
def campaign_overview(request):
    """Overview of all campaigns with message counts"""
    campaigns = Campaign.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Add message statistics for each campaign
    for campaign in campaigns:
        campaign.total_messages = campaign.message_set.count()
        campaign.delivered_messages = campaign.message_set.filter(status__in=['delivered', 'read']).count()
        campaign.failed_messages = campaign.message_set.filter(status='failed').count()
        campaign.pending_messages = campaign.message_set.filter(status='pending').count()
    
    context = {
        'campaigns': campaigns,
    }
    return render(request, 'outreach/campaign_overview.html', context)

@login_required
def campaign_messages(request, campaign_id):
    """View individual messages for a specific campaign"""
    campaign = get_object_or_404(Campaign, id=campaign_id, created_by=request.user)
    messages_list = campaign.message_set.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'campaign': campaign,
        'page_obj': page_obj,
    }
    return render(request, 'outreach/campaign_messages.html', context)

@login_required
def message_detail(request, message_id):
    """View detailed message information"""
    message = get_object_or_404(Message, id=message_id, campaign__created_by=request.user)
    
    context = {
        'message': message,
    }
    return render(request, 'outreach/message_detail.html', context)

@login_required
def manage_templates(request):
    """Manage message templates"""
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect('outreach:manage_templates')
    else:
        form = MessageTemplateForm()
    
    templates = MessageTemplate.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'form': form,
        'templates': templates,
    }
    return render(request, 'outreach/manage_templates.html', context)

@login_required
def template_detail(request, template_id):
    """View and edit template details"""
    template = get_object_or_404(MessageTemplate, id=template_id, created_by=request.user)
    
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect('outreach:manage_templates')
    else:
        form = MessageTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
    }
    return render(request, 'outreach/template_detail.html', context)

@login_required
def delete_template(request, template_id):
    """Delete a message template"""
    template = get_object_or_404(MessageTemplate, id=template_id, created_by=request.user)
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect('outreach:manage_templates')
    
    context = {
        'template': template,
    }
    return render(request, 'outreach/delete_template.html', context)

# API views for AJAX requests
@login_required
def get_providers(request):
    """Get available providers for a specific channel"""
    channel = request.GET.get('channel')
    if channel == 'email':
        providers = [
            {'value': 'aws-ses', 'label': 'AWS SES'},
            {'value': 'twilio-sendgrid', 'label': 'SendGrid (Twilio)'},
            {'value': 'msg91-email', 'label': 'MSG91 Email'},
        ]
    elif channel == 'sms':
        providers = [
            {'value': 'gupshup-sms', 'label': 'Gupshup'},
            {'value': 'msg91-sms', 'label': 'MSG91'},
            {'value': 'twilio-sms', 'label': 'Twilio'},
        ]
    elif channel == 'whatsapp':
        providers = [
            {'value': 'meta-whatsapp', 'label': 'Meta Cloud API'},
            {'value': 'gupshup-whatsapp', 'label': 'Gupshup'},
        ]
    else:
        providers = []
    
    return JsonResponse({'providers': providers})

@login_required
def get_vendor_templates(request):
    """
    Fetch templates from vendor APIs or local database based on provider type
    """
    channel = request.GET.get('channel')
    provider = request.GET.get('provider')

    if not channel or not provider:
        return JsonResponse({'templates': []})

    try:
        # Define which providers use API vs manual templates
        api_providers = ['msg91-email', 'meta-whatsapp', 'gupshup-whatsapp']  # Add more API-based providers here
        manual_providers = ['gupshup-sms']  # Add more manual providers here
        
        if provider in api_providers:
            # API-based template fetching
            if channel == 'email' and provider == 'msg91-email':
                return _fetch_msg91_templates(request, channel, provider)
            elif channel == 'whatsapp' and provider == 'meta-whatsapp':
                return _fetch_meta_whatsapp_templates(request, channel, provider)
            elif channel == 'whatsapp' and provider == 'gupshup-whatsapp':
                return _fetch_gupshup_whatsapp_templates(request, channel, provider)
            else:
                return JsonResponse({'templates': [], 'error': f'API provider {provider} not supported for channel {channel}'})
                
        elif provider in manual_providers:
            # Manual template fetching from database (Gupshup SMS)
            return _fetch_manual_templates(request, channel, provider)
        else:
            return JsonResponse({'templates': [], 'error': f'Unknown provider: {provider}'})
                
    except Exception as e:
        return JsonResponse({'templates': [], 'error': f'Error fetching templates: {str(e)}'})


def _fetch_msg91_templates(request, channel, provider):
    """Fetch templates from MSG91 API and upsert to database"""
    try:
        from .msg91_service import MSG91EmailService
        msg91_service = MSG91EmailService()
        success, templates = msg91_service.get_templates()
        
        if success:
            data = []
            for t in templates:
                # Get the first version of the template
                version = t.get('versions', [{}])[0] if t.get('versions') else {}
                
                # Create or get MessageTemplate record for MSG91 template
                msg91_template_id = str(t.get('id', ''))
                
                # Skip templates that are not approved/registered (like 5171)
                if msg91_template_id == '5171':
                    continue
                
                template, created = MessageTemplate.objects.get_or_create(
                    external_id=msg91_template_id,
                    defaults={
                        'name': t.get('name', 'Unknown Template'),
                        'channel': channel,
                        'provider': provider,
                        'content': version.get('body', '') or version.get('html', '') or '',
                        'subject': version.get('subject', ''),
                        'created_by': request.user,
                    }
                )
                
                template_data = {
                    'id': str(template.id),  # Use Django model UUID
                    'name': template.name,
                    'external_id': msg91_template_id,
                    'content': template.content,
                    'subject': template.subject,
                    'preview_link': version.get('preview_link', ''),
                    'variables': version.get('variables', []),
                    'source': 'msg91'
                }
                data.append(template_data)
            
            # Fallback to local DB templates if MSG91 list is empty after filtering
            if not data:
                return _fetch_manual_templates(request, channel, provider)
            return JsonResponse({'templates': data})
        else:
            # On failure, fallback to local DB templates so UI isn't empty
            return _fetch_manual_templates(request, channel, provider)
            
    except Exception as e:
        return JsonResponse({'templates': [], 'error': f'Error fetching MSG91 templates: {str(e)}'})


def _fetch_meta_whatsapp_templates(request, channel, provider):
    """Fetch templates from Meta WhatsApp API and upsert to database"""
    try:
        from .meta_whatsapp_service import MetaWhatsAppService
        
        # Fetch templates from Meta WhatsApp API
        meta_service = MetaWhatsAppService()
        success, templates_data, error_msg = meta_service.get_message_templates()
        
        if not success:
            logger.error(f"Meta WhatsApp API error: {error_msg}")
            # Fallback to manual templates if API fails
            return _fetch_manual_templates(request, channel, provider)
        
        if not templates_data:
            logger.warning("No templates returned from Meta WhatsApp API")
            # Fallback to manual templates if no data
            return _fetch_manual_templates(request, channel, provider)
        
        # Process and upsert templates to database
        processed_templates = []
        for template_data in templates_data:
            try:
                # Extract template information
                template_name = template_data.get('name', '')
                template_id = template_data.get('id', '')
                template_status = template_data.get('status', '')
                
                # Only process approved templates
                if template_status != 'APPROVED':
                    continue
                
                # Extract components to build content
                components = template_data.get('components', [])
                content = ""
                subject = ""
                
                for component in components:
                    if component.get('type') == 'HEADER':
                        header_text = component.get('text', '')
                        if header_text:
                            subject = header_text
                    elif component.get('type') == 'BODY':
                        body_text = component.get('text', '')
                        if body_text:
                            content = body_text
                
                # Create or update template in database
                template, created = MessageTemplate.objects.get_or_create(
                    external_id=template_id,
                    channel=channel,
                    provider=provider,
                    defaults={
                        'name': template_name,
                        'content': content,
                        'subject': subject,
                        'created_by': request.user,
                    }
                )
                
                if not created:
                    # Update existing template
                    template.name = template_name
                    template.content = content
                    template.subject = subject
                    template.save()
                
                # Extract variables from content using regex
                import re
                variables = re.findall(r'\{\{(\w+)\}\}', content)
                # Remove duplicates while preserving order
                seen = set()
                variables = [v for v in variables if not (v in seen or seen.add(v))]
                
                processed_templates.append({
                    'id': str(template.id),
                    'name': template_name,
                    'external_id': template_id,
                    'content': content,
                    'subject': subject,
                    'preview_link': '',
                    'variables': variables,
                    'source': 'api'
                })
                
            except Exception as e:
                logger.error(f"Error processing Meta WhatsApp template {template_data.get('name', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(processed_templates)} Meta WhatsApp templates")
        return JsonResponse({'templates': processed_templates})
        
    except Exception as e:
        logger.error(f"Error fetching Meta WhatsApp templates: {str(e)}")
        # Fallback to manual templates
        return _fetch_manual_templates(request, channel, provider)


def _fetch_gupshup_whatsapp_templates(request, channel, provider):
    """Fetch templates from Gupshup WhatsApp API and upsert to database"""
    try:
        from .gupshup_whatsapp_service import GupshupWhatsAppService
        
        # Fetch templates from Gupshup WhatsApp API
        gupshup_service = GupshupWhatsAppService()
        success, templates_data, error_msg = gupshup_service.get_message_templates()
        
        if not success:
            logger.error(f"Gupshup WhatsApp API error: {error_msg}")
            # Fallback to manual templates if API fails
            return _fetch_manual_templates(request, channel, provider)
        
        if not templates_data:
            logger.warning("No templates returned from Gupshup WhatsApp API")
            # Fallback to manual templates if no data
            return _fetch_manual_templates(request, channel, provider)
        
        # Process and upsert templates to database
        processed_templates = []
        for template_data in templates_data:
            try:
                # Extract template information
                template_name = template_data.get('name', '')
                template_id = template_data.get('id', '')
                template_status = template_data.get('status', '')
                
                # Only process approved templates
                if template_status != 'APPROVED':
                    continue
                
                # Extract components to build content
                components = template_data.get('components', [])
                content = ""
                subject = ""
                
                for component in components:
                    if component.get('type') == 'HEADER':
                        header_text = component.get('text', '')
                        if header_text:
                            subject = header_text
                    elif component.get('type') == 'BODY':
                        body_text = component.get('text', '')
                        if body_text:
                            content = body_text
                
                # Create or update template in database
                template, created = MessageTemplate.objects.get_or_create(
                    external_id=template_id,
                    channel=channel,
                    provider=provider,
                    defaults={
                        'name': template_name,
                        'content': content,
                        'subject': subject,
                        'created_by': request.user,
                    }
                )
                
                if not created:
                    # Update existing template
                    template.name = template_name
                    template.content = content
                    template.subject = subject
                    template.save()
                
                # Extract variables from content using regex
                import re
                variables = re.findall(r'\{\{(\w+)\}\}', content)
                # Remove duplicates while preserving order
                seen = set()
                variables = [v for v in variables if not (v in seen or seen.add(v))]
                
                processed_templates.append({
                    'id': str(template.id),
                    'name': template_name,
                    'external_id': template_id,
                    'content': content,
                    'subject': subject,
                    'preview_link': '',
                    'variables': variables,
                    'source': 'api'
                })
                
            except Exception as e:
                logger.error(f"Error processing Gupshup WhatsApp template {template_data.get('name', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(processed_templates)} Gupshup WhatsApp templates")
        return JsonResponse({'templates': processed_templates})
        
    except Exception as e:
        logger.error(f"Error fetching Gupshup WhatsApp templates: {str(e)}")
        # Fallback to manual templates
        return _fetch_manual_templates(request, channel, provider)


def _fetch_manual_templates(request, channel, provider):
    """Fetch templates from local database (manual entry)"""
    import re
    data = []
    local_templates = MessageTemplate.objects.filter(channel=channel, provider=provider)
    
    for lt in local_templates:
        content = lt.content or ''
        vars_found = re.findall(r'\{\{(\w+)\}\}', content)
        # dedupe while preserving order
        seen = set()
        variables = [v for v in vars_found if not (v in seen or seen.add(v))]
        data.append({
            'id': str(lt.id),
            'name': lt.name,
            'external_id': lt.external_id,
            'content': lt.content,
            'subject': lt.subject,
            'preview_link': '',
            'variables': variables,
            'source': 'manual'
        })
    
    return JsonResponse({'templates': data})

@login_required
def csv_processing_status(request):
    """Poll Celery task for CSV processing and redirect when done."""
    task_id = request.session.get('csv_processing_task_id')
    if not task_id:
        messages.error(request, 'No CSV processing task found.')
        return redirect('outreach:add_customers')

    from celery.result import AsyncResult
    async_res = AsyncResult(task_id)

    if async_res.failed():
        messages.error(request, f'CSV processing failed: {async_res.result}')
        del request.session['csv_processing_task_id']
        return redirect('outreach:add_customers')

    if async_res.successful():
        result = async_res.get() or {}
        affected_ids = result.get('affected_ids', [])
        if affected_ids:
            customers = Customer.objects.filter(id__in=affected_ids)
            request.session['campaign_customers'] = [str(c.id) for c in customers]
            del request.session['csv_processing_task_id']
            messages.success(request, (
                f"CSV processed! Created: {result.get('created', 0)}, "
                f"Updated: {result.get('updated', 0)}, Errors: {result.get('errors', 0)}"
            ))
            return redirect('outreach:create_campaign')
        else:
            del request.session['csv_processing_task_id']
            messages.warning(request, 'CSV processed but no valid customers found.')
            return redirect('outreach:add_customers')

    # Still processing
    context = {
        'job_id': task_id,
        'job_status': {'status': 'processing', 'progress': 0},
    }
    return render(request, 'outreach/csv_processing_status.html', context)

def _get_customers_for_session_from_result(result, user):
    """Compatibility helper (unused by Celery path)."""
    affected_ids = result.get('affected_ids', [])
    return list(Customer.objects.filter(id__in=affected_ids))

@login_required
def test_msg91_integration(request):
    """Test MSG91 integration from web interface"""
    if request.method == 'POST':
        try:
            from .msg91_service import MSG91EmailService
            
            msg91_service = MSG91EmailService()
            
            # Test 1: Connection test
            connection_success, connection_message = msg91_service.test_connection()
            
            if not connection_success:
                messages.error(request, f'MSG91 connection test failed: {connection_message}')
                return redirect('outreach:test_msg91_integration')
            
            messages.success(request, f'MSG91 connection test successful: {connection_message}')
            
            # Test 2: Send template email
            template_success, template_message = msg91_service.send_template_email(
                to_email="avivish000@gmail.com",  # Test email
                customer_name="Test User",
                template_id="global_otp",
                variables={
                    "company_name": "Josh Talks",
                    "otp": "123456"
                }
            )
            
            if template_success:
                messages.success(request, f'Template email test successful: {template_message}')
            else:
                messages.error(request, f'Template email test failed: {template_message}')
            
            # Test 3: Send bulk template emails
            bulk_success, bulk_message = msg91_service.send_bulk_template_emails([
                {
                    'name': 'Test User 1',
                    'email': 'avivish000@gmail.com',
                    'variables': {
                        'company_name': 'Josh Talks',
                        'otp': '123456'
                    },
                    'template_id': 'global_otp'
                },
                {
                    'name': 'Test User 2',
                    'email': 'avikumar@joshtalks.com',
                    'variables': {
                        'company_name': 'Josh Jobs',
                        'otp': '654321'
                    },
                    'template_id': 'global_otp'
                }
            ])
            
            if bulk_success:
                messages.success(request, f'Bulk template email test successful: {bulk_message}')
            else:
                messages.error(request, f'Bulk template email test failed: {bulk_message}')
                
        except Exception as e:
            messages.error(request, f'Error testing MSG91 integration: {str(e)}')
        
        return redirect('outreach:test_msg91_integration')
    
    # Get MSG91 configuration info
    context = {
        'msg91_auth_key': settings.MSG91_AUTH_KEY[:10] + '...' if len(settings.MSG91_AUTH_KEY) > 10 else settings.MSG91_AUTH_KEY,
        'msg91_email_endpoint': settings.MSG91_EMAIL_ENDPOINT,
        'msg91_from_email': "developers@joshtalks.com",  # Use working email
        'msg91_from_name': "Josh2",  # Use working name
        'msg91_domain': "joshjobs.joshtalks.com",  # Use working domain
    }
    
    return render(request, 'outreach/test_msg91_integration.html', context)

@login_required
def test_meta_whatsapp_integration(request):
    """Test Meta WhatsApp integration from web interface"""
    context = {
        'page_title': 'Test Meta WhatsApp Integration',
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': reverse('outreach:dashboard')},
            {'name': 'Test Meta WhatsApp', 'url': None}
        ],
        'templates': [],
        'test_result': None
    }
    
    try:
        from .meta_whatsapp_service import MetaWhatsAppService
        
        # Fetch templates
        service = MetaWhatsAppService()
        success, templates, error_msg = service.get_message_templates(limit=20)
        
        if success:
            context['templates'] = templates
            context['templates_count'] = len(templates)
        else:
            messages.warning(request, f'Could not fetch templates: {error_msg}')
            
    except Exception as e:
        messages.error(request, f'Error initializing Meta WhatsApp service: {str(e)}')
    
    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            
            if action == 'send_test_message':
                phone = request.POST.get('phone', '').strip()
                template_name = request.POST.get('template_name', '').strip()
                parameters = request.POST.get('parameters', '').strip()
                
                if not phone or not template_name:
                    messages.error(request, 'Phone number and template name are required')
                else:
                    # Parse parameters if provided
                    param_list = []
                    if parameters:
                        param_list = [p.strip() for p in parameters.split(',') if p.strip()]
                    
                    success, response_msg, response_data = service.send_message(
                        to_phone=phone,
                        template_name=template_name,
                        language_code='en_US',
                        parameters=param_list if param_list else None
                    )
                    
                    if success:
                        context['test_result'] = {
                            'success': True,
                            'message': response_msg,
                            'data': response_data
                        }
                        messages.success(request, f'Message sent successfully: {response_msg}')
                    else:
                        context['test_result'] = {
                            'success': False,
                            'message': response_msg
                        }
                        messages.error(request, f'Failed to send message: {response_msg}')
                        
        except Exception as e:
            messages.error(request, f'Error testing Meta WhatsApp: {str(e)}')
    
    return render(request, 'outreach/test_meta_whatsapp_integration.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def msg91_template_details(request):
    """Fetch complete template details from MSG91 API"""
    try:
        data = json.loads(request.body)
        template_name = data.get('template_name')
        
        # Add debugging
        print(f"MSG91 API call received for template: '{template_name}'")
        
        if not template_name:
            return JsonResponse({
                'success': False,
                'error': 'Template name is required'
            })
        
        # MSG91 API endpoint for template search
        url = "https://control.msg91.com/api/v5/email/templates"
        params = {
            'page': 1,
            'with': 'versions',
            'keyword': template_name,
            'per_page': 25,
            'search_in': 'name',
            'status_id': 2
        }
        headers = {
            'authkey': settings.MSG91_AUTH_KEY
        }
        
        print(f"MSG91 API request: {url} with params: {params}")
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"MSG91 API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"MSG91 API response: {result}")
            
            if result.get('status') == 'success':
                templates = result.get('data', {}).get('data', [])
                print(f"Found {len(templates)} templates")
                
                # Find the exact template match
                for template in templates:
                    template_api_name = template.get('name')
                    # print(f"Checking template: '{template_api_name}' against requested: '{template_name}'")
                    
                    if template_api_name == template_name:
                        # Get the latest version
                        versions = template.get('versions', [])
                        if versions:
                            latest_version = versions[0]  # Assuming first is latest
                            
                            template_details = {
                                'id': template.get('id'),
                                'name': template.get('name'),
                                'subject': latest_version.get('subject', ''),
                                'body': latest_version.get('body', ''),
                                'content': latest_version.get('body', ''),
                                'variables': latest_version.get('variables', []),
                                'html_content': latest_version.get('body', ''),
                                'text_content': latest_version.get('text_plain', ''),
                                'preview_link': latest_version.get('preview_link', ''),
                                'status': template.get('status_id'),
                                'is_active': template.get('is_active', False)
                            }
                            
                            # print(f"Template found and details extracted: {template_details}")
                            
                            return JsonResponse({
                                'success': True,
                                'template': template_details
                            })
                
                return JsonResponse({
                    'success': False,
                    'error': f'Template "{template_name}" not found'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'MSG91 API error: {result.get("message", "Unknown error")}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': f'MSG91 API request failed with status {response.status_code}'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        print(f"Unexpected error in msg91_template_details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })

def test_dynamic_form(request):
    """Test page for dynamic form functionality"""
    return render(request, 'outreach/test_dynamic_form.html')
