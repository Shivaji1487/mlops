import os
import pandas as pd
import mlflow
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Config Setup
os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://192.168.235.130:9000")

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://192.168.235.130:5000"))

app = FastAPI(title="Customer Tiering Serving API")

# Global model variable
model = None

class PredictionInput(BaseModel):
    auto_renew: str
    subscription_count: int
    subscription_term: str

@app.on_event("startup")
def load_latest_model():
    global model
    try:
        # Load latest model version from MLflow Registry
        model_uri = "models:/CustomerTieringModel/latest"
        print(f"📦 Loading model from MLflow Registry: {model_uri}")
        model = mlflow.pyfunc.load_model(model_uri)
        print("✅ Model loaded successfully and ready for serving!")
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)}")

@app.get("/health")
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    return {"status": "healthy", "service": "Customer Tiering Inference API"}

@app.post("/predict")
def predict(payload: PredictionInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model service uninitialized")
    
    input_data = pd.DataFrame([{
        'Auto Renew': payload.auto_renew,
        'Subscription Count': payload.subscription_count,
        'Subscription Term': payload.subscription_term
    }])
    
    prediction = model.predict(input_data)
    return {"predicted_tier": prediction[0]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)