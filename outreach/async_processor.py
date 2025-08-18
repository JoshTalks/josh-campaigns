import threading
import logging
from typing import Dict, Any
from django.core.cache import cache
from .csv_processor import process_csv_upload_sync

logger = logging.getLogger(__name__)

class AsyncCSVProcessor:
    """
    Simple asynchronous CSV processor using threading
    Provides progress tracking and status updates
    """
    
    def __init__(self):
        self.processing_jobs = {}
    
    def start_csv_processing(self, csv_file, user, job_id: str) -> str:
        """
        Start CSV processing in background thread
        Returns job_id for tracking
        """
        # Initialize job status
        self.processing_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'result': None,
            'error': None
        }
        
        # Store file content in cache for processing
        csv_content = csv_file.read()
        cache.set(f'csv_job_{job_id}', csv_content, timeout=3600)  # 1 hour timeout
        
        # Start background thread
        thread = threading.Thread(
            target=self._process_csv_background,
            args=(job_id, csv_content, user)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started CSV processing job {job_id}")
        return job_id
    
    def _process_csv_background(self, job_id: str, csv_content: bytes, user):
        """
        Background thread for CSV processing
        """
        try:
            # Create a file-like object from cached content
            from io import BytesIO
            csv_file = BytesIO(csv_content)
            
            # Process CSV
            result = process_csv_upload_sync(csv_file, user)
            
            # Update job status
            self.processing_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'result': result
            })
            
            logger.info(f"CSV processing job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in CSV processing job {job_id}: {str(e)}")
            self.processing_jobs[job_id].update({
                'status': 'failed',
                'error': str(e)
            })
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get current status of a processing job
        """
        return self.processing_jobs.get(job_id, {'status': 'not_found'})
    
    def cleanup_job(self, job_id: str):
        """
        Clean up completed/failed jobs
        """
        if job_id in self.processing_jobs:
            del self.processing_jobs[job_id]
            cache.delete(f'csv_job_{job_id}')

# Global instance
csv_processor = AsyncCSVProcessor()

def start_csv_processing_job(csv_file, user) -> str:
    """
    Start a new CSV processing job
    """
    import uuid
    job_id = str(uuid.uuid4())
    return csv_processor.start_csv_processing(csv_file, user, job_id)

def get_csv_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a CSV processing job
    """
    return csv_processor.get_job_status(job_id)

def cleanup_csv_job(job_id: str):
    """
    Clean up a CSV processing job
    """
    csv_processor.cleanup_job(job_id)
