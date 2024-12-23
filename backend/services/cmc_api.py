from database.mongodb import MongoManager
from datetime import datetime, timedelta

def time_ago(timestamp):
    timestamp = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    delta = now - timestamp

    if delta.days > 0:
        return f"{delta.days} day(s) ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour(s) ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute(s) ago"
    else:
        return "Just now"
    

def get_cmc_news():
    
    mongo_client = MongoManager('blog-data')
    cmc_data = mongo_client.find(
        collection_name='cmc_sentiment_data',
        filter={
            "symbol":"BTC",
        },
        sort=("timestamp",-1),
        limit=10
    )
    cmc_data
    # cmc_data.sort(key=lambda x:x["timestamp"],reverse=True)
    # cmc_data

    # for data in cmc_data:
    #     print(time_ago(int(data['timestamp'])))
    result = []
    for data in cmc_data:
        sentiments = []
        for sentiment,descript in data["btc_sentiment"].items():
            if descript["result"] == 1:
                if "positive" in sentiment.lower():
                    sentiments.append({
                        "type":"Positive",
                        "content":descript["reasoning"]
                    })
                elif "negative" in sentiment.lower():
                    sentiments.append({
                        "type":"Negative",
                        "content":descript["reasoning"]
                    })
                elif "reporting" in sentiment.lower():
                    sentiments.append({
                        "type":"reporting",
                        "content":descript["reasoning"]
                    })
                elif "manipulation" in sentiment.lower():
                    sentiments.append({
                        "type":"manipulate",
                        "content":descript["reasoning"]
                    })
        result.append({
            "timestamp":time_ago(int(data["timestamp"])),
            "title": data['source_data'][0]['title'],
            "description": data['source_data'][0]["content"][:260]+'...',
            "link": data['source_data'][0]["url"],
            "sentiments":sentiments
        })
        # print({
        #     "timestamp":time_ago(int(data["timestamp"])),
        #     "title": data['source_data'][0]['title'],
        #     "description": data['source_data'][0]["content"],
        #     "link": data['source_data'][0]["url"],
        #     "sentiments":sentiments
        # })
    return result
    # return [
    #     {
    #         "timestamp": "1 hours ago",
    #         "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
    #         "description": "The world of cryptocurrencies is in turmoil...",
    #         "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
    #         "sentiments": [
    #             {
    #                 "type": "Positive",
    #                 "content": "the article presents a reasonable and wellsubstantiated case..."
    #             },
    #             {
    #                 "type": "Negative",
    #                 "content": "the article also presents concerns about..."
    #             }
    #         ]
    #     },
    #     {
    #         "timestamp": "1 hours ago",
    #         "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
    #         "description": "The world of cryptocurrencies is in turmoil...",
    #         "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
    #         "sentiments": [
    #             {
    #                 "type": "Negative",
    #                 "content": "the article also presents concerns about..."
    #             }
    #         ]
    #     },
    #     {
    #         "timestamp": "1 hours ago",
    #         "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
    #         "description": "The world of cryptocurrencies is in turmoil...",
    #         "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
    #         "sentiments": [
    #             {
    #                 "type": "Positive",
    #                 "content": "the article presents a reasonable and wellsubstantiated case..."
    #             }
    #         ]
    #     },
    #     {
    #         "timestamp": "1 hours ago",
    #         "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
    #         "description": "The world of cryptocurrencies is in turmoil...",
    #         "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
    #         "sentiments": [
    #             {
    #                 "type": "Positive",
    #                 "content": "the article presents a reasonable and wellsubstantiated case..."
    #             },
    #             {
    #                 "type": "Negative",
    #                 "content": "the article also presents concerns about..."
    #             }
    #         ]
    #     },
    # ]