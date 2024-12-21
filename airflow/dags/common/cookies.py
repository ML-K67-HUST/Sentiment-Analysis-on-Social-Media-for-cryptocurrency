from datetime import datetime
import pytz


class CookieManager:
    def __init__(self, cookies):
        self.cookies = cookies

    def get_active_cookies(self, max_cookies=999):
        current_time = int(datetime.now(pytz.utc).timestamp())
        arr_cookies_active = []
        time_min = self.cookies[0]["time_reset"]
        sorted_cookies = sorted(self.cookies, key=lambda x: x["count"])

        for cookie in sorted_cookies:
            if len(arr_cookies_active) == max_cookies:
                break

            if cookie["time_reset"] < time_min:
                time_min = cookie["time_reset"]

            if (not cookie["is_used"] and cookie["time_reset"] < current_time) or (
                not cookie["is_used"] and cookie["rate_limit"] > 30
            ):
                cookie["is_used"] = True
                arr_cookies_active.append(cookie)

        # if len(arr_cookies_active) < max_cookies:
        #     return {"code": 1, "time_reset": time_min}

        return {"code": 0, "cookies": arr_cookies_active}

    def get_active_cookie(self, old_cookie_id=None):
        current_time = int(datetime.now(pytz.utc).timestamp())
        time_min = self.cookies[0]["time_reset"]
        sorted_cookies = sorted(self.cookies, key=lambda x: x["count"])

        for cookie in sorted_cookies:
            if cookie["time_reset"] < time_min:
                time_min = cookie["time_reset"]

            if (
                cookie["id"] != old_cookie_id
                and not cookie["is_used"]
                and (cookie["time_reset"] < current_time or cookie["rate_limit"] > 20)
            ):
                cookie["is_used"] = True
                return {"code": 0, "cookie": cookie}

        return {"code": 1, "time_reset": time_min}

    def update_release_used_cookie(
        self, cookie_id=False, status_cookie=False, new_rate_limit=None, time_reset=None
    ):
        for cookie in self.cookies:
            if cookie["id"] == cookie_id:
                cookie["is_used"] = status_cookie
                cookie["count"] += 1
                if new_rate_limit is not None:
                    cookie["rate_limit"] = new_rate_limit
                if time_reset is not None:
                    cookie["time_reset"] = time_reset

                # return True

        # return False

    def remaining_cookies(self):
        return self.cookies
