
import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    data_path = "sentiman_labeled_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        sys.exit(1)
    return pd.read_csv(data_path)

def analyze_correlations():
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
    
    # Fill NAs
    df_clean = df[feature_cols + [target_col]].fillna(0)
    
    # Calculate Correlation with Target
    correlations = df_clean.corr()[target_col].drop(target_col)
    
    # Sort by absolute value correlation
    sorted_corr = correlations.abs().sort_values(ascending=False)
    
    print("\nFeature Correlations with Price Movement (Pearson):")
    print(f"{'Rank':<5} | {'Feature':<45} | {'Correlation':<10}")
    print("-" * 65)
    
    for i, (feature, corr) in enumerate(sorted_corr.items()):
        raw_corr = correlations[feature]
        print(f"{i + 1:<5} | {feature:<45} | {raw_corr:.5f}")

    # Check Sentiment Stats
    print("\n\nSentiment Statistics:")
    print(df_clean['llm_sentiment_avg'].describe())

if __name__ == "__main__":
    analyze_correlations()
