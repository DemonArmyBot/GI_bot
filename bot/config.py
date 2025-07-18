#    This file is part of the GI_bot distribution.
#    Copyright (c) 2024 Nubuki-all
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/Nubuki-all/GI_bot/blob/WA/License> .
import traceback

from decouple import config


class Config:
    def __init__(self):
        try:
            self.ALWAYS_DEPLOY_LATEST = config(
                "ALWAYS_DEPLOY_LATEST", default=False, cast=bool
            )
            self.API_ID = config("API_ID", default="")
            self.API_HASH = config("API_HASH", default="")
            self.ALLOWED_CHATS = config(
                "ALLOWED_CHATS",
                default=str(),
            )
            self.BANNED_USERS = config(
                "BANNED_USERS",
                default=str(),
            )
            self.BLOCK_NSFW = config("BLOCK_NSFW", default=False, cast=bool)
            self.BOT_TOKEN = config("BOT_TOKEN", default="")
            self.DATABASE_URL = config("DATABASE_URL", default=None)
            self.DBNAME = config("DBNAME", default="GI_bot")
            self.DEBUG = config("DEBUG", default=False, cast=bool)
            self.DEV = config("DEV", default=0, cast=int)
            self.DYNO = config("DYNO", default=None)
            self.IGNORE_PM = config("IGNORE_PM", default=False, cast=bool)
            self.LOG_GROUP = config("LOG_GROUP", default="-1002327918459")
            self.RSS_CHAT = config(
                "RSS_CHAT",
                default=str(),
            )
            self.RSS_DELAY = config("RSS_DELAY", default=60, cast=int)
            self.OWNER = config(
                "OWNER",
                default=str(),
            )
            self.TELEGRAPH_API = config(
                "TELEGRAPH_API", default="https://api.telegra.ph"
            )
            self.WORKERS = config("WORKERS", default=5, cast=int)
        except Exception:
            print("Environment vars Missing; or")
            print("Something went wrong:")
            print(traceback.format_exc())
            exit()


class Runtime_Config:
    def __init__(self):
        self.author = None
        self.author_url = None
        self.block_nsfw = False
        self.client = None
        self.docker_deployed = False
        self.enka_dict = {}
        self.group_dict = {}
        self.ignore_pm = False
        self.max_message_length = 4096
        self.offline = False
        self.paused = False
        self.gift_dict = {}
        self.rss_dict = {}
        self.rss_ran_once = False
        self.user_dict = {}
        self.version = None


conf = Config()
bot = Runtime_Config()
