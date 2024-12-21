import time
from datetime import datetime, timedelta, timezone
from requests.exceptions import Timeout
import asyncio

from constants.twitter import (
    TWITTER_MAX_COOKIE_RETRIES,
    TWITTER_MAX_PROXY_RETRIES,
    TWITTER_STATUS_CODE,
)
from constants.config import (
    PROXY_AUTH_PASSWORD,
    PROXY_AUTH_USERNAME,
    TWITTER_AUTH_TOKEN,
)

from common.processor import fetch
from utils.common import random, check_list_include_string


# Using proxies pool and cookies pool (Twitter accounts) to try to fetch data from Twitter without getting rate limited or banned
def fetch_twitter_api(url, params, headers, cookie_manager, proxies):
    old_cookie_id = None
    proxy_retry = 0
    cookie_retry = 0

    while cookie_retry < TWITTER_MAX_COOKIE_RETRIES:
        cookie = cookie_manager.get_active_cookie(old_cookie_id)

        if cookie["code"] == 1:
            print("NOT FOUND ACTIVE COOKIE TO PROCESS")
            time.sleep(3)
            cookie_retry += 1
            continue

        cookie_obj = cookie["cookie"]
        cookie_id = cookie_obj["id"]
        old_cookie_id = cookie_id
        headers = {**headers, "x-csrf-token": cookie_obj["cookie"]["ct0"]}

        while proxy_retry < TWITTER_MAX_PROXY_RETRIES:
            try:
                proxies_https = {
                    "http": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
                    "https": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
                }

                response = fetch(
                    method="GET",
                    url=url,
                    params=params,
                    cookies=cookie_obj["cookie"],
                    headers=headers,
                    proxies=proxies_https,
                    timeout=5,
                )

                print(response.status_code, "STT CODE")

                if response.status_code == TWITTER_STATUS_CODE["RATE_LIMITED"]:
                    print(f"---[TOO MANY RQ POSTS 429 FOR COOKIE: {cookie_id}]---")
                    remaining = int(response.headers["x-rate-limit-remaining"])
                    time_reset = int(response.headers["x-rate-limit-reset"])
                    cookie_manager.update_release_used_cookie(
                        cookie_id=cookie_id,
                        # status_cookie=True,
                        new_rate_limit=remaining,
                        time_reset=time_reset,
                    )

                    # Cookie got rate limited --> try with another cookie
                    break

                if response.status_code == TWITTER_STATUS_CODE["UNAUTHORIZED"]:
                    print(f"---[RQ UNAUTHORIZED 401 FOR COOKIE: {cookie_id}]---")
                    code_error = response.json()["errors"][0]["code"]
                    if code_error == 32:
                        cookie_manager.update_release_used_cookie(cookie_id=cookie_id)

                    # Cookie got unauthorized --> try with another cookie
                    break

                if response.status_code == TWITTER_STATUS_CODE["SUCCESS"]:
                    remaining = int(response.headers["x-rate-limit-remaining"])
                    time_reset = int(response.headers["x-rate-limit-reset"])

                    cookie_manager.update_release_used_cookie(
                        cookie_id=cookie_id,
                        new_rate_limit=remaining,
                        time_reset=time_reset,
                    )

                    print(
                        f"REMAINING IS {str(remaining)} AND TIMESTAMP IS {str(time_reset)} FOR COOKIE ID: {cookie_id}"
                    )

                    return response.json()

                print(f"ERROR UNKNOWN FETCH TWITTER API - CODE: {response.status_code}")

            except Timeout:
                print(f"TIMEOUT FETCHING API FOR POST...")

            except Exception as e:
                print(f"ERROR API GET POST: {str(e)}")

            finally:
                proxy_retry += 1

        cookie_manager.update_release_used_cookie(cookie_id=cookie_id)
        cookie_retry += 1

    return None


def fetch_twitter_api_v2(url, params, headers, cookie_manager, proxies):
    old_cookie_id = None
    proxy_retry = 0
    cookie_retry = 0

    while cookie_retry < TWITTER_MAX_COOKIE_RETRIES:
        cookie = cookie_manager.get_active_cookie(old_cookie_id)

        if not cookie:
            print("NOT FOUND ACTIVE COOKIE TO PROCESS")
            time.sleep(5)
            cookie_retry += 1
            continue

        cookie_id = cookie["user_name"]
        old_cookie_id = cookie_id
        headers = {**headers, "x-csrf-token": cookie["cookie"]["ct0"]}

        while proxy_retry < TWITTER_MAX_PROXY_RETRIES:
            try:
                proxies_https = {
                    "http": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
                    "https": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
                }

                response = fetch(
                    method="GET",
                    url=url,
                    params=params,
                    cookies=cookie["cookie"],
                    headers=headers,
                    proxies=proxies_https,
                    timeout=5,
                )

                print(response.status_code, "STT CODE")

                if response.status_code == TWITTER_STATUS_CODE["RATE_LIMITED"]:
                    print(f"---[TOO MANY RQ POSTS 429 FOR COOKIE: {cookie_id}]---")
                    remaining = int(response.headers["x-rate-limit-remaining"])
                    time_reset = int(response.headers["x-rate-limit-reset"])
                    asyncio.run(
                        cookie_manager.update_cookie(
                            user_name=cookie_id,
                            rate_limit=remaining,
                            time_reset=time_reset,
                            is_active=True,
                        )
                    )

                    # Cookie got rate limited --> try with another cookie
                    break

                if response.status_code == TWITTER_STATUS_CODE["UNAUTHORIZED"]:
                    print(f"---[RQ UNAUTHORIZED 401 FOR COOKIE: {cookie_id}]---")
                    code_error = response.json()["errors"][0]["code"]
                    if code_error == 32:
                        asyncio.run(
                            cookie_manager.update_cookie(
                                user_name=cookie_id, is_live=False
                            )
                        )

                    # Cookie got unauthorized --> try with another cookie
                    break

                if response.status_code == TWITTER_STATUS_CODE["SUCCESS"]:
                    try:
                        errors = response.json().get("errors", None)
                        if errors and len(errors) > 0:
                            if (
                                errors[0].get("code")
                                == TWITTER_STATUS_CODE["ACCOUNT_BANNED"]
                            ):
                                asyncio.run(
                                    cookie_manager.update_cookie(
                                        user_name=cookie_id, is_live=False
                                    )
                                )
                                break

                        remaining = int(response.headers["x-rate-limit-remaining"])
                        time_reset = int(response.headers["x-rate-limit-reset"])

                        asyncio.run(
                            cookie_manager.update_cookie(
                                user_name=cookie_id,
                                rate_limit=remaining,
                                time_reset=time_reset,
                                is_active=True,
                            )
                        )

                        print(
                            f"REMAINING IS {str(remaining)} AND TIMESTAMP IS {str(time_reset)} FOR COOKIE ID: {cookie_id}"
                        )

                        return response.json()
                    except Exception as e:
                        print("Error when status code is 200: ", e)

                print(f"ERROR UNKNOWN FETCH TWITTER API - CODE: {response.status_code}")

            except Timeout:
                print(f"TIMEOUT FETCHING API FOR POST...")

            except Exception as e:
                print(f"ERROR API GET POST: {str(e)}")

            finally:
                proxy_retry += 1

        asyncio.run(cookie_manager.update_cookie(user_name=cookie_id, is_active=True))
        cookie_retry += 1

    return None


def extract_info(content, data_topic, filter_content_arr=None):
    data = {}
    type_content = content.get("__typename", None)

    if type_content is None or type_content != "Tweet":
        print(f"NOT VALID TWEET =>  {type_content} <:")
        return None

    type_views = content["views"].get("state", None)
    if type_views is None or type_views == "Enabled":
        print("TWEET IS RETWEET <:")
        return None

    user_info_raw = content["core"]["user_results"].get("result", None)

    if user_info_raw is None or user_info_raw.get("__typename", None) != "User":
        print("NOT FOUND USER INFO")
        return None

    user_info = {}

    user_info["id"] = user_info_raw.get("id", None)
    user_info["rest_id"] = user_info_raw.get("rest_id", None)
    user_info["is_blue_verified"] = user_info_raw.get("is_blue_verified", False)
    user_info_legacy = user_info_raw.get("legacy", None)

    if user_info_legacy:
        user_info["created_at"] = user_info_legacy.get("created_at", None)
        user_info["favourites_count"] = user_info_legacy.get("favourites_count", None)
        user_info["followers_count"] = user_info_legacy.get("followers_count", None)
        user_info["friends_count"] = user_info_legacy.get("friends_count", None)
        user_info["listed_count"] = user_info_legacy.get("listed_count", None)
        user_info["location"] = user_info_legacy.get("location", None)
        user_info["name"] = user_info_legacy.get("name", None)
        user_info["screen_name"] = user_info_legacy.get("screen_name", None)
        user_info["statuses_count"] = user_info_legacy.get("statuses_count", None)
        user_info["profile_image_url_https"] = user_info_legacy.get(
            "profile_image_url_https", None
        )

    data["user"] = user_info

    legacy = content["legacy"]
    data["hash_id"] = legacy.get("id_str", None)
    data["post_id"] = legacy.get("id_str", None)
    data["conversation_id"] = legacy.get("conversation_id_str", None)
    data["reply_id"] = legacy.get("in_reply_to_status_id_str", None)
    data["reply_user_id"] = legacy.get("in_reply_to_user_id_str", None)
    data["user_id"] = legacy.get("user_id_str", None)
    data["favorite"] = legacy.get("favorite_count", None)
    data["quote"] = legacy.get("quote_count", None)
    data["reply"] = legacy.get("reply_count", None)
    data["retweet"] = legacy.get("retweet_count", None)
    data["bookmark"] = legacy.get("bookmark_count", None)
    data["views"] = int(content["views"].get("count", None))
    data["data_topic"] = data_topic
    data["is_replied"] = False

    entities = legacy.get("entities", None)
    if entities:
        media = entities.get("media", None)

        if media and len(media) > 0:
            user_info["media"] = [item["media_url_https"] for item in media]
        else:
            user_info["media"] = None

    note_tweet = content.get("note_tweet", None)
    if note_tweet:

        data["content"] = note_tweet["note_tweet_results"]["result"].get("text", None)
    else:
        data["content"] = legacy.get("full_text", None)

    if filter_content_arr:
        filter_content_check = filter_content(
            raw_content=data["content"], required_string_list=filter_content_arr
        )
        if not filter_content_check:
            return None

    data["timestamp"] = int(
        datetime.strptime(
            legacy.get("created_at", None), "%a %b %d %H:%M:%S %z %Y"
        ).timestamp()
    )
    return data


def save_tweet(data, mongo_client, collection_name):
    # hash_ids = []

    inserted_ids, error_ids, hash_ids = mongo_client.insert_many(
        collection_name=collection_name, data=data
    )

    # if len(inserted_ids) > 0:
    #     hash_ids = [item["hash_id"] for item in data if item["_id"] in inserted_ids]

    return {"hash_ids": hash_ids, "error_ids": error_ids}


# def filter_crypto_spam_content(tweet_date, content, symbol):
#     keywords = ["give away", "giveaway", "airdrop"]
#     time_now = datetime.now(timezone.utc)

#     if tweet_date < (time_now - timedelta(days=3)):
#         return False

#     content_lower = content.lower()
#     if (
#         symbol["name"].lower() not in content_lower
#         and symbol["symbol"].lower() not in content_lower
#     ) or any(keyword in content_lower for keyword in keywords):
#         return False

#     return True


def filter_content(
    raw_content,
    required_string_list,
    tweet_date=None,
    latest_number_of_days_threshold=None,
):
    time_now = datetime.now(timezone.utc)

    if tweet_date and latest_number_of_days_threshold:
        if tweet_date < (time_now - timedelta(days=latest_number_of_days_threshold)):
            return False

    if not (check_list_include_string(raw_content, required_string_list)):
        return False

    return True


def fetch_twitter_mentions_api(cookie, url, params, headers, proxies):
    proxy_retry = 0

    while proxy_retry < TWITTER_MAX_PROXY_RETRIES:
        try:
            proxies_https = {
                "http": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
                "https": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
            }

            response = fetch(
                method="GET",
                url=url,
                params=params,
                cookies=cookie,
                headers=headers,
                proxies=proxies_https,
                timeout=10,
            )

            if response.status_code == TWITTER_STATUS_CODE["RATE_LIMITED"]:
                return None

            if response.status_code == TWITTER_STATUS_CODE["UNAUTHORIZED"]:
                return None

            if response.status_code == TWITTER_STATUS_CODE["SUCCESS"]:
                return response.json()

            print(f"ERROR UNKNOWN FETCH TWITTER API - CODE: {response.status_code}")

        except Timeout:
            print(f"TIMEOUT FETCHING API FOR POST...")

        except Exception as e:
            print(f"ERROR API GET POST: {str(e)}")

        finally:
            proxy_retry += 1

    return None


def create_reply_twitter(
    cookie, tweet_id, content, mongo_client, collection_name, proxies
):
    proxy_retry = 0
    while proxy_retry < 2:
        try:
            proxies_https = {
                "http": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
                "https": f"http://{PROXY_AUTH_USERNAME}:{PROXY_AUTH_PASSWORD}@{proxies[random(0, len(proxies) - 1, proxy_retry)]}",
            }

            url = "https://x.com/i/api/graphql/znq7jUAqRjmPj7IszLem5Q/CreateTweet"
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9,vi;q=0.8",
                "authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
                "content-type": "application/json",
                "origin": "https://x.com",
                "user-agent": UserAgent().chrome,
                "x-client-transaction-id": "P8CzrbsVaRDmR8WZLN+cXrkIruXfTsT2PIh7KbscWcQY281A0GtNSGF/H1kZyrY4zQNR5T1Cc+sDqTTK9dScXDmDLCf+PA",
                "x-client-uuid": "003223e9-a685-4e5b-a8ff-9f229fa644bc",
                "x-csrf-token": cookie["ct0"],
                "x-twitter-active-user": "yes",
                "x-twitter-auth-type": "OAuth2Session",
                "x-twitter-client-language": "en",
            }
            payload = {
                "variables": {
                    "tweet_text": content,
                    "reply": {
                        "in_reply_to_tweet_id": tweet_id,
                        "exclude_reply_user_ids": [],
                    },
                    "dark_request": False,
                    "media": {
                        "media_entities": [],
                        "possibly_sensitive": False,
                    },
                    "semantic_annotation_ids": [],
                    "disallowed_reply_options": None,
                },
                "features": {
                    "communities_web_enable_tweet_community_results_fetch": True,
                    "c9s_tweet_anatomy_moderator_badge_enabled": True,
                    "responsive_web_edit_tweet_api_enabled": True,
                    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                    "view_counts_everywhere_api_enabled": True,
                    "longform_notetweets_consumption_enabled": True,
                    "responsive_web_twitter_article_tweet_consumption_enabled": True,
                    "tweet_awards_web_tipping_enabled": False,
                    "creator_subscriptions_quote_tweet_preview_enabled": False,
                    "longform_notetweets_rich_text_read_enabled": True,
                    "longform_notetweets_inline_media_enabled": True,
                    "articles_preview_enabled": True,
                    "rweb_video_timestamps_enabled": True,
                    "rweb_tipjar_consumption_enabled": True,
                    "responsive_web_graphql_exclude_directive_enabled": True,
                    "verified_phone_label_enabled": False,
                    "freedom_of_speech_not_reach_fetch_enabled": True,
                    "standardized_nudges_misinfo": True,
                    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                    "responsive_web_graphql_timeline_navigation_enabled": True,
                    "responsive_web_enhance_cards_enabled": False,
                },
                "queryId": "znq7jUAqRjmPj7IszLem5Q",
            }

            response = fetch(
                method="POST",
                url=url,
                cookies=cookie,
                data=json.dumps(payload),
                headers=headers,
                proxies=proxies_https,
                timeout=10,
            )

            if response.status_code == TWITTER_STATUS_CODE["RATE_LIMITED"]:
                print(f"---[TOO MANY RQ POSTS 429")
                return
                # remaining = int(response.headers["x-rate-limit-remaining"])
                # time_reset = int(response.headers["x-rate-limit-reset"])

            if response.status_code == TWITTER_STATUS_CODE["UNAUTHORIZED"]:
                print(f"---[RQ UNAUTHORIZED 401---")
                return

            if response.status_code == TWITTER_STATUS_CODE["SUCCESS"]:
                print(f"REPLY DONE FOR TWEET {tweet_id}")
                print(f"RESULT: {response.json()}")
                mongo_client.update_one(
                    collection_name=collection_name,
                    filter={"hash_id": tweet_id},
                    data={"$set": {"is_reply": True}},
                )
                return
                # remaining = int(response.headers["x-rate-limit-remaining"])
                # time_reset = int(response.headers["x-rate-limit-reset"])

                # return response.json()

            print(f"ERROR CODE: {response.status_code}")
            print(f"RESPONSE: {response.text}")

        except Timeout:
            print(f"TIMEOUT FETCHING API FOR POST...")

        except Exception as e:
            print(f"ERROR API GET POST: {str(e)}")

        finally:
            proxy_retry += 1
