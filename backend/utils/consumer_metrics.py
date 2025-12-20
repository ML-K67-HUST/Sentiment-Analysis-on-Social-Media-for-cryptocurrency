"""
Consumer Metrics Tracker
Tracks consumer statistics and stores in MongoDB
"""

from datetime import datetime
from database.mongodb import MongoManager


class ConsumerMetrics:
    def __init__(self, consumer_name: str, db_name: str = 'blog-data'):
        self.consumer_name = consumer_name
        self.mongo = MongoManager(db_name)
        self.collection = 'consumer_metrics'
        
        # Initialize metrics
        self.metrics = {
            'consumer_name': consumer_name,
            'total_processed': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'last_processed_at': None,
            'last_error_at': None,
            'last_error_message': None,
            'status': 'initializing',
            'started_at': int(datetime.utcnow().timestamp()),
            'updated_at': int(datetime.utcnow().timestamp())
        }
        
        # Load existing metrics or create new
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing metrics from DB or create new"""
        existing = self.mongo.find_one(
            collection_name=self.collection,
            filter={'consumer_name': self.consumer_name}
        )
        
        if existing:
            self.metrics = existing
            print(f"📊 Loaded metrics for {self.consumer_name}")
        else:
            self._save()
            print(f"📊 Created new metrics for {self.consumer_name}")
    
    def _save(self):
        """Save metrics to MongoDB"""
        self.metrics['updated_at'] = int(datetime.utcnow().timestamp())
        
        self.mongo.update_one(
            collection_name=self.collection,
            filter={'consumer_name': self.consumer_name},
            data={'$set': self.metrics},
            upsert=True
        )
    
    def increment_processed(self, batch_size: int = 1):
        """Increment processed count"""
        self.metrics['total_processed'] += batch_size
        self.metrics['last_processed_at'] = int(datetime.utcnow().timestamp())
        self.metrics['status'] = 'running'
        self._save()
    
    def increment_errors(self, error_message: str = None):
        """Increment error count"""
        self.metrics['total_errors'] += 1
        self.metrics['last_error_at'] = int(datetime.utcnow().timestamp())
        if error_message:
            self.metrics['last_error_message'] = str(error_message)[:500]  # Limit length
        self._save()
    
    def increment_skipped(self, reason: str = None):
        """Increment skipped count"""
        self.metrics['total_skipped'] += 1
        if reason:
            self.metrics['last_skip_reason'] = str(reason)[:200]
        self._save()
    
    def set_status(self, status: str):
        """Set consumer status (running, stopped, error)"""
        self.metrics['status'] = status
        self._save()
    
    def get_metrics(self):
        """Get current metrics"""
        return self.metrics
    
    def log_summary(self):
        """Print metrics summary"""
        print(f"\n{'='*60}")
        print(f"📊 {self.consumer_name} Metrics")
        print(f"{'='*60}")
        print(f"  Status: {self.metrics['status']}")
        print(f"  Total Processed: {self.metrics['total_processed']}")
        print(f"  Total Errors: {self.metrics['total_errors']}")
        print(f"  Total Skipped: {self.metrics['total_skipped']}")
        
        if self.metrics['last_processed_at']:
            last_processed = datetime.fromtimestamp(self.metrics['last_processed_at'])
            print(f"  Last Processed: {last_processed}")
        
        if self.metrics['last_error_at']:
            last_error = datetime.fromtimestamp(self.metrics['last_error_at'])
            print(f"  Last Error: {last_error}")
            print(f"  Error Message: {self.metrics.get('last_error_message', 'N/A')}")
        
        print(f"{'='*60}\n")
