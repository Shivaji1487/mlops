pipeline {
    agent any
    
    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Starting MLflow Server...'
                sh '''
                export PATH=$PATH:/var/lib/jenkins/.local/bin
                
                # पुराना कोई अटका हो तो साफ़ करें
                fuser -k 5000/tcp || true
                
                mkdir -p ${WORKSPACE}/mlflow_artifacts
                
                nohup mlflow server \
                  --host 0.0.0.0 \
                  --port 5000 \
                  --backend-store-uri sqlite:///${WORKSPACE}/mlflow.db \
                  --default-artifact-root ${WORKSPACE}/mlflow_artifacts > mlflow_server.log 2>&1 &
                
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
                sleep time: 3600, unit: 'SECONDS'
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