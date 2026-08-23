FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update \
    && apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

ARG DOCKER_GID=117

RUN groupmod -g ${DOCKER_GID} docker \
    && usermod -aG docker jenkins

USER jenkins