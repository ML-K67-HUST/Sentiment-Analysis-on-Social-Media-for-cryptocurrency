from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from constants.crypto import TOP_50_CRYPTO_COINMARKETCAP
from constants.config import MONGO_MODESTUS_DB_NAME
from database.kafka import Kafka
from database.mongodb import MongoManager
from utils.common import execute_multithreading_functions, get_chunks
from crawler.coinmarketcap import CMC_NEWS_KAFKA_TOPIC, article_content_of_cmc_, article_content_of_other_, articles_link_of_, crawl_article_by_coin_id

DAG_NAME = "cmc_news_24h"
TASK_CRAWL_CMC_NEWS = "collect_latest_10_pages_cmc_article_data"


def crawl_articles(coin_id, symbol, page_num, kafka, max_page):
# def crawl_articles(coin_id, symbol, page_num, max_page):
    mongo_client = MongoManager(MONGO_MODESTUS_DB_NAME)

    while page_num <= max_page:
        try:
            contents = crawl_article_by_coin_id(coin_id, symbol, page_num)

            if len(contents):
                inserted_ids, error_ids, hash_ids = mongo_client.insert_many(
                    "cmc_news", contents
                )
                # print("🚀 ~ error_ids:", error_ids)
                print("COMPLETE INSERT MANY: ", hash_ids)

                chunk_hash_ids = get_chunks(hash_ids, 10)

                for hash_ids in chunk_hash_ids:
                    message = {"hash_ids": hash_ids}
                    kafka.producer_send(CMC_NEWS_KAFKA_TOPIC, message)
                    print("COMPLETED PUSH : ", hash_ids)

            return
        except Exception as e:
            print("Error while crawl news: ", e)
        finally:
            page_num += 1


def crawl_cmc_news(list_crypto):
    crawl_article_by_coin_id_functions = []
    print('KAFKA TOPIC: ',CMC_NEWS_KAFKA_TOPIC)
    kafka = Kafka()

    for token in list_crypto:
        crawl_article_by_coin_id_functions.append(
            {
                "fn": crawl_articles,
                "args": {
                    "coin_id": token["id"],
                    "symbol": token["symbol"],
                    "page_num": 1,
                    "kafka": kafka,
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
    description="Crawl new articles from CoinMarketCap in the last 24 hours",
    schedule_interval="0 */1 * * *",
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
