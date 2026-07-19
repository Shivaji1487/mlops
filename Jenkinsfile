pipeline {
    agent any

    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Checking and starting MLflow Tracking Server...'
                sh '''
                # PATH को Jenkins शेल के लिए एक्सपोर्ट करना ताकि वह mlflow ढूंढ सके
                export PATH=$PATH:/var/lib/jenkins/.local/bin
                
                fuser -k 5000/tcp || true
                nohup mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///tmp/mlflow.db --default-artifact-root /tmp/artifacts > /dev/null 2>&1 &
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
                sh 'docker run --rm --net=host -v $(pwd)/production.db:/app/production.db internal-mlops-engine:latest'
            }
        }
    }

    post {
        always {
            echo '🧹 Post-Execution Cleanup: Clearing Docker Cache...'
            sh 'docker image rm internal-mlops-engine:latest --force || true'
            sh 'docker image prune -f'
            cleanWs()
        }
    }
}