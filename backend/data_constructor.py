import requests
import json
from datetime import datetime, timedelta
import time
# from datetime import datetime, timedelta

def get_bitcoin_change(timePeriod):
    headers = {
        'x-access-token': 'coinrankingcf28de3a1e8ccdad31ea8cb51ed9f8e4a98df79b535570a1',
        # 'referenceCurrencyUuid':'Qwsogvtv82FCd',
        # 'timePeriod':'30d'
    }

    response = requests.request("GET", f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd?timePeriod={timePeriod}",headers=headers)
    try:
        return json.loads(response.text)["data"]["coin"]["change"]
    except Exception as e:
        print('ERROR GETING THIS RESPONSE:',response.text)
        print(f'ERROR WHILE GET BITCOIN CHANGE: {e}, RETRY 10 second...')
        time.sleep(10)
        return json.loads(response.text)["data"]["coin"]["change"]

def get_bitcoin_price(timestamp):
    headers = {
        'x-access-token': 'coinrankingcf28de3a1e8ccdad31ea8cb51ed9f8e4a98df79b535570a1',
    }
    response = requests.request("GET", f"https://api.coinranking.com/v2/coin/Qwsogvtv82FCd/price?timestamp={timestamp}",headers=headers)
    return response.text

def get_bitcoin_price_one_hour(timestamp):
    one_hour_ahead = str(int(timestamp) + 3600)
    try:
        return json.loads(get_bitcoin_price(one_hour_ahead))["data"]["price"]
    except Exception as e:
        return None

def get_bitcoin_change_overtime():
    return {
        "timestamp": (int(datetime.now().timestamp())),
        "7_days_ago": get_bitcoin_change("7d"),
        "1_days_ago": get_bitcoin_change("24h"),
        "12_hours_ago":get_bitcoin_change("12h"),
        "3_hours_ago":get_bitcoin_change("3h")
    }

def construct_unlabeled_dataset(bot_sentiment):
    btc_price_over_time = get_bitcoin_change_overtime()
    btc_price_over_time["bot_sentiment"] = bot_sentiment
    btc_price_over_time["labeled"] = 'false'
    return btc_price_over_time
# get_bitcoin_price("1714215700")

# get_bitcoin_price_one_hour("1730509760")
# print(construct_unlabeled_dataset("-2.38"))