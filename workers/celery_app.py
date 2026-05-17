# Celery Application Configuration
# Configures Celery to use Redis as both message broker and result backend

from celery import Celery
import os

# Read Redis URL from environment variable
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery application
celery_app = Celery(
    'hireiq_workers',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'workers.tasks.send_invite_email',
        'workers.tasks.rank_candidates',
        'workers.tasks.generate_report'
    ]
)

# Configure Celery
celery_app.conf.update(
    # Timezone configuration
    timezone='Asia/Kolkata',
    
    # Task acknowledgement after execution (not before) to prevent message loss
    task_acks_late=True,
    
    # Worker prefetch multiplier
    worker_prefetch_multiplier=1,
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Result expiration (1 hour)
    result_expires=3600,
    
    # Task routes (if needed)
    task_routes={},
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
)


# Optional: Auto-discover tasks in the tasks directory
celery_app.autodiscover_tasks(['workers.tasks'])


if __name__ == '__main__':
    celery_app.start()
