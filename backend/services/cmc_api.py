from database.mongodb import MongoManager
from datetime import datetime, timedelta

def time_ago(timestamp):
    timestamp = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    delta = now - timestamp

    if delta.days > 0:
        return f"{delta.days} day(s) ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour(s) ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute(s) ago"
    else:
        return "Just now"
    

def get_cmc_news():
    """
    Fetch CoinMarketCap news from MongoDB and join with sentiment data.
    """
    mongo_client = MongoManager('blog-data')
    
    # 1. Get latest news articles
    cmc_data = list(mongo_client.find(
        collection_name='cmc_news',
        filter={'title': {'$exists': True, '$ne': None}},
        sort=("timestamp", -1),
        limit=50
    ))
    
    if not cmc_data:
        return []
        
    # 2. Get hash_ids to fetch sentiment
    hash_ids = [doc.get('hash_id') for doc in cmc_data if doc.get('hash_id')]
    
    # 3. Fetch sentiment data
    sentiment_map = {}
    if hash_ids:
        sentiments = list(mongo_client.find(
            collection_name='cmc_sentiment_data',
            filter={'hash_id': {'$in': hash_ids}}
        ))
        for s in sentiments:
            sentiment_map[s.get('hash_id')] = s
    
    result = []
    for data in cmc_data:
        # Extract description
        content = data.get('content', '')
        description = content[:260] + '...' if len(content) > 260 else content
        
        # Extract title
        title = data.get('title')
        if not title:
            source_data = data.get('source_data')
            if source_data:
                if isinstance(source_data, list) and source_data:
                    title = source_data[0].get('title')
                elif isinstance(source_data, dict):
                    title = source_data.get('title')
        if not title:
            title = 'No title'

        # enrich with sentiment
        hash_id = data.get('hash_id')
        sentiment_record = sentiment_map.get(hash_id)
        
        sentiments_list = []
        if sentiment_record:
            # Check for 'btc_sentiment' structure (new format)
            btc_sentiment = sentiment_record.get('btc_sentiment')
            if btc_sentiment:
                # Iterate over keys (metrics/policies)
                for key, val in btc_sentiment.items():
                    if isinstance(val, dict):
                        sentiment_type = val.get('result', 'neutral')
                        reasoning = val.get('reasoning', '')
                        
                        # Map to frontend types
                        if 'positive' in sentiment_type.lower():
                            fe_type = 'positive'
                        elif 'negative' in sentiment_type.lower():
                            fe_type = 'negative'
                        else:
                            fe_type = 'reporting'
                            
                        sentiments_list.append({
                            "type": fe_type,
                            "content": reasoning
                        })
            # Fallback/Old format check
            elif sentiment_record.get('sentiment_score') is not None:
                score = sentiment_record.get('sentiment_score')
                reasoning = sentiment_record.get('sentiment_reasoning', '')
                fe_type = 'positive' if score > 0 else 'negative' if score < 0 else 'reporting'
                
                sentiments_list.append({
                    "type": fe_type,
                    "content": reasoning or f"Sentiment Score: {score}"
                })

        result.append({
            "timestamp": time_ago(int(data.get("timestamp", 0))),
            "title": title,
            "description": description,
            "link": data.get('url', '#'),
            "sentiments": sentiments_list
        })

    return result