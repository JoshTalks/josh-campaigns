from django import forms
from .models import Customer, Campaign, MessageTemplate, VendorTemplate
import csv
import io

class CustomerUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Upload CSV File',
        help_text='File should contain columns: name, email, phone, address, job_link',
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError('Please upload a valid CSV file.')
        
        try:
            # Read and validate CSV
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            
            # Check required columns
            required_columns = ['name', 'email', 'phone', 'address', 'job_link']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                raise forms.ValidationError(
                    f'CSV must contain these columns: {", ".join(required_columns)}'
                )
            
            # Reset file pointer
            csv_file.seek(0)
            return csv_file
            
        except Exception as e:
            raise forms.ValidationError(f'Error reading CSV file: {str(e)}')

class CustomerManualForm(forms.Form):
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    job_link = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))

class CampaignForm(forms.ModelForm):
    channel = forms.ChoiceField(
        choices=Campaign.CHANNEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Communication Channel *'
    )
    
    provider = forms.ChoiceField(
        choices=[],  # Will be populated dynamically based on channel
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Service Provider *'
    )
    
    template = forms.ModelChoiceField(
        queryset=MessageTemplate.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Message Template *'
    )
    
    class Meta:
        model = Campaign
        fields = ['channel', 'provider', 'template']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set channel choices
        self.fields['channel'].choices = [('', 'Select Channel')] + Campaign.CHANNEL_CHOICES
        
        # Set initial provider choices (empty, will be populated via JavaScript)
        self.fields['provider'].choices = [('', 'Select Channel First')]
        
        # Set initial template queryset (empty, will be populated via JavaScript)
        self.fields['template'].queryset = MessageTemplate.objects.none()
        
        # If we have POST data, populate the choices dynamically
        if self.data:
            channel = self.data.get('channel')
            provider = self.data.get('provider')
            
            if channel:
                # Set provider choices based on submitted channel
                provider_choices = self.get_provider_choices_for_channel(channel)
                self.fields['provider'].choices = [('', 'Select Provider')] + provider_choices
                
                if provider:
                    # Set template queryset based on submitted channel and provider
                    self.fields['template'].queryset = MessageTemplate.objects.filter(
                        channel=channel,
                        provider=provider
                    )
        
        # If editing existing campaign, populate the fields
        elif self.instance.pk:
            # Set provider choices based on existing channel
            if self.instance.channel:
                provider_choices = self.get_provider_choices_for_channel(self.instance.channel)
                self.fields['provider'].choices = [('', 'Select Provider')] + provider_choices
                
                # Set template queryset based on existing channel and provider
                if self.instance.provider:
                    self.fields['template'].queryset = MessageTemplate.objects.filter(
                        channel=self.instance.channel,
                        provider=self.instance.provider
                    )
    
    def get_provider_choices_for_channel(self, channel):
        """Get provider choices for a specific channel"""
        if channel == 'email':
            return [
                ('aws-ses', 'AWS SES'),
                ('twilio-sendgrid', 'SendGrid (Twilio)'),
                ('msg91-email', 'MSG91 Email'),
            ]
        elif channel == 'sms':
            return [
                ('gupshup-sms', 'Gupshup'),
                ('msg91-sms', 'MSG91'),
                ('twilio-sms', 'Twilio'),
            ]
        elif channel == 'whatsapp':
            return [
                ('meta-whatsapp', 'Meta Cloud API'),
                ('gupshup-whatsapp', 'Gupshup'),
            ]
        else:
            return []
    
    def clean(self):
        cleaned_data = super().clean()
        channel = cleaned_data.get('channel')
        provider = cleaned_data.get('provider')
        template = cleaned_data.get('template')
        
        # Validate provider belongs to selected channel
        if channel and provider:
            valid_providers = [p[0] for p in self.get_provider_choices_for_channel(channel)]
            if provider not in valid_providers:
                self.add_error('provider', f'Provider "{provider}" is not valid for channel "{channel}".')
        
        # Template is required for all campaigns
        if not template:
            self.add_error('template', 'Message template is required for all campaigns.')
        
        return cleaned_data

class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ['name', 'channel', 'subject', 'content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make subject required only for email templates
        self.fields['subject'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        channel = cleaned_data.get('channel')
        subject = cleaned_data.get('subject')
        
        if channel == 'email' and not subject:
            self.add_error('subject', 'Subject is required for email templates.')
        
        return cleaned_data

class CampaignSearchForm(forms.Form):
    search_contact = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number, email, or name'
        })
    )
    search_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    filter_channel = forms.ChoiceField(
        choices=[('', 'All Channels')] + Campaign.CHANNEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    filter_status = forms.ChoiceField(
        choices=[('', 'All Status')] + [('pending', 'Pending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('read', 'Read'), ('failed', 'Failed')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    filter_provider = forms.ChoiceField(
        choices=[('', 'All Providers')] + Campaign.PROVIDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
