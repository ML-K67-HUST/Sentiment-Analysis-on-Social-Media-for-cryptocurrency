from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from constants.crypto import TOP_50_CRYPTO_COINMARKETCAP
from constants.config import MONGO_MODESTUS_DB_NAME
from database.mongodb import MongoManager
from utils.common import execute_multithreading_functions
from crawler.coinmarketcap import CMC_NEWS_KAFKA_TOPIC, crawl_article_by_coin_id
from kafka_producer import send_article_ids  # Import from DAGs folder

DAG_NAME = "cmc_news_10m"
TASK_CRAWL_CMC_NEWS = "collect_latest_10_pages_cmc_article_data"


def crawl_articles(coin_id, symbol, page_num, max_page):
    mongo_client = MongoManager(MONGO_MODESTUS_DB_NAME)

    while page_num <= max_page:
        try:
            contents = crawl_article_by_coin_id(coin_id, symbol, page_num)

            if contents and len(contents):
                inserted_ids, error_ids, hash_ids = mongo_client.insert_many(
                    "cmc_news", contents
                )
                print("COMPLETE INSERT MANY: ", hash_ids)

                # Send to Kafka with simple producer
                if hash_ids:
                    if symbol == 'BTC':
                        send_article_ids(CMC_NEWS_KAFKA_TOPIC, hash_ids)
                        print(f"Sent {len(hash_ids)} BTC articles to Kafka")
                    else:
                        print(f"Skipped Kafka for symbol {symbol} (Only BTC allowed)")

            return
        except Exception as e:
            print("Error while crawl news: ", e)
        finally:
            page_num += 1


def crawl_cmc_news(list_crypto):
    crawl_article_by_coin_id_functions = []
    print('KAFKA TOPIC: ', CMC_NEWS_KAFKA_TOPIC)

    for token in list_crypto:
        crawl_article_by_coin_id_functions.append(
            {
                "fn": crawl_articles,
                "args": {
                    "coin_id": token["id"],
                    "symbol": token["symbol"],
                    "page_num": 1,
                    "max_page": 1,
                },
            }
        )

    execute_multithreading_functions(
        functions=crawl_article_by_coin_id_functions, timeout=60
    )

    return


def fetch_article(**kwargs):
    crawl_cmc_news(TOP_50_CRYPTO_COINMARKETCAP)


default_args = {
    "owner": "khangpt",
    "start_date": datetime(2024, 1, 18),
    "depends_on_past": False,
}


dag = DAG(
    DAG_NAME,
    default_args=default_args,
    description="Crawl new articles from CoinMarketCap in the last 10 minutes",
    schedule_interval="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["coinmarketcap", "article"],
)

fetch_newest_article = PythonOperator(
    task_id=TASK_CRAWL_CMC_NEWS,
    python_callable=fetch_article,
    dag=dag,
)

fetch_newest_article
