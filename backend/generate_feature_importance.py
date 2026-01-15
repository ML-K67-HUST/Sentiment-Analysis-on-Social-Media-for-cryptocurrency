
import pandas as pd
import numpy as np
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    data_path = "sentiman_labeled_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        sys.exit(1)
    return pd.read_csv(data_path)

def get_feature_importance():
    print("Loading data...")
    df = load_data()
    
    # Features as used in push_training.py
    feature_cols = [
        'num_articles', 'llm_sentiment_avg', 'llm_confidence_avg',
        'nlp_features_agg.avg_positive_word_ratio', 'nlp_features_agg.avg_negative_word_ratio',
        'nlp_features_agg.avg_neutral_word_ratio', 'nlp_features_agg.avg_compound_score',
        'nlp_features_agg.total_avg_sentence_length', 'nlp_features_agg.total_word_count',
        'nlp_features_agg.avg_unique_word_ratio', 'nlp_features_agg.total_exclamation_count',
        'nlp_features_agg.total_question_count', 'nlp_features_agg.total_btc_mention_count',
        'nlp_features_agg.total_price_keyword_count', 'nlp_features_agg.avg_technical_term_ratio',
        'nlp_features_agg.total_ne_person_count', 'nlp_features_agg.total_ne_org_count'
    ]
    target_col = 'price_movement_10min'
    
    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0)
    
    # Train Random Forest
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\nFeature Ranking:")
    print(f"{'Rank':<5} | {'Feature':<45} | {'Importance':<10}")
    print("-" * 65)
    
    results = []
    for f in range(X.shape[1]):
        feature_name = feature_cols[indices[f]]
        importance_val = importances[indices[f]]
        print(f"{f + 1:<5} | {feature_name:<45} | {importance_val:.5f}")
        results.append((feature_name, importance_val))
        
    return results

if __name__ == "__main__":
    get_feature_importance()
