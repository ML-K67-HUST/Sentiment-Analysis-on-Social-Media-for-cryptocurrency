"""
Bitcoin Data Constructor.
Fetches Bitcoin price data from Coinranking API and constructs datasets.
"""
import requests
import json
from datetime import datetime
import time
from typing import Optional

from config import config

# Bitcoin UUID in Coinranking API
BITCOIN_UUID = "Qwsogvtv82FCd"
COINRANKING_API_BASE = "https://api.coinranking.com/v2"


def _get_headers() -> dict:
    """Get headers for Coinranking API requests."""
    if not config.COINRANKING_API_KEY:
        raise ValueError(
            "COINRANKING_API_KEY not configured. "
            "Please set it in your .env file."
        )
    
    return {
        'x-access-token': config.COINRANKING_API_KEY,
    }


def get_bitcoin_change(time_period: str) -> Optional[str]:
    """
    Get Bitcoin price change for a specific time period.
    
    Args:
        time_period: Time period (e.g., '24h', '7d', '30d')
        
    Returns:
        str: Price change percentage, or None if request fails
    """
    url = f"{COINRANKING_API_BASE}/coin/{BITCOIN_UUID}"
    params = {"timePeriod": time_period}
    
    response = requests.get(url, headers=_get_headers(), params=params)
    
    try:
        data = response.json()
        return data["data"]["coin"]["change"]
        
    except (KeyError, json.JSONDecodeError) as e:
        print(f'❌ Error parsing Bitcoin change response: {e}')
        print(f'Response status: {response.status_code}')
        print(f'Response text: {response.text[:200]}...')
        
        # Retry once after 10 seconds
        print('Retrying in 10 seconds...')
        time.sleep(10)
        
        try:
            response = requests.get(url, headers=_get_headers(), params=params)
            data = response.json()
            return data["data"]["coin"]["change"]
        except Exception as retry_error:
            print(f'❌ Retry failed: {retry_error}')
            return None


def get_bitcoin_price(timestamp: str) -> Optional[str]:
    """
    Get Bitcoin price at a specific timestamp.
    
    Args:
        timestamp: Unix timestamp as string
        
    Returns:
        str: JSON response text, or None if request fails
    """
    url = f"{COINRANKING_API_BASE}/coin/{BITCOIN_UUID}/price"
    params = {"timestamp": timestamp}
    
    try:
        response = requests.get(url, headers=_get_headers(), params=params)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f'❌ Error fetching Bitcoin price: {e}')
        return None


def get_bitcoin_price_one_hour(timestamp: str) -> Optional[str]:
    """
    Get Bitcoin price one hour after the given timestamp.
    
    Args:
        timestamp: Unix timestamp as string
        
    Returns:
        str: Bitcoin price, or None if request fails
    """
    one_hour_ahead = str(int(timestamp) + 3600)
    
    try:
        price_data = get_bitcoin_price(one_hour_ahead)
        if price_data:
            return json.loads(price_data)["data"]["price"]
    except (KeyError, json.JSONDecodeError) as e:
        print(f'❌ Error parsing Bitcoin price: {e}')
    
    return None


def get_bitcoin_change_overtime() -> dict:
    """
    Get Bitcoin price changes over multiple time periods.
    
    Returns:
        dict: Price changes for different time periods
    """
    return {
        "timestamp": int(datetime.now().timestamp()),
        "7_days_ago": get_bitcoin_change("7d"),
        "1_days_ago": get_bitcoin_change("24h"),
        "12_hours_ago": get_bitcoin_change("12h"),
        "3_hours_ago": get_bitcoin_change("3h")
    }


def construct_unlabeled_dataset(bot_sentiment: float) -> dict:
    """
    Construct an unlabeled dataset with Bitcoin price changes and sentiment score.
    
    Args:
        bot_sentiment: Sentiment score from LLM analysis
        
    Returns:
        dict: Dataset ready for ML training
    """
    btc_price_over_time = get_bitcoin_change_overtime()
    btc_price_over_time["bot_sentiment"] = bot_sentiment
    btc_price_over_time["labeled"] = False  # Use boolean instead of string
    
    return btc_price_over_time