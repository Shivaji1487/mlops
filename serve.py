from fastapi import FastAPI
import mlflow.pyfunc
from pydantic import BaseModel
import pandas as pd

app = FastAPI(title="Customer Tiering Inference Service")

# 1. Server startup par Model Load
model_uri = "models:/CustomerTieringModel/Latest"
model = mlflow.pyfunc.load_model(model_uri)

class CustomerData(BaseModel):
    Auto_Renew: str
    Subscription_Count: int
    Subscription_Term: str

# 2. Health Check Endpoint (For Kubernetes)
@app.get("/health")
def health_check():
    return {"status": "healthy", "model_uri": model_uri}

# 3. Live Prediction Endpoint
@app.post("/predict")
def predict_tier(data: CustomerData):
    df = pd.DataFrame([{
        'Auto Renew': data.Auto_Renew,
        'Subscription Count': data.Subscription_Count,
        'Subscription Term': data.Subscription_Term
    }])
    
    prediction = model.predict(df)
    return {"predicted_tier": prediction[0]}