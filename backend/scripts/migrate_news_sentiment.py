from database.mongodb import MongoManager

def migrate_news_sentiment():
    print("🚀 Starting migration of sentiment to cmc_news...")
    mongo = MongoManager('blog-data')
    
    # Get all sentiment data
    sentiments = list(mongo.find('cmc_sentiment_data'))
    print(f"Found {len(sentiments)} sentiment records.")
    
    updated_count = 0
    for sent in sentiments:
        hash_id = sent.get('hash_id')
        if not hash_id:
            continue
            
        # Update corresponding news article
        mongo.update_one(
            'cmc_news',
            filter={'hash_id': hash_id},
            data={
                '$set': {
                    'sentiment': sent.get('sentiment'),
                    'sentiment_score': sent.get('sentiment_score'),
                    'sentiment_confidence': sent.get('confidence'),
                    'llm_prediction': sent.get('reasoning'),
                    'category': sent.get('sentiment') # Map sentiment to category
                }
            }
        )
        updated_count += 1
        
    print(f"✅ Migration complete. Updated {updated_count} news articles.")

if __name__ == "__main__":
    migrate_news_sentiment()
