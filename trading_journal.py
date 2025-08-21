import os
import requests
from datetime import datetime, timedelta
from notion_client import Client

# ==== Настройки ====
BYBIT_API_KEY = os.environ.get("BYBIT_API_KEY")
BYBIT_API_SECRET = os.environ.get("BYBIT_API_SECRET")
MEXC_API_KEY = os.environ.get("MEXC_API_KEY")
MEXC_API_SECRET = os.environ.get("MEXC_API_SECRET")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# Инициализация Notion
notion = Client(auth=NOTION_TOKEN)

# ==== Функции для Bybit ====
def fetch_bybit_futures_trades():
    """Закрытые сделки фьючерсов (V5 API)"""
    all_trades = []
    url = "https://api.bybit.com/v5/order/realised-profit/list"
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    params = {
        "category": "linear",
        "symbol": "",
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
        "limit": 50
    }
    headers = {"X-BAPI-API-KEY": BYBIT_API_KEY, "Content-Type": "application/json"}

    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        if data.get("retCode") != 0:
            print("Ошибка Bybit Futures:", data)
            return []
        for trade in data.get("result", {}).get("list", []):
            all_trades.append({
                "symbol": trade.get("symbol"),
                "side": trade.get("side"),
                "price": trade.get("price"),
                "qty": trade.get("qty"),
                "pnl": trade.get("realisedPnl"),
                "timestamp": datetime.utcfromtimestamp(trade.get("tradeTime") / 1000),
                "type": "futures"
            })
    except Exception as e:
        print("Ошибка при запросе фьючерсов:", e, getattr(r, 'text', ''))
    return all_trades

def fetch_bybit_spot_trades():
    """История ордеров спот"""
    all_trades = []
    url = "https://api.bybit.com/v5/spot/order/history"
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    params = {
        "startTime": int(start.timestamp() * 1000),
        "endTime": int(end.timestamp() * 1000),
        "limit": 50
    }
    headers = {"X-BAPI-API-KEY": BYBIT_API_KEY, "Content-Type": "application/json"}

    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        if data.get("retCode") != 0:
            print("Ошибка Bybit Spot:", data)
            return []
        for trade in data.get("result", []):
            all_trades.append({
                "symbol": trade.get("symbol"),
                "side": trade.get("side"),
                "price": trade.get("price"),
                "qty": trade.get("qty"),
                "status": trade.get("orderStatus"),
                "timestamp": datetime.utcfromtimestamp(trade.get("createTime") / 1000),
                "type": "spot"
            })
    except Exception as e:
        print("Ошибка при запросе спота:", e, getattr(r, 'text', ''))
    return all_trades

# ==== Функции для MEXC ====
def fetch_mexc_futures_trades():
    """Закрытые сделки фьючерсов (MEXC API)"""
    all_trades = []
    url = "https://contract.mexc.com/api/v1/private/order/external"
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    params = {
        "symbol": "BTC_USDT",  # Пример: BTC/USDT
        "startTime": int(start.timestamp() * 1000),
        "endTime": int(end.timestamp() * 1000),
        "limit": 50
    }
    headers = {"X-MEXC-APIKEY": MEXC_API_KEY}

    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        if data.get("code") != 0:
            print("Ошибка MEXC Futures:", data)
            return []
        for trade in data.get("data", []):
            all_trades.append({
                "symbol": trade.get("symbol"),
                "side": "buy" if trade.get("side") == 1 else "sell",
                "price": trade.get("dealAvgPrice"),
                "qty": trade.get("dealVol"),
                "pnl": trade.get("profit"),
                "timestamp": datetime.utcfromtimestamp(trade.get("createTime") / 1000),
                "type": "futures"
            })
    except Exception as e:
        print("Ошибка при запросе фьючерсов MEXC:", e, getattr(r, 'text', ''))
    return all_trades

def fetch_mexc_spot_trades():
    """История ордеров спот (MEXC API)"""
    all_trades = []
    url = "https://api.mexc.com/api/v3/private/order/history"
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    params = {
        "startTime": int(start.timestamp() * 1000),
        "endTime": int(end.timestamp() * 1000),
        "limit": 50
    }
    headers = {"X-MEXC-APIKEY": MEXC_API_KEY}

    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        if data.get("code") != 0:
            print("Ошибка MEXC Spot:", data)
            return []
        for trade in data.get("data", []):
            all_trades.append({
                "symbol": trade.get("symbol"),
                "side": "buy" if trade.get("side") == 1 else "sell",
                "price": trade.get("dealAvgPrice"),
                "qty": trade.get("dealVol"),
                "status": trade.get("status"),
                "timestamp": datetime.utcfromtimestamp(trade.get("createTime") / 1000),
                "type": "spot"
            })
    except Exception as e:
        print("Ошибка при запросе спота MEXC:", e, getattr(r, 'text', ''))
    return all_trades

# ==== Функция для отправки в Notion ====
def send_trades_to_notion(trades):
    for trade in trades:
        try:
            notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties={
                    "Дата": {"date": {"start": trade["timestamp"].isoformat()}},
                    "Символ": {"title": [{"text": {"content": trade["symbol"]}}]},
                    "Сторона": {"rich_text": [{"text": {"content": trade["side"]}}]},
                    "Цена": {"number": float(trade["price"])},
                    "Кол-во": {"number": float(trade.get("qty", 0))},
                    "PnL": {"number": float(trade.get("pnl", 0))},
                    "Статус": {"rich_text": [{"text": {"content": trade.get("status", "")}}]},
                    "Тип": {"select": {"name": trade.get("type")}}
                }
            )
        except Exception as e:
            print("Ошибка при отправке в Notion:", e)

# ==== Основной блок ====
if __name__ == "__main__":
    print("Запуск скрипта: получение сделок Bybit и MEXC")
    bybit_futures_trades = fetch_bybit_futures_trades()
    bybit_spot_trades = fetch_bybit_spot_trades()
    mexc_futures_trades = fetch_mexc_futures_trades()
    mexc_spot_trades = fetch_mexc_spot_trades()

    all_trades = bybit_futures_trades + bybit_spot_trades + mexc_futures_trades + mexc_spot_trades
    print(f"Найдено {len(all_trades)} сделок. Отправка в Notion...")
    send_trades_to_notion(all_trades)
    print("Готово ✅")
