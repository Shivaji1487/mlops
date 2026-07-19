pipeline {
    agent any

    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Checking and starting MLflow Tracking Server...'
                sh '''
                # 1. यदि होस्ट पर mlflow नहीं है, तो उसे इंस्टॉल करें
                if ! pip3 show mlflow > /dev/null 2>&1; then
                    echo "Installing mlflow on host..."
                    pip3 install --user mlflow
                fi
                
                # 2. पोर्ट 5000 को खाली करें ताकि पुराना प्रोसेस अटक न जाए
                fuser -k 5000/tcp || true
                
                # 3. MLflow सर्वर को बैकग्राउंड में चालू करें
                nohup mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///tmp/mlflow.db --default-artifact-root /tmp/artifacts > /dev/null 2>&1 &
                
                # सर्वर को ठीक से बूट होने के लिए 5 सेकंड का समय दें
                sleep 5
                '''
            }
        }

        stage('Code Quality Check') {
            steps {
                echo '🔍 Checking Python Syntax and Errors...'
                sh 'python3 -m py_compile app.py database.py'
            }
        }
        
        stage('Database Sync') {
            steps {
                echo '🔄 Syncing Production Database via database.py...'
                sh 'python3 database.py'
            }
        }
        
        stage('Dockerize & Run Pipeline') {
            steps {
                echo '🏗️ Building Immutable Docker Container...'
                sh 'docker build -t internal-mlops-engine:latest .'
                
                echo '🏃 Running Containerized Model Logic...'
                # नोट: $(pwd)/production.db को कंटेनर के WORKDIR यानी /app/production.db पर माउंट किया गया है, 
                # और --net=host ताकि कंटेनर आसानी से बाहर चल रहे MLflow (localhost:5000) से बात कर सके।
                sh 'docker run --rm --net=host -v $(pwd)/production.db:/app/production.db internal-mlops-engine:latest'
            }
        }
    }

    post {
        always {
            echo '🧹 Post-Execution Cleanup: Clearing Docker Cache to save RHEL Disk Space...'
            // आपकी 32GB/47GB की लिमिट को मेंटेन रखने के लिए क्लीनअप
            sh 'docker image rm internal-mlops-engine:latest --force || true'
            sh 'docker image prune -f'
            cleanWs()
        }
    }
}