import os
import pandas as pd

def validate_data(df: pd.DataFrame) -> bool:
    print("🔍 [Data Validation] Starting Quality Checks...")
    
    # 1. Required Columns Check
    required_cols = {'Auto Renew', 'Subscription Count', 'Subscription Term'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"❌ [Validation Error] Missing required columns: {missing_cols}")
        
    # 2. Null Value Check
    if df[list(required_cols)].isnull().any().any():
        raise ValueError("❌ [Validation Error] Found NULL values in key features")
        
    # 3. Data Integrity Check
    if (df['Subscription Count'] < 0).any():
        raise ValueError("❌ [Validation Error] 'Subscription Count' contains negative values")

    print("✅ [Data Validation] All checks passed successfully!")
    return True

if __name__ == "__main__":
    # MinIO se data read karke standalone validation run karein
    MINIO_ENDPOINT = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://192.168.235.130:9000")
    AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

    s3_path = "s3://cust-tier/customer_data.csv"
    storage_options = {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT}
    }
    
    df = pd.read_csv(s3_path, storage_options=storage_options)
    validate_data(df)