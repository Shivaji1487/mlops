pipeline {
    agent any

    stages {
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
                // Local DB को कंटेनर के अंदर माउंट करके रन करना
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