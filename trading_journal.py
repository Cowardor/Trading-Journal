import requests
import datetime
from notion_client import Client

# ------------------------
# Настройки
# ------------------------
NOTION_TOKEN = "secret_твой_интеграционный_ключ"
DATABASE_ID = "твоя_id_таблицы_journal"

BYBIT_API_KEY = "твой_ключ"
BYBIT_API_SECRET = "твой_секрет"

MEXC_API_KEY = "твой_ключ"
MEXC_API_SECRET = "твой_секрет"

# ------------------------
# Инициализация Notion
# ------------------------
notion = Client(auth=NOTION_TOKEN)

# ------------------------
# Функция добавления сделки
# ------------------------
def add_trade(trade):
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "DateTime": {"date": {"start": trade["date"]}},
            "Account": {"relation": [{"id": trade["account_id"]}]},
            "Exchange": {"select": {"name": trade["exchange"]}},
            "Type": {"select": {"name": trade["type"]}},
            "Symbol": {"title": [{"text": {"content": trade["symbol"]}}]},
            "Direction": {"select": {"name": trade.get("direction","")}},
            "Entry Price": {"number": trade.get("entry_price",0)},
            "Exit Price": {"number": trade.get("exit_price",0)},
            "Position Size (USDT)": {"number": trade.get("position_size",0)},
            "Account Balance": {"number": trade.get("account_balance",0)},
            "StopLoss %": {"number": trade.get("stop_loss",0)},
            "TakeProfit %": {"number": trade.get("take_profit",0)},
            "Status": {"select": {"name": trade.get("status","")}},
            "Strategy": {"select": {"name": trade.get("strategy","")}},
            "Kill Zone": {"select": {"name": trade.get("kill_zone","")}}
        }
    )

# ------------------------
# Пример получения сделок с Bybit
# ------------------------
def get_bybit_closed_trades():
    # TODO: добавить вызов Bybit API для закрытых позиций
    # вернуть список словарей с ключами: date, account_id, exchange, type, symbol, direction, entry_price, exit_price, position_size, account_balance, stop_loss, take_profit, status
    return []

# ------------------------
# Пример получения сделок с MEXC
# ------------------------
def get_mexc_closed_trades():
    # TODO: аналогично Bybit
    return []

# ------------------------
# Основной цикл
# ------------------------
def main():
    trades = get_bybit_closed_trades() + get_mexc_closed_trades()
    for t in trades:
        add_trade(t)

if __name__ == "__main__":
    main()
