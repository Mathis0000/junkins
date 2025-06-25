FROM jenkins/jenkins:lts

USER root
# Installe la CLI Docker
RUN apt-get update \
 && apt-get install -y docker.io \
 && rm -rf /var/lib/apt/lists/*

USER jenkins
