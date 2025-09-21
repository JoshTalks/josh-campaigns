from django.core.management.base import BaseCommand
from outreach.meta_whatsapp_service import MetaWhatsAppService
import json

class Command(BaseCommand):
    help = 'Test Meta WhatsApp Cloud API integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['list-templates', 'send-message'],
            default='list-templates',
            help='Action to perform: list-templates or send-message'
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number for sending message (with country code)'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='hello_world',
            help='Template name for sending message'
        )
        parser.add_argument(
            '--params',
            type=str,
            nargs='*',
            help='Template parameters for sending message'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['APPROVED', 'PENDING', 'REJECTED', 'ALL'],
            default='APPROVED',
            help='Filter templates by status'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of templates to fetch'
        )

    def handle(self, *args, **options):
        service = MetaWhatsAppService()
        
        if options['action'] == 'list-templates':
            self.list_templates(service, options)
        elif options['action'] == 'send-message':
            self.send_message(service, options)

    def list_templates(self, service, options):
        """List WhatsApp message templates"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Fetching WhatsApp Message Templates...')
        )
        
        success, templates, message = service.get_message_templates(
            limit=options['limit'],
            status=options['status']
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {message}')
            )
            self.stdout.write(f'📊 Found {len(templates)} templates\n')
            
            if templates:
                for i, template in enumerate(templates, 1):
                    self.stdout.write(f'{i}. {template.get("name", "N/A")}')
                    self.stdout.write(f'   ID: {template.get("id", "N/A")}')
                    self.stdout.write(f'   Status: {template.get("status", "N/A")}')
                    self.stdout.write(f'   Category: {template.get("category", "N/A")}')
                    self.stdout.write(f'   Language: {template.get("language", "N/A")}')
                    
                    # Show components
                    components = template.get('components', [])
                    if components:
                        self.stdout.write('   Components:')
                        for comp in components:
                            comp_type = comp.get('type', 'N/A')
                            comp_text = comp.get('text', 'N/A')
                            preview = comp_text[:50] + '...' if len(comp_text) > 50 else comp_text
                            self.stdout.write(f'     - {comp_type}: {preview}')
                    self.stdout.write('')
            else:
                self.stdout.write('⚠️  No templates found')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {message}')
            )

    def send_message(self, service, options):
        """Send a WhatsApp message"""
        phone = options.get('phone')
        if not phone:
            self.stdout.write(
                self.style.ERROR('❌ Phone number is required for sending messages')
            )
            return
        
        template = options.get('template')
        params = options.get('params', [])
        
        self.stdout.write(
            self.style.SUCCESS(f'📱 Sending WhatsApp message...')
        )
        self.stdout.write(f'   To: {phone}')
        self.stdout.write(f'   Template: {template}')
        if params:
            self.stdout.write(f'   Parameters: {", ".join(params)}')
        
        success, message, response_data = service.send_message(
            to_phone=phone,
            template_name=template,
            language_code='en_US',
            parameters=params
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {message}')
            )
            if response_data:
                self.stdout.write('📊 Response:')
                self.stdout.write(json.dumps(response_data, indent=2))
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {message}')
            )

