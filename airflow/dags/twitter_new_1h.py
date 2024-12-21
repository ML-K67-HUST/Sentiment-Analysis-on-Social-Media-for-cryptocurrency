import pytz
import os
from airflow import DAG
from pymongo import UpdateOne
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

from common.cookies import CookieManager
from database.mongodb import MongoManager
from database.kafka import Kafka
from utils.common import get_chunks, execute_multithreading_functions
from utils.twitter import save_tweet
from common.twitter import process_crawl_user_flow
from utils.discord import push_notification
from constants.config import (
    MONGO_MODESTUS_DB_NAME,
    TWITTER_COOKIES_CRYPTO_COLLECTION_NAME,
    DISCORD_URL_ERROR,
    DISCORD_SERVER_NAME,
)
from constants.politics import DATA_TOPIC, IDS_KOL_CRYPTO
from constants.proxies import PROXIES_TWITTER_CRYPTO


DAG_NAME = os.path.basename(__file__)
COLLECTION_POST = "twitter_posts"
# COLLECTION_POST_TEST = "twitter_posts_test"
COLLECTION_COMMENT = "twitter_comments"
# COLLECTION_COMMENT_TEST = "twitter_comments_test"

KAFKA_TOPIC = "social-comment-twitter-crypto"
NUMBER_CHUNK_KOL = 20


def process_twitter_crypto():
    try:
        mongo_client = MongoManager(MONGO_MODESTUS_DB_NAME)
        kafka = Kafka()
        response_cookies = mongo_client.find(
            collection_name=TWITTER_COOKIES_CRYPTO_COLLECTION_NAME,
            projection={
                "_id": 0,
                "id": 1,
                "cookie": 1,
                "rate_limit": 1,
                "time_reset": 1,
            },
        )
        cookies = [{**item, "is_used": False, "count": 0} for item in response_cookies]
        cookie_manager = CookieManager(cookies=cookies)

        arr_kol_chunks = get_chunks(IDS_KOL_CRYPTO, NUMBER_CHUNK_KOL)

        for arr_id_kol in arr_kol_chunks:
            responses_post = []
            responses_comments = []
            THREADS = len(arr_id_kol)

            functions_process = [
                {
                    "fn": process_crawl_user_flow,
                    "args": {
                        "cookie_manager": cookie_manager,
                        # "cookie": cookies_active[index],
                        "user": arr_id_kol[index],
                        "proxies": PROXIES_TWITTER_CRYPTO,
                        "data_topic": DATA_TOPIC["CRYPTO"],
                        # Number of LATEST posts collect each run
                        "max_process_latest_posts": 2,
                        # Number of pages comment (about 20 comments) collect each post
                        "max_comments_page": 2,
                    },
                }
                for index in range(0, THREADS)
            ]

            results = execute_multithreading_functions(functions=functions_process)
            for item in results:
                if item is not None:
                    responses_post.extend(item["arr_posts"])
                    responses_comments.extend(item["arr_comments"])

            functions_save = []

            if len(responses_comments) > 0:
                functions_save.append(
                    {
                        "fn": save_tweet,
                        "args": {
                            "data": responses_comments,
                            "mongo_client": mongo_client,
                            "collection_name": COLLECTION_COMMENT,
                        },
                    }
                )

            if len(responses_post) > 0:
                functions_save.append(
                    {
                        "fn": save_tweet,
                        "args": {
                            "data": responses_post,
                            "mongo_client": mongo_client,
                            "collection_name": COLLECTION_POST,
                        },
                    }
                )

            if len(functions_save) > 0:
                results_save = execute_multithreading_functions(
                    functions=functions_save
                )
                hash_ids = []
                number_duplicate = []

                for item in results_save:
                    hash_ids.extend(item["hash_ids"])
                    number_duplicate.extend(item["error_ids"])

                print(f"SAVE TO DATABASE DONE {len(hash_ids)} DOCUMENTS!!!")
                if len(hash_ids) > 0:
                    print("___________________________")
                    print("NEW COMMENTS PUSH TO KAFKA: ", len(hash_ids))
                    print("DUPLICATE COMMENTS: ", len(number_duplicate))
                    chunk_hash_ids = get_chunks(hash_ids, 10)
                    for ids in chunk_hash_ids:
                        message = {"hash_ids": ids}
                        kafka.producer_send(KAFKA_TOPIC, message)
                        print("COMPLETED PUSH : ", ids)

        # UPDATE COOKIES
        cookie_remaining = cookie_manager.remaining_cookies()
        print(f"COOKIES REMAINING: {cookie_remaining}")
        data_update_remaining_cookies = [
            UpdateOne(
                {"id": item["id"]},
                {"$set": item},
                upsert=True,
            )
            for item in cookie_remaining
        ]

        mongo_client.upsert_many(
            collection_name=TWITTER_COOKIES_CRYPTO_COLLECTION_NAME,
            data=data_update_remaining_cookies,
        )
        print("UPDATE COOKIES DONE.")
    except Exception as e:
        push_notification(
            DISCORD_URL_ERROR,
            DISCORD_SERVER_NAME,
            "CRAWLER TWITTER DATA MODESTUS",
            datetime.now(pytz.utc),
            str(e),
            DAG_NAME,
            False,
        )
        raise Exception(e)


default_args = {
    "owner": "haw.nv",
    "start_date": datetime(2024, 2, 18),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "max_active_runs": 1,
}


dag = DAG(
    "modestus_twitter_crypto_interval_20m",
    default_args=default_args,
    description="Fetch new tweets for topic crypto interval 20m",
    schedule_interval="0 */2 * * *",
    catchup=False,
    tags=["sentiman", "twitter"],
    max_active_runs=1,
)

task_process_twitter_crypto = PythonOperator(
    task_id="task_process_twitter_crypto",
    python_callable=process_twitter_crypto,
    provide_context=True,
    dag=dag,
)

task_process_twitter_crypto
