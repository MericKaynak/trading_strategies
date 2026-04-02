import os
import sys
from datetime import datetime
from alpaca.trading.client import TradingClient
from src.strategy import check_and_sell, check_and_buy
from src.config import AMDConfig, MUConfig
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("KEY")
API_SECRET = os.getenv("SECRET")

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
    Phase 1: Verkaufs-Check für ALLE Symbole (Stop-Loss + Signal-Verkauf)
    Phase 2: Kauf-Check mit 50/50-Split — jedes Symbol bekommt equity*leverage/N Budget
    """
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] Trading Bot Run")
    print(f"{'='*50}")

    try:
        client = TradingClient(API_KEY, API_SECRET, paper=STRATEGIES[0].PAPER)
        account = client.get_account()
        equity = float(account.equity)
        buying_power = float(account.buying_power)
        positions = client.get_all_positions()

        held_symbols = {p.symbol: float(p.qty) for p in positions}
        print(f"  Equity: ${equity:,.2f} | Buying Power: ${buying_power:,.2f}")
        print(f"  Positionen: {held_symbols if held_symbols else 'keine'}")

        # ── Phase 1: Alle Verkäufe zuerst ────────────────────────────────
        print(f"\n  --- Phase 1: Verkauf ({len(STRATEGIES)} Symbole) ---")
        any_sold = False
        for config in STRATEGIES:
            result = check_and_sell(client, config, positions)
            if result in ("sold", "stop"):
                any_sold = True

        if any_sold:
            account = client.get_account()
            equity = float(account.equity)
            buying_power = float(account.buying_power)
            positions = client.get_all_positions()
            print(f"  Equity nach Verkäufen: ${equity:,.2f} | BP: ${buying_power:,.2f}")

        # ── Phase 2: Käufe mit 50/50-Split ───────────────────────────────
        print(f"\n  --- Phase 2: Kauf 50/50-Split ({len(STRATEGIES)} Symbole) ---")
        n = len(STRATEGIES)
        for config in STRATEGIES:
            pos = next((p for p in positions if p.symbol == config.SYMBOL), None)
            pos_value = float(pos.market_value) if pos else 0.0
            # Zielallokation: equity * leverage gleichmäßig auf alle Symbole verteilt
            target = (equity * config.LEVERAGE) / n
            budget = min(max(0.0, target - pos_value), buying_power * 0.95)
            pct = pos_value / equity * 100 if equity > 0 else 0
            print(f"  [{config.SYMBOL}] Ziel: ${target:,.0f} | Ist: ${pos_value:,.0f} ({pct:.1f}%) | Budget: ${budget:,.0f}")

            if budget > 10:
                result = check_and_buy(client, config, positions, budget)
                if result == "bought":
                    account = client.get_account()
                    buying_power = float(account.buying_power)
                    positions = client.get_all_positions()

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
print(f"Modus: {'PAPER' if STRATEGIES[0].PAPER else 'LIVE'}")

# Direkt ausführen — Scheduling läuft über Jenkins Pipeline
job()
print("--- BOT BEENDET ---")