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
        PAPER  = 'true'
    }

    stages {
        stage('Dependencies installieren') {
            steps {
                sh 'uv sync --frozen --no-dev'
            }
        }

        stage('Trading Bot ausführen') {
            steps {
                sh 'uv run python -m src.main'
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
