pipeline {
  agent any

  environment {
    DOCKER_REGISTRY = 'docker.io'            // ou votre registry
    MODEL_NAME      = 'vision-classifier'    // nom de votre image/chart
    REGISTRY_CRED   = 'registry-credentials' // ID du credential Docker
    KUBE_CRED       = 'k8s-config'           // ID du credential kubeconfig
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Data Validation') {
      steps {
        // On exécute un container python:3.9-slim en shell
        sh '''
          docker run --rm \\
            -u root:root \\
            -v "$PWD":/workspace -w /workspace \\
            python:3.9-slim bash -lc "
              pip install --no-cache-dir -r requirements.txt &&
              python scripts/validate_input_data.py &&
              python scripts/check_data_quality.py
            "
        '''
      }
    }

    stage('Feature Engineering') {
      steps {
        sh '''
          docker run --rm \\
            -u root:root \\
            -v "$PWD":/workspace -w /workspace \\
            python:3.9-slim bash -lc "
              pip install --no-cache-dir -r requirements.txt &&
              python src/feature_engineering.py
            "
        '''
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
          def t = build job: 'model-training-job',
            parameters: [
              string(name: 'DATA_VERSION', value: env.DATA_VERSION ?: 'v1'),
              string(name: 'MODEL_CONFIG',  value: 'production')
            ]
          env.MODEL_VERSION = t.getBuildVariables().MODEL_VERSION
        }
      }
    }

    stage('Model Evaluation') {
      steps {
        sh '''
          docker run --rm \\
            -u root:root \\
            -v "$PWD":/workspace -w /workspace \\
            python:3.9-slim bash -lc "
              pip install --no-cache-dir -r requirements.txt &&
              python src/evaluate_model.py --model-version ${MODEL_VERSION} --threshold 0.9
            "
        '''
        script {
          def eval = readJSON file: 'evaluation_results.json'
          if (eval.accuracy < 0.9) {
            error("Accuracy too low (${eval.accuracy} < 0.9)")
          }
        }
      }
    }

    stage('Docker Build') {
      steps {
        sh """
          docker build -t ${DOCKER_REGISTRY}/${MODEL_NAME}:${MODEL_VERSION} .
          echo '$DOCKER_REGISTRY_PASSWORD' | docker login ${DOCKER_REGISTRY} --username '$DOCKER_REGISTRY_USERNAME' --password-stdin
          docker push ${DOCKER_REGISTRY}/${MODEL_NAME}:${MODEL_VERSION}
          docker tag ${DOCKER_REGISTRY}/${MODEL_NAME}:${MODEL_VERSION} ${DOCKER_REGISTRY}/${MODEL_NAME}:latest
          docker push ${DOCKER_REGISTRY}/${MODEL_NAME}:latest
        """
      }
    }

    stage('Deploy to Staging') {
      steps {
        withCredentials([file(credentialsId: KUBE_CRED, variable: 'KUBECONFIG')]) {
          sh """
            helm upgrade --install ${MODEL_NAME}-staging helm/ml-service \\
              --namespace ml-staging \\
              --set image.tag=${MODEL_VERSION} \\
              --set environment=staging
          """
        }
      }
    }

    stage('Integration Tests') {
      steps {
        sh '''
          docker run --rm \\
            -u root:root \\
            -v "$PWD":/workspace -w /workspace \\
            python:3.9-slim bash -lc "
              pip install --no-cache-dir -r requirements.txt &&
              python tests/integration_tests.py --endpoint http://ml-staging.internal/predict
            "
        '''
      }
    }

    stage('Deploy to Production') {
      when { branch 'main' }
      input { message "Deploy in production?"; ok "Go" }
      steps {
        withCredentials([file(credentialsId: KUBE_CRED, variable: 'KUBECONFIG')]) {
          sh """
            helm upgrade --install ${MODEL_NAME} helm/ml-service \\
              --namespace ml-production \\
              --set image.tag=${MODEL_VERSION} \\
              --set replicas=3 \\
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
