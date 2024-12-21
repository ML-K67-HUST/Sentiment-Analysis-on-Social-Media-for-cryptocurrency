from discordwebhook import Discord
from constants.config import (
    DISCORD_LOGO_SUCCESS,
    DISCORD_LOGO_ERROR,
    DISCORD_USER_NAME,
    DISCORD_AVATAR_URL
)


def push_notification(url_webhook, server, title, time, message, dag=None, status=True):
    discord = Discord(url=url_webhook)
    if status:
        discord.post(
            username=DISCORD_USER_NAME,
            avatar_url=DISCORD_AVATAR_URL,
            embeds=[
                {
                    "author": {
                        "name": "SUCCESS!",
                        "icon_url": DISCORD_LOGO_SUCCESS
                    },
                    "title": title,
                    "description": """
                    SERVER: {}
                    ------------------------
                    TIME: {}
                    ------------------------
                    MESSAGE: {}
                    """.format(server, time, message),
                }
            ],
        )
    else:
        discord.post(
            username=DISCORD_USER_NAME,
            avatar_url=DISCORD_AVATAR_URL,
            embeds=[
                {
                    "author": {
                        "name": "FAILED!",
                        "icon_url": DISCORD_LOGO_ERROR
                    },
                    "title": title,
                    "description": """
                    SERVER: {}
                    ------------------------
                    TIME: {}
                    ------------------------
                    DAG: {}
                    ------------------------
                    MESSAGE: {}
                    """.format(server, time, dag, message),
                }
            ],
        )
