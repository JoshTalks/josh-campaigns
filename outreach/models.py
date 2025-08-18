from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    job_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['email'], ['phone']]

    def __str__(self):
        return self.name

class MessageTemplate(models.Model):
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['channel']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"

class Campaign(models.Model):
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    PROVIDER_CHOICES = [
        # Email providers
        ('aws-ses', 'AWS SES'),
        ('twilio-sendgrid', 'SendGrid'),
        # SMS providers
        ('gupshup-sms', 'Gupshup SMS'),
        ('msg91-sms', 'MSG91'),
        ('twilio-sms', 'Twilio SMS'),
        # WhatsApp providers
        ('meta-whatsapp', 'Meta Cloud API'),
        ('gupshup-whatsapp', 'Gupshup WhatsApp'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)  # Will be auto-generated
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    customers = models.ManyToManyField(Customer, through='CampaignCustomer')
    template = models.ForeignKey(MessageTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['channel']),
            models.Index(fields=['provider']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['sent_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.name:
            # Auto-generate campaign name
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            channel_display = self.get_channel_display()
            self.name = f"{channel_display}_Campaign_{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CampaignCustomer(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'customer']),
            models.Index(fields=['added_at']),
        ]
        unique_together = [['campaign', 'customer']]

class Message(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['campaign']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['delivered_at']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['campaign', 'customer']]

    def __str__(self):
        return f"{self.campaign.name} - {self.customer.name} ({self.status})"


class VendorTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    channel = models.CharField(max_length=20, choices=Campaign.CHANNEL_CHOICES)
    provider = models.CharField(max_length=50, choices=Campaign.PROVIDER_CHOICES)
    external_id = models.CharField(max_length=255, unique=True, help_text="ID from the vendor's template system")
    content = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft')
    is_approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['channel']),
            models.Index(fields=['provider']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['channel', 'provider', 'external_id']]

    def __str__(self):
        return f"{self.name} ({self.provider} - {self.channel})"


# Link selected vendor template to campaign (optional for non-email)
Campaign.add_to_class(
    'vendor_template',
    models.ForeignKey('VendorTemplate', on_delete=models.SET_NULL, null=True, blank=True)
)
