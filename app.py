import os
import pandas as pd
import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature
from sklearn.metrics import accuracy_score

# Environment & Config Setup
os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://192.168.235.130:9000")

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://192.168.235.130:5000"))
mlflow.set_experiment("Production_Customer_Tiering")

# 1. Define Model Class for Registry
class CustomerTieringModel(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        # Create a copy to avoid modifying original dataframe
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
    # Dummy / Sample Evaluation Data (Validation Test)
    sample_data = pd.DataFrame([
        {'Auto Renew': 'Yes', 'Subscription Count': 30, 'Subscription Term': 'Yearly', 'Actual_Tier': 'Elite'},
        {'Auto Renew': 'No', 'Subscription Count': 10, 'Subscription Term': 'Monthly', 'Actual_Tier': 'Normal'},
        {'Auto Renew': 'Yes', 'Subscription Count': 18, 'Subscription Term': 'Monthly', 'Actual_Tier': 'Pro+'},
        {'Auto Renew': 'No', 'Subscription Count': 40, 'Subscription Term': 'Yearly', 'Actual_Tier': 'Elite'}
    ])

    X_test = sample_data[['Auto Renew', 'Subscription Count', 'Subscription Term']]
    y_true = sample_data['Actual_Tier']

    model = CustomerTieringModel()
    predictions = model.predict(context=None, model_input=X_test)

    # Calculate Evaluation Metrics
    acc = accuracy_score(y_true, predictions)

    # Infer Data Schema (Validation)
    signature = infer_signature(X_test, predictions)

    with mlflow.start_run(run_name="Jenkins_MinIO_Automation"):
        # 1. Log Metrics to MLflow UI
        mlflow.log_metric("accuracy", acc)
        mlflow.log_param("test_samples_count", len(sample_data))

        # 2. Log Model with Schema & Registered Name
        mlflow.pyfunc.log_model(
            artifact_path="customer_tier_model",
            python_model=model,
            signature=signature, # Enable Data Validation/Schema in MLflow UI
            registered_model_name="CustomerTieringModel"
        )
        print(f"✅ Model Version registered in MLflow! Accuracy Logged: {acc * 100}%")