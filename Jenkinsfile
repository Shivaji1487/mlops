pipeline {
    agent any
    
    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Cleaning older instances and starting MLflow...'
                sh '''
                export PATH=$PATH:/var/lib/jenkins/.local/bin
                
                # पोर्ट 5000 को साफ़ करें
                #fuser -k 5000/tcp || true
                
                # वर्कस्पेस के अंदर आर्टिफ़ैक्ट्स डायरेक्टरी सुनिश्चित करें
                mkdir -p ${WORKSPACE}/mlflow_artifacts
                
                # SQLite डेटाबेस को सीधे Jenkins वर्कस्पेस पाथ पर सेट करें
                nohup mlflow server \
                  --host 0.0.0.0 \
                  --port 5000 \
                  --backend-store-uri sqlite:///${WORKSPACE}/mlflow.db \
                  --default-artifact-root ${WORKSPACE}/mlflow_artifacts > mlflow_server.log 2>&1 &
                
                sleep 7
                
                if ! curl -sI http://127.0.0.1:5000; then
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
                HOST_IP=$(hostname -I | awk '{print $1}')
                echo "🎯 Host IP Detected: ${HOST_IP}"
                
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