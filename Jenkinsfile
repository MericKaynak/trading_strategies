pipeline {
    agent any

    triggers {
        // Mo-Fr um 18:00 CET: Trading Bot ausführen
        cron('25 18 * * 1-5')
        // Bei Push: Neu bauen (Webhook in GitHub konfigurieren)
        pollSCM('')
    }

    environment {

        ALPACA_API_KEY_PAPER      = credentials('ALPACA_API_KEY_PAPER')
        ALPACA_API_SECRET_PAPER   = credentials('ALPACA_API_SECRET_PAPER')
    }

    stages {
        stage('Build') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Run Trading Bot') {
            steps {
                sh '''
                    docker compose run --rm \
                        -e KEY=$ALPACA_API_KEY_PAPER \
                        -e SECRET=$ALPACA_API_SECRET_PAPER \
                        -e PAPER=true \
                        trading-bot \
                        python -m src.main
                '''
            }
        }

        stage('Cleanup') {
            steps {
                sh 'docker compose down || true'
            }
        }
    }

    post {
        failure {
            echo '❌ Trading Bot fehlgeschlagen!'
        }
        success {
            echo '✅ Erfolgreich.'
        }
    }
}
