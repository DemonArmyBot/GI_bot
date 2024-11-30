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
            self.API_KEY = config("API_KEY", default="")
            self.API_HASH = config("API_HASH", default="")
            self.BANNED = config(
                "BANNED",
                default=str(),
            )
            self.BOT_TOKEN = config("BOT_TOKEN", default="")
            self.DATABASE_URL = config("DATABASE_URL", default=None)
            self.DBNAME = config("DBNAME", default="ENC")
            self.DEV = config("DEV", default=0, cast=int)
            self.DYNO = config("DYNO", default=None)
            self.IGNORE_PM = config("IGNORE_PM", default=True, cast=bool)
            self.OWNER = config(
                "OWNER",
                default=str(),
            )
            self.WORKERS = config("WORKERS", default=5, cast=int)
        except Exception:
            print("Environment vars Missing; or")
            print("Something went wrong:")
            print(traceback.format_exc())
            exit()


class Runtime_Config:
    def __init__(self):
        self.banned = None
        self.client = None
        self.ignore_pm = False
        self.offline = False
        self.paused = False
        self.version = None


conf = Config()
bot = Runtime_Config()
