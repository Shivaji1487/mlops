pipeline {
    agent any

    environment {
        IMAGE_NAME            = "sshivaji555/customer-tiering-mlops:latest"
        NAMESPACE             = "mlops-prod"
        RELEASE               = "customer-tiering-release"
        
        MINIO_ENDPOINT        = "http://192.168.235.130:9000"
        MLFLOW_TRACKING_URI   = "http://192.168.235.130:5000"
        AWS_ACCESS_KEY_ID     = "minioadmin"
        AWS_SECRET_ACCESS_KEY = "minioadmin"
    }

    stages {
        stage('1. Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('2. Execute Model Training') {
            steps {
                script {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        python train.py
                    '''
                }
            }
        }

        stage('3. Build & Security Scan') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME} ."
                    sh "trivy image --vuln-type os --severity HIGH,CRITICAL ${IMAGE_NAME} || true"
                }
            }
        }

        stage('4. Push Image to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'U', passwordVariable: 'P')]) {
                    sh """
                        echo '$P' | docker login -u '$U' --password-stdin
                        docker push ${IMAGE_NAME}
                        docker logout
                    """
                }
            }
        }

        stage('5. Helm Deploy & Verification') {
            steps {
                script {
                    sh "helm upgrade --install ${RELEASE} ./helm --namespace ${NAMESPACE} --create-namespace"
                    sh "kubectl rollout status deployment/${RELEASE}-deployment -n ${NAMESPACE} --timeout=2m"
                    sh "kubectl get pods,svc -n ${NAMESPACE}"
                }
            }
        }
    }

    post {
        always {
            script {
                sh "docker rmi ${IMAGE_NAME} || true"
                sh "rm -rf venv"
            }
        }
    }
}