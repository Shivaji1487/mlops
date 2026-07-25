import os
import pandas as pd
import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature
from sklearn.metrics import accuracy_score
from fastapi import FastAPI
import uvicorn

# ------------------------------------------------------------------
# 1. Environment & MLflow Setup
# ------------------------------------------------------------------
MINIO_ENDPOINT = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://192.168.235.130:9000")
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

os.environ["AWS_ACCESS_KEY_ID"] = AWS_KEY
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://192.168.235.130:5000"))
mlflow.set_experiment("Production_Customer_Tiering")


# ------------------------------------------------------------------
# 2. Define Model Class
# ------------------------------------------------------------------
class CustomerTieringModel(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        df = model_input.copy()
        
        def evaluate(row):
            auto_renew = True if str(row['Auto Renew']).strip().lower() == 'yes' else False
            subs = row['Subscription Count']
            term = str(row['Subscription Term']).strip().lower()
            if (auto_renew and subs >= 25) or subs > 35:
                return "Elite"
            elif term == 'yearly' or subs >= 15:
                return "Pro+"
            return "Normal"
            
        df['Predicted_Tier'] = df.apply(evaluate, axis=1)
        return df['Predicted_Tier']


# ------------------------------------------------------------------
# 3. FastAPI Service Initialization
# ------------------------------------------------------------------
app = FastAPI(title="Customer Tiering MLOps Service")

@app.get("/")
def home():
    return {"status": "running", "service": "Customer Tiering Prediction API"}

@app.get("/health")
def health():
    return {"status": "healthy"}


# ------------------------------------------------------------------
# 4. Read Real Data from MinIO & Train/Log Model
# ------------------------------------------------------------------
def train_and_log_model():
    print("📥 Reading real data 'customer_data.csv' from MinIO S3 bucket 'cust-tier'...")
    
    # Reading directly from MinIO using S3 protocol
    s3_path = "s3://cust-tier/customer_data.csv"
    storage_options = {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT}
    }
    
    # Fetching real CSV
    df = pd.read_csv(s3_path, storage_options=storage_options)
    
    X = df[['Auto Renew', 'Subscription Count', 'Subscription Term']]
    
    model = CustomerTieringModel()
    predictions = model.predict(context=None, model_input=X)

    # Infer Data Schema / Signature from real data
    signature = infer_signature(X, predictions)

    with mlflow.start_run(run_name="Jenkins_MinIO_Automation"):
        mlflow.log_param("dataset_source", s3_path)
        mlflow.log_param("total_records_processed", len(df))

        # Log accuracy if 'Actual_Tier' column exists in CSV
        if 'Actual_Tier' in df.columns:
            acc = accuracy_score(df['Actual_Tier'], predictions)
            mlflow.log_metric("accuracy", acc)
            print(f"📊 Evaluated Accuracy on Real Data: {acc * 100}%")

        mlflow.pyfunc.log_model(
            artifact_path="customer_tier_model",
            python_model=model,
            signature=signature,
            registered_model_name="CustomerTieringModel"
        )
        print("✅ Real Model Version registered in MLflow from MinIO Data!")


# Execute Pipeline on Startup
@app.on_event("startup")
def startup_event():
    train_and_log_model()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)