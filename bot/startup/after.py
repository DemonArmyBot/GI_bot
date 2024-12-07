import signal

import aiohttp

from bot import asyncio, bot, conf, sys, version_file
from bot.fun.emojis import enmoji, enmoji2
from bot.fun.quips import enquip, enquip2
from bot.utils.log_utils import logger
from bot.utils.rss_utils import scheduler


async def onrestart():
    try:
        if sys.argv[1] == "restart":
            msg = "**Restarted!** "
        elif sys.argv[1].startswith("update"):
            s = sys.argv[1].split()[1]
            if s == "True":
                with open(version_file, "r") as file:
                    v = file.read()
                msg = f"**Updated to >>>** `{v}`"
            else:
                msg = "**No major update found!**\n" f"`Bot restarted! {enmoji()}`"
        else:
            return
        chat_id, msg_id = map(int, sys.argv[2].split(":"))
        await bot.client.edit_message_text(chat_id, msg_id, msg)
    except Exception:
        await logger(Exception)


async def onstart():
    try:
        for i in conf.OWNER.split():
            try:
                await bot.client.send_message(int(i), f"**I'm {enquip()} {enmoji()}**")
            except Exception:
                pass
    except BaseException:
        pass


async def on_termination(loop):
    try:
        dead_msg = f"**I'm {enquip2()} {enmoji2()}**"
        for i in conf.OWNER.split():
            try:
                await bot.client.send_message(int(i), dead_msg)
            except Exception:
                pass
    except Exception:
        pass
    # More cleanup code?
    await bot.requests.close()
    exit()


async def on_startup():
    try:
        scheduler.start()
        loop = asyncio.get_running_loop()
        bot.requests = aiohttp.ClientSession(loop=loop)
        for signame in {"SIGINT", "SIGTERM", "SIGABRT"}:
            loop.add_signal_handler(
                getattr(signal, signame),
                lambda: asyncio.create_task(on_termination(loop)),
            )
        if len(sys.argv) == 3:
            await onrestart()
        else:
            await asyncio.sleep(1)
            await onstart()
    except Exception:
        logger(Exception)
