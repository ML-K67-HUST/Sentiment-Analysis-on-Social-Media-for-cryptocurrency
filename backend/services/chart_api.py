import requests
import json
from datetime import datetime, timedelta
from database.mongodb import MongoManager



def get_bitcoin_history(days=30):
    """Fetch Bitcoin price history from CoinGecko (Hourly resolution)"""
    try:
        # Remove interval=daily to get granular data (hourly for > 1 day, minutely for 1 day)
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=10)
        data = response.json()
        prices = data.get('prices', [])
        
        # Return dict: timestamp (seconds) -> price
        # CoinGecko returns [timestamp_ms, price]
        return {
            int(p[0]/1000): p[1] 
            for p in prices
        }
    except Exception as e:
        print(f"Error fetching BTC history: {e}")
        return {}

def get_closest_price(target_ts, price_history):
    """Find the price record with timestamp closest to target_ts"""
    if not price_history:
        return None
    
    # This is a naive O(N) search per point, but fast enough for small N (720 hours)
    # For production, use bisect or a sorted list matching
    closest_ts = min(price_history.keys(), key=lambda t: abs(t - target_ts))
    
    # Only use if within reasonable range (e.g. 2 hours)
    if abs(closest_ts - target_ts) > 7200: 
        return None
        
    return price_history[closest_ts]

def get_chart_data():
    """
    Get chart data from 30-min aggregated features
    Returns LLM sentiment and Bitcoin price for visualization
    """
    try:
        mongo_client = MongoManager('blog-data')
        
        # Get 10-min aggregations from last 30 days
        thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
        
        # Fetch real BTC price history (Hourly resolution)
        btc_prices = get_bitcoin_history(30)
        
        # Get aggregated features
        aggregations = list(mongo_client.find(
            collection_name='aggregated_features_10min',
            filter={
                'window_start': {'$gte': thirty_days_ago},
                'aggregation_status': 'complete'
            },
            sort=("window_start", 1)
        ))
        
        if not aggregations:
            print("No aggregated data available")
            return []
        
        # Merge with price data
        chart_data = []
        
        # 2. Add Aggregation points (High resolution) with Moving Average
        sentiment_buffer = [] # Buffer for SMA-6 (1 hour)
        
        for agg in aggregations:
            # 1. Try to get Price from record itself
            price = agg.get('btc_price')
            
            # 2. If missing, look up closest hourly price from CoinGecko
            if not price:
                window_ts = agg.get('window_start')
                price = get_closest_price(window_ts, btc_prices)
            
            if price is None:
                continue
            
            # LLM sentiment (already -1 to 1)
            llm_sentiment = agg.get('llm_sentiment_avg', 0.0)
            
            # Handle legacy data that was multiplied by 100
            if abs(llm_sentiment) > 1.0:
                llm_sentiment = llm_sentiment / 100.0
                
            # Safety clamp for raw value before buffer
            llm_sentiment = max(-1.0, min(1.0, llm_sentiment))
            
            # Add to buffer and calculate SMA
            sentiment_buffer.append(llm_sentiment)
            if len(sentiment_buffer) > 6:
                sentiment_buffer.pop(0)
            
            # Calculate Moving Average
            if sentiment_buffer:
                sma_sentiment = sum(sentiment_buffer) / len(sentiment_buffer)
            else:
                sma_sentiment = llm_sentiment

            # Calculate Positive Rate from SMA
            positive_rate = ((sma_sentiment + 1) / 2) * 100
            
            chart_data.append({
                'timestamp': agg['window_datetime'],
                'price': price,
                'bitcoin_index_score': round(positive_rate, 2),
                'num_articles': agg.get('num_articles', 0),
                'llm_sentiment': round(sma_sentiment, 4), 
                'llm_confidence': round(agg.get('llm_confidence_avg', 0.0), 4)
            })
        
        return chart_data
        
    except Exception as e:
        print(f"Error in get_chart_data: {e}")
        return []
