pipeline {
    agent any
    
    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Starting MLflow Server...'
                sh '''
					export PATH=$PATH:/var/lib/jenkins/.local/bin
					fuser -k 5000/tcp || true
					
					# Set MinIO Credentials so MLflow Server can access it
					export AWS_ACCESS_KEY_ID="minioadmin"
					export AWS_SECRET_ACCESS_KEY="minioadmin"
					export MLFLOW_S3_ENDPOINT_URL="http://192.168.235.130:9000"
		
					# Pass MinIO S3 bucket path as default-artifact-root
					nohup mlflow server \
					--host 0.0.0.0 \
					--port 5000 \
					--backend-store-uri sqlite:////var/lib/jenkins/workspace/mlops-pipeline/mlflow.db \
					--default-artifact-root s3://customer-data-lake/mlflow-artifacts \
					> mlflow.log 2>&1 &
					
					sleep 5
			'''
            }
        }

        stage('Code Quality & DB Sync') {
            steps {
                sh '''
                python3 -m py_compile app.py database.py
                python3 database.py
                '''
            }
        }
        
        stage('Dockerize & Run MLOps Engine') {
            steps {
                sh '''
                docker build -t internal-mlops-engine:latest .
                HOST_IP=$(hostname -I | awk '{print $1}')
                
                docker run --rm \
                  --net=host \
                  -e MLFLOW_TRACKING_URI="http://${HOST_IP}:5000" \
                  -v $(pwd)/production.db:/app/production.db \
                  internal-mlops-engine:latest
                '''
            }
        }

        // ⏱️ यह स्टेज पाइपलाइन को लाइव रखेगा ताकि आप ब्राउज़र देख सकें
        stage('Keep Alive for UI Review') {
            steps {
                echo '⏱️ Pipeline is keeping MLflow alive for 2 minutes...'
                echo '👉 Open laptop terminal: ssh -L 8095:127.0.0.1:5000 jenkins@192.168.235.130'
                echo '👉 Open Browser: http://localhost:8095'
                
                // 120 सेकंड (2 मिनट) तक यह स्टेज चलता रहेगा, फिर अपने आप आगे बढ़ेगा
                sleep time: 7200, unit: 'SECONDS'
            }
        }
    }

    post {
        always {
            echo '🧹 Cleaning up everything automatically...'
            sh '''
            # Docker साफ़ करें
            docker image rm internal-mlops-engine:latest --force || true
            docker image prune -f
            
            # MLflow सर्वर को अपने आप बंद करें
            fuser -k 5000/tcp || true
            '''
            cleanWs()
        }
    }
}