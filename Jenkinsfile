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
                        script: """
                            docker inspect -f '{{.Config.Image}}' python-devops-demo 2>/dev/null || true
                        """,
                        returnStdout: true
                    ).trim()

                    echo "DEBUG: Previous image = '${env.PREVIOUS_IMAGE}'"

                    if (env.PREVIOUS_IMAGE) {
                        echo "Previously deployed image: ${env.PREVIOUS_IMAGE}"
                    } else {
                        echo "No previous deployment found."
                    }

                    env.DEPLOYMENT_ATTEMPTED = 'true'
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

                    echo "Waiting for container to start..."

                    sleep 2

                    if [ "$(docker inspect -f '{{.State.Running}}' python-devops-demo)" != "true" ]; then
                        echo "ERROR: Application container failed to stay running."
                        echo "Container logs:"
                        docker logs python-devops-demo
                        exit 1
                    fi

                    echo "Application container is running."echo "Application container is running."
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

    post {
        failure {
            script {

                if (env.DEPLOYMENT_ATTEMPTED == 'true' && env.PREVIOUS_IMAGE) {

                    echo "=========================================="
                    echo "DEPLOYMENT FAILED"
                    echo "=========================================="

                    echo "Rolling back to: ${env.PREVIOUS_IMAGE}"

                    sh """
                        echo "Stopping failed deployment..."

                        docker stop python-devops-demo || true

                        echo "Removing failed deployment..."

                        docker rm python-devops-demo || true

                        echo "Starting previous image: ${env.PREVIOUS_IMAGE}"

                        docker run -d \
                            --name python-devops-demo \
                            --network devops-network \
                            -p 5000:5000 \
                            ${env.PREVIOUS_IMAGE}

                        echo "Waiting for rollback container..."

                        sleep 2

                        if [ "\$(docker inspect -f '{{.State.Running}}' python-devops-demo)" != "true" ]; then
                            echo "ERROR: Rollback container failed to stay running."

                            echo "Rollback container logs:"
                            docker logs python-devops-demo

                            exit 1
                        fi

                        echo "Rollback container is running."

                        echo "Checking rollback health..."

                        curl --fail http://python-devops-demo:5000/health

                        echo "Rollback health check passed!"

                        echo "=========================================="
                        echo "ROLLBACK SUCCESSFUL"
                        echo "=========================================="
                    """

                } else {

                    echo "No rollback performed."
                    echo "Deployment was not attempted or no previous image was available."

                }
            }
        }
    }


}