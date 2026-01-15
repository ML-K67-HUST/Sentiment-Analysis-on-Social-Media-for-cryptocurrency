#!/usr/bin/env python3
"""
Data Leakage Detection: Correlation Analysis
Identify features that are suspiciously correlated with target (potential leakage)
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiman_labeled_data.csv")

# All features
FEATURES = [
    'num_articles',
    'llm_sentiment_avg',
    'llm_confidence_avg',
    'nlp_features_agg.avg_positive_word_ratio',
    'nlp_features_agg.avg_negative_word_ratio',
    'nlp_features_agg.avg_neutral_word_ratio',
    'nlp_features_agg.avg_compound_score',
    'nlp_features_agg.total_avg_sentence_length',
    'nlp_features_agg.total_word_count',
    'nlp_features_agg.avg_unique_word_ratio',
    'nlp_features_agg.total_exclamation_count',
    'nlp_features_agg.total_question_count',
    'nlp_features_agg.total_btc_mention_count',
    'nlp_features_agg.total_price_keyword_count',
    'nlp_features_agg.avg_technical_term_ratio',
    'nlp_features_agg.total_ne_person_count',
    'nlp_features_agg.total_ne_org_count'
]

TARGET = 'price_movement_10min'

def analyze_correlations():
    """Compute correlations between features and target"""
    print("="*60)
    print("🔍 DATA LEAKAGE DETECTION: Correlation Analysis")
    print("="*60)
    print("\nGoal: Find features with suspiciously high correlation")
    print("Threshold: |correlation| > 0.8 → Potential leakage\n")
    
    # Load data
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} samples\n")
    
    # Check target
    if TARGET not in df.columns:
        print(f"❌ Target '{TARGET}' not found!")
        return
    
    # Filter available features
    available_features = [f for f in FEATURES if f in df.columns]
    print(f"📊 Analyzing {len(available_features)} features\n")
    
    # Compute correlations
    correlations = []
    
    print("="*60)
    print("CORRELATION WITH TARGET")
    print("="*60)
    
    for feature in available_features:
        # Remove NaN
        valid_idx = ~(df[feature].isna() | df[TARGET].isna())
        x = df.loc[valid_idx, feature]
        y = df.loc[valid_idx, TARGET]
        
        if len(x) == 0:
            continue
        
        # Pearson correlation
        corr, p_value = pearsonr(x, y)
        
        correlations.append({
            'feature': feature,
            'correlation': corr,
            'abs_correlation': abs(corr),
            'p_value': p_value,
            'n_samples': len(x)
        })
    
    # Sort by absolute correlation
    corr_df = pd.DataFrame(correlations)
    corr_df = corr_df.sort_values('abs_correlation', ascending=False)
    
    # Print results
    print(f"{'Feature':<45} {'Corr':<10} {'|Corr|':<10} {'P-value':<12} Status")
    print("-"*90)
    
    for _, row in corr_df.iterrows():
        feature = row['feature']
        corr = row['correlation']
        abs_corr = row['abs_correlation']
        p_val = row['p_value']
        
        # Determine status
        if abs_corr > 0.8:
            status = "🚨 VERY SUSPICIOUS (Likely Leakage)"
        elif abs_corr > 0.5:
            status = "⚠️  High correlation"
        elif abs_corr > 0.3:
            status = "✅ Moderate (Normal)"
        else:
            status = "✅ Low (Safe)"
        
        # Shorten feature name for display
        display_name = feature.replace('nlp_features_agg.', '').replace('total_', 't_').replace('avg_', 'a_')
        
        print(f"{display_name:<45} {corr:>+9.4f} {abs_corr:>9.4f} {p_val:>11.2e} {status}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("📊 SUMMARY STATISTICS")
    print("="*60)
    
    very_high = len(corr_df[corr_df['abs_correlation'] > 0.8])
    high = len(corr_df[(corr_df['abs_correlation'] > 0.5) & (corr_df['abs_correlation'] <= 0.8)])
    moderate = len(corr_df[(corr_df['abs_correlation'] > 0.3) & (corr_df['abs_correlation'] <= 0.5)])
    low = len(corr_df[corr_df['abs_correlation'] <= 0.3])
    
    print(f"🚨 Very High (>0.8): {very_high} features")
    print(f"⚠️  High (0.5-0.8):   {high} features")
    print(f"✅ Moderate (0.3-0.5): {moderate} features")
    print(f"✅ Low (<0.3):        {low} features")
    
    # Recommendations
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    suspicious = corr_df[corr_df['abs_correlation'] > 0.8]
    
    if len(suspicious) > 0:
        print("⚠️  POTENTIAL DATA LEAKAGE DETECTED!")
        print("\nFeatures to investigate:")
        for _, row in suspicious.iterrows():
            feat = row['feature'].replace('nlp_features_agg.', '')
            print(f"   - {feat} (r={row['correlation']:+.3f})")
        
        print("\nPossible causes:")
        print("   1. Feature computed AFTER target event (time contamination)")
        print("   2. Feature derived from target (circular dependency)")
        print("   3. Spurious correlation (both affected by third variable)")
        
        print("\nSuggested actions:")
        print("   1. Remove highly correlated features")
        print("   2. Add time lag (use news [t-20, t-10] for price [t, t+10])")
        print("   3. Cross-validate on completely separate time period")
    else:
        print("✅ No obvious data leakage detected")
        print("   All correlations are within reasonable range")
    
    # Save results
    corr_df.to_csv('correlation_analysis.csv', index=False)
    print(f"\n💾 Results saved to correlation_analysis.csv")
    
    # Create visualization
    print("\n📊 Generating correlation heatmap...")
    
    # Create feature-target correlation bar plot
    plt.figure(figsize=(12, 8))
    
    # Top 10 by absolute correlation
    top_10 = corr_df.head(10)
    
    colors = ['red' if abs(c) > 0.8 else 'orange' if abs(c) > 0.5 else 'green' 
              for c in top_10['correlation']]
    
    plt.barh(range(len(top_10)), top_10['correlation'], color=colors)
    plt.yticks(range(len(top_10)), 
               [f.replace('nlp_features_agg.', '').replace('total_', 't_').replace('avg_', 'a_') 
                for f in top_10['feature']])
    plt.xlabel('Correlation with Price Movement')
    plt.title('Top 10 Features by Correlation with Target')
    plt.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    plt.axvline(x=0.8, color='red', linestyle='--', label='Leakage threshold')
    plt.axvline(x=-0.8, color='red', linestyle='--')
    plt.legend()
    plt.tight_layout()
    plt.savefig('correlation_analysis.png', dpi=150)
    print("   ✅ Saved to correlation_analysis.png")
    
    return corr_df

if __name__ == "__main__":
    analyze_correlations()
