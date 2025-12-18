import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

def rolling_linreg(series, window):
    y = series.values
    x = np.arange(window)
    reg = np.full(len(y), np.nan)
    for i in range(window, len(y)):
        y_window = y[i-window:i]
        m, c = np.polyfit(x, y_window, 1)
        reg[i] = m * (window - 1) + c
    return pd.Series(reg, index=series.index)

def run_regression_strategy(config):
    """
    Führt die Strategie einmal aus. 
    Erwartet ein Dictionary 'config' mit API-Keys und Parametern.
    """
    print(f"[{datetime.now()}] Starte Strategie-Check für {config['SYMBOL']}...")
    
    try:
        client = TradingClient(config['API_KEY'], config['API_SECRET'], paper=config['PAPER'])
        
        # 1. Datenanalyse
        data = yf.download(tickers=config['SYMBOL'], period="1y", progress=False)
        data.columns = data.columns.get_level_values(0)
        
        data['Reg_Line'] = rolling_linreg(data['Close'], config['REG_WINDOW'])
        data = data.dropna()

        last_price = float(data['Close'].iloc[-1])
        last_reg = float(data['Reg_Line'].iloc[-1])
        upper_band = last_reg * (1 + config['SELL_DEVIATION'])
        lower_band = last_reg * (1 - config['BUY_DEVIATION'])

        # 2. Account & Positionen
        account = client.get_account()
        equity = float(account.equity)
        buying_power = float(account.buying_power)
        
        positions = client.get_all_positions()
        holding_qty = sum(float(p.qty) for p in positions if p.symbol == config['SYMBOL'])

        # Offene Orders checken
        order_filter = GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[config['SYMBOL']])
        has_open_order = len(client.get_orders(filter=order_filter)) > 0

        print(f"Preis: {last_price:.2f} | Fair Value: {last_reg:.2f} | Halte: {holding_qty}")

        if has_open_order:
            print("Abbruch: Es gibt bereits eine aktive Order.")
            return

        # 3. Handelsentscheidung
        # KAUFEN
        if last_price < lower_band and holding_qty == 0:
            target_val = equity * config['LEVERAGE']
            # Sicherheitslimit: 95% der Buying Power
            safe_val = min(target_val, buying_power * 0.95)
            qty = int(safe_val / last_price)
            
            if qty > 0:
                client.submit_order(MarketOrderRequest(
                    symbol=config['SYMBOL'], qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.DAY
                ))
                print(f"ORDER GESENDET: Kauf von {qty} {config['SYMBOL']}")

        # VERKAUFEN
        elif last_price > upper_band and holding_qty > 0:
            client.submit_order(MarketOrderRequest(
                symbol=config['SYMBOL'], qty=holding_qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY
            ))
            print(f"ORDER GESENDET: Verkauf von {holding_qty} {config['SYMBOL']}")
        
        else:
            print("Keine Aktion erforderlich.")

    except Exception as e:
        print(f"STRATEGIE-FEHLER: {e}")