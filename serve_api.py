from fastapi import FastAPI
import mlflow.pyfunc
import pandas as pd
import os

app = FastAPI(title="Customer Tiering Production API")

# MinIO & MLflow Configuration
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://192.168.235.130:9000"
mlflow.set_tracking_uri("http://192.168.235.130:5000")

# Load registered model from MLflow
MODEL_URI = "models:/CustomerTieringModel/latest"
model = mlflow.pyfunc.load_model(MODEL_URI)

@app.post("/predict")
def predict_tier(customer_data: dict):
    # Convert incoming JSON payload to DataFrame
    df = pd.DataFrame([customer_data])
    result = model.predict(df)
    return {"status": "success", "predicted_tier": result['Tier'].iloc[0]}