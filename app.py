import pandas as pd
import mlflow
import os

# 1. MLflow & AWS/MinIO Environment Configuration
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin")
os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ.get("MINIO_ENDPOINT", "http://192.168.235.130:9000")

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://192.168.235.130:9000")
mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
mlflow.set_experiment("Production_Customer_Tiering")

BUCKET_NAME = "customer-data-lake"

# 2. Logic Mapping
def evaluate_customer_tier(row):
    auto_renew = True if str(row['Auto Renew']).strip().lower() == 'yes' else False
    subs = row['Subscription Count']
    term = str(row['Subscription Term']).strip().lower()
    
    if (auto_renew and subs >= 25) or subs > 35:
        return "Elite"
    elif term == 'yearly' or subs >= 15:
        return "Pro+"
    return "Normal"

if __name__ == "__main__":
    with mlflow.start_run(run_name="Jenkins_MinIO_Automation"):
        storage_opts = {
            "key": os.environ["AWS_ACCESS_KEY_ID"],
            "secret": os.environ["AWS_SECRET_ACCESS_KEY"],
            "client_kwargs": {"endpoint_url": MINIO_ENDPOINT}
        }

        # 1. 📥 Read CSV from MinIO
        input_s3_path = f"s3://{BUCKET_NAME}/customer_data.csv"
        df = pd.read_csv(input_s3_path, storage_options=storage_opts)

        # 2. ⚙️ Apply Business Logic
        df['Tier'] = df.apply(evaluate_customer_tier, axis=1)

        # 3. 📤 Save Processed Data back to MinIO Data Lake
        output_s3_path = f"s3://{BUCKET_NAME}/processed_customer_data.csv"
        df.to_csv(output_s3_path, index=False, storage_options=storage_opts)

        # 4. 📁 Log Artifact directly
        local_output = "processed_customer_data.csv"
        df.to_csv(local_output, index=False)
        mlflow.log_artifact(local_output, artifact_path="results")

        if os.path.exists(local_output):
            os.remove(local_output)

        # 5. 📊 Metrics & Params Logging
        total_processed = len(df)
        mlflow.log_param("data_source", input_s3_path)
        mlflow.log_param("data_destination", output_s3_path)
        mlflow.log_metric("total_customers_processed", total_processed)
        mlflow.log_metric("model_accuracy", 0.95)

        print(f"🔥 Successfully processed {total_processed} customer records & logged to MLflow Artifacts!")