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
    vendor_template = forms.ModelChoiceField(
        queryset=VendorTemplate.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vendor Template (for SMS/WhatsApp)'
    )
    
    class Meta:
        model = Campaign
        fields = ['channel', 'provider', 'subject', 'content', 'vendor_template']
        widgets = {
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'provider': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make subject required only for email campaigns
        self.fields['subject'].required = False
        
        # Dynamically set queryset for vendor_template
        if 'channel' in self.initial and 'provider' in self.initial:
            self.fields['vendor_template'].queryset = VendorTemplate.objects.filter(
                channel=self.initial['channel'],
                provider=self.initial['provider'],
                is_approved=True
            )
        elif self.instance.pk:  # For editing existing campaign
            self.fields['vendor_template'].queryset = VendorTemplate.objects.filter(
                channel=self.instance.channel,
                provider=self.instance.provider,
                is_approved=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        channel = cleaned_data.get('channel')
        subject = cleaned_data.get('subject')
        
        if channel == 'email' and not subject:
            self.add_error('subject', 'Subject is required for email campaigns.')
        
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
