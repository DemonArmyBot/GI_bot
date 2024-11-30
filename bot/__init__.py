import argparse
import asyncio
import logging
import os
import re
import shlex
import sys
import time
import traceback
from logging import DEBUG, INFO, basicConfig, getLogger, warning
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlparse

from pyrogram import Client
from pyrogram import errors as pyro_errors
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .config import bot, conf

uptime = time.time()
version_file = "version.txt"

if os.path.exists("logs.txt"):
    with open("logs.txt", "r+") as f_d:
        f_d.truncate(0)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=2097152000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("telethon").setLevel(logging.INFO)
LOGS = logging.getLogger(__name__)

if os.path.exists(version_file):
    with open(version_file, "r") as file:
        _bot.version = file.read().strip()

if sys.version_info < (3, 10):
    LOGS.critical("Please use Python 3.10+")
    exit(1)

LOGS.info(f"Bot version: {_bot.version}")
LOGS.info("Starting...")

try:
    bot.client = Client(
        "GI",
        api_id=conf.APP_ID,
        api_hash=conf.API_HASH,
        bot_token=conf.BOT_TOKEN,
        workers=conf.WORKERS,
    )
except Exception:
    LOGS.critical(traceback.format_exc())
    LOGS.info("quiting…")
    exit()
