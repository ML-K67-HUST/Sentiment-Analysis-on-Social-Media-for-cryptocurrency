import requests
import json
from datetime import datetime, timedelta
# from datetime import datetime, timedelta
def construct():
    # Lấy tất cả data có 'constructed' = 0 
    # Construct data xong lưu vào db
    # Update data vừa query 'constructed' = 1
    pass

def get_bitcoin_change(timePeriod):
    response = requests.request("GET", f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd?timePeriod={timePeriod}")
    return json.loads(response.text)["data"]["coin"]["change"]

def get_bitcoin_price(timestamp):
    response = requests.request("GET", f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/price?timestamp={timestamp}")
    return response.text

def get_bitcoin_price_one_hour(timestamp):
    one_hour_ahead = str(int(timestamp) + 3600)
    try:
        return json.loads(get_bitcoin_price(one_hour_ahead))["data"]["price"]
    except Exception as e:
        return None

def get_bitcoin_change_overtime():
    return {
        "timestamp": int(datetime.now().timestamp()),
        "7_days_ago": get_bitcoin_change("7d"),
        "1_days_ago": get_bitcoin_change("24h"),
        "12_hours_ago":get_bitcoin_change("12h"),
        "3_hours_ago":get_bitcoin_change("3h")
    }

def construct_unlabeled_dataset(bot_sentiment):
    btc_price_over_time = get_bitcoin_change_overtime()
    btc_price_over_time["bot_sentiment"] = bot_sentiment
    return btc_price_over_time
# get_bitcoin_price("1714215700")

# get_bitcoin_price_one_hour("1730509760")
# print(construct_unlabeled_dataset("-2.38"))