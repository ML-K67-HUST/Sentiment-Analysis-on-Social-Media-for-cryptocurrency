import json
from fake_useragent import UserAgent

from constants.config import TWITTER_AUTH_TOKEN
from utils.twitter import extract_info, fetch_twitter_api, fetch_twitter_api_v2


def get_comment(cookie_manager, post_id, proxies, max_comments_page):
    try:
        data_conversation_threads = []
        token_cursor_next = None
        current_comment_page = 0
        url = "https://x.com/i/api/graphql/QuBlQ6SxNAQCt6-kBiCXCQ/TweetDetail"
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,vi;q=0.8",
            "authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
            "content-type": "application/json",
            "user-agent": UserAgent().random,
            "x-client-transaction-id": "WR5jDJm0e/NKe+9ySLX3NIxBNTZ29IhEILe53m1jBkUdG5S3tVuRktr2q3nCYiFTYrzhAFtS/1IAK3BuFK8qMb3T6qboWg",
            "x-client-uuid": "46f93b4e-5ebb-497d-9506-d2a8691c53e0",
            # "x-csrf-token": cookie["cookie"]["ct0"],
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
        }

        while current_comment_page < max_comments_page:
            variables = {
                "focalTweetId": post_id,
                "with_rux_injections": False,
                "rankingMode": "Relevance",
                "includePromotedContent": True,
                "withCommunity": True,
                "withQuickPromoteEligibilityTweetFields": True,
                "withBirdwatchNotes": True,
                "withVoice": True,
            }

            if token_cursor_next:
                variables = {**variables, "cursor": token_cursor_next}

            params = {
                "variables": json.dumps(variables),
                "features": '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
                "fieldToggles": '{"withArticleRichContentState":true,"withArticlePlainText":false,"withGrokAnalyze":false,"withDisallowedReplyControls":false}',
            }

            response_get_comment = fetch_twitter_api(
                url=url,
                params=params,
                headers=headers,
                cookie_manager=cookie_manager,
                proxies=proxies,
            )

            post_raw_list = []

            try:
                post_raw_list = response_get_comment["data"][
                    "threaded_conversation_with_injections_v2"
                ]["instructions"]
            except Exception as e:
                print(
                    f"Error when status code of comment is 200: {e}, {response_get_comment}"
                )
                pass

            for item in post_raw_list:
                if item["type"] == "TimelineAddEntries":
                    for conversation in item["entries"]:
                        if "conversationthread" in conversation["entryId"]:
                            data_conversation_threads.append(conversation)
                        if "cursor-bottom" in conversation["entryId"]:
                            token_cursor_next = conversation["content"]["itemContent"][
                                "value"
                            ]

            if len(data_conversation_threads) == 0:
                raise Exception(f"Not found comments for post id: {post_id}")

            current_comment_page += 1
    except Exception as e:
        print(f"Error while fetching comments: {e}")

    finally:
        return {
            "data_conversation_threads": data_conversation_threads,
        }


def extract_comments_info(raw_comments, post_id, data_topic):
    extracted_comments = []

    for comment in raw_comments:
        try:
            entries = []
            entry_type = comment["content"]["entryType"]
            if entry_type == "TimelineTimelineItem":
                entry_item = comment["content"]["itemContent"]["tweet_results"][
                    "result"
                ]
                entries.append(entry_item)

            if entry_type == "TimelineTimelineModule":
                for entry_module in comment["content"]["items"]:
                    item_type = entry_module["item"]["itemContent"]["__typename"]
                    if item_type == "TimelineTweet":
                        entries.append(
                            entry_module["item"]["itemContent"]["tweet_results"][
                                "result"
                            ]
                        )
            if len(entries) == 0:
                # print(f"---[NOT FOUND ENTRY COMMENTS]---")
                continue

            for entry in entries:

                legacy = entry.get("legacy", None)

                if legacy is None:
                    # print("---[NOT FOUND LEGACY COMMENTS]---")
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
                    quote_raw_content = None
                    type_quote = quote["result"].get("__typename", None)
                    if (
                        type_quote is not None
                        and type_quote == "TweetWithVisibilityResults"
                    ):
                        quote_raw_content = quote["result"]["tweet"]

                    if type_quote is not None and type_quote == "Tweet":
                        quote_raw_content = quote["result"]

                    if quote_raw_content is not None:
                        quote_tweet_content = extract_info(
                            quote_raw_content, data_topic
                        )
                        if (
                            quote_tweet_content is not None
                            and quote_tweet_content["conversation_id"] == post_id
                        ):
                            # print(f"QUOTE {quote_tweet_content['post_id']}")
                            extracted_comments.append(quote_tweet_content)

                    main_tweet_content = extract_info(entry, data_topic)
                    if (
                        main_tweet_content is not None
                        and main_tweet_content["conversation_id"] == post_id
                    ):
                        # print(f"QUOTE {main_tweet_content['post_id']}")
                        extracted_comments.append(main_tweet_content)

                elif retweet:
                    retweet_tweet_content = extract_info(retweet["result"], data_topic)
                    if (
                        retweet_tweet_content is not None
                        and retweet_tweet_content["conversation_id"] == post_id
                    ):
                        # print(f"RETWEET {retweet_tweet_content['post_id']}")
                        extracted_comments.append(retweet_tweet_content)

                else:
                    tweet_content = extract_info(entry, data_topic)
                    if (
                        tweet_content is not None
                        and tweet_content["conversation_id"] == post_id
                    ):
                        # print(f"NORMAL {tweet_content['post_id']}")
                        extracted_comments.append(tweet_content)
        except Exception as e:
            print(f"ERROR EXTRACT CONTENT COMMENT - MESS: {str(e)}")
            continue

    return extracted_comments


def get_comment_v2(cookie_manager, post_id, proxies, max_comments_page):
    try:
        data_conversation_threads = []
        token_cursor_next = None
        current_comment_page = 0
        url = "https://x.com/i/api/graphql/QuBlQ6SxNAQCt6-kBiCXCQ/TweetDetail"
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,vi;q=0.8",
            "authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
            "content-type": "application/json",
            "user-agent": UserAgent().random,
            "x-client-transaction-id": "WR5jDJm0e/NKe+9ySLX3NIxBNTZ29IhEILe53m1jBkUdG5S3tVuRktr2q3nCYiFTYrzhAFtS/1IAK3BuFK8qMb3T6qboWg",
            "x-client-uuid": "46f93b4e-5ebb-497d-9506-d2a8691c53e0",
            # "x-csrf-token": cookie["cookie"]["ct0"],
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
        }

        while current_comment_page < max_comments_page:
            variables = {
                "focalTweetId": post_id,
                "with_rux_injections": False,
                "rankingMode": "Relevance",
                "includePromotedContent": True,
                "withCommunity": True,
                "withQuickPromoteEligibilityTweetFields": True,
                "withBirdwatchNotes": True,
                "withVoice": True,
            }

            if token_cursor_next:
                variables = {**variables, "cursor": token_cursor_next}

            params = {
                "variables": json.dumps(variables),
                "features": '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
                "fieldToggles": '{"withArticleRichContentState":true,"withArticlePlainText":false,"withGrokAnalyze":false,"withDisallowedReplyControls":false}',
            }

            response_get_comment = fetch_twitter_api_v2(
                url=url,
                params=params,
                headers=headers,
                cookie_manager=cookie_manager,
                proxies=proxies,
            )

            post_raw_list = []

            try:
                post_raw_list = response_get_comment["data"][
                    "threaded_conversation_with_injections_v2"
                ]["instructions"]
            except Exception as e:
                print(
                    f"Error when status code of comment is 200: {e}, {response_get_comment}"
                )
                pass

            for item in post_raw_list:
                if item["type"] == "TimelineAddEntries":
                    for conversation in item["entries"]:
                        if "conversationthread" in conversation["entryId"]:
                            data_conversation_threads.append(conversation)
                        if "cursor-bottom" in conversation["entryId"]:
                            token_cursor_next = conversation["content"]["itemContent"][
                                "value"
                            ]

            if not token_cursor_next:
                break

            if len(data_conversation_threads) == 0:
                raise Exception(f"Not found comments for post id: {post_id}")

            current_comment_page += 1
    except Exception as e:
        print(f"Error while fetching comments: {e}")

    finally:
        return {
            "data_conversation_threads": data_conversation_threads,
        }
