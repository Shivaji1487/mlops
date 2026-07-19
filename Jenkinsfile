stage('Start MLflow Tracking Server') {
            steps {
                echo '🚀 Cleaning older instances and starting MLflow...'
                sh '''
                export PATH=$PATH:/var/lib/jenkins/.local/bin
                
                # पोर्ट 5000 को साफ़ करें
                fuser -k 5000/tcp || true
                
                # वर्कस्पेस के अंदर आर्टिफ़ैक्ट्स डायरेक्टरी सुनिश्चित करें
                mkdir -p ${WORKSPACE}/mlflow_artifacts
                
                # स्पष्ट रूप से Jenkins वर्कस्पेस का पाथ देते हुए
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