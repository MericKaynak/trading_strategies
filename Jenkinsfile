pipeline {
    agent any

    triggers {
        // Mo-Fr um 18:00 CET: Trading Bot ausführen
        cron('0 18 * * 1-5')
        // Bei Push auf main/production: Neu bauen
        // Voraussetzung: Webhook in GitHub/GitLab auf Jenkins URL konfigurieren
        // GitHub: Settings → Webhooks → http://<jenkins-url>/github-webhook/
        pollSCM('')  // Aktiviert Webhook-Listener
    }

    environment {
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
            // Nur beim Cron-Trigger ausführen, nicht beim Push
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
    }

    post {
        failure {
            echo '❌ Trading Bot fehlgeschlagen!'
        }
        success {
            echo '✅ Erfolgreich.'
        }
        always {
            sh 'docker compose down || true'
        }
    }
}
