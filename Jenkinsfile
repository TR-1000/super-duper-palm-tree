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
                    docker build -t python-devops-demo:build-${BUILD_NUMBER} .
                    docker tag python-devops-demo:build-${BUILD_NUMBER} python-devops-demo:current
                '''
            }
        }

        stage('Deploy') {
            steps {
                script {
                    env.PREVIOUS_IMAGE = sh(
                        script: "docker inspect -f '{{.Config.Image}}' python-devops-demo 2>/dev/null || true",
                        returnStdout: true
                    ).trim()
                
                    echo "Previously deployed image: ${env.PREVIOUS_IMAGE ?: 'none'}"
                }       

                sh '''
                    echo "Stopping existing container..."
                    docker stop python-devops-demo || true

                    echo "Removing existing container..."
                    docker rm python-devops-demo || true

                    echo "Deploying image: python-devops-demo:build-${BUILD_NUMBER}"

                    docker run -d \
                        --name python-devops-demo \
                        --network devops-network \
                        -p 5000:5000 \
                        python-devops-demo:build-${BUILD_NUMBER}

                    sleep 2

                    if [ "$(docker inspect -f '{{.State.Running}}' python-devops-demo)" != "true" ]; then
                        echo "ERROR: Application container failed to stay running."
                        echo "Container logs:"
                        docker logs python-devops-demo
                        exit 1
                    fi
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
