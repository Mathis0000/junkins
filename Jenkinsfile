pipeline {
    agent any

    stages {
        stage('SCM Check') {
            steps {
                script {
                    echo "Liste des fichiers :"
                    sh 'ls -la'

                    echo "Révision git :"
                    sh 'git rev-parse HEAD'
                }
            }
        }
    }
}
