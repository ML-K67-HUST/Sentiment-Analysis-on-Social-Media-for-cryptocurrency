import requests
import json
from database.mongodb import MongoManager
from datetime import datetime, timedelta

def get_info(user_id):

    url = f"https://api.x.com/graphql/LWxkCeL8Hlx0-f24DmPAJw/UserByRestId?variables=%7B%22userId%22%3A%22{user_id}%22%7D&features=%7B%22hidden_profile_subscriptions_enabled%22%3Atrue%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Afalse%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22highlights_tweets_tab_ui_enabled%22%3Atrue%2C%22responsive_web_twitter_article_notes_tab_enabled%22%3Atrue%2C%22subscriptions_feature_can_gift_premium%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D"

    payload = {}
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'content-type': 'application/json',
        'cookie': 'guest_id=173492627222648888; night_mode=2; guest_id_marketing=v1%3A173492627222648888; guest_id_ads=v1%3A173492627222648888; gt=1871087886294306841; personalization_id="v1_W8t8S83rlbc0/7ztw0zJeQ=="; guest_id=v1%3A173493964735252031; guest_id_ads=v1%3A173493964735252031; guest_id_marketing=v1%3A173493964735252031; personalization_id="v1_HMuPMTmrsAz34gL7P8Fvsg=="; twid=u%3D1695107922400030720',
        'origin': 'https://x.com',
        'priority': 'u=1, i',
        'referer': 'https://x.com/',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-client-transaction-id': '8LrgmxDDTOOld9M0nj5BOr4i9kd0vNzjg5nWLnsNuN+eajP8YkLySWn+3K8lR+y4RXdJ6fPJZtW9Vj3fpMjsfw8ZFHEK8w',
        'x-guest-token': '1871087886294306841',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en'
        }

    response = requests.request("GET", url, headers=headers, data=payload)

    return json.loads(response.text)

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
    

def get_tweet_news():
    
    mongo_client = MongoManager('blog-data')
    twitter_data = mongo_client.find(
        collection_name='twitter_sentiment_data',
        sort=("timestamp",-1),
        limit=100
    )
    # cmc_data.sort(key=lambda x:x["timestamp"],reverse=True)
    # cmc_data

    # for data in cmc_data:
    #     print(time_ago(int(data['timestamp'])))
    result = []
    seen = set()
    for data in twitter_data:
        # print(data)
        if data['link'] in seen:
            continue
        else:
            seen.add(data['link'])
        try:
            sentiments = []
            if data['sentiments'] and 'metrics' in data['sentiments']:
                for descript in data['sentiments']["metrics"]:
                    if descript["classification"] == 1:
                        if 'positive' in descript["policy"].lower():
                            sentiments.append(
                                {
                                    "type":"Positive",
                                    "content":descript["reasoning"]
                                }
                            )
                        elif 'negative' in descript["policy"].lower():
                            sentiments.append(
                                {
                                    "type":"Positive",
                                    "content":descript["reasoning"]
                                }
                            )
                        elif 'reporting' in descript["policy"].lower():
                            sentiments.append(
                                {
                                    "type":"reporting",
                                    "content":descript["reasoning"]
                                }
                            )
                        elif 'manipulation' in descript["policy"].lower():
                            sentiments.append(
                                {
                                    "type":"manipulate",
                                    "content":descript["reasoning"]
                                }
                            )
                if not sentiments:
                    continue
                result.append({
                    "timestamp":time_ago(data['timestamp']),
                    "title": data['title'],
                    "description": data['description'],
                    "link": data['link'],
                    "sentiments":sentiments
                })
        except Exception as e:
            print(f'ERROR WHILE HANDLING DATA FOR BACKENDS TWITTER API: {e} ')
            print(data)
        # print({
        #     "timestamp":time_ago(int(data["timestamp"])),
        #     "title": data['source_data'][0]['title'],
        #     "description": data['source_data'][0]["content"],
        #     "link": data['source_data'][0]["url"],
        #     "sentiments":sentiments
        # })
    return result

#     return [
#     {
#         timestamp: "2 hours ago",
#         title: "X Platform News Example",
#         description: "@userid",
#         link: 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
#         sentiments: [
#             {
#                 type: "Positive",
#                 content: "Positive sentiment from X..."
#             }
#         ]
#     },
# ]