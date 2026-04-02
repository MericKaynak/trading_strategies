pipeline {
    agent any

    triggers {
        // Mo-Fr um 18:25 CET: Trading Bot ausführen
        cron('25 18 * * 1-5')
        // Bei Push: Neu bauen (Webhook in GitHub konfigurieren)
        pollSCM('')
    }

    environment {
        // In Jenkins anlegen: Manage Jenkins → Credentials → Add Credentials
        // Kind: "Secret text", ID: "ALPACA_API_KEY_PAPER" / "ALPACA_API_SECRET_PAPER"
        KEY    = credentials('ALPACA_API_KEY_PAPER')
        SECRET = credentials('ALPACA_API_SECRET_PAPER')
    }

    stages {
        stage('Build') {
            steps {
                sh 'docker build -t trading-bot .'
            }
        }

        stage('Trading Bot ausführen') {
            steps {
                sh '''
                    docker run --rm \
                        -e KEY=$KEY \
                        -e SECRET=$SECRET \
                        -e PAPER=true \
                        trading-bot
                '''
            }

        }
    }

    post {
        failure {
            echo 'Trading Bot fehlgeschlagen!'
        }
        success {
            echo 'Erfolgreich.'
        }
    }
}
