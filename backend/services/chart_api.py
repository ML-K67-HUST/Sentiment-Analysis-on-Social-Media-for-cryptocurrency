import requests
import json
from datetime import datetime, timedelta
from database.mongodb import MongoManager


def get_bitcoin_history(days=30):
    """Fetch Bitcoin price history from CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}&interval=daily"
        response = requests.get(url, timeout=10)
        data = response.json()
        prices = data.get('prices', [])
        return {
            datetime.fromtimestamp(p[0]/1000).strftime('%Y-%m-%d'): p[1] 
            for p in prices
        }
    except Exception as e:
        print(f"Error fetching BTC history: {e}")
        return {}

def get_chart_data():
    """
    Get chart data from 30-min aggregated features
    Returns LLM sentiment and Bitcoin price for visualization
    """
    try:
        mongo_client = MongoManager('blog-data')
        
        # Get 10-min aggregations from last 30 days
        thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
        
        # Fetch real BTC price history
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
        
        # 1. Add historical daily points (for context) when aggregation is missing
        # We know btc_prices keys are 'YYYY-MM-DD'
        sorted_dates = sorted(btc_prices.keys())
        
        # Helper to check if a date is already covered by aggregations (roughly)
        # Actually, aggregations are high-res (10 min). Daily points are low-res.
        # We can just add all daily points that correspond to timestamps OLDER than our oldest aggregation.
        
        oldest_agg_ts = aggregations[0]['window_start'] if aggregations else int(datetime.now().timestamp())
        
        for date_str in sorted_dates:
            price = btc_prices[date_str]
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            ts = int(dt.timestamp())
            
            # If this daily point is significantly older than our first aggregation, add it as a historical point
            # timestamp is isoformat for consistency with agg 'window_datetime'
            if ts < oldest_agg_ts - 86400: # Keep daily points distinct from recent high-res data
                 chart_data.append({
                    'timestamp': dt.isoformat(),
                    'price': price,
                    'bitcoin_index_score': None, # No sentiment for history
                    'num_articles': 0,
                    'llm_sentiment': 0,
                    'llm_confidence': 0
                })

        # 2. Add Aggregation points (High resolution) with Moving Average
        sentiment_buffer = [] # Buffer for SMA-6 (1 hour)
        
        for agg in aggregations:
            # Get price for this date
            price = agg.get('btc_price')
            
            # Fallback to daily history if price is missing or 0 (for old records)
            if not price:
                window_datetime = datetime.fromisoformat(agg['window_datetime'])
                date_key = window_datetime.strftime('%Y-%m-%d')
                price = btc_prices.get(date_key, None)
            
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
            # If we don't have enough data yet (start of chart), average whatever we have
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
                'llm_sentiment': round(sma_sentiment, 4), # Return SMA instead of raw
                'llm_confidence': round(agg.get('llm_confidence_avg', 0.0), 4)
            })
        
        return chart_data
        
    except Exception as e:
        print(f"Error in get_chart_data: {e}")
        return []
