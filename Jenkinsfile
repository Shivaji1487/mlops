pipeline {
    agent any

    stages {
        stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Starting MLflow Tracking Server properly...'
                sh '''
                # 1. Jenkins को बैकग्राउंड प्रोसेस किल करने से रोकें
                export JENKINS_NODE_COOKIE=dontKillMe
                
                # अगर आपके यूजर प्रोफाइल में पाथ पहले से जुड़ा है तो ठीक, नहीं तो इसे सेफ साइड रखें
                export PATH=$PATH:/var/lib/jenkins/.local/bin
                
                # 2. पोर्ट 5000 पर पुराने अटके प्रोसेस को साफ़ करें
                fuser -k 5000/tcp || true
                
                # 3. MLflow सर्वर को शुरू करें
                nohup mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///tmp/mlflow.db --default-artifact-root /tmp/artifacts > mlflow_server.log 2>&1 &
                
                # 4. सर्वर को शुरू होने के लिए पर्याप्त (7 सेकंड) का समय दें
                sleep 7
                
                # 5. चेक करें कि बैकग्राउंड में सर्वर एक्टिव है या नहीं (डीबगिंग के लिए)
                curl -I http://127.0.0.1:5000 || echo "⚠️ MLflow server might still be starting..."
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
                
                echo '🏃 Running Containerized Model Logic...'
                # --net=host मोड होस्ट के नेटवर्क स्टैक का उपयोग करता है
                sh 'docker run --rm --net=host -v $(pwd)/production.db:/app/production.db internal-mlops-engine:latest'
            }
        }
    }

    post {
        always {
            echo '🧹 Post-Execution Cleanup: Clearing Space...'
            sh 'docker image rm internal-mlops-engine:latest --force || true'
            sh 'docker image prune -f'
            
            # (ऑप्शनल) अगर आप पाइपलाइन खत्म होने के बाद MLflow बंद करना चाहते हैं तो:
            # sh 'fuser -k 5000/tcp || true'
            
            cleanWs()
        }
    }
}