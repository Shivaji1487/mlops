import sqlite3
import pandas as pd
import mlflow

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("Production_Customer_Tiering")

def evaluate_customer_tier(row):
    auto_renew = row['auto_renewal']
    years = row['years_as_customer']
    subs = row['subscriptions']
    if (auto_renew and years > 3) or (subs > 5):
        return "Elite"
    if subs < 5 and years > 3:
        return "Pro+"
    return "Normal"

if __name__ == "__main__":
    with mlflow.start_run(run_name="Jenkins_DB_Automation"):
        mlflow.log_param("pipeline_stage", "QA_DB_Read_Baseline")
        
        # 🔗 डेटाबेस से सीधे डेटा खींचना (Real Industry Style)
        conn = sqlite3.connect("production.db")
        df = pd.read_sql_query("SELECT * FROM customer_data", conn)
        conn.close()

        # मॉडल लॉजिक चलाना
        df['tier'] = df.apply(evaluate_customer_tier, axis=1)

        total_processed = len(df)
        mlflow.log_metric("total_customers_processed", total_processed)
        
        output_file = "processed_metrics.csv"
        df.to_csv(output_file, index=False)
        mlflow.log_artifact(output_file)
        
        print(f"🔥 Successfully processed {total_processed} records from Database!")