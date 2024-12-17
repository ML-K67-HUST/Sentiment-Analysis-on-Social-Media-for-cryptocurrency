import os
import concurrent.futures
import requests
import time
import json
import re
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup

# from database.mongodb import MongoManager

# from constants.config import MONGO_MODESTUS_DB_NAME
# from constants.crypto import TOP_50_CRYPTO_COINMARKETCAP

from common.processor import fetch_use_proxy
# from database.mongodb import MongoManager
# from database.kafka import Kafka
# from utils.common import execute_multithreading_functions, get_chunks

CMC_NEWS_KAFKA_TOPIC = "coinmarketcap-news"

url = "https://api.coinmarketcap.com/aggr/v4/content/user"

headers = {
    "accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


def filter_relevant_content(text):
    irrelevant_phrases = [
        "Advertisement Banner",
        "I have read and agree to the terms & conditions",
        "Your email address will not be published",
        "Save my name, email, and website in this browser for the next time I comment",
        "Stay updated with The Bit Journal",
        "Sign in to your account",
        "All Rights Reserved",
        "Be the first",
        "Disclaimer",
        "©",
    ]

    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", text)
    filtered_sentences = [
        sentence
        for sentence in sentences
        if all(phrase.lower() not in sentence.lower() for phrase in irrelevant_phrases)
    ]
    filtered_text = " ".join(filtered_sentences)
    filtered_text = re.sub(r"\n+", "\n", filtered_text).strip()

    return filtered_text


def get_hash_id(url):
    if not isinstance(url, str):
        raise ValueError("The URL must be a string.")
    hash_object = hashlib.sha256()
    hash_object.update(url.encode("utf-8"))
    hash_id = hash_object.hexdigest()

    return hash_id


def articles_link_of_(page, coin_id) -> list:
    links = []
    payload = json.dumps(
        {
            "mode": "LATEST",
            "page": page,
            "size": 10,
            "language": "en",
            "coins": [coin_id],
            "newsTypes": ["NEWS", "ALEXANDRIA"],
        }
    )
    content = fetch_use_proxy("POST", url, headers=headers, data=payload).json()
    for article in content.get("data"):
        # if 'https://coinmarketcap.com/' in article['meta']['sourceUrl']:
        links.append(
            (
                article["meta"]["sourceUrl"],
                article["meta"]["title"],
                article["meta"]["releasedAt"],
            )
        )
    return links


def remove_html_tags(text) -> str:
    text = re.sub(r"(</?(?!a\b)[^>]+>)", r"\1\n", text)
    text = re.sub("<.*?>", "", text)
    text = re.sub(r"^\s*\n", "", text, flags=re.MULTILINE)
    return text.strip()


def article_content_of_cmc_(url, title, date, symbol, category):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = soup.find("script", id="__NEXT_DATA__").text
        # print('-'*8)
        # print(articles)
        overal_info = json.loads(articles)["props"]["pageProps"]["article"]
        # overal_info = eval(articles)['props']['pageProps']['article']
        # print('-'*8)

        content = remove_html_tags(overal_info["content"])
        hash_id = overal_info["id"]

        # print(content)
        data = {
            "title": title,
            "url": url,
            "symbol": symbol,
            "content": content,
            "timestamp": datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp(),
            "hash_id": hash_id,
            "category": category
        }
        # print(f"Finished article {url}")

        return data
    except Exception as e:
        # print(f"exception {e} happened")
        return None


def article_content_of_other_(url, title, date, symbol, category):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        content = ""
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            content += p.text + "\n"
        hash_id = get_hash_id(url)

        content = filter_relevant_content(content)
        data = {
            "title": title,
            "url": url,
            "content": content,
            "symbol": symbol,
            "timestamp": datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp(),
            "hash_id": hash_id,
            "category": category
        }
        # print(f"Finished article {url}")

        return data
    except Exception as e:
        # print(f"exception {e} happened")
        return None


def crawl_article_by_coin_id(coin_id, symbol, page_num, category=None):
    links = articles_link_of_(page_num, coin_id)
    if len(links) == 0:
        return

    contents = []
    for link in links:
        # content = article_content_of_cmc_(link) if link.startswith('https://coinmarketcap.com/') else article_content_of_other_(link)
        # if content and content['content']:
        #     result.append(content)
        #     hash_ids.append(content['hash_id'])
        # else:
        #     continue
        url, title, date = link[0], link[1], link[2]
        if not url.startswith("https://coinmarketcap.com/") and int(date[:4]):
            content = article_content_of_other_(url, title, date, symbol, category)
            if content and content["content"]:
                contents.append(content)
            else:
                continue
        elif url.startswith("https://coinmarketcap.com/") and int(date[:4]):
            content = article_content_of_cmc_(url, title, date, symbol, category)
            if content and content["content"]:
                contents.append(content)
            else:
                continue

    print(f"DONE PAGE {page_num} FOR TOKEN: {symbol}")
    return contents

print(crawl_article_by_coin_id(1,'BTC',1))