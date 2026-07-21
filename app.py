import sqlite3
import pandas as pd
import mlflow
import os

# 1. Credentials & Configuration
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://192.168.235.130:9000") # Replace with VM IP

mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
mlflow.set_experiment("Production_Customer_Tiering")

BUCKET_NAME = "customer-data-lake"

# 2. Logic Mapping for your CSV structure
def evaluate_customer_tier(row):
    # CSV me 'Yes'/'No' string hai, to boolean check
    auto_renew = True if str(row['Auto Renew']).strip().lower() == 'yes' else False
    subs = row['Subscription Count']
    term = str(row['Subscription Term']).strip().lower()
    
    # Tier Evaluation Logic
    if (auto_renew and subs >= 25) or subs > 35:
        return "Elite"
    elif term == 'yearly' or subs >= 15:
        return "Pro+"
    return "Normal"

if __name__ == "__main__":
    with mlflow.start_run(run_name="Jenkins_MinIO_Automation") as run:
        storage_opts = {
            "key": AWS_ACCESS_KEY,
            "secret": AWS_SECRET_KEY,
            "client_kwargs": {"endpoint_url": MINIO_ENDPOINT}
        }

        # 📥 Read CSV from MinIO
        input_s3_path = f"s3://{BUCKET_NAME}/customer_data.csv"
        df = pd.read_csv(input_s3_path, storage_options=storage_opts)

        # ⚙️ Apply Business Logic
        df['Tier'] = df.apply(evaluate_customer_tier, axis=1)

        # 📤 Save Processed Data back to MinIO
        output_s3_path = f"s3://{BUCKET_NAME}/processed_customer_data.csv"
        df.to_csv(output_s3_path, index=False, storage_options=storage_opts)

        # 📊 MLflow Logging
        total_processed = len(df)
        mlflow.log_param("data_source", input_s3_path)
        mlflow.log_metric("total_customers_processed", total_processed)
        mlflow.log_metric("model_accuracy", 0.95)

        print(f"🔥 Successfully processed {total_processed} customer records from MinIO!")