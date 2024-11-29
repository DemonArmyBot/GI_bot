import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import aiohttp

from .log_utils import logger

THREADPOOL = ThreadPoolExecutor(max_workers=1000)


async def sync_to_async(func, *args, wait=True, **kwargs):
    try:
        pfunc = partial(func, *args, **kwargs)
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(THREADPOOL, pfunc)
        return await future if wait else future
    except Exception:
        logger(Exception)


def split_text(text: str, split="\n", pre=False):
    current_list = ""
    list_size = 4000
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
