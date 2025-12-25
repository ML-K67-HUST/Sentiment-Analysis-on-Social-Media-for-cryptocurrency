import os
from fastapi import FastAPI, HTTPException
import numpy as np
import joblib
from pydantic import BaseModel
import mlflow.pyfunc
from mlflow import MlflowClient
from datetime import datetime

# Define input schema for 10-min aggregated features
class PredictionInput(BaseModel):
    num_articles: int
    llm_sentiment_avg: float
    llm_confidence_avg: float
    # NLP aggregated features (14)
    avg_positive_word_ratio: float
    avg_negative_word_ratio: float
    avg_neutral_word_ratio: float
    avg_compound_score: float
    total_avg_sentence_length: float
    total_word_count: int
    avg_unique_word_ratio: float
    total_exclamation_count: int
    total_question_count: int
    total_btc_mention_count: int
    total_price_keyword_count: int
    avg_technical_term_ratio: float
    total_ne_person_count: int
    total_ne_org_count: int

app = FastAPI()
mlflow.set_tracking_uri("http://mlflow:5000")

# Global model and scaler variables (lazy loading)
# Global variables
model = None
scaler = None
model_meta = {"last_train_time": "Unknown"}

def load_scaler():
    """Load scaler for feature normalization"""
    global scaler
    if scaler is None:
        try:
            scaler = joblib.load('services/scaler_10min.pkl')
            print(f"✅ Loaded scaler_10min.pkl with {scaler.n_features_in_} features")
        except FileNotFoundError:
            print("❌ scaler_10min.pkl NOT FOUND. Cannot load scaler.")
            raise HTTPException(status_code=500, detail="ML Scaler file missing")
        except Exception as e:
            print(f"❌ Error loading scaler: {e}")
            raise HTTPException(status_code=500, detail=f"Scaler load error: {e}")
    return scaler

def get_model():
    """Lazy load ML model from MLflow"""
    global model, model_meta
    if model is None:
        try:
            # Try loading 10-min model first
            model_uri = "models:/BestModel_10min/Production"
            model = mlflow.pyfunc.load_model(model_uri)
            print("✅ Loaded BestModel_10min from MLflow")
            
            # Fetch metadata
            try:
                client = MlflowClient()
                versions = client.get_latest_versions("BestModel_10min", stages=["Production"])
                if versions:
                    ts_ms = versions[0].creation_timestamp
                    dt = datetime.fromtimestamp(ts_ms / 1000.0)
                    model_meta["last_train_time"] = dt.strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                print(f"⚠️ Failed to fetch model metadata: {e}")
                
        except Exception as e:
            print(f"⚠️ Failed to load model: {e}")
            model = None
    return model


@app.post("/predict")
def predict(input_data: PredictionInput):
    """
    Predict Bitcoin price movement based on 10-min aggregated features
    """
    try:
        # Prepare feature vector (17 features)
        features = np.array([[
            input_data.num_articles,
            input_data.llm_sentiment_avg,
            input_data.llm_confidence_avg,
            input_data.avg_positive_word_ratio,
            input_data.avg_negative_word_ratio,
            input_data.avg_neutral_word_ratio,
            input_data.avg_compound_score,
            input_data.total_avg_sentence_length,
            input_data.total_word_count,
            input_data.avg_unique_word_ratio,
            input_data.total_exclamation_count,
            input_data.total_question_count,
            input_data.total_btc_mention_count,
            input_data.total_price_keyword_count,
            input_data.avg_technical_term_ratio,
            input_data.total_ne_person_count,
            input_data.total_ne_org_count
        ]])
        
        # Scale features
        scaler = load_scaler()
        if scaler:
            features_scaled = scaler.transform(features)
        else:
            features_scaled = features
            
        # Get model and predict
        model = get_model()
        
        if model is None:
            # Fallback if model is missing (e.g. registry wiped)
            # Use simple heuristic: if sentiment > 0.6 -> UP, else -> DOWN
            sentiment = input_data.llm_sentiment_avg
            dummy_prediction = 0.02 * (sentiment - 0.5) # Simple linear mapping
            print(f"⚠️ Using FALLBACK heuristic. Sentiment={sentiment}, Pred={dummy_prediction}")
            return {
                "prediction": float(dummy_prediction),
                "status": "fallback",
                "model_type": "heuristic",
                "last_train_time": model_meta.get("last_train_time", "Unknown")
            }

        prediction = model.predict(features_scaled)
        
        return {
            "prediction": float(prediction[0]),
            "status": "success",
            "model_type": "10min_aggregated",
            "last_train_time": model_meta.get("last_train_time", "Unknown")
        }


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "model": "BestModel_10min",
        "features": 17,
        "aggregation_window": "10 minutes"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
