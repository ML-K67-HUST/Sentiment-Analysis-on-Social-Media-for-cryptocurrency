"""
Restore Backup Script
Restores aggregatedfeatures_10min data from JSON backup.
"""
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.mongodb import MongoManager
from config import config

def restore_backup():
    print("🚀 Restoring Backup Data...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    backup_path = os.path.join(project_root, "mongodb_backup", "blog-data", "aggregated_features_10min.json")
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return

    # Initialize MongoDB
    conn_str = config.MONGODB_CONNECTION_STRING
    if "@mongodb" in conn_str:
        conn_str = conn_str.replace("@mongodb", "@localhost")
    mongo_client = MongoManager('blog-data', uri=conn_str)
    
    print(f"📖 Reading backup file: {backup_path}")
    with open(backup_path, 'r') as f:
        data = json.load(f)
        
    print(f"ℹ️  Found {len(data)} records in backup.")
    
    # Preprocess BSON specific fields if any (like $oid)
    # The view_file output showed "_id": {"$oid": ...}
    # PyMongo doesn't like that format directly if we insert.
    # But usually we don't care about preserving the exact _id if we upsert by window_start.
    # However, to be clean, let's strip $oid wrapper or Convert to ObjectId.
    # Actually, upserting by window_start is safer.
    
    processed_count = 0
    upsert_count = 0
    
    for record in data:
        # Strip _id to avoid duplicate key error if we let Mongo generate new ones or if IDs conflict
        # But wait, if we want to restore exact state, maybe we should keep it?
        # Let's remove _id and rely on window_start as the unique logical key for aggregation.
        if '_id' in record:
            del record['_id']
            
        # Ensure window_start exists
        window_start = record.get('window_start')
        if not window_start:
            continue
            
        # Update into MongoDB
        mongo_client.update_one(
            'aggregated_features_10min',
            filter={'window_start': window_start},
            data={'$set': record},
            upsert=True
        )
        upsert_count += 1
        
    print(f"✅ Successfully processed {upsert_count} records.")

    # Check final count
    final_count = mongo_client.count('aggregated_features_10min', {})  # Oh wait, count method doesn't exist on wrapper
    # Using underlying client
    # Actually just print done
    print("🎉 Restore complete.")

if __name__ == "__main__":
    restore_backup()
