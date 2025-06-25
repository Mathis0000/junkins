pipeline {
  agent any

  tools {
    jdk 'jdk11'
  }

  environment {
    DOCKER_REGISTRY = 'your-registry.com'
    REGISTRY_CRED   = 'registry-credentials'
    KUBE_CRED       = 'k8s-config'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Data Validation') {
      // Cet agent va pull l'image python:3.9-slim et y exécuter les steps
      agent {
        docker {
          image 'python:3.9-slim'
          // on se connecte en root pour pouvoir installer si besoin
          args '-u root:root'
        }
      }
      steps {
        sh '''
          pip install --no-cache-dir -r requirements.txt
          python scripts/validate_input_data.py
        '''
      }
    }

    stage('Feature Engineering') {
      agent {
        docker {
          image 'python:3.9-slim'
          args '-u root:root'
        }
      }
      steps {
        sh '''
          pip install --no-cache-dir -r requirements.txt
          python src/feature_engineering.py
        '''
      }
    }

    stage('Build & Push Docker') {
      agent any
      steps {
        script {
          def img = docker.build("${DOCKER_REGISTRY}/vision-classifier:${env.BUILD_NUMBER}")
          docker.withRegistry("https://${DOCKER_REGISTRY}", REGISTRY_CRED) {
            img.push()
            img.push('latest')
          }
        }
      }
    }

    stage('Deploy to Staging') {
      agent any
      steps {
        withCredentials([file(credentialsId: KUBE_CRED, variable: 'KUBECONFIG')]) {
          sh """
            helm upgrade --install vision-classifier-staging helm/ml-service \
              --namespace ml-staging \
              --set image.tag=${env.BUILD_NUMBER}
          """
        }
      }
    }
  }
}
