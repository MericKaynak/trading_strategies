import pandas as pd
import numpy as np
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import yfinance as yf
import os

# --- Konfiguration ---
API_KEY = os.getenv("KEY")
API_SECRET = os.getenv("SECRET")
PAPER = True 

SYMBOL = "AMD"
REGRESSION_WINDOW = 100
BUY_DEVIATION = 0.14   
SELL_DEVIATION = 0.13

# --- NEU: HEBEL EINSTELLUNG ---
LEVERAGE = 2.0  # 2.0 bedeutet 200% deines Kapitals einsetzen

# ==============================
# 1. Alpaca Trading Client
# ==============================
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)

# ==============================
# 2. Historische Daten via yfinance
# ==============================
# Wir brauchen genug Daten für die Regression (mind. REGRESSION_WINDOW Tage)
START_DATE = (datetime.now() - pd.Timedelta(days=200)).strftime("%Y-%m-%d")
END_DATE = datetime.today().strftime("%Y-%m-%d")

data = yf.download(tickers=SYMBOL, start=START_DATE, end=END_DATE, progress=False)
data.columns = data.columns.get_level_values(0)

# ==============================
# 3. Rolling Regression (Fair Value)
# ==============================
def rolling_linreg(series, window):
    y = series.values
    x = np.arange(window)
    reg = np.full(len(y), np.nan)
    for i in range(window, len(y)):
        y_window = y[i-window:i]
        m, c = np.polyfit(x, y_window, 1)
        reg[i] = m * (window - 1) + c
    return pd.Series(reg, index=series.index)

data['Reg_Line'] = rolling_linreg(data['Close'], REGRESSION_WINDOW)
data = data.dropna()

# Letzte Werte extrahieren
last_price = data['Close'].iloc[-1]
last_reg = data['Reg_Line'].iloc[-1]
upper_band = last_reg * (1 + SELL_DEVIATION)
lower_band = last_reg * (1 - BUY_DEVIATION)

print(f"--- STATUS {SYMBOL} ---")
print(f"Preis: {last_price:.2f} | Fair Value: {last_reg:.2f}")
print(f"Kauf-Limit: {lower_band:.2f} | Verkauf-Limit: {upper_band:.2f}")

# ==============================
# 4. Konto & Positionen abrufen
# ==============================
account = trading_client.get_account()
# 'equity' ist der Gesamtwert deines Kontos (Cash + Wert der Aktien)
current_equity = float(account.equity)
buying_power = float(account.buying_power)

positions = trading_client.get_all_positions()
holding_qty = 0
for p in positions:
    if p.symbol == SYMBOL:
        holding_qty = float(p.qty)
        break

# ==============================
# 5. Order-Logik mit Hebel
# ==============================

if last_price < lower_band and holding_qty == 0:
    # 1. Ziel-Wert berechnen
    target_value = current_equity * LEVERAGE
    
    # 2. SICHERHEITS-PUFFER: Nutze nur 97% der verfügbaren Kaufkraft
    # Das verhindert den "insufficient buying power" Fehler bei Preisschwankungen
    available_safe_power = buying_power * 0.97 
    
    if target_value > available_safe_power:
        target_value = available_safe_power
        
    # 3. Stückzahl berechnen
    qty = int(target_value / last_price)
    
    if qty > 0:
        try:
            order_data = MarketOrderRequest(
                symbol=SYMBOL,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            trading_client.submit_order(order_data)
            print(f"ERFOLG: {qty} Aktien mit {LEVERAGE}x Hebel gekauft.")
        except Exception as e:
            print(f"FEHLER beim Senden der Order: {e}")
    else:
        print("Kauf fehlgeschlagen: Zu wenig Kapital für 1 Aktie.")

# VERKAUFEN (Wenn Preis > Upper Band und wir Aktien halten)
elif last_price > upper_band and holding_qty > 0:
    try:
        order_data = MarketOrderRequest(
            symbol=SYMBOL,
            qty=holding_qty, 
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        trading_client.submit_order(order_data)
        print(f"ERFOLG: Position von {holding_qty} Aktien glattgestellt.")
    except Exception as e:
        print(f"FEHLER beim Verkauf: {e}")

else:
    print("Keine Aktion: Bedingungen nicht erfüllt oder bereits investiert.")
