pipeline {
  agent any

  environment {
    // l’URL (host) de votre registry Docker
    DOCKER_REGISTRY = 'docker.io'        
  
    // le nom de votre image (et du chart Helm)
    MODEL_NAME      = 'vision-classifier' 
  
    // l’ID du credential Jenkins contenant votre login + token Docker Hub
    REGISTRY_CRED   = 'registry-credentials'  
  
    // l’ID du credential Jenkins contenant votre fichier kubeconfig
    KUBE_CRED       = 'k8s-config'           
  }


  stages {
    stage('Data Processing') {
      parallel {
        stage('Data Validation') {
          steps {
            script {
              docker.image('python:3.9-slim').inside('-u root:root') {
                sh '''
                  pip install --no-cache-dir -r requirements.txt
                  python scripts/validate_input_data.py
                  python scripts/check_data_quality.py
                '''
              }
            }
          }
        }
        stage('Feature Engineering') {
          steps {
            script {
              docker.image('python:3.9-slim').inside('-u root:root') {
                sh '''
                  pip install --no-cache-dir -r requirements.txt
                  python src/feature_engineering.py
                '''
              }
            }
          }
        }
      }
    }

    stage('Model Training') {
      when {
        anyOf {
          expression { return params.RETRAIN_MODEL == true }
          expression { return currentBuild.previousBuild?.result != 'SUCCESS' }
        }
      }
      steps {
        script {
          def training = build job: 'model-training-job',
            parameters: [
              string(name: 'DATA_VERSION', value: env.DATA_VERSION ?: 'v1'),
              string(name: 'MODEL_CONFIG',  value: 'production')
            ]
          env.MODEL_VERSION = training.getBuildVariables().MODEL_VERSION
        }
      }
    }

    stage('Model Evaluation') {
      steps {
        script {
          docker.image('python:3.9-slim').inside('-u root:root') {
            sh """
              pip install --no-cache-dir -r requirements.txt
              python src/evaluate_model.py --model-version ${MODEL_VERSION} --threshold 0.9
            """
          }
          def eval = readJSON file: 'evaluation_results.json'
          if (eval.accuracy < 0.9) {
            error("Accuracy ${eval.accuracy} < threshold")
          }
        }
      }
    }

    stage('Docker Build') {
      steps {
        script {
          def img = docker.build("${DOCKER_REGISTRY}/${MODEL_NAME}:${MODEL_VERSION}")
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
          sh """
            helm upgrade --install ${MODEL_NAME}-staging helm/ml-service \
              --namespace ml-staging \
              --set image.tag=${MODEL_VERSION} \
              --set environment=staging
          """
        }
      }
    }

    stage('Integration Tests') {
      steps {
        script {
          docker.image('python:3.9-slim').inside('-u root:root') {
            sh '''
              pip install --no-cache-dir -r requirements.txt
              python tests/integration_tests.py --endpoint http://ml-staging.internal/predict
            '''
          }
        }
      }
    }

    stage('Deploy to Production') {
      when {
        branch 'main'
      }
      input {
        message "Deploy to production?"
        ok "Deploy"
      }
      steps {
        withCredentials([file(credentialsId: KUBE_CRED, variable: 'KUBECONFIG')]) {
          sh """
            helm upgrade --install ${MODEL_NAME} helm/ml-service \
              --namespace ml-production \
              --set image.tag=${MODEL_VERSION} \
              --set replicas=3 \
              --set environment=production
          """
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
