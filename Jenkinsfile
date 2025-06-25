pipeline {
    agent any

    options {
        skipDefaultCheckout() // ✅ empêche Jenkins de refaire un checkout
    }

    stages {
        stage('Clone propre') {
            steps {
                checkout([$class: 'GitSCM',
                    userRemoteConfigs: [[
                        url: 'https://github.com/Mathis0000/junkins'
                    ]],
                    branches: [[name: '*/main']]
                ])
            }
        }

        stage('Check .git') {
            steps {
                echo "Contenu du workspace :"
                sh 'ls -la'
                echo "SHA du commit :"
                sh 'git rev-parse HEAD'
            }
        }
    }
}
