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
                        -p 5000:5000 \
                        python-devops-demo:${BUILD_NUMBER}
                '''
            }
        }
    }
}
