import os
import pandas as pd
import mlflow
import mlflow.pyfunc

# Environment & Config Setup
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://192.168.235.130:9000"

mlflow.set_tracking_uri("http://192.168.235.130:5000")
mlflow.set_experiment("Production_Customer_Tiering")

# 1. Define Model Class for Registry
class CustomerTieringModel(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input):
        def evaluate(row):
            auto_renew = True if str(row['Auto Renew']).strip().lower() == 'yes' else False
            subs = row['Subscription Count']
            term = str(row['Subscription Term']).strip().lower()
            if (auto_renew and subs >= 25) or subs > 35:
                return "Elite"
            elif term == 'yearly' or subs >= 15:
                return "Pro+"
            return "Normal"
            
        model_input['Tier'] = model_input.apply(evaluate, axis=1)
        return model_input

if __name__ == "__main__":
    with mlflow.start_run(run_name="Jenkins_MinIO_Automation"):
        # Log & Register Model in MLflow Registry
        mlflow.pyfunc.log_model(
            artifact_path="customer_tier_model",
            python_model=CustomerTieringModel(),
            registered_model_name="CustomerTieringModel"
        )
        print("✅ Model Version registered in MLflow Model Registry!")