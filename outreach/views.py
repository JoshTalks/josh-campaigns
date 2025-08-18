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
import io
from .message_delivery import send_campaign_messages_sync
from .csv_processor import process_csv_upload_sync
from .tasks import process_customers_csv_task, send_campaign_messages as send_campaign_messages_task

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
            campaign.save()
            
            # Get customers from session
            customer_ids = request.session.get('campaign_customers', [])
            if customer_ids:
                customers = Customer.objects.filter(id__in=customer_ids)
                campaign.customers.set(customers)
                # Clear session
                del request.session['campaign_customers']
                
                # Trigger message delivery asynchronously
                if customers.exists():
                    send_campaign_messages_task.delay(str(campaign.id))
                    messages.success(request, f'Campaign "{campaign.name}" created. Messages are being sent in the background.')
                else:
                    messages.warning(request, f'Campaign "{campaign.name}" created but no customers were found to send messages to.')
            
            return redirect('outreach:campaign_overview')
    else:
        form = CampaignForm()
    
    context = {
        'form': form,
        'customers_count': len(request.session.get('campaign_customers', [])),
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
    
    # Try to find existing customer by email or phone
    customer = None
    if email:
        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            pass
    
    if not customer and phone:
        try:
            customer = Customer.objects.get(phone=phone)
        except Customer.DoesNotExist:
            pass
    
    if customer:
        # Update existing customer fields (except email/phone identifiers)
        customer.name = customer_data.get('name', customer.name)
        customer.address = customer_data.get('address', customer.address)
        customer.job_link = customer_data.get('job_link', customer.job_link)
        customer.save()
    else:
        # Create new customer
        customer = Customer.objects.create(**customer_data)
    
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
    """Get approved vendor templates for a specific channel and provider (non-email)."""
    channel = request.GET.get('channel')
    provider = request.GET.get('provider')

    if not channel or not provider or channel == 'email':
        return JsonResponse({'templates': []})

    templates = VendorTemplate.objects.filter(
        channel=channel,
        provider=provider,
        is_approved=True,
        status='approved',
    ).order_by('name')

    data = [
        {
            'id': str(t.id),
            'name': t.name,
            'external_id': t.external_id,
            'content': t.content,
        }
        for t in templates
    ]

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
