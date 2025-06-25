pipeline {
  agent any

  options {
    // Empêche le checkout automatique en début de pipeline
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
        // UNIQUE checkout de votre repo
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
      // Archiver depuis le workspace courant (node) : fonctionne car on est bien dans un node
      archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
    }
  }
}
