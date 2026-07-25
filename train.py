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

if __name__ == "__main__":
    print("📥 Reading 'customer_data.csv' from MinIO S3 bucket...")
    s3_path = "s3://cust-tier/customer_data.csv"
    storage_options = {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT}
    }
    
    df = pd.read_csv(s3_path, storage_options=storage_options)
    X = df[['Auto Renew', 'Subscription Count', 'Subscription Term']]

    model = CustomerTieringModel()
    predictions = model.predict(context=None, model_input=X)
    signature = infer_signature(X, predictions)

    with mlflow.start_run(run_name="Jenkins_MinIO_Training_Run"):
        # 1. Model Parameters Logging
        mlflow.log_param("dataset_source", s3_path)
        mlflow.log_param("features_list", list(X.columns))

        # 2. Pure Model Metrics Logging
        tier_counts = predictions.value_counts()
        total_records = len(df)
        
        mlflow.log_metric("total_customers_processed", float(total_records))
        mlflow.log_metric("elite_tier_count", float(tier_counts.get("Elite", 0)))
        mlflow.log_metric("pro_plus_tier_count", float(tier_counts.get("Pro+", 0)))
        mlflow.log_metric("normal_tier_count", float(tier_counts.get("Normal", 0)))
        
        # Percentage distribution of tiers
        mlflow.log_metric("elite_tier_ratio", float(tier_counts.get("Elite", 0) / total_records))
        mlflow.log_metric("pro_plus_tier_ratio", float(tier_counts.get("Pro+", 0) / total_records))

        # 3. Log Model Artifact & Register
        mlflow.pyfunc.log_model(
            artifact_path="customer_tier_model",
            python_model=model,
            signature=signature,
            registered_model_name="CustomerTieringModel"
        )
        print("✅ Model trained & Model-related metrics logged successfully!")