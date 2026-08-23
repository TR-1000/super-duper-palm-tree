# Python Jenkins Docker CI/CD Lab

A small, reproducible DevOps lab demonstrating a basic **CI/CD pipeline using Git, Jenkins, Docker, and Python**.

The project starts with a simple Flask application and uses Jenkins to automatically test the application, build a Docker image, and deploy the application as a Docker container.

This is **Version 1** of the project. Future versions will extend the pipeline to include container registries, Proxmox, Raspberry Pi, AWS, security scanning, monitoring, and additional deployment automation.

---

## Architecture

```text
                        Git Repository
                              │
                         git push
                              │
                              ▼
                       ┌─────────────┐
                       │   Jenkins   │
                       │  Container  │
                       └──────┬──────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
                  ▼                       ▼
              Python/pytest          Docker CLI
                  │                       │
                  ▼                       ▼
             Run Tests             Docker Daemon
                                          │
                                          ▼
                                  ┌────────────────┐
                                  │ Flask Container│
                                  │                │
                                  │ Python + Flask │
                                  └───────┬────────┘
                                          │
                                          ▼
                                   Flask Web App
                                  localhost:5000
```

---

## Technology Stack

| Technology | Purpose                         |
| ---------- | ------------------------------- |
| Python     | Application language            |
| Flask      | Web application framework       |
| pytest     | Automated testing               |
| Git        | Source control                  |
| GitHub     | Git repository                  |
| Jenkins    | CI/CD automation                |
| Docker     | Containerization and deployment |
| Linux      | Jenkins/Docker environment      |

---

## Project Structure

```text
python-devops-demo/
├── app.py
├── requirements.txt
├── test_app.py
├── Dockerfile
├── Jenkinsfile
├── .gitignore
└── README.md
```

### Application

`app.py` contains the Flask application.

The application exposes two endpoints:

```text
GET /
GET /health
```

The root endpoint returns a simple message:

```text
Hello from my DevOps pipeline!
```

The health endpoint returns:

```json
{
  "status": "healthy"
}
```

---

# CI/CD Pipeline

The Jenkins pipeline currently consists of four stages:

```text
Checkout
   ↓
Test
   ↓
Build Docker Image
   ↓
Deploy
```

## 1. Checkout

Jenkins checks out the source code from the Git repository.

```groovy
stage('Checkout') {
    steps {
        checkout scm
    }
}
```

## 2. Test

Jenkins creates a Python virtual environment and installs the application's dependencies.

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/pytest
```

If the tests fail, the pipeline stops and the application is not deployed.

## 3. Build Docker Image

Jenkins builds a Docker image using the project's `Dockerfile`.

```bash
docker build -t python-devops-demo:${BUILD_NUMBER} .
```

Jenkins' `BUILD_NUMBER` is used to give each image a unique version.

For example:

```text
python-devops-demo:1
python-devops-demo:2
python-devops-demo:3
```

## 4. Deploy

The pipeline stops and removes the previous application container and starts a new container from the newly built image.

```bash
docker stop python-devops-demo || true
docker rm python-devops-demo || true

docker run -d \
    --name python-devops-demo \
    -p 5000:5000 \
    python-devops-demo:${BUILD_NUMBER}
```

---

# Running the Application Locally

## Prerequisites

The following should be installed:

* Python 3
* Git
* Docker

Clone the repository:

```bash
git clone <repository-url>
cd python-devops-demo
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it.

### Linux/macOS

```bash
source venv/bin/activate
```

### Windows

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the tests:

```bash
pytest
```

Start the application:

```bash
python app.py
```

The application will be available at:

```text
http://localhost:5000
```

Health check:

```text
http://localhost:5000/health
```

---

# Running the Application with Docker

Build the image:

```bash
docker build -t python-devops-demo .
```

Run the container:

```bash
docker run -d \
    --name python-devops-demo \
    -p 5000:5000 \
    python-devops-demo
```

Verify the container:

```bash
docker ps
```

Open:

```text
http://localhost:5000
```

---

# Jenkins Setup

Jenkins is itself running inside a Docker container.

The Jenkins environment includes:

* Jenkins
* Java
* Python 3
* pip
* Python virtual environment support
* Docker CLI

The Jenkins container also has access to the host Docker daemon through the Docker socket.

Example:

```bash
docker run -d \
    -p 8080:8080 \
    -p 50000:50000 \
    --name jenkins-flask \
    -v jenkins_home:/var/jenkins_home \
    -v /var/run/docker.sock:/var/run/docker.sock \
    jenkins-python-docker
```

Jenkins is then available at:

```text
http://localhost:8080
```

---

## Jenkins Docker Image

The Jenkins image is customized using the following Dockerfile:

```dockerfile
FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update \
    && apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

ARG DOCKER_GID

RUN groupmod -g ${DOCKER_GID} docker \
    && usermod -aG docker jenkins

USER jenkins
```

The Docker group ID is passed during the image build so that the Jenkins user can access the host Docker socket.

Example:

```bash
docker build \
    --build-arg DOCKER_GID=$(stat -c '%g' /var/run/docker.sock) \
    -t jenkins-python-docker jenkins/
```

> **Note:** Mounting `/var/run/docker.sock` gives the Jenkins container significant control over the Docker host. This configuration is intended for this personal learning lab and should not be treated as a production security architecture.

---

# Jenkinsfile

The pipeline is defined as code using a `Jenkinsfile`.

This allows the CI/CD configuration to be version-controlled alongside the application.

Example pipeline:

```groovy
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
```

---

# Version 1 Learning Objectives

This project was created to refresh and practice fundamental DevOps concepts:

* Git-based development workflows
* Git repositories and commits
* Python virtual environments
* Automated testing
* Jenkins pipelines
* Jenkins Pipeline-as-Code
* Jenkins agents and workspaces
* Docker image creation
* Docker containers
* Docker daemon communication
* Linux users and groups
* Unix socket permissions
* CI/CD pipeline stages
* Build numbering and image versioning
* Automated application deployment

---

# Troubleshooting Lessons

Version 1 intentionally involved several real-world configuration problems.

## Jenkins did not have Python

Initial error:

```text
python3: not found
```

### Cause

The standard Jenkins image provides Jenkins and Java but does not necessarily contain the Python tooling required by the pipeline.

### Solution

Create a custom Jenkins image containing Python.

---

## pip reported an externally managed environment

Error:

```text
error: externally-managed-environment
```

### Cause

The system Python installation is managed by the operating system, preventing pip from installing packages directly into it.

### Solution

Create a project-specific Python virtual environment:

```bash
python3 -m venv venv
```

and run pip and pytest through that environment.

---

## Jenkins could not access Docker

Error:

```text
permission denied while trying to connect to the Docker daemon socket
```

### Cause

The Jenkins container could see `/var/run/docker.sock`, but the Jenkins user did not have permission to access the socket.

### Solution

Match the Docker group's GID inside the Jenkins image with the GID of the host Docker socket.

This required understanding:

* Linux users
* Linux groups
* Group IDs
* Unix socket permissions
* Docker daemon access

---

# Version 1 Milestone

Version 1 is considered complete when the following workflow succeeds:

```text
git push
    │
    ▼
Jenkins
    │
    ▼
Checkout
    │
    ▼
Python virtual environment
    │
    ▼
pytest
    │
    ▼
Docker build
    │
    ▼
Docker deployment
    │
    ▼
Flask application
```

A successful Jenkins build should result in a running container:

```bash
docker ps
```

with the application available at:

```text
http://localhost:5000
```

---

# Roadmap

This project is intended to evolve into a larger personal DevOps/homelab environment.

## Version 2 — Pipeline Improvements

* [ ] Add automated application health checks
* [ ] Fail deployment if the health check fails
* [ ] Add Docker image cleanup
* [ ] Improve Jenkins pipeline error handling
* [ ] Add pipeline notifications
* [ ] Add GitHub webhook-triggered builds

## Version 3 — Container Registry

* [ ] Push Docker images to a registry
* [ ] Use immutable image tags
* [ ] Separate build and deployment stages
* [ ] Store build artifacts/images outside the Jenkins host

## Version 4 — Proxmox Homelab

* [ ] Set up Proxmox on repurposed HTPC hardware
* [ ] Create a dedicated Linux VM for Docker workloads
* [ ] Deploy the Flask application to the Proxmox environment
* [ ] Automate deployment through Jenkins
* [ ] Experiment with multiple environments

## Version 5 — Raspberry Pi

* [ ] Deploy the application to Raspberry Pi 4
* [ ] Learn ARM64 Docker images
* [ ] Build multi-architecture images
* [ ] Experiment with `docker buildx`

Target architecture:

```text
Docker Image
     │
     ├── linux/amd64
     │
     └── linux/arm64
```

## Version 6 — AWS

Potential deployment targets:

* [ ] AWS EC2
* [ ] Amazon ECR
* [ ] Amazon ECS
* [ ] AWS Fargate
* [ ] Application Load Balancer

Potential architecture:

```text
GitHub
   │
   ▼
Jenkins
   │
   ▼
Docker Build
   │
   ▼
Amazon ECR
   │
   ▼
Amazon ECS/Fargate
   │
   ▼
Flask Application
```

## Future Enhancements

Additional technologies that may eventually be incorporated:

* Infrastructure as Code
* Terraform
* Ansible
* Docker Compose
* Kubernetes
* Prometheus
* Grafana
* Container security scanning
* Dependency scanning
* Secrets management
* Blue/green deployments
* Rolling deployments
* Multiple environments
* Automated rollback

---

# Project Goal

The long-term goal is to evolve this small Flask application into a **reproducible DevOps laboratory** that demonstrates the complete software delivery lifecycle:

```text
Source Control
      ↓
Continuous Integration
      ↓
Automated Testing
      ↓
Containerization
      ↓
Artifact Management
      ↓
Continuous Deployment
      ↓
Infrastructure
      ↓
Monitoring
      ↓
Security
```

The same application should eventually be deployable across:

```text
Local Docker
     │
     ├── Proxmox
     │
     ├── Raspberry Pi
     │
     └── AWS
```

The goal is not simply to learn individual tools, but to understand **how the tools work together to automate software delivery.**

---

## Current Status

**Version:** `1.0.0`

**Status:** ✅ Complete

**Current deployment:**

```text
GitHub → Jenkins → Docker → Flask
```

**Next milestone:**

```text
Automated health checks + improved deployment pipeline
```
