from fastapi import FastAPI, HTTPException
import numpy as np
import joblib
from pydantic import BaseModel
import mlflow.pyfunc
from sklearn.preprocessing import MinMaxScaler



def load_scaler():
    scaler = joblib.load('services/scaler.pkl')
    return scaler

# Define input schema
class PredictionInput(BaseModel):
    timestamp:float
    seven_days_ago: float
    one_days_ago: float
    twelve_hours_ago: float
    three_hours_ago: float
    bot_sentiment: float

app = FastAPI()
mlflow.set_tracking_uri("http://localhost:5001")
# Load the registered model and scaler
model_uri = "models:/BestModel/latest"  # Update with your model version or stage
model = mlflow.pyfunc.load_model(model_uri)
# scaler = joblib.load("scaler.pkl")  # Save the scaler during training
# scaler = load_scaler()

@app.post("/predict")
def predict(input_data: PredictionInput):
    try:
        input_features = np.array([[
            input_data.timestamp,
            input_data.seven_days_ago,
            input_data.one_days_ago,
            input_data.twelve_hours_ago,
            input_data.three_hours_ago,
            input_data.bot_sentiment
        ]])
        
        scaler = load_scaler()
        # Scale the input features
        normalized_features = scaler.transform(input_features)
        
        # Make prediction
        prediction = model.predict(normalized_features)
        return {"prediction": prediction.tolist()}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/")
def read_root():
    return {"message": "Welcome to the BestModel API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
