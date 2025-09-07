from django.core.management.base import BaseCommand
from django.conf import settings
from outreach.msg91_service import MSG91EmailService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test MSG91 email service integration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test MSG91 API connection',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send a test email to the specified email address',
        )
        parser.add_argument(
            '--list-templates',
            action='store_true',
            help='List available MSG91 email templates',
        )
    
    def handle(self, *args, **options):
        print("DEBUG: Command started")  # Debug line
        self.stdout.write(self.style.SUCCESS('Testing MSG91 Email Service...'))
        
        # Check configuration
        self.stdout.write(f"MSG91 Auth Key: {settings.MSG91_AUTH_KEY[:10]}...")
        self.stdout.write(f"MSG91 Email Endpoint: {settings.MSG91_EMAIL_ENDPOINT}")
        self.stdout.write(f"From Email: {settings.MSG91_EMAIL_FROM}")
        self.stdout.write(f"From Name: {settings.MSG91_EMAIL_FROM_NAME}")
        
        msg91_service = MSG91EmailService()
        
        if options['test_connection']:
            self.stdout.write('\nTesting MSG91 API connection...')
            success, message = msg91_service.test_connection()
            if success:
                self.stdout.write(self.style.SUCCESS(f"✓ {message}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ {message}"))
        
        if options['list_templates']:
            self.stdout.write('\nFetching MSG91 email templates...')
            success, templates = msg91_service.get_templates()
            if success:
                self.stdout.write(f"✓ Found {len(templates)} templates:")
                for template in templates[:5]:  # Show first 5
                    self.stdout.write(f"  - {template.get('name', 'Unknown')} (ID: {template.get('id', 'Unknown')})")
                if len(templates) > 5:
                    self.stdout.write(f"  ... and {len(templates) - 5} more")
            else:
                self.stdout.write(self.style.ERROR("✗ Failed to fetch templates"))
        
        if options['test_email']:
            test_email = options['test_email']
            self.stdout.write(f'\nSending test email to {test_email}...')
            
            success, message = msg91_service.send_email(
                to_email=test_email,
                subject='Test Email from MSG91 Integration',
                content='<h1>Test Email</h1><p>This is a test email sent through MSG91 integration.</p>',
                customer_name='Test User',
                is_html=True
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"✓ {message}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ {message}"))
        
        if not any([options['test_connection'], options['test_email'], options['list_templates']]):
            self.stdout.write('\nNo specific test specified. Use --help to see available options.')
            self.stdout.write('Available options:')
            self.stdout.write('  --test-connection: Test MSG91 API connection')
            self.stdout.write('  --list-templates: List available email templates')
            self.stdout.write('  --test-email EMAIL: Send a test email')
        
        self.stdout.write(self.style.SUCCESS('\nMSG91 integration test completed!'))
        print("DEBUG: Command finished")  # Debug line
