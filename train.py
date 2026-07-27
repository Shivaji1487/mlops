import os
import pandas as pd
import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature

# Config & S3 Setup
MINIO_ENDPOINT = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://192.168.235.130:9000")
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

os.environ["AWS_ACCESS_KEY_ID"] = AWS_KEY
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET
os.environ["MLFLOW_S3_ENDPOINT_URL"] = MINIO_ENDPOINT

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://192.168.235.130:5000"))
mlflow.set_experiment("Production_Customer_Tiering")


# 🛡️ INDUSTRY STEP: Simple & Effective Data Validation
def validate_data(df: pd.DataFrame):
    print("🔍 Starting Data Validation Checks...")
    
    # 1. Schema / Column Check
    required_cols = {'Auto Renew', 'Subscription Count', 'Subscription Term'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"❌ Data Validation Failed: Missing columns {missing_cols}")
        
    # 2. Null Value Check
    if df[list(required_cols)].isnull().any().any():
        raise ValueError("❌ Data Validation Failed: Found NULL values in required features")
        
    # 3. Data Integrity Check (Negative values check)
    if (df['Subscription Count'] < 0).any():
        raise ValueError("❌ Data Validation Failed: 'Subscription Count' cannot be negative")

    print("✅ Data Validation Passed Successfully!")


@mlflow.trace(name="evaluate_customer_tier")
def evaluate_row(row):
    auto_renew = True if str(row['Auto Renew']).strip().lower() == 'yes' else False
    subs = row['Subscription Count']
    term = str(row['Subscription Term']).strip().lower()
    if (auto_renew and subs >= 25) or subs > 35:
        return "Elite"
    elif term == 'yearly' or subs >= 15:
        return "Pro+"
    return "Normal"


class CustomerTieringModel(mlflow.pyfunc.PythonModel):
    @mlflow.trace(name="customer_tier_prediction_pipeline")
    def predict(self, context, model_input):
        df = model_input.copy()
        df['Predicted_Tier'] = df.apply(evaluate_row, axis=1)
        return df['Predicted_Tier']


if __name__ == "__main__":
    print("📥 Reading 'customer_data.csv' from MinIO S3 bucket...")
    s3_path = "s3://cust-tier/customer_data.csv"
    storage_options = {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT}
    }
    
    df = pd.read_csv(s3_path, storage_options=storage_options)
    
    # 🛡️ RUN DATA VALIDATION BEFORE TRAINING
    validate_data(df)

    X = df[['Auto Renew', 'Subscription Count', 'Subscription Term']]

    model = CustomerTieringModel()
    predictions = model.predict(context=None, model_input=X)
    signature = infer_signature(X, predictions)

    with mlflow.start_run(run_name="Jenkins_MinIO_Training_Run"):
        # Parameters
        mlflow.log_param("dataset_source", s3_path)
        mlflow.log_param("features_list", list(X.columns))

        # Metrics
        tier_counts = predictions.value_counts()
        total_records = len(df)
        
        mlflow.log_metric("total_customers_processed", float(total_records))
        mlflow.log_metric("elite_tier_count", float(tier_counts.get("Elite", 0)))
        mlflow.log_metric("pro_plus_tier_count", float(tier_counts.get("Pro+", 0)))
        mlflow.log_metric("normal_tier_count", float(tier_counts.get("Normal", 0)))

        # Log & Register
        mlflow.pyfunc.log_model(
            artifact_path="customer_tier_model",
            python_model=model,
            signature=signature,
            registered_model_name="CustomerTieringModel"
        )
        print("✅ Training complete with Data Validation & Traces captured!")