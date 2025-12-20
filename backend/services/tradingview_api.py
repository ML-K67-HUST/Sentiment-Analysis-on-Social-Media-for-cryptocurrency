from database.mongodb import MongoManager
from datetime import datetime, timedelta


def time_ago(timestamp):
    """Convert timestamp to human-readable time ago format"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return "Unknown"
    elif isinstance(timestamp, int):
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


def get_tradingview_ideas():
    """
    Fetch TradingView ideas from MongoDB.
    Returns list of trading ideas with timestamp, title, description, and link.
    Prioritizes ideas with sentiment analysis.
    """
    mongo_client = MongoManager('blog-data')
    
    # Get ideas WITH sentiment first (sorted by timestamp)
    ideas_with_sentiment = list(mongo_client.find(
        collection_name='tradingview_ideas',
        filter={'sentiment': {'$exists': True, '$ne': None}},
        sort=("timestamp", -1),
        limit=40
    ))
    
    # Get recent ideas WITHOUT sentiment to fill up to 50
    ideas_without_sentiment = list(mongo_client.find(
        collection_name='tradingview_ideas',
        filter={'sentiment': {'$exists': False}},
        sort=("timestamp", -1),
        limit=10
    ))
    
    # Combine: prioritize ideas with sentiment
    all_ideas = ideas_with_sentiment + ideas_without_sentiment
    
    result = []
    for idea in all_ideas:
        # Extract description
        description = idea.get('description', '')
        if len(description) > 200:
            description = description[:200] + '...'
        
        # Get sentiment data if available
        sentiments = []
        if idea.get('sentiment'):
            sentiment_type = idea.get('sentiment', 'neutral').capitalize()
            sentiment_reasoning = idea.get('sentiment_reasoning', '')
            confidence = idea.get('sentiment_confidence', 0.0)
            
            # Format sentiment for frontend
            sentiments.append({
                "type": sentiment_type,
                "content": f"{sentiment_reasoning} (Confidence: {confidence:.2f})" if sentiment_reasoning else f"{sentiment_type} sentiment detected"
            })
        
        # Extract metadata
        published_at = idea.get('published_at', idea.get('crawled_at', ''))
        
        result.append({
            "timestamp": time_ago(published_at),
            "title": idea.get('title', 'No title'),
            "description": description,
            "link": idea.get('url', '#'),
            "author": idea.get('author', 'Unknown'),
            "symbol": idea.get('symbol', ''),
            "likes": idea.get('likes', 0),
            "views": idea.get('views', 0),
            "comments_count": idea.get('comments_count', 0),
            "labels": idea.get('labels', []),
            "sentiments": sentiments
        })
    
    return result

