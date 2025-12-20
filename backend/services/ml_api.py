from fastapi import FastAPI, HTTPException
import numpy as np
import joblib
from pydantic import BaseModel
import mlflow.pyfunc

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
model = None
scaler = None

def load_scaler():
    """Load scaler for feature normalization"""
    global scaler
    if scaler is None:
        try:
            scaler = joblib.load('services/scaler_10min.pkl')
        except FileNotFoundError:
            # Fallback to old scaler if new one not found
            try:
                scaler = joblib.load('services/scaler.pkl')
            except:
                print("Warning: No scaler found")
    return scaler

def get_model():
    """Lazy load ML model from MLflow"""
    global model
    if model is None:
        try:
            # Try loading 10-min model first
            model_uri = "models:/BestModel_10min/Production"
            model = mlflow.pyfunc.load_model(model_uri)
        except Exception as e:
            # Fallback to old model
            try:
                model_uri = "models:/BestModel/Production"
                model = mlflow.pyfunc.load_model(model_uri)
            except Exception as e2:
                raise HTTPException(status_code=503, detail=f"Model not available: {e2}")
    return model

@app.post("/predict")
def predict(input_data: PredictionInput):
    """
    Predict Bitcoin price movement based on 10-min aggregated features
    
    Input: 17 features from aggregated 10-min window
    Output: Price movement prediction (percentage)
    """
    try:
        # Prepare feature vector (17 features in order)
        features = np.array([[
            input_data.num_articles,
            input_data.llm_sentiment_avg,
            input_data.llm_confidence_avg,
            # NLP features
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
        prediction = model.predict(features_scaled)
        
        return {
            "prediction": float(prediction[0]),
            "status": "success",
            "model_type": "10min_aggregated"
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
