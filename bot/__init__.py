import argparse
import asyncio
import logging
import os
import re
import shlex
import subprocess
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

bot_id = conf.BOT_TOKEN.split(":", 1)[0]
local_rdb = ".local_rssdb.pkl"
local_budb = ".banned_users.pkl"
log_file_name = "logs.txt"
rss_dict_lock = asyncio.Lock()
uptime = time.time()
version_file = "version.txt"

if os.path.exists(log_file_name):
    with open(log_file_name, "r+") as f_d:
        f_d.truncate(0)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(log_file_name, maxBytes=2097152000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("urllib3").setLevel(logging.INFO)
LOGS = logging.getLogger(__name__)

no_verbose = [
    "apscheduler.executors.default",
    "pyrogram.session.session",
    "pyrogram.connection.connection",
]
if not conf.DEBUG:
    for item in no_verbose:
        logging.getLogger(item).setLevel(logging.WARNING)

bot.repo_branch = (
    subprocess.check_output(["git rev-parse --abbrev-ref HEAD"], shell=True)
    .decode()
    .strip()
    if os.path.exists(".git")
    else None
)
if os.path.exists(version_file):
    with open(version_file, "r") as file:
        bot.version = file.read().strip()

if sys.version_info < (3, 10):
    LOGS.critical("Please use Python 3.10+")
    exit(1)

LOGS.info("Starting...")

bot.ignore_pm = conf.IGNORE_PM

try:
    bot.client = Client(
        "GI",
        api_id=conf.API_ID,
        api_hash=conf.API_HASH,
        bot_token=conf.BOT_TOKEN,
        workers=conf.WORKERS,
    )
except Exception:
    LOGS.critical(traceback.format_exc())
    LOGS.info("quiting…")
    exit()
