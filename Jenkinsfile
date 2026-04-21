pipeline {
    agent any

    triggers {
        // Mo-Fr um 18:25 CET: Trading Bot ausführen
        cron('23 21 * * 1-5')
        // Bei Push: Neu bauen (Webhook in GitHub konfigurieren)
        pollSCM('')
    }

    environment {
        // In Jenkins anlegen: Manage Jenkins → Credentials → Add Credentials
        // Kind: "Secret text", ID: "ALPACA_API_KEY_PAPER" / "ALPACA_API_SECRET_PAPER"
        KEY    = credentials('ALPACA_API_KEY_PAPER')
        SECRET = credentials('ALPACA_API_SECRET_PAPER')
        TELEGRAM_BOT_TOKEN = credentials('TELEGRAM_BOT_TOKEN')
        TELEGRAM_CHAT_ID = credentials('TELEGRAM_CHAT_ID')
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
                        -e TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN \
                        -e TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID \
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
