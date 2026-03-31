pipeline {
    agent any

    triggers {
        // Mo-Fr um 18:00 CET: Trading Bot ausführen
        cron('0 18 * * 1-5')
        // Bei Push: Neu bauen (Webhook in GitHub konfigurieren)
        pollSCM('')
    }

    environment {
        // In Jenkins anlegen: Manage Jenkins → Credentials → Add Credentials
        // Kind: "Secret text", ID: "ALPACA_API_KEY" / "ALPACA_API_SECRET"
        KEY      = credentials('ALPACA_API_KEY')
        SECRET   = credentials('ALPACA_API_SECRET')
    }

    stages {
        stage('Build') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Run Trading Bot') {
            when {
                triggeredBy 'TimerTrigger'
            }
            steps {
                sh '''
                    docker compose run --rm \
                        -e KEY=$KEY \
                        -e SECRET=$SECRET \
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
