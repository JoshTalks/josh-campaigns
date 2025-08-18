import csv
import io
import logging
from typing import List, Dict, Tuple
from django.db import transaction
from django.db.models import Q
from .models import Customer
import time

logger = logging.getLogger(__name__)

class BulkCSVProcessor:
    """
    Scalable CSV processor for handling large customer imports (up to 50k+ records)
    Uses bulk operations and efficient database queries
    """
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.stats = {
            'total_rows': 0,
            'processed': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'duplicates_skipped': 0,
            'affected_ids': []
        }
    
    def process_csv_file(self, csv_file, user) -> Dict:
        """
        Process CSV file and return processing statistics
        """
        try:
            # Read CSV data
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            
            # Validate headers
            required_columns = ['name', 'email', 'phone', 'address', 'job_link']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                raise ValueError(f'CSV must contain these columns: {", ".join(required_columns)}')
            
            # Convert to list for processing
            rows = list(csv_reader)
            self.stats['total_rows'] = len(rows)
            
            logger.info(f"Starting CSV processing for {len(rows)} rows")
            
            # Process in batches
            self._process_batches(rows, user)
            
            logger.info(f"CSV processing completed. Stats: {self.stats}")
            return self.stats
            
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            raise
    
    def _process_batches(self, rows: List[Dict], user):
        """
        Process rows in batches for memory efficiency
        """
        for i in range(0, len(rows), self.batch_size):
            batch = rows[i:i + self.batch_size]
            self._process_batch(batch, user)
            
            # Log progress
            if i % (self.batch_size * 10) == 0:
                logger.info(f"Processed {i + len(batch)}/{len(rows)} rows...")
    
    def _process_batch(self, batch: List[Dict], user):
        """
        Process a single batch of rows
        """
        # Prepare batch data
        batch_data = []
        for row in batch:
            try:
                # Clean and validate data
                cleaned_data = self._clean_row_data(row)
                if cleaned_data:
                    batch_data.append(cleaned_data)
                else:
                    self.stats['errors'] += 1
            except Exception as e:
                logger.error(f"Error processing row {row}: {str(e)}")
                self.stats['errors'] += 1
                continue
        
        if not batch_data:
            return
        
        # Process batch with bulk operations
        self._bulk_process_customers(batch_data, user)
    
    def _clean_row_data(self, row: Dict) -> Dict:
        """
        Clean and validate row data
        """
        # Basic validation
        if not row.get('name', '').strip():
            return None
        
        # Clean data
        cleaned = {
            'name': row.get('name', '').strip(),
            'email': row.get('email', '').strip() or None,
            'phone': row.get('phone', '').strip() or None,
            'address': row.get('address', '').strip() or None,
            'job_link': row.get('job_link', '').strip() or None,
        }
        
        # Validate email format if present
        if cleaned['email'] and '@' not in cleaned['email']:
            cleaned['email'] = None
        
        # At least one contact method required
        if not cleaned['email'] and not cleaned['phone']:
            return None
        
        return cleaned
    
    def _bulk_process_customers(self, batch_data: List[Dict], user):
        """
        Process customers using bulk operations for efficiency
        """
        try:
            with transaction.atomic():
                # Get existing customers for this batch (email and phone lookups)
                existing_customers = self._get_existing_customers(batch_data)
                
                # Separate new and existing customers
                new_customers = []
                update_customers = []
                
                for data in batch_data:
                    customer_id = self._find_existing_customer_id(data, existing_customers)
                    
                    if customer_id:
                        # Update existing customer
                        update_customers.append((customer_id, data))
                        self.stats['duplicates_skipped'] += 1
                    else:
                        # Create new customer
                        new_customers.append(data)
                
                # Bulk create new customers
                if new_customers:
                    new_customer_objects = [
                        Customer(
                            name=data['name'],
                            email=data['email'],
                            phone=data['phone'],
                            address=data['address'],
                            job_link=data['job_link']
                        )
                        for data in new_customers
                    ]
                    
                    created_customers = Customer.objects.bulk_create(
                        new_customer_objects,
                        ignore_conflicts=True  # Skip if duplicates found during bulk create
                    )
                    
                    # Track created IDs
                    self.stats['affected_ids'].extend([str(c.id) for c in created_customers])
                    
                    self.stats['created'] += len(created_customers)
                    logger.info(f"Bulk created {len(created_customers)} new customers")
                
                # Bulk update existing customers
                if update_customers:
                    self._bulk_update_customers(update_customers)
                    self.stats['updated'] += len(update_customers)
                    # Track updated IDs
                    self.stats['affected_ids'].extend([str(cid) for cid, _ in update_customers])
                
                self.stats['processed'] += len(batch_data)
                
        except Exception as e:
            logger.error(f"Error in bulk processing: {str(e)}")
            raise
    
    def _get_existing_customers(self, batch_data: List[Dict]) -> Dict:
        """
        Efficiently get existing customers for this batch
        """
        # Collect all emails and phones from batch
        emails = [data['email'] for data in batch_data if data['email']]
        phones = [data['phone'] for data in batch_data if data['phone']]
        
        # Build query for existing customers
        existing_query = Q()
        if emails:
            existing_query |= Q(email__in=emails)
        if phones:
            existing_query |= Q(phone__in=phones)
        
        if not existing_query:
            return {}
        
        # Get existing customers with only needed fields
        existing_customers = Customer.objects.filter(existing_query).values(
            'id', 'email', 'phone'
        )
        
        # Create lookup dictionaries
        email_lookup = {}
        phone_lookup = {}
        
        for customer in existing_customers:
            if customer['email']:
                email_lookup[customer['email']] = customer['id']
            if customer['phone']:
                phone_lookup[customer['phone']] = customer['id']
        
        return {
            'emails': email_lookup,
            'phones': phone_lookup
        }
    
    def _find_existing_customer_id(self, data: Dict, existing_customers: Dict) -> int:
        """
        Find existing customer ID based on email or phone
        """
        # Check email first
        if data['email'] and data['email'] in existing_customers['emails']:
            return existing_customers['emails'][data['email']]
        
        # Check phone
        if data['phone'] and data['phone'] in existing_customers['phones']:
            return existing_customers['phones'][data['phone']]
        
        return None
    
    def _bulk_update_customers(self, update_customers: List[Tuple]):
        """
        Bulk update existing customers
        """
        # Group updates by field to minimize database calls
        updates_by_id = {}
        
        for customer_id, data in update_customers:
            if customer_id not in updates_by_id:
                updates_by_id[customer_id] = {}
            
            # Only update non-empty fields
            for field, value in data.items():
                if value is not None:
                    updates_by_id[customer_id][field] = value
        
        # Perform bulk updates
        for customer_id, updates in updates_by_id.items():
            Customer.objects.filter(id=customer_id).update(**updates)

def process_csv_upload_async(csv_file, user) -> Dict:
    """
    Main function to process CSV upload asynchronously
    This can be called from a Celery task or background job
    """
    processor = BulkCSVProcessor(batch_size=1000)
    return processor.process_csv_file(csv_file, user)

def process_csv_upload_sync(csv_file, user) -> Dict:
    """
    Synchronous version for immediate processing (good for small files)
    """
    processor = BulkCSVProcessor(batch_size=500)  # Smaller batch size for sync processing
    return processor.process_csv_file(csv_file, user)
