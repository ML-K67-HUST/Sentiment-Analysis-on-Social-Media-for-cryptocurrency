"""
Export Labeled Aggregated Data to CSV for Training
Queries `aggregated_features_10min` and flattens it for `push_training.py`
"""
import pandas as pd
from database.mongodb import MongoManager
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import config

def export_data():
    print("🚀 Exporting Labeled Data for Training...")
    
    # Initialize MongoDB
    conn_str = config.MONGODB_CONNECTION_STRING
    if "@mongodb" in conn_str:
        conn_str = conn_str.replace("@mongodb", "@localhost")
    mongo_client = MongoManager('blog-data', uri=conn_str)
    
    # Query Labeled Data
    pipeline = [
        {
            "$match": {
                "aggregation_status": "complete",
                "labeled": True
            }
        }
    ]
    
    data = list(mongo_client.aggregate('aggregated_features_10min', pipeline))
    print(f"   Found {len(data)} labeled records.")
    
    if not data:
        print("❌ No labeled data found to export.")
        return

    # Flatten Data
    flattened_data = []
    
    for record in data:
        row = {
            'window_start': record.get('window_start'),
            'window_end': record.get('window_end'),
            'num_articles': record.get('num_articles'),
            'llm_sentiment_avg': record.get('llm_sentiment_avg'),
            'llm_confidence_avg': record.get('llm_confidence_avg'),
            'btc_price': record.get('btc_price'),
            'price_movement_10min': record.get('price_movement_10min')
        }
        
        # Flatten NLP features
        nlp_feats = record.get('nlp_features_agg', {})
        for k, v in nlp_feats.items():
            row[f'nlp_features_agg.{k}'] = v
            
        flattened_data.append(row)
        
    df = pd.DataFrame(flattened_data)
    
    # Sort by time
    df = df.sort_values('window_start')
    
    output_path = "sentiman_labeled_data.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Exported {len(df)} rows to {output_path}")
    print(f"   Columns: {list(df.columns)}")

if __name__ == "__main__":
    export_data()
