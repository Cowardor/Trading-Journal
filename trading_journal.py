import os
import hmac
import hashlib
import time
import requests
from notion_client import Client
from datetime import datetime

# Notion
notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Bybit API keys
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# MEXC API keys
MEXC_API_KEY = os.getenv("MEXC_API_KEY")
MEXC_API_SECRET = os.getenv("MEXC_API_SECRET")

# ================================
# BYBIT CLOSED TRADES
# ================================
def fetch_bybit_trades():
    url = "https://api.bybit.com/v5/execution/list"
    params = {
        "category": "linear",   # деривативы (фьючерсы)
        "limit": 10,
        "timestamp": str(int(time.time() * 1000)),
        "api_key": BYBIT_API_KEY,
    }
    # подпись
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    sign = hmac.new(BYBIT_API_SECRET.encode("utf-8"), param_str.encode("utf-8"), hashlib.sha256).hexdigest()
    params["sign"] = sign

    r = requests.get(url, params=params)
    data = r.json()
    trades = []

    if "result" in data and "list" in data["result"]:
        for t in data["result"]["list"]:
            trades.append({
                "date": datetime.fromtimestamp(int(t["createdTime"]) / 1000).isoformat(),
                "symbol": t["symbol"],
                "type": "Futures",
                "account": "Bybit",
                "direction": "Long" if t["side"] == "Buy" else "Short",
                "pnl": float(t.get("closedPnl", 0)),
                "pnl_percent": None,  # можно доработать при желании
                "rr": None,           # можно рассчитать по SL/TP
                "status": "TP" if float(t.get("closedPnl", 0)) > 0 else "SL"
            })
    return trades

# ================================
# MEXC CLOSED TRADES
# ================================
def fetch_mexc_trades():
    url = "https://contract.mexc.com/api/v1/private/order/list/historyOrders"
    timestamp = str(int(time.time() * 1000))
    query = f"api_key={MEXC_API_KEY}&req_time={timestamp}"
    sign = hmac.new(MEXC_API_SECRET.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    params = {
        "api_key": MEXC_API_KEY,
        "req_time": timestamp,
        "sign": sign
    }

    r = requests.get(url, params=params)
    data = r.json()
    trades = []

    if "data" in data:
        for t in data["data"]:
            trades.append({
                "date": datetime.fromtimestamp(int(t["createTime"]) / 1000).isoformat(),
                "symbol": t["symbol"],
                "type": "Futures",
                "account": "MEXC",
                "direction": "Long" if t["side"] == 1 else "Short",
                "pnl": float(t.get("profitReal", 0)),
                "pnl_percent": None,
                "rr": None,
                "status": "TP" if float(t.get("profitReal", 0)) > 0 else "SL"
            })
    return trades

# ================================
# PUSH TO NOTION
# ================================
def push_to_notion(trades):
    for trade in trades:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Date": {"date": {"start": trade["date"]}},
                "Symbol": {"title": [{"text": {"content": trade["symbol"]}}]},
                "Type": {"select": {"name": trade["type"]}},
                "Account": {"select": {"name": trade["account"]}},
                "Direction": {"select": {"name": trade["direction"]}},
                "PnL": {"number": trade["pnl"]},
                "PnL %": {"number": trade["pnl_percent"] if trade["pnl_percent"] else 0},
                "RR": {"number": trade["rr"] if trade["rr"] else 0},
                "Status": {"select": {"name": trade["status"]}}
            }
        )

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    all_trades = []
    all_trades += fetch_bybit_trades()
    all_trades += fetch_mexc_trades()
    if all_trades:
        push_to_notion(all_trades)
        print(f"✅ {len(all_trades)} trades pushed to Notion!")
    else:
        print("⚠️ No trades found.")
