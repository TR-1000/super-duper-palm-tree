pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }
    
    environment {
        APP_NAME = 'python-devops-demo'
        DOCKER_NETWORK = 'devops-network'
        APP_PORT = '5000'

        HOST_PORT = '5000'
        CONTAINER_PORT = '5000'

        HEALTH_ENDPOINT = '/health'
        HEALTH_RETRIES = '10'
        HEALTH_RETRY_DELAY = '5'
    }

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
                '''
            }
        }

        stage('Deploy') {
            steps {
                script {
                    env.PREVIOUS_IMAGE = sh(
                        script: """
                            docker inspect -f '{{.Config.Image}}' ${APP_NAME} 2>/dev/null || true
                        """,
                        returnStdout: true
                    ).trim()

                    echo "DEBUG: Previous image = '${env.PREVIOUS_IMAGE}'"

                    if (env.PREVIOUS_IMAGE) {
                        echo "Previously deployed image: ${env.PREVIOUS_IMAGE}"
                    } else {
                        echo "No previous deployment found."
                    }

                    // Record deployment attempt.
                    sh 'touch .deployment-attempted'
                    echo "DEBUG: Deployment marker created."
                }       

                sh '''
                    echo "Stopping existing container..."
                    docker stop ${APP_NAME} || true

                    echo "Removing existing container..."
                    docker rm ${APP_NAME} || true

                    echo "Deploying image: ${APP_NAME}:build-${BUILD_NUMBER}"

                    docker run -d \
                        --name ${APP_NAME} \
                        --network ${DOCKER_NETWORK} \
                        -p ${HOST_PORT}:${CONTAINER_PORT} \
                        ${APP_NAME}:build-${BUILD_NUMBER}

                    echo "Waiting for container to start..."

                    sleep 2

                    if [ "$(docker inspect -f '{{.State.Running}}' ${APP_NAME})" != "true" ]; then
                        echo "ERROR: Application container failed to stay running."
                        echo "Container logs:"
                        docker logs ${APP_NAME}
                        exit 1
                    fi

                    echo "Application container is running."
                '''
            }
        }

        stage('Health Check') {
            steps {
                script {
                    // Retries the block up to 10 times before failing
                    retry(env.HEALTH_RETRIES.toInteger()) {
                        echo "Waiting for application to start..."

                        // Check if curl fails
                        def statusCode = sh(
                            script: 'curl --fail http://${APP_NAME}:${CONTAINER_PORT}${HEALTH_ENDPOINT}',
                            returnStatus: true
                        )

                        if (statusCode != 0) {
                            echo "Health check failed. Retrying in 5 seconds..."
                            sleep env.HEALTH_RETRY_DELAY
                            error "Application not ready yet." // Forces the retry block to loop
                        }

                        echo "Application health check passed!"

                        
                        // Tag tag deployed image as current and clean up deployment marker file
                        sh '''
                            docker tag ${APP_NAME}:build-${BUILD_NUMBER} ${APP_NAME}:current

                            rm -f .deployment-attempted
                        '''
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
            
                if (fileExists('.deployment-attempted') && env.PREVIOUS_IMAGE) {
                
                    echo "=========================================="
                    echo "DEPLOYMENT FAILED"
                    echo "=========================================="

                    
    
                    echo "Previous image: ${env.PREVIOUS_IMAGE}"
                    echo "Rolling back..."
    
                    sh """
                        echo "Stopping failed deployment..."
    
                        docker stop ${APP_NAME} || true
    
                        echo "Removing failed deployment..."
    
                        docker rm ${APP_NAME} || true
    
                        echo "Starting previous image: ${env.PREVIOUS_IMAGE}"
    
                        docker run -d \
                            --name ${APP_NAME} \
                            --network ${DOCKER_NETWORK} \
                            -p ${HOST_PORT}:${CONTAINER_PORT} \
                            ${env.PREVIOUS_IMAGE}
    
                        echo "Waiting for rollback container..."
    
                        sleep 2
    
                        if [ "\$(docker inspect -f '{{.State.Running}}' ${APP_NAME})" != "true" ]; then
                            echo "ERROR: Rollback container failed to stay running."
    
                            echo "Rollback container logs:"
                            docker logs ${APP_NAME}
    
                            exit 1
                        fi
    
                        echo "Rollback container is running."
    
                        echo "Checking rollback health..."
    
                        curl --fail http://${APP_NAME}:${CONTAINER_PORT}${HEALTH_ENDPOINT}
    
                        echo "Rollback health check passed!"
    
                        echo "=========================================="
                        echo "ROLLBACK SUCCESSFUL"
                        echo "=========================================="
    
                        docker tag ${PREVIOUS_IMAGE} ${APP_NAME}:current
                    """
    
                } else {
                
                    echo "No rollback performed."
    
                    if (!fileExists('.deployment-attempted')) {
                        echo "Deployment was not attempted."
                    }
    
                    if (!env.PREVIOUS_IMAGE) {
                        echo "No previous image was available."
                    }
                }
            }
        }
    }
    
}