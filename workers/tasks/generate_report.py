# Generate Report Task - Celery task for generating PDF reports
from celery import shared_task
import os


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_report(self, mongo_session_id: str):
    """
    Generate and cache a PDF report for a completed interview.
    
    This task calls the existing modules/report functions (read-only) to 
    regenerate and cache the PDF report. It is triggered after interview 
    completion as a background job so the HR does not wait for PDF 
    generation during the API response.
    
    Args:
        mongo_session_id: The MongoDB session ID for the interview
    """
    try:
        # Import the report module (read-only access to existing functionality)
        from modules.report import generate_pdf_report
        
        # Generate the PDF report
        pdf_data = generate_pdf_report(mongo_session_id)
        
        return {
            "success": True,
            "message": f"Report generated successfully for session {mongo_session_id}",
            "mongo_session_id": mongo_session_id,
            "pdf_size_bytes": len(pdf_data) if pdf_data else 0
        }
        
    except ImportError:
        # Report module doesn't exist yet
        return {
            "success": False,
            "error": "Report module not available",
            "mongo_session_id": mongo_session_id
        }
        
    except Exception as e:
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except AttributeError:
            # Not running in Celery context
            return {
                "success": False,
                "error": str(e),
                "mongo_session_id": mongo_session_id
            }


# For testing without Celery broker
def generate_report_eager(mongo_session_id: str):
    """
    Synchronous version for testing without a Celery broker.
    
    This function directly executes the report generation logic.
    """
    return generate_report(mongo_session_id=mongo_session_id)
