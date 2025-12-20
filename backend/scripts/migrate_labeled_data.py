from database.mongodb import MongoManager
import time

def migrate():
    print("🚀 Starting migration of cmc_labeled_data...")
    mongo = MongoManager('blog-data')
    
    # Find records without source_data
    records = list(mongo.find('cmc_labeled_data', filter={'source_data': {'$exists': False}}))
    
    if not records:
        print("✅ No records need migration.")
        return

    print(f"found {len(records)} records to migrate.")
    
    updated_count = 0
    for record in records:
        hash_id = record.get('hash_id')
        if not hash_id:
            print(f"⚠️ Record {record.get('_id')} has no hash_id, skipping.")
            continue
            
        # Find original news
        news = mongo.find_one('cmc_news', filter={'hash_id': hash_id})
        
        if not news:
            print(f"⚠️ Original news not found for {hash_id}, skipping.")
            continue
            
        # Construct source_data
        source_data = {
            "title": news.get('title'),
            "url": news.get('url'),
            "symbol": news.get('symbol'),
            "content": news.get('content'),
            "timestamp": news.get('timestamp'),
            "hash_id": news.get('hash_id'),
            "category": news.get('category')
        }
        
        # Update record
        mongo.update_one(
            'cmc_labeled_data',
            filter={'_id': record['_id']},
            data={'$set': {'source_data': source_data}}
        )
        updated_count += 1
        
    print(f"✅ Migration complete. Updated {updated_count} records.")

if __name__ == "__main__":
    migrate()
