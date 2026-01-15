
import pandas as pd
import numpy as np
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    data_path = "sentiman_labeled_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        sys.exit(1)
    return pd.read_csv(data_path)

def evaluate_models():
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
    
    # 70/15/15 Split
    # First split: Train (70%) vs Temp (30%)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, shuffle=False)
    # Second split: Val (15%) vs Test (15%) -> Split Temp in half
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, shuffle=False)
    
    print(f"Data Split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    models = {
        "Baseline (Dummy)": DummyRegressor(strategy="mean"),
        "Linear Regression": Pipeline([('scaler', StandardScaler()), ('model', LinearRegression())]),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42, n_jobs=1)
    }
    
    results = []
    
    print("\nTraining and Evaluating Models on TEST SET...")
    print(f"{'Model':<25} | {'MAE':<10} | {'MSE':<10} | {'R2':<10}")
    print("-" * 65)
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"{name:<25} | {mae:<10.5f} | {mse:<10.5f} | {r2:<10.5f}")
        results.append({
            "Model": name,
            "MAE": f"{mae:.5f}",
            "MSE": f"{mse:.5f}",
            "R2": f"{r2:.5f}"
        })

if __name__ == "__main__":
    evaluate_models()
