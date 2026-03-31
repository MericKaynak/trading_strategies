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


def check_stop_loss(client, config, positions):
    """
    Prüft Stop-Loss für dieses Symbol.
    Gibt True zurück wenn ein Stop-Loss Verkauf stattfand.
    """
    if not config.STOP_LOSS_ACTIVE:
        return False

    for pos in positions:
        if pos.symbol == config.SYMBOL:
            avg_entry = float(pos.avg_entry_price)
            current_price = float(pos.current_price)
            qty = float(pos.qty)
            loss_pct = (avg_entry - current_price) / avg_entry

            if loss_pct >= config.STOP_LOSS:
                print(f"  ⚠️  STOP-LOSS für {config.SYMBOL}! Verlust: {loss_pct*100:.1f}%")
                client.submit_order(MarketOrderRequest(
                    symbol=config.SYMBOL, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY
                ))
                print(f"  STOP-LOSS ORDER: Verkauf von {qty} {config.SYMBOL}")
                return True
    return False


def analyze_symbol(config):
    """Analysiert ein Symbol. Gibt (last_price, last_reg, lower_band, upper_band) zurück."""
    data = yf.download(tickers=config.SYMBOL, period="1y", progress=False)
    data.columns = data.columns.get_level_values(0)
    data['Reg_Line'] = rolling_linreg(data['Close'], config.REG_WINDOW)
    data = data.dropna()

    last_price = float(data['Close'].iloc[-1])
    last_reg = float(data['Reg_Line'].iloc[-1])
    upper_band = last_reg * (1 + config.SELL_DEVIATION)
    lower_band = last_reg * (1 - config.BUY_DEVIATION)

    return last_price, last_reg, lower_band, upper_band


def run_strategy(client, config, positions, equity, buying_power):
    """
    Prüft eine einzelne Strategie (ein Symbol).
    Gibt zurück: 'bought', 'sold', 'stop', 'skip' oder 'none'
    """
    symbol = config.SYMBOL
    print(f"\n  [{symbol}] Analyse...")

    # 1. Stop-Loss
    if check_stop_loss(client, config, positions):
        return "stop"

    # 2. Offene Orders?
    order_filter = GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol])
    if len(client.get_orders(filter=order_filter)) > 0:
        print(f"  [{symbol}] Offene Order vorhanden → überspringe.")
        return "skip"

    # 3. Aktuelle Position?
    holding_qty = sum(float(p.qty) for p in positions if p.symbol == symbol)

    # 4. Analyse
    last_price, last_reg, lower_band, upper_band = analyze_symbol(config)
    print(f"  [{symbol}] Preis: ${last_price:.2f} | Fair Value: ${last_reg:.2f}")
    print(f"  [{symbol}] Kauf < ${lower_band:.2f} | Verkauf > ${upper_band:.2f} | Halte: {holding_qty}")

    # 5. VERKAUFEN
    if holding_qty > 0 and last_price > upper_band:
        client.submit_order(MarketOrderRequest(
            symbol=symbol, qty=holding_qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY
        ))
        print(f"  ✅ VERKAUF: {holding_qty} {symbol} @ ~${last_price:.2f}")
        return "sold"

    # 6. KAUFEN (nur wenn keine Position in diesem Symbol)
    if holding_qty == 0 and last_price < lower_band:
        target_val = equity * config.LEVERAGE
        safe_val = min(target_val, buying_power * 0.95)
        qty = int(safe_val / last_price)

        if qty > 0:
            client.submit_order(MarketOrderRequest(
                symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.DAY
            ))
            print(f"  ✅ KAUF: {qty} {symbol} @ ~${last_price:.2f} ({config.LEVERAGE}x Hebel)")
            return "bought"
        else:
            print(f"  ❌ {symbol}: Nicht genug Kaufkraft.")

    return "none"
