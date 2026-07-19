pipeline {
    agent any

    stages {
        stage('Start MLflow Server') {
            steps {
                echo '🚀 Starting MLflow Tracking Server in background...'
                // यह कमांड चेक करेगी कि पोर्ट 5000 खाली है या नहीं, और बैकग्राउंड में MLflow शुरू कर देगी
                sh '''
                if ! pip3 show mlflow > /dev/null 2>&1; then
                    echo "Installing mlflow on host..."
                    pip3 install --user mlflow
                fi
                
                # पोर्ट 5000 पर पुराना कोई प्रोसेस चल रहा हो तो उसे हटाना और नया सर्वर बैकग्राउंड में शुरू करना
                fuser -k 5000/tcp || true
                nohup mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///tmp/mlflow.db --default-artifact-root /tmp/artifacts > /dev/null 2>&1 &
                sleep 5
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
        
        stage('Dockerize & Run Model') {
            steps {
                echo '🏗️ Building Docker Container and logging to MLflow...'
                sh 'docker build -t internal-mlops-engine:latest .'
                // --net=host की मदद से कंटेनर सीधे होस्ट के localhost:5000 (MLflow) को एक्सेस कर पाएगा
                sh 'docker run --rm --net=host -v $(pwd)/production.db:/workspace/production.db internal-mlops-engine:latest'
            }
        }
    }

    post {
        always {
            echo '🧹 Clearing Docker Cache to save RHEL Disk Space...'
            sh 'docker image rm internal-mlops-engine:latest --force || true'
            sh 'docker image prune -f'
            cleanWs()
        }
    }
}