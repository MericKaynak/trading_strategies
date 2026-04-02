import os
import sys
from datetime import datetime
from alpaca.trading.client import TradingClient
from src.strategy import run_strategy
from src.config import AMDConfig, MUConfig
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("KEY")
API_SECRET = os.getenv("SECRET")
IS_PAPER = os.getenv("PAPER", "true").strip().lower() == "true"

# ==========================================
# ALLE STRATEGIEN / SYMBOLE HIER DEFINIEREN
# Reihenfolge = Priorität (erste wird zuerst geprüft)
# ==========================================
STRATEGIES = [
    AMDConfig(API_KEY=API_KEY, API_SECRET=API_SECRET),
    MUConfig(API_KEY=API_KEY, API_SECRET=API_SECRET),
]


def job():
    """
    Geht durch alle Strategien der Reihe nach:
    1. Stop-Loss + Verkaufs-Checks für ALLE Symbole
    2. Kauf-Check: Kauft beim ERSTEN Symbol mit Kaufsignal
       (nur wenn kein Geld bereits investiert ist)
    """
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] Trading Bot Run")
    print(f"{'='*50}")

    try:
        client = TradingClient(API_KEY, API_SECRET, paper=IS_PAPER)
        account = client.get_account()
        equity = float(account.equity)
        buying_power = float(account.buying_power)
        positions = client.get_all_positions()

        held_symbols = {p.symbol: float(p.qty) for p in positions}
        print(f"  Equity: ${equity:,.2f} | Buying Power: ${buying_power:,.2f}")
        print(f"  Positionen: {held_symbols if held_symbols else 'keine'}")
        print(f"  Strategien: {[c.SYMBOL for c in STRATEGIES]}")

        for config in STRATEGIES:
            result = run_strategy(client, config, positions, equity, buying_power)

            if result in ("sold", "stop"):
                account = client.get_account()
                equity = float(account.equity)
                buying_power = float(account.buying_power)
                positions = client.get_all_positions()

            if result == "bought":
                print(f"\n  ✅ {config.SYMBOL} gekauft → Rest überspringen.")
                break

        print(f"\n{'='*50}")
        print(f"  Run abgeschlossen.")
        print(f"{'='*50}")

    except Exception as e:
        print(f"❌ FEHLER: {e}")


# Startup Info
print(f"--- BOT GESTARTET ---")
print(f"Strategien:")
for cfg in STRATEGIES:
    print(f"  • {cfg.SYMBOL}: {cfg.LEVERAGE}x Hebel | Stop-Loss: {cfg.STOP_LOSS*100:.0f}% | "
          f"Buy: -{cfg.BUY_DEVIATION*100:.0f}% | Sell: +{cfg.SELL_DEVIATION*100:.0f}%")
print(f"Modus: {'PAPER' if IS_PAPER else 'LIVE'}")

# Direkt ausführen — Scheduling läuft über Jenkins Pipeline
job()
print("--- BOT BEENDET ---")