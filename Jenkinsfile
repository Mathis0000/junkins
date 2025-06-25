pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io'
        MODEL_NAME = 'vision-classifier'
        KUBECONFIG = credentials('k8s-config')
    }

    stages {
        stage('Data Processing') {
            parallel {
                stage('Data Validation') {
                    steps {
                        script {
                            sh '''
                            python scripts/validate_input_data.py
                            python scripts/check_data_quality.py
                            '''
                        }
                    }
                }

                stage('Feature Engineering') {
                    steps {
                        sh 'python src/feature_engineering.py'
                    }
                }
            }
        }

        stage('Model Training') {
            when {
                expression {
                    return params.RETRAIN_MODEL == true ||
                           currentBuild.previousBuild?.result != 'SUCCESS'
                }
            }
            steps {
                script {
                    def trainingJob = build job: 'model-training-job',
                        parameters: [
                            string(name: 'DATA_VERSION', value: env.DATA_VERSION),
                            string(name: 'MODEL_CONFIG', value: 'production')
                        ]
                    env.MODEL_VERSION = trainingJob.getBuildVariables().MODEL_VERSION
                }
            }
        }

        stage('Model Evaluation') {
            steps {
                script {
                    sh '''
                    python src/evaluate_model.py \
                    --model-version ${MODEL_VERSION} \
                    --threshold 0.9
                    '''
                    def evaluation = readJSON file: 'evaluation_results.json'
                    if (evaluation.accuracy < 0.9) {
                        error("Model accuracy below threshold: ${evaluation.accuracy}")
                    }
                }
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${MODEL_NAME}:${MODEL_VERSION}")
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'registry-credentials') {
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh '''
                helm upgrade --install ${MODEL_NAME}-staging helm/ml-service \
                --set image.tag=${MODEL_VERSION} \
                --set environment=staging \
                --namespace ml-staging
                '''
            }
        }

        stage('Integration Tests') {
            steps {
                sh '''
                python tests/integration_tests.py \
                --endpoint http://ml-staging.internal/predict
                '''
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
                sh '''
                helm upgrade --install ${MODEL_NAME} helm/ml-service \
                --set image.tag=${MODEL_VERSION} \
                --set environment=production \
                --set replicas=3 \
                --namespace ml-production
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'model_report.html',
                reportName: 'Model Report'
            ])
        }
    }
}
