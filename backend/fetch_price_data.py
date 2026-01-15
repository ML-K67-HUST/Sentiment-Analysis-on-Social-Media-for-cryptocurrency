#!/usr/bin/env python3
"""
Fetch Bitcoin Historical Price Data
Uses CoinGecko API (free, no key required) to get OHLCV data
"""

import os
import sys
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_labeled_data.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_with_price.csv")

def fetch_bitcoin_price_coingecko(start_timestamp, end_timestamp):
    """
    Fetch Bitcoin price from CoinGecko
    Returns: DataFrame with timestamp, open, high, low, close, volume
    """
    print(f"📡 Fetching Bitcoin price data from CoinGecko...")
    print(f"   Time range: {datetime.fromtimestamp(start_timestamp)} to {datetime.fromtimestamp(end_timestamp)}")
    
    # CoinGecko API endpoint (1-hour candles, free tier)
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
    
    params = {
        'vs_currency': 'usd',
        'from': start_timestamp,
        'to': end_timestamp
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract price data
        prices = data.get('prices', [])
        volumes = data.get('total_volumes', [])
        
        if not prices:
            print("❌ No price data returned")
            return None
        
        # Convert to DataFrame
        df_price = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df_price['timestamp'] = df_price['timestamp'] / 1000  # Convert to seconds
        
        df_volume = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
        df_volume['timestamp'] = df_volume['timestamp'] / 1000
        
        # Merge
        df = pd.merge(df_price, df_volume, on='timestamp', how='left')
        
        print(f"   ✅ Fetched {len(df)} data points")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def engineer_price_features(df):
    """
    Engineer technical features from OHLCV data
    """
    print("\n🔧 Engineering technical features...")
    
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 1. Price Returns (Momentum)
    print("   - Lagged returns...")
    df['price'] = df['close']
    df['return_1'] = df['price'].pct_change(1)
    df['return_2'] = df['price'].pct_change(2)
    df['return_3'] = df['price'].pct_change(3)
    df['return_5'] = df['price'].pct_change(5)
    df['return_10'] = df['price'].pct_change(10)
    
    # 2. Volatility
    print("   - Volatility (rolling std)...")
    df['volatility_5'] = df['return_1'].rolling(window=5).std()
    df['volatility_10'] = df['return_1'].rolling(window=10).std()
    df['volatility_20'] = df['return_1'].rolling(window=20).std()
    
    # 3. Moving Averages
    print("   - Moving averages...")
    df['ma_5'] = df['price'].rolling(window=5).mean()
    df['ma_10'] = df['price'].rolling(window=10).mean()
    df['ma_20'] = df['price'].rolling(window=20).mean()
    
    # 4. RSI (Relative Strength Index)
    print("   - RSI...")
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    df['rsi_14'] = calculate_rsi(df['price'], 14)
    
    # 5. MACD
    print("   - MACD...")
    exp1 = df['price'].ewm(span=12, adjust=False).mean()
    exp2 = df['price'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    
    # 6. Bollinger Bands
    print("   - Bollinger Bands...")
    df['bb_middle'] = df['price'].rolling(window=20).mean()
    bb_std = df['price'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # 7. Volume features
    print("   - Volume features...")
    df['volume_ma5'] = df['volume'].rolling(window=5).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma5']
    
    print(f"   ✅ Created {len([c for c in df.columns if c not in ['timestamp', 'close', 'volume', 'price']])} technical features")
    
    return df

def merge_with_sentiment(sentiment_df, price_df):
    """
    Merge sentiment data with price data based on timestamp
    """
    print("\n🔗 Merging sentiment with price data...")
    
    # Round timestamps to nearest minute for matching
    sentiment_df['timestamp_rounded'] = (sentiment_df['window_start'] // 60) * 60
    price_df['timestamp_rounded'] = (price_df['timestamp'] // 60) * 60
    
    # Merge
    merged = pd.merge_asof(
        sentiment_df.sort_values('timestamp_rounded'),
        price_df.sort_values('timestamp_rounded'),
        left_on='timestamp_rounded',
        right_on='timestamp_rounded',
        direction='backward'  # Use most recent price data
    )
    
    print(f"   Original sentiment data: {len(sentiment_df)} rows")
    print(f"   Merged data: {len(merged)} rows")
    print(f"   Rows with price data: {merged['price'].notna().sum()}")
    
    return merged

def main():
    print("="*60)
    print("🔄 REBUILDING DATASET WITH PRICE FEATURES")
    print("="*60)
    
    # Load sentiment data
    if not os.path.exists(DATA_PATH):
        print(f"❌ Sentiment data not found: {DATA_PATH}")
        return
    
    sentiment_df = pd.read_csv(DATA_PATH)
    print(f"\n✅ Loaded sentiment data: {len(sentiment_df)} rows")
    
    # Get time range
    if 'window_start' not in sentiment_df.columns:
        print("❌ No 'window_start' column found")
        return
    
    min_time = sentiment_df['window_start'].min()
    max_time = sentiment_df['window_start'].max()
    
    print(f"   Time range: {datetime.fromtimestamp(min_time)} to {datetime.fromtimestamp(max_time)}")
    
    # Fetch price data
    price_df = fetch_bitcoin_price_coingecko(int(min_time), int(max_time))
    
    if price_df is None:
        print("\n❌ Failed to fetch price data. Trying alternative approach...")
        print("   Consider using local OHLCV data if available.")
        return
    
    # Engineer features
    price_df = engineer_price_features(price_df)
    
    # Merge
    merged_df = merge_with_sentiment(sentiment_df, price_df)
    
    # Save
    merged_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n💾 Saved merged data to: {OUTPUT_PATH}")
    print(f"   Total rows: {len(merged_df)}")
    print(f"   Total features: {len(merged_df.columns)}")
    
    # Show sample
    print("\n📊 Sample of new features:")
    price_cols = ['price', 'return_1', 'volatility_10', 'rsi_14', 'macd', 'bb_width']
    available_cols = [c for c in price_cols if c in merged_df.columns]
    print(merged_df[available_cols].head(10))
    
    print("\n✅ Dataset preparation complete!")

if __name__ == "__main__":
    main()
