pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    ./venv/bin/python -m pip install -r requirements.txt
                    ./venv/bin/pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t python-devops-demo:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker stop python-devops-demo || true
                    docker rm python-devops-demo || true

                    docker run -d \
                        --name python-devops-demo \
                        --network devops-network \
                        -p 5000:5000 \
                        python-devops-demo:${BUILD_NUMBER}
                '''
            }
        }

        stage('Health Check') {
            steps {
                script {
                    // Retries the block up to 10 times before failing
                    retry(10) {
                        echo "Waiting for application to start..."

                        // Check if curl fails
                        def statusCode = sh(
                            script: 'curl --fail http://python-devops-demo:5000/health', 
                            returnStatus: true
                        )

                        if (statusCode != 0) {
                            echo "Health check failed. Retrying in 5 seconds..."
                            sleep 5
                            error "Application not ready yet." // Forces the retry block to loop
                        }

                        echo "Application health check passed!"
                    }
                }
            }
        }
    }
}
