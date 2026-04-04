# Alpaca Trading Bot

Ein automatisierter Trading-Bot für die [Alpaca](https://alpaca.markets/) API, der eine Rolling-Regression-Strategie mit Hebelwirkung einsetzt. Der Bot wird täglich via Jenkins-Pipeline gebaut und ausgeführt und sendet nach jedem Lauf eine Zusammenfassung per Telegram.

## Inhaltsverzeichnis

- [Funktionsweise](#funktionsweise)
- [Implementierte Strategien](#implementierte-strategien)
- [Projektstruktur](#projektstruktur)
- [Installation & lokale Ausführung](#installation--lokale-ausführung)
- [Umgebungsvariablen (.env)](#umgebungsvariablen-env)
- [Docker](#docker)
- [Jenkins CI/CD](#jenkins-cicd)
- [Backtesting (Notebook)](#backtesting-notebook)
- [Disclaimer](#disclaimer)

---

## Funktionsweise

Bei jedem Lauf führt der Bot folgende Schritte aus:

1. Alpaca-Konto abfragen (Equity, Buying Power, offene Positionen)
2. Für jedes konfigurierte Symbol:
   - **Stop-Loss prüfen** – Verlust >= Schwellwert → sofortiger Marktverkauf
   - **Offene Orders prüfen** – Symbol überspringen, falls bereits eine Order läuft
   - **Analyse** – 1-Jahres-Kursdaten via yfinance laden, Rolling-Regression berechnen, Kauf-/Verkaufsbänder ermitteln
   - **Verkaufen** – aktueller Preis > oberes Band (und Position gehalten) → Markverkauf
   - **Kaufen** – aktueller Preis < unteres Band (und keine Position) → Marktkauf mit Hebel
3. Nach dem ersten Kauf werden die restlichen Symbole übersprungen
4. Die komplette Ausgabe wird als Telegram-Nachricht versendet

---

## Implementierte Strategien

Alle Strategien basieren auf einer **Rolling Linear Regression** über ein konfigurierbares Fenster. Der Regressionsendwert dient als „Fair Value". Kauf- und Verkaufsbänder werden als prozentualer Abstand zum Fair Value berechnet.

| Symbol | Hebel | Reg.-Fenster | Kauf-Abstand | Verkauf-Abstand | Stop-Loss |
|--------|-------|-------------|--------------|-----------------|-----------|
| AMD    | 3x    | 100 Tage    | -14 %        | +16 %           | -20 %     |
| MU     | 3x    | 100 Tage    | -8 %         | +8 %            | -10 %     |

Parameter können in `src/config.py` angepasst werden.

---

## Projektstruktur

```
trading_strategies/
├── src/
│   ├── main.py            # Einstiegspunkt – Orchestrierung aller Strategien
│   ├── strategy.py        # Rolling-Regression-Logik, Kauf-/Verkaufslogik
│   ├── config.py          # Pydantic-Konfigurationsklassen je Symbol (AMD, MU)
│   └── telegram_notify.py # Telegram-Benachrichtigung nach jedem Lauf
├── backtest_strategies.ipynb  # Backtesting & Visualisierung (Plotly)
├── Dockerfile             # Python 3.11 slim + uv
├── docker-compose.yml     # Lokales Starten mit .env-Datei
├── Jenkinsfile            # CI/CD-Pipeline (Build + tägliche Ausführung Mo–Fr 18:25 CET)
├── pyproject.toml         # Abhängigkeiten & Projektmetadaten
├── uv.lock                # Eingefrorene Abhängigkeiten (uv)
└── README.md
```

---

## Installation & lokale Ausführung

**Voraussetzungen:** Python >= 3.9, [uv](https://docs.astral.sh/uv/)

```bash
# Repository klonen
git clone https://github.com/MericKaynak/trading_strategies.git
cd trading_strategies

# Abhängigkeiten installieren
uv sync

# Bot einmalig ausführen
uv run -m src.main
```

---

## Umgebungsvariablen (.env)

Für die lokale Ausführung eine `.env`-Datei im Projektroot anlegen:

```dotenv
# Alpaca API-Credentials
# Paper-Trading:  https://app.alpaca.markets/paper-trading/overview → API Keys
# Live-Trading:   https://app.alpaca.markets/brokerage/overview      → API Keys
KEY=<dein-alpaca-api-key>
SECRET=<dein-alpaca-api-secret>

# true  = Paper-Trading-Konto (kein echtes Geld)
# false = Live-Trading-Konto
PAPER=true

# Telegram-Benachrichtigung (optional – ohne diese Werte wird keine Nachricht gesendet)
# Bot erstellen: https://t.me/BotFather → /newbot
TELEGRAM_BOT_TOKEN=<token-von-botfather>
# Chat-ID ermitteln: Bot Message senden, dann https://api.telegram.org/bot<TOKEN>/getUpdates aufrufen
TELEGRAM_CHAT_ID=<chat-id>
```

> Ohne `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` läuft der Bot normal, sendet aber keine Telegram-Nachricht.

---

## Docker

### docker-compose (empfohlen lokal)

```bash
# Baut das Image und startet den Bot einmalig (liest .env automatisch)
docker compose up --build
```

### Manuell

```bash
docker build -t trading-bot .

docker run --rm \
  -e KEY=<api-key> \
  -e SECRET=<api-secret> \
  -e PAPER=true \
  -e TELEGRAM_BOT_TOKEN=<token> \
  -e TELEGRAM_CHAT_ID=<chat-id> \
  trading-bot
```

---

## Jenkins CI/CD

Die `Jenkinsfile` definiert eine Pipeline mit zwei Stages:

| Stage | Beschreibung |
|-------|-------------|
| **Build** | `docker build -t trading-bot .` |
| **Trading Bot ausführen** | `docker run` mit allen Umgebungsvariablen aus den Jenkins-Credentials |

**Trigger:**
- **Täglich Mo–Fr um 18:25 Uhr CET** (cron `25 18 * * 1-5`)
- **Bei Push** auf den Branch (via GitHub Webhook / pollSCM)

### Jenkins Credentials einrichten

Unter **Manage Jenkins → Credentials → Add Credentials** folgende vier Einträge vom Typ *Secret text* anlegen:

| ID (exakt so eintragen)     | Inhalt                          |
|-----------------------------|---------------------------------|
| `ALPACA_API_KEY_PAPER`      | Alpaca Paper-Trading API Key    |
| `ALPACA_API_SECRET_PAPER`   | Alpaca Paper-Trading API Secret |
| `TELEGRAM_BOT_TOKEN`        | Telegram Bot Token              |
| `TELEGRAM_CHAT_ID`          | Telegram Chat ID                |

> Für Live-Trading die IDs in der `Jenkinsfile` auf `ALPACA_API_KEY_LIVE` / `ALPACA_API_SECRET_LIVE` umbenennen und `PAPER=false` setzen.

---

## Backtesting (Notebook)

Das Jupyter-Notebook `backtest_strategies.ipynb` ermöglicht die Visualisierung und Auswertung der Strategie auf historischen Daten (1 Jahr via yfinance). Es werden Regressionslinien, Kauf-/Verkaufsbänder und simulierte Trades mit Plotly dargestellt.

```bash
uv run jupyter notebook backtest_strategies.ipynb
```

---

## Disclaimer

Dieses Projekt dient ausschließlich zu Lern- und Forschungszwecken. Die implementierten Strategien und Backtesting-Ergebnisse stellen keine Finanzberatung dar. Der Handel mit Finanzinstrumenten ist mit erheblichen Risiken verbunden und kann zum vollständigen Verlust des eingesetzten Kapitals führen. Die Autoren übernehmen keinerlei Haftung für finanzielle Verluste, die durch die Nutzung dieser Software entstehen.
