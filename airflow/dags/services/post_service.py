import json
import traceback
from constants.config import TWITTER_AUTH_TOKEN
from constants.twitter import TWITTER_MAX_POSTS_PAGE
from utils.twitter import extract_info, fetch_twitter_api, fetch_twitter_api_v2
from fake_useragent import UserAgent


def get_user_post(cookie_manager, user_id, user_refer, proxies, max_posts_page=1):
    # data_posts_pin_raw = []
    data_posts_add_raw = []
    token_cursor_next = None
    current_post_page = 0
    url = "https://x.com/i/api/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets"
    headers = {
        "authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
        "referer": f"https://x.com/{user_refer}",
        "user-agent": UserAgent().random,
        "x-client-transaction-id": "ewkKaVpcI0/GbAk9H6ZWVPsiNuQ1RWQht0XVOML+3XGuqFs4JC+rDcIuGxev2gHV+YbVIXm/HO5HFSGfu+rTWvm+7Nr7eA",
        "x-client-uuid": "46f93b4e-5ebb-497d-9506-d2a8691c53e0",
        # "x-csrf-token": cookie["cookie"]["ct0"],
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
    }

    while current_post_page < max_posts_page:
        variables = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }

        if token_cursor_next:
            variables = {**variables, "cursor": token_cursor_next}

        params = {
            "variables": json.dumps(variables),
            "features": '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
            "fieldToggles": '{"withArticlePlainText":false}',
        }

        response_get_post = fetch_twitter_api(
            url=url,
            params=params,
            headers=headers,
            cookie_manager=cookie_manager,
            proxies=proxies,
        )

        if not response_get_post:
            return None

        posts_raw = []

        try:
            posts_raw = response_get_post["data"]["user"]["result"]["timeline_v2"][
                "timeline"
            ]["instructions"]
        except Exception as e:
            print(f"Error when status code of post is 200: {e}, {response_get_post}")
            pass

        for post_raw in posts_raw:
            # if post_raw["type"] == "TimelinePinEntry":
            #     data_posts_pin_raw.append(post_raw["entry"])
            if post_raw["type"] == "TimelineAddEntries":
                for post in post_raw["entries"]:
                    if (
                        "tweet-" in post["entryId"]
                        or "profile-conversation" in post["entryId"]
                    ):
                        data_posts_add_raw.append(post)

                    if "cursor-bottom" in post["entryId"]:
                        token_cursor_next = post["content"]["value"]

        current_post_page += 1

    return {
        # "code": response.status_code,
        # "data_posts_pin_raw": data_posts_pin_raw,
        "data_posts_add_raw": data_posts_add_raw,
        # "token_cursor_next": token_cursor_next,
    }


def get_search_timeline_post(cookie_manager, proxies, search_query):
    # data_posts_pin_raw = []
    data_posts_add_raw = []
    token_cursor_next = None
    current_post_page = 0
    url = "https://x.com/i/api/graphql/UN1i3zUiCWa-6r-Uaho4fw/SearchTimeline"
    headers = {
        "authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
        "referer": f'https://x.com/search?q="{search_query}"&src=typed_query',
        "user-agent": UserAgent().random,
        "x-client-transaction-id": "hRiE0er7yUaGlAEessaeJHplsgCv69/u5zRHneDF0gwMSArQuXQMoKZZ9fzh+NoIj4dNGIflp/q0fqfqayGtvxwzRhvrhg",
        "x-client-uuid": "9875f10d-f296-4db2-9f67-164b0b63effb",
        # "x-csrf-token": cookie_value["ct0"],
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
    }

    while current_post_page < TWITTER_MAX_POSTS_PAGE:
        variables = {
            "rawQuery": search_query,
            "count": 20,
            "querySource": "recent_search_click",
            "product": "Latest",
        }

        if token_cursor_next:
            variables = {**variables, "cursor": token_cursor_next}

        params = {
            "variables": json.dumps(variables),
            "features": '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
        }

        response_get_post_timeline = fetch_twitter_api(
            url=url,
            params=params,
            headers=headers,
            cookie_manager=cookie_manager,
            proxies=proxies,
        )

        if not response_get_post_timeline:
            return None

        posts_raw = []

        try:
            posts_raw = response_get_post_timeline["data"]["search_by_raw_query"][
                "search_timeline"
            ]["timeline"]["instructions"]
        except Exception as e:
            print(
                f"Error when status code of post is 200: {e}, {response_get_post_timeline}"
            )
            pass

        for post_raw in posts_raw:
            # if post_raw["type"] == "TimelinePinEntry":
            #     data_posts_pin_raw.append(post_raw["entry"])
            if post_raw["type"] == "TimelineAddEntries":
                for post in post_raw["entries"]:
                    if (
                        "tweet-" in post["entryId"]
                        or "profile-conversation" in post["entryId"]
                    ):
                        data_posts_add_raw.append(post)

                    if "cursor-bottom" in post["entryId"]:
                        token_cursor_next = post["content"]["value"]

        current_post_page += 1

    return {
        # "code": response.status_code,
        # "data_posts_pin_raw": data_posts_pin_raw,
        "data_posts_add_raw": data_posts_add_raw,
        # "token_cursor_next": token_cursor_next,
    }


def extract_posts_info(
    raw_posts,
    max_process_latest_posts,
    data_topic,
    filter_content=None,
):
    extracted_posts = []

    for item in raw_posts[0:max_process_latest_posts]:
        entries = []
        entry_type = item["content"]["entryType"]
        if entry_type == "TimelineTimelineItem":
            entry_item = item["content"]["itemContent"]["tweet_results"]["result"]
            entries.append(entry_item)

        if entry_type == "TimelineTimelineModule":
            for entry_module in item["content"]["items"]:
                entries.append(
                    entry_module["item"]["itemContent"]["tweet_results"]["result"]
                )

        if len(entries) == 0:
            # print(f"---[NOT FOUND ENTRY POSTS]---")
            continue

        for entry in entries:
            try:
                legacy = entry.get("legacy", None)

                if legacy is None:
                    # print("---[NOT FOUND LEGACY POSTS]---")
                    continue

                try:
                    retweet = legacy.get("retweeted_status_result", None)
                except Exception as e:
                    pass

                try:
                    quote = entry.get("quoted_status_result", None)
                except Exception as e:
                    pass

                if quote:
                    # print(f"QUOTE {quote['result']['rest_id']}")
                    quote_tweet_content = extract_info(
                        quote["result"],
                        data_topic,
                        filter_content,
                    )

                    if quote_tweet_content is not None:
                        extracted_posts.append(quote_tweet_content)

                    main_tweet_content = extract_info(
                        entry,
                        data_topic,
                        filter_content,
                    )

                    if main_tweet_content is not None:
                        extracted_posts.append(main_tweet_content)

                elif retweet:
                    # print(f"RETWEET {retweet['result']['rest_id']}")
                    retweet_tweet_content = extract_info(
                        retweet["result"],
                        data_topic,
                        filter_content,
                    )

                    if retweet_tweet_content is not None:
                        extracted_posts.append(retweet_tweet_content)

                else:
                    # print(f"NORMAL {entry['rest_id']}")
                    tweet_content = extract_info(
                        entry,
                        data_topic,
                        filter_content,
                    )

                    if tweet_content is not None:
                        extracted_posts.append(tweet_content)
            except Exception as e:
                print(f"ERROR EXTRACT CONTENT POST - MESS: {str(e)}")
                continue

    return [item for item in extracted_posts if item is not None]


def get_post(cookie_manager, user_id, user_refer, proxies, max_posts_page=1):
    data_posts_add_raw = []
    token_cursor_next = None
    current_post_page = 0
    url = "https://x.com/i/api/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets"
    headers = {
        "authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
        "referer": f"https://x.com/{user_refer}",
        "user-agent": UserAgent().random,
        "x-client-transaction-id": "ewkKaVpcI0/GbAk9H6ZWVPsiNuQ1RWQht0XVOML+3XGuqFs4JC+rDcIuGxev2gHV+YbVIXm/HO5HFSGfu+rTWvm+7Nr7eA",
        "x-client-uuid": "46f93b4e-5ebb-497d-9506-d2a8691c53e0",
        # "x-csrf-token": cookie["cookie"]["ct0"],
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
    }

    while current_post_page < max_posts_page:
        variables = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }

        if token_cursor_next:
            variables = {**variables, "cursor": token_cursor_next}

        params = {
            "variables": json.dumps(variables),
            "features": '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
            "fieldToggles": '{"withArticlePlainText":false}',
        }

        response_get_post = fetch_twitter_api_v2(
            url=url,
            params=params,
            headers=headers,
            cookie_manager=cookie_manager,
            proxies=proxies,
        )

        if not response_get_post:
            return None

        posts_raw = []

        try:
            posts_raw = response_get_post["data"]["user"]["result"]["timeline_v2"][
                "timeline"
            ]["instructions"]
        except Exception as e:
            print(f"Error when status code of post is 200: {e}, {response_get_post}")
            pass

        for post_raw in posts_raw:
            # if post_raw["type"] == "TimelinePinEntry":
            #     data_posts_pin_raw.append(post_raw["entry"])
            if post_raw["type"] == "TimelineAddEntries":
                for post in post_raw["entries"]:
                    if (
                        "tweet-" in post["entryId"]
                        or "profile-conversation" in post["entryId"]
                    ):
                        data_posts_add_raw.append(post)

                    if "cursor-bottom" in post["entryId"]:
                        token_cursor_next = post["content"]["value"]

        current_post_page += 1

    return {
        # "code": response.status_code,
        # "data_posts_pin_raw": data_posts_pin_raw,
        "data_posts_add_raw": data_posts_add_raw,
        # "token_cursor_next": token_cursor_next,
    }
