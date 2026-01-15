import requests
import time
import random
from constants.config import PROXY_AUTH_PASSWORD, PROXY_AUTH_USERNAME
from constants.proxies import PROXIES_TWITTER_CRYPTO

# List of modern User-Agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }

def fetch_thread(method, url, response, params=None, headers=None, data=None):
    if headers is None:
        headers = get_random_headers()
    res = requests.request(method, url, headers=headers, params=params, data=data)
    response.extend(res.json())


def fetch(
    method,
    url,
    headers=None,
    params=None,
    data=None,
    timeout=15,
    cookies=None,
    proxies=None,
):
    # Auto-inject headers if not provided or to augment existing ones
    if headers is None:
        headers = get_random_headers()
    elif 'User-Agent' not in headers:
        headers['User-Agent'] = random.choice(USER_AGENTS)

    # Simple retry logic for 429/503
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout,
                cookies=cookies,
                proxies=proxies,
            )
            
            if response.status_code in [429, 503]:
                wait_time = (attempt + 1) * 2 + random.uniform(0, 1)
                print(f"⚠️  Rate limited ({response.status_code}). Waiting {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue
                
            return response
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)
    
    return response


def fetch_use_proxy(
    method,
    url,
    headers,
    params=None,
    data=None,
    round=1,
    proxy_list=PROXIES_TWITTER_CRYPTO,
):
    count_retry = 0
    current_proxy_index = 0
    response = None
    
    # Ensure User-Agent is randomized
    if 'User-Agent' not in headers:
        headers['User-Agent'] = random.choice(USER_AGENTS)

    while count_retry < len(proxy_list) * round:
        try:
            proxy = proxy_list[current_proxy_index]
            proxies = {
                "http": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxy}",
                "https": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxy}",
            }
            # print(f"Using proxy: {proxy}")
            
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                proxies=proxies,
                timeout=15,
            )

            if response.status_code == 200:
                return response
            
            if response.status_code == 429:
                print("⚠️ Proxy rate limited. Switching...")

            count_retry += 1
            time.sleep(2) # Short sleep before next proxy
            
        except Exception as e:
            count_retry += 1
            print(f"❌ Proxy error ({proxy}): {str(e)[:50]}...")
            time.sleep(2)
        finally:
            current_proxy_index = (current_proxy_index + 1) % len(proxy_list)

    return response
