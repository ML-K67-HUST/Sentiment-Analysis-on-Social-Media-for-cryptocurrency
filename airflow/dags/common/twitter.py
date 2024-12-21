import traceback
from services.comment_service import extract_comments_info, get_comment
from services.post_service import (
    extract_posts_info,
    get_user_post,
    get_search_timeline_post,
)


def process_crawl_search_timeline_flow(
    cookie_manager,
    symbol,
    proxies,
    data_topic,
    max_process_latest_posts,
    max_comments_page,
):
    extracted_posts = []
    extracted_comments = []

    try:
        response_get_posts = get_search_timeline_post(
            cookie_manager=cookie_manager,
            proxies=proxies,
            search_query=f"{symbol['name']} #{symbol['symbol']} ${symbol['symbol']}",
        )
        raw_posts = response_get_posts.get("data_posts_add_raw", [])

        if not len(raw_posts):
            raise Exception(f"Not found any post for symbol: {symbol['symbol']}")

        print(f"Done crawl raw posts for user: {symbol['symbol']}")

        extracted_posts = extract_posts_info(
            raw_posts=raw_posts,
            max_process_latest_posts=min(len(raw_posts), max_process_latest_posts),
            data_topic=data_topic,
        )

        for post in extracted_posts:
            print(
                f"=================[START POST ID {post['post_id']}]===================="
            )
            post_id = post["post_id"]

            response_comments = get_comment(
                cookie_manager=cookie_manager,
                post_id=post_id,
                proxies=proxies,
                max_comments_page=max_comments_page,
            )
            raw_comments = response_comments.get("data_conversation_threads", None)

            if not len(raw_comments):
                print(f"Not found any comments for post id: {post_id}")

            extracted_post_comments = extract_comments_info(
                raw_comments=raw_comments, post_id=post_id, data_topic=data_topic
            )

            if len(extracted_post_comments):
                extracted_comments.extend(extracted_post_comments)

    except Exception as e:
        print(f"Exception when crawl data of user: {str(e)}")
        traceback.print_exc()

    finally:
        return {"arr_comments": extracted_comments, "arr_posts": extracted_posts}


def process_crawl_user_flow(
    cookie_manager,
    user,
    proxies,
    data_topic,
    max_process_latest_posts,
    max_comments_page,
):
    extracted_posts = []
    extracted_comments = []

    try:
        response_get_posts = get_user_post(
            cookie_manager=cookie_manager,
            user_id=user["user_id"],
            user_refer=user["user_name"],
            proxies=proxies,
            max_posts_page=1,
        )
        raw_posts = response_get_posts.get("data_posts_add_raw", [])

        if not len(raw_posts):
            raise Exception(f"Not found any post for user: {user['user_name']}")

        print(f"Done crawl raw posts for user: {user['user_name']}")

        extracted_posts = extract_posts_info(
            raw_posts=raw_posts,
            max_process_latest_posts=min(len(raw_posts), max_process_latest_posts),
            data_topic=data_topic,
        )

        for post in extracted_posts:
            print(
                f"=================[START POST ID {post['post_id']}]===================="
            )
            post_id = post["post_id"]

            response_comments = get_comment(
                cookie_manager=cookie_manager,
                post_id=post_id,
                proxies=proxies,
                max_comments_page=max_comments_page,
            )
            raw_comments = response_comments.get("data_conversation_threads", None)

            if not len(raw_comments):
                print(f"Not found any comments for post id: {post_id}")

            extracted_post_comments = extract_comments_info(
                raw_comments=raw_comments, post_id=post_id, data_topic=data_topic
            )

            if len(extracted_post_comments):
                extracted_comments.extend(extracted_post_comments)

    except Exception as e:
        print(f"Exception when crawl data of user: {str(e)}")

    finally:
        return {"arr_comments": extracted_comments, "arr_posts": extracted_posts}
