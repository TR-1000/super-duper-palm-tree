# Python Jenkins Docker CI/CD Lab

A small, reproducible DevOps laboratory demonstrating a CI/CD pipeline using **Git, Jenkins, Docker, Python, and Flask**.

The project started as a simple Flask application and has evolved into a progressively hardened deployment pipeline. Jenkins automatically checks out the source code, runs automated tests, builds a versioned Docker image, deploys the application, performs health checks, and can automatically roll back to the previously deployed image when a deployment fails.

The project is intentionally developed in versioned checkpoints so that each stage can be reproduced, tested, broken intentionally, and recovered.

---

## Current Status

**Version:** `V2.7.1`
**Status:** ✅ Stable checkpoint

Current deployment flow:

```text
GitHub
   │
   │ git push / webhook
   ▼
Jenkins
   │
   ├── Checkout
   │
   ├── Test
   │
   ├── Build Docker Image
   │
   ├── Deploy
   │
   └── Health Check
          │
          ▼
     Flask Container
```

The current pipeline also includes deployment tracking and automatic rollback when a deployment fails after deployment has been attempted.

---

# Architecture

```text
                         Git Repository
                              │
                              │ git push
                              ▼
                    ┌─────────────────────┐
                    │       Jenkins       │
                    │      Container      │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
          Python / pytest              Docker CLI
                 │                           │
                 ▼                           ▼
          Automated Tests             Docker Daemon
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │   Flask Container    │
                                  │                     │
                                  │ Python + Flask       │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                      Flask Application
                                             │
                                             ▼
                                       localhost:5000
```

Jenkins runs inside Docker and communicates with the Docker daemon through the Docker socket.

The application container is connected to the Docker network:

```text
devops-network
```

The Jenkins health check communicates with the application using the container's internal port rather than the host-mapped port.

---

# Technology Stack

| Technology | Purpose                           |
| ---------- | --------------------------------- |
| Python     | Application language              |
| Flask      | Web application framework         |
| pytest     | Automated testing                 |
| Git        | Source control                    |
| GitHub     | Git repository and webhook source |
| Jenkins    | CI/CD automation                  |
| Docker     | Containerization and deployment   |
| Linux      | Jenkins/Docker environment        |

---

# Project Structure

```text
python-devops-demo/
│
├── app.py
├── requirements.txt
├── test_app.py
├── Dockerfile
├── Jenkinsfile
├── .gitignore
└── README.md
```

---

# Application

`app.py` contains the Flask application.

The application exposes two endpoints:

```text
GET /
GET /health
```

The root endpoint returns:

```text
Hello from my DevOps pipeline!
```

The health endpoint returns:

```json
{
  "status": "healthy"
}
```

The `/health` endpoint is used by Jenkins to determine whether a newly deployed container is ready to receive traffic.

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

# CI/CD Pipeline

The current Jenkins pipeline consists of five stages:

```text
Checkout
   ↓
Test
   ↓
Build Docker Image
   ↓
Deploy
   ↓
Health Check
```

The pipeline is defined as code in the repository's `Jenkinsfile`.

---

## 1. Checkout

Jenkins checks out the source code from the configured Git repository.

```groovy
stage('Checkout') {
    steps {
        checkout scm
    }
}
```

The pipeline uses:

```groovy
options {
    skipDefaultCheckout(true)
}
```

so that checkout is explicitly controlled by the pipeline.

---

# 2. Test

Jenkins creates a Python virtual environment and installs the application's dependencies.

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/pytest
```

The tests run before the Docker image is built.

If the tests fail:

```text
Checkout
   ↓
Test ❌
   ↓
Pipeline stops
```

The Docker build and deployment stages are skipped.

This prevents an application that fails its automated tests from being deployed.

---

# 3. Build Docker Image

Jenkins builds a Docker image using the project's `Dockerfile`.

Each Jenkins build receives a unique image tag based on the Jenkins build number:

```bash
docker build -t python-devops-demo:build-${BUILD_NUMBER} .
```

For example:

```text
python-devops-demo:build-59
python-devops-demo:build-60
python-devops-demo:build-61
```

Using build-specific image tags allows the pipeline to identify exactly which image was deployed.

The successfully deployed image can additionally be promoted to:

```text
python-devops-demo:current
```

---

# 4. Deploy

Before deployment, Jenkins determines which image the currently running application container is using.

```bash
docker inspect -f '{{.Config.Image}}' python-devops-demo
```

The result is stored as:

```text
PREVIOUS_IMAGE
```

This allows the pipeline to know exactly which image should be restored if the new deployment fails.

The deployment process then:

1. Stops the existing container.
2. Removes the existing container.
3. Starts the newly built image.
4. Verifies that the container remains running.

The application is deployed using:

```bash
docker run -d \
    --name python-devops-demo \
    --network devops-network \
    -p ${HOST_PORT}:${CONTAINER_PORT} \
    python-devops-demo:build-${BUILD_NUMBER}
```

---

# Host Port vs. Container Port

The pipeline deliberately keeps the host and container ports as separate configuration values:

```groovy
HOST_PORT = '5000'
CONTAINER_PORT = '5000'
```

The mapping is:

```text
Host Port
   │
   │ 5000
   ▼
Container Port
   │
   │ 5000
   ▼
Flask Application
```

These values can be changed independently.

For example:

```groovy
HOST_PORT = '9999'
CONTAINER_PORT = '5000'
```

produces:

```text
localhost:9999
      │
      ▼
Docker container:5000
      │
      ▼
Flask:5000
```

This configuration was intentionally tested as part of V2.7.1.

An important distinction is that Jenkins performs its health check against the container's internal port:

```text
http://python-devops-demo:5000/health
```

rather than the host port.

---

# 5. Health Check

After deployment, Jenkins verifies that the application is actually responding.

The health check uses:

```bash
curl --fail http://${APP_NAME}:${CONTAINER_PORT}${HEALTH_ENDPOINT}
```

The current configuration is:

```groovy
HEALTH_ENDPOINT = '/health'
HEALTH_RETRIES = '10'
HEALTH_RETRY_DELAY = '5'
```

Jenkins retries the health check when the application is not immediately ready.

```text
Deploy
   ↓
Container starts
   ↓
Health Check
   │
   ├── Healthy → Continue
   │
   └── Not ready
          │
          ▼
       Retry
          │
          └── Up to 10 attempts
```

Only after the health check succeeds is the deployed image tagged as:

```text
python-devops-demo:current
```

---

# Automatic Rollback

One of the major improvements introduced during Version 2 is automatic rollback.

Before deployment, Jenkins records the image currently being used by the application container.

For example:

```text
Currently deployed:
python-devops-demo:build-60
```

A new build is then deployed:

```text
python-devops-demo:build-61
```

If the deployment fails after deployment has been attempted, Jenkins can restore:

```text
python-devops-demo:build-60
```

The rollback process is:

```text
New Deployment
      │
      ▼
Container Fails
      │
      ▼
Pipeline Failure
      │
      ▼
Was Deployment Attempted?
      │
     YES
      │
      ▼
Previous Image Available?
      │
     YES
      │
      ▼
Stop Failed Container
      │
      ▼
Remove Failed Container
      │
      ▼
Start Previous Image
      │
      ▼
Verify Container
      │
      ▼
Verify Health
      │
      ▼
Rollback Successful
```

The rollback also performs a health check against the restored application.

---

# Deployment Tracking

The pipeline uses a deployment marker:

```text
.deployment-attempted
```

The marker is created immediately before the deployment operation begins.

This allows the pipeline to distinguish between:

```text
Test failure
```

and:

```text
Deployment failure
```

For example, if a unit test fails:

```text
Checkout
   ↓
Test ❌
   ↓
No deployment occurred
   ↓
No rollback required
```

If deployment begins and the new container fails:

```text
Checkout
   ↓
Test
   ↓
Build
   ↓
Deploy ❌
   ↓
Rollback
```

This prevents the pipeline from attempting to roll back when no deployment actually occurred.

---

# Failure Testing

Failure scenarios are intentionally tested as part of the project.

The pipeline has been tested against several real-world failure conditions.

## Failed Automated Test

A test was intentionally broken to verify that:

* pytest detects the failure
* the Test stage fails
* subsequent stages are skipped
* no deployment occurs
* rollback is not attempted

Expected behavior:

```text
Checkout     ✅
Test         ❌
Build        ⏭️
Deploy       ⏭️
Health Check ⏭️
```

---

## Failed Container Startup

The Dockerfile was intentionally modified so that the application could not start.

The resulting container failure was detected by the Deploy stage.

Jenkins reported the container logs and triggered rollback to the previously deployed image.

---

## Failed Health Check

The health endpoint and health-check configuration were intentionally modified during testing.

This demonstrated that a container being "running" does not necessarily mean that the application is healthy.

The pipeline therefore has two separate deployment checks:

```text
Container Running
       +
Application Healthy
       =
Successful Deployment
```

---

## Health Check Retry Testing

The health check was configured to retry multiple times:

```groovy
HEALTH_RETRIES = '10'
HEALTH_RETRY_DELAY = '5'
```

This provides time for the application to initialize before Jenkins declares the deployment unsuccessful.

---

## Host/Container Port Testing

The host port was intentionally changed from:

```text
5000
```

to:

```text
9999
```

while leaving the container port at:

```text
5000
```

The resulting Docker mapping was:

```text
9999:5000
```

The application remained healthy and the Jenkins pipeline completed successfully.

This verified that the pipeline correctly distinguishes between host networking and container networking.

---

# Jenkins Setup

Jenkins runs inside a Docker container.

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

Jenkins is available at:

```text
http://localhost:8080
```

---

# Custom Jenkins Docker Image

The Jenkins image is customized using a Dockerfile.

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

### Security Note

Mounting:

```text
/var/run/docker.sock
```

gives the Jenkins container significant control over the Docker host.

This configuration is intended for this personal learning laboratory and should not be considered a production security architecture.

A future version of the project may replace this approach with a more isolated architecture.

---

# Jenkinsfile

The pipeline is defined as code using a `Jenkinsfile`.

This allows the CI/CD configuration to be version-controlled alongside the application.

The current pipeline contains:

* Centralized environment configuration
* Explicit Git checkout
* Python virtual environment creation
* Automated pytest execution
* Versioned Docker image builds
* Previous-image detection
* Deployment tracking
* Docker network configuration
* Host/container port configuration
* Container startup validation
* Health-check retries
* Image promotion
* Automatic rollback
* Rollback health validation

The Jenkinsfile is intentionally kept in source control so that pipeline changes can be reviewed and reproduced alongside application changes.

---

# Versioning Strategy

The project uses Git commits and tags to create stable checkpoints.

The current stable checkpoint is:

```text
V2.7.1
```

Version checkpoints are used to preserve known-good versions of the laboratory.

The general workflow is:

```text
Make change
    ↓
Test
    ↓
Intentionally test failure paths
    ↓
Fix problems
    ↓
Run clean build
    ↓
Commit
    ↓
Tag stable version
```

This approach makes it possible to return to a known-good state when experimenting with future pipeline changes.

---

# V2.7.1 Validation

V2.7.1 represents a stable checkpoint after testing the current deployment architecture.

The following scenarios have been validated:

* ✅ Git/Jenkins integration
* ✅ Webhook-triggered builds
* ✅ Python virtual environment creation
* ✅ Automated pytest execution
* ✅ Docker image builds
* ✅ Versioned Docker image tags
* ✅ Docker deployment
* ✅ Docker network configuration
* ✅ Container startup validation
* ✅ Health-check retries
* ✅ Application health validation
* ✅ Host/container port separation
* ✅ Deployment tracking
* ✅ Previous-image detection
* ✅ Automatic rollback
* ✅ Rollback health validation
* ✅ Intentional application failure testing
* ✅ Intentional test failure testing

---

# Learning Objectives

This project is being used to develop practical experience with:

* Git-based development workflows
* Git commits and tags
* GitHub repositories
* GitHub webhooks
* Python virtual environments
* Automated testing
* pytest
* Jenkins
* Jenkins Pipeline-as-Code
* Jenkins agents and workspaces
* Jenkins environment variables
* Docker image creation
* Docker containers
* Docker networks
* Docker daemon communication
* Linux users and groups
* Group IDs
* Unix socket permissions
* CI/CD pipeline stages
* Build numbering
* Image versioning
* Application deployment
* Application health checks
* Deployment failure detection
* Automatic rollback
* Failure-path testing
* Reproducible development workflows

---

# Troubleshooting Lessons

This project intentionally involved several real-world configuration problems.

These problems are documented because the troubleshooting process is part of the learning objective.

## Jenkins did not have Python

Initial error:

```text
python3: not found
```

### Cause

The standard Jenkins image did not contain the Python tooling required by the pipeline.

### Solution

A custom Jenkins image was created containing:

```text
python3
python3-pip
python3-venv
```

---

## pip reported an externally managed environment

Error:

```text
error: externally-managed-environment
```

### Cause

The system Python installation was managed by the operating system and prevented pip from installing packages directly into the system environment.

### Solution

A project-specific virtual environment was created:

```bash
python3 -m venv venv
```

The pipeline then uses:

```bash
./venv/bin/python
```

for package installation and testing.

---

## Jenkins could not access Docker

Error:

```text
permission denied while trying to connect to the Docker daemon socket
```

### Cause

The Jenkins container could see:

```text
/var/run/docker.sock
```

but the Jenkins user did not have permission to access the socket.

### Solution

The Docker group GID inside the Jenkins image was matched to the GID of the host Docker socket.

This required understanding:

* Linux users
* Linux groups
* Group IDs
* Unix socket permissions
* Docker daemon access

---

## Container was running but the application was not healthy

A running Docker container does not necessarily mean that the application inside the container is ready.

The project therefore introduced a dedicated:

```text
/health
```

endpoint and Jenkins health-check stage.

This changed deployment validation from:

```text
Container is running
```

to:

```text
Container is running
+
Application is responding
```

---

## Failure-handling code can fail

One of the most important lessons from the project was that rollback logic must be treated as production code.

A malformed health-check URL caused the rollback health check itself to fail.

This demonstrated that:

```text
Deployment failure
        ↓
Rollback
        ↓
Rollback failure
```

is possible.

Future pipeline versions will therefore focus on making failure-handling and rollback logic more defensive.

---

# Roadmap

The project is intended to evolve into a larger personal DevOps/homelab environment.

## Version 2 — Pipeline Improvements

### V2.7.1 — Current Stable Checkpoint

* [x] Automated application health checks
* [x] Fail deployment if the health check fails
* [x] Health-check retries
* [x] GitHub webhook-triggered builds
* [x] Previous-image detection
* [x] Deployment tracking
* [x] Automatic rollback
* [x] Rollback health validation
* [x] Host/container port separation
* [x] Failure-path testing

### V2.8 — Pipeline Hardening

* [ ] Validate pipeline configuration before deployment
* [ ] Improve health-check configuration validation
* [ ] Make rollback logic more defensive
* [ ] Improve deployment state tracking
* [ ] Improve failure logging
* [ ] Improve cleanup of temporary artifacts
* [ ] Test rollback failure scenarios
* [ ] Introduce a more structured Git branching workflow

The goal of V2.8 is to make the existing pipeline safer and more predictable rather than immediately adding new infrastructure.

---

# Version 3 — Container Registry

Planned improvements:

* [ ] Push Docker images to a container registry
* [ ] Use immutable image tags
* [ ] Separate build and deployment stages
* [ ] Store build artifacts/images outside the Jenkins host
* [ ] Introduce image retention and cleanup policies

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
Container Registry
   │
   ▼
Deployment Environment
```

---

# Version 4 — Proxmox Homelab

Planned work:

* [ ] Set up Proxmox on repurposed HTPC hardware
* [ ] Create a dedicated Linux VM for Docker workloads
* [ ] Deploy the Flask application to the Proxmox environment
* [ ] Automate deployment through Jenkins
* [ ] Experiment with multiple environments

Potential architecture:

```text
Jenkins
   │
   ▼
Docker Image
   │
   ▼
Proxmox
   │
   ▼
Linux VM
   │
   ▼
Docker
   │
   ▼
Flask Application
```

---

# Version 5 — Raspberry Pi

Planned work:

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

---

# Version 6 — AWS

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
Amazon ECS / Fargate
   │
   ▼
Flask Application
```

---

# Future Enhancements

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
* Improved artifact management
* Centralized logging
* Deployment notifications
* Environment-specific configuration

---

# Project Goal

The long-term goal is to evolve this small Flask application into a **reproducible DevOps laboratory** that demonstrates the software delivery lifecycle from source code through infrastructure and operations.

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

The same application should eventually be deployable across multiple environments:

```text
                    Flask Application
                           │
                           ▼
                     Docker Image
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     Local Docker       Proxmox         Raspberry Pi
                                             │
                                             │
                                             ▼
                                            AWS
```

The goal is not simply to learn individual tools.

The goal is to understand **how the tools work together to automate software delivery**.

---

# Reproducibility Philosophy

Reproducibility is a core objective of this project.

Each major development milestone should leave behind:

1. A known-good Git commit.
2. A Git tag identifying the version.
3. A documented pipeline configuration.
4. A documented environment.
5. Tested success and failure scenarios.
6. A clear explanation of what was learned.

The laboratory is intentionally developed incrementally so that future changes can be introduced without losing the ability to reproduce earlier configurations.

This makes the project useful not only as a learning exercise, but also as a reference for future DevOps, DataOps, infrastructure, and automation projects.

---

# Current Status

**Version:** `V2.7.1`

**Status:** ✅ Stable checkpoint

**Current pipeline:**

```text
GitHub
   ↓
Jenkins
   ↓
Checkout
   ↓
Automated Tests
   ↓
Docker Build
   ↓
Deployment
   ↓
Container Validation
   ↓
Health Check
   ↓
Image Promotion
```

**Failure path:**

```text
Deployment Failure
       ↓
Previous Image Detection
       ↓
Rollback
       ↓
Container Validation
       ↓
Rollback Health Check
       ↓
Previous Image Restored
```

**Next milestone:**

```text
V2.8 — Pipeline Hardening
```

The next phase will focus on making the existing CI/CD pipeline more robust, defensive, and maintainable before expanding the laboratory into external infrastructure such as container registries, Proxmox, Raspberry Pi, and AWS.
 