import requests
import time
from constants.config import PROXY_AUTH_PASSWORD, PROXY_AUTH_USERNAME
from constants.proxies import PROXIES_TWITTER_CRYPTO


def fetch_thread(method, url, response, params=None, headers=None, data=None):
    res = requests.request(method, url, headers=headers, params=params, data=data)
    response.extend(res.json())


def fetch(
    method,
    url,
    headers,
    params=None,
    data=None,
    timeout=None,
    cookies=None,
    proxies=None,
):
    return requests.request(
        method,
        url,
        headers=headers,
        params=params,
        data=data,
        timeout=timeout,
        cookies=cookies,
        proxies=proxies,
    )


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
    while count_retry < len(proxy_list) * round:
        try:
            proxy = proxy_list[current_proxy_index]
            proxies = {
                "http": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxy}",
                "https": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxy}",
            }
            print(proxies)
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                proxies=proxies,
                timeout=10,
            )

            if response.status_code == 200:
                return response

            count_retry += 1
            time.sleep(5)
        except Exception as e:
            count_retry += 1
            print("Proxy error: ", str(e))
            time.sleep(5)
        finally:
            current_proxy_index = (current_proxy_index + 1) % len(proxy_list)

    return response
