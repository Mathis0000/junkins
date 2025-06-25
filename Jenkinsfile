pipeline {
  agent any

  options {
    // Désactive le checkout automatique initial
    skipDefaultCheckout()
  }

  environment {
    DOCKER_REGISTRY = 'docker.io/mathis'
    IMAGE_NAME      = 'vision-classifier'
    REGISTRY_CRED   = 'registry-credentials'
  }

  stages {
    stage('Checkout') {
      steps {
        // Premier et unique checkout de votre repo
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
          // On build à partir de Dockerfile.ml-service
          def img = docker.build(
            "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}",
            "-f Dockerfile.ml-service ."
          )
          // Puis on push dans Docker Hub
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
      // Archive les logs en fin de pipeline
      archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
    }
  }
}
