pipeline {
  agent any

  environment {
    // Ton registry Docker Hub
    DOCKER_REGISTRY = 'docker.io/mathis'
    // Nom de ton image et chart Helm
    IMAGE_NAME      = 'vision-classifier'
    // ID des credentials Jenkins pour Docker Hub (username/token)
    REGISTRY_CRED   = 'registry-credentials'
    // ID du credential Secret File contenant ton ~/.kube/config
    KUBE_CRED       = 'k8s-config'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Data Validation') {
      steps {
        // Exécution de tes scripts Python dans un container dédié
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
          // On build en se basant sur Dockerfile.ml-service
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

    stage('Deploy to Staging') {
      steps {
        withCredentials([file(credentialsId: KUBE_CRED, variable: 'KUBECONFIG')]) {
          sh '''
            helm upgrade --install ${IMAGE_NAME}-staging helm/ml-service \
              --namespace ml-staging \
              --set image.tag=${BUILD_NUMBER} \
              --set environment=staging
          '''
        }
      }
    }

    stage('Deploy to Production') {
      when { branch 'main' }
      input {
        message "Prêt pour la production ?"
        ok      "Déployer"
      }
      steps {
        withCredentials([file(credentialsId: KUBE_CRED, variable: 'KUBECONFIG')]) {
          sh '''
            helm upgrade --install ${IMAGE_NAME} helm/ml-service \
              --namespace ml-production \
              --set image.tag=${BUILD_NUMBER} \
              --set replicas=3 \
              --set environment=production
          '''
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
