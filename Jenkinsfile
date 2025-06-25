pipeline {
  agent any

  environment {
    DOCKER_REGISTRY = 'docker.io/mathis'
    IMAGE_NAME      = 'vision-classifier'
    REGISTRY_CRED   = 'registry-credentials'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Data Validation') {
      steps {
        sh '''
          docker run --rm \
            -u root:root \
            -v "$PWD":/workspace -w /workspace \
            python:3.11-slim bash -lc "
              pip install --no-cache-dir -r requirements.txt &&
              python scripts/validate_input_data.py &&
              python scripts/check_data_quality.py
            "
        '''
      }
    }

    stage('Build & Push Docker') {
      steps {
        script {
          def img = docker.build(
            "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}",
            "-f Dockerfile.ml-service ."
          )
          docker.withRegistry("https://${DOCKER_REGISTRY}", REGISTRY_CRED) {
            img.push()
            img.push('latest')
          }
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
    }
  }
}
