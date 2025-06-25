pipeline {
    agent any

    stages {
        stage('Force clone complet') {
            steps {
                checkout([$class: 'GitSCM',
                    userRemoteConfigs: [[
                        url: 'https://github.com/Mathis0000/junkins'
                    ]],
                    branches: [[name: '*/main']]
                ])
            }
        }

        stage('Vérification Git') {
            steps {
                echo "Contenu du workspace :"
                sh 'ls -la'
                echo "SHA actuel du repo :"
                sh 'git rev-parse HEAD'
            }
        }
    }
}
