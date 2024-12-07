import asyncio
import itertools
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import aiohttp
import requests

from bot import LOGS, bot, telegraph_errors, time

THREADPOOL = ThreadPoolExecutor(max_workers=1000)


def gfn(fn):
    "gets module path"
    return ".".join([fn.__module__, fn.__qualname__])


async def sync_to_async(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(THREADPOOL, pfunc)
    return await future if wait else future


def create_api_token(retries=10):
    telgrph_tkn_err_msg = "Couldn't not successfully create telegraph api token!."
    while retries:
        try:
            bot.tgp_client.create_api_token("Rss")
            break
        except (requests.exceptions.ConnectionError, ConnectionError) as e:
            retries -= 1
            if not retries:
                LOGS.info(telgrph_tkn_err_msg)
                break
            time.sleep(1)
    return retries


async def post_to_tgph(title, text):
    bot.author = (await bot.client.get_me()).first_name if not bot.author else bot.author
    bot.author_url = f"https://t.me/{((await bot.client.get_me()).username)}" if not bot.author_url else bot.author_url

    retries = 10
    while retries:
        try:
            page = await sync_to_async(
                bot.tgp_client.post,
                title=title,
                author=author,
                author_url=author_url,
                text=text,
            )
            return page
        except telegraph_errors.APITokenRequiredError as e:
            result = await sync_to_async(create_api_token)
            if not result:
                raise e
        except (requests.exceptions.ConnectionError, ConnectionError) as e:
            retries -= 1
            if not retries:
                raise e
            await asyncio.sleep(1)


def list_to_str(lst: list, sep=" ", start: int = None, md=True):
    string = str()
    t_start = start if isinstance(start, int) else 1
    for i, count in zip(lst, itertools.count(t_start)):
        if start is None:
            string += str(i) + sep
            continue
        entry = f"`{i}`"
        string += f"{count}. {entry} {sep}"

    return string.rstrip(sep)


def split_text(text: str, split="\n", pre=False, list_size=4000):
    current_list = ""
    message_list = []
    for string in text.split(split):
        line = string + split if not pre else split + string
        if len(current_list) + len(line) <= list_size:
            current_list += line
        else:
            # Add current_list to account_list
            message_list.append(current_list)
            # Reset the current_list with a new "line".
            current_list = line
    # Add the last line into list.
    message_list.append(current_list)
    return message_list


async def get_json(link):
    async with aiohttp.ClientSession() as requests:
        result = await requests.get(link)
        return await result.json()
