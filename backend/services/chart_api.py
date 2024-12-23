import requests
import json 

def get_chart_data():
    url = "https://data.modestus.ai/crypto/index?offset=0&size=100&socialCommentWeight=2&cmcNewsWeight=5&tradingViewIdeasWeight=3"

    payload = {}
    headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'if-none-match': 'W/"2690-rg/2+h1RRghgmF62mgkcRetbpIE"',
    'origin': 'https://modestus.ai',
    'priority': 'u=1, i',
    'referer': 'https://modestus.ai/',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return json.loads(response.text)
