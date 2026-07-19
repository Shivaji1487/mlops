pipeline {
    agent any
    
    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Cleaning older instances and starting MLflow...'
                sh '''
                export PATH=$PATH:/var/lib/jenkins/.local/bin
                
                # पोर्ट 5000 को पूरी तरह साफ़ करें
                fuser -k 5000/tcp || true
                
                # डायरेक्टरी मौजूद होना सुनिश्चित करें
                mkdir -p /tmp/artifacts
                
                # बैकग्राउंड में शुरू करने के बाद उसका PID सेव करें
                nohup mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///tmp/mlflow.db --default-artifact-root /tmp/artifacts > mlflow_server.log 2>&1 &
                
                sleep 5
                
                # अगर सर्वर क्रैश हुआ होगा, तो यहाँ लॉग प्रिंट हो जाएंगे
                if ! text=$(curl -sI http://127.0.0.1:5000); then
                    echo "❌ MLflow Server failed to start! Printing logs:"
                    cat mlflow_server.log
                    exit 1
                fi
                echo "✅ MLflow server is successfully up and running!"
                '''
            }
        }

        stage('Code Quality Check') {
            steps {
                echo '🔍 Checking Python Syntax...'
                sh 'python3 -m py_compile app.py database.py'
            }
        }
        
        stage('Database Sync') {
            steps {
                echo '🔄 Syncing Production Database...'
                sh 'python3 database.py'
            }
        }
        
        stage('Dockerize & Run Pipeline') {
            steps {
                echo '🏗️ Building Immutable Docker Container...'
                sh 'docker build -t internal-mlops-engine:latest .'
                
                echo '🏃 Running Containerized Model Logic with Host Network...'
                sh '''
                # होस्ट मशीन का असली IP एड्रेस निकालें ताकि कंटेनर भ्रमित न हो
                HOST_IP=$(hostname -I | awk '{print $1}')
                echo "🎯 Host IP Detected: ${HOST_IP}"
                
                # कंटेनर चलाते समय MLFLOW_TRACKING_URI एनवायरनमेंट वेरिएबल के रूप में पास करें
                docker run --rm \
                  --net=host \
                  -e MLFLOW_TRACKING_URI="http://${HOST_IP}:5000" \
                  -v $(pwd)/production.db:/app/production.db \
                  internal-mlops-engine:latest
                '''
            }
        }
    }

    post {
        always {
            echo '🧹 Post-Execution Cleanup: Clearing Space...'
            sh '''
            docker image rm internal-mlops-engine:latest --force || true
            docker image prune -f
            fuser -k 5000/tcp || true
            '''
            cleanWs()
        }
    }
}