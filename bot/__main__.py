from . import LOGS, asyncio, bot, filters, traceback
from .startup.after import on_startup
from .utils.msg_utils import event_handler
from .workers.handlers.dev import bash, eval_message, get_logs
from .workers.handlers.gi import (
    enka_handler,
    get_events,
    getgiftcodes,
    random_challenge,
    weapon_handler,
)
from .workers.handlers.manage import (
    ban,
    disable,
    enable,
    pause_handler,
    restart_handler,
    rss_handler,
    sudoers,
    unban,
    update_handler,
)
from .workers.handlers.stuff import getmeme, hello, up


@bot.client.on_message(filters.incoming & filters.command(["start", "help"]))
async def _(client, message):
    await event_handler(message, hello)


@bot.client.on_message(filters.incoming & filters.command(["pause"]))
async def _(client, message):
    await event_handler(message, pause_handler)


@bot.client.on_message(filters.incoming & filters.command(["ban"]))
async def _(client, message):
    await event_handler(message, ban)


@bot.client.on_message(filters.incoming & filters.command(["disable"]))
async def _(client, message):
    await event_handler(message, disable)


@bot.client.on_message(filters.incoming & filters.command(["enable"]))
async def _(client, message):
    await event_handler(message, enable)


@bot.client.on_message(filters.incoming & filters.command(["sudo"]))
async def _(client, message):
    await event_handler(message, sudoers)


@bot.client.on_message(filters.incoming & filters.command(["unban"]))
async def _(client, message):
    await event_handler(message, unban)


@bot.client.on_message(filters.incoming & filters.command(["logs"]))
async def _(client, message):
    await event_handler(message, get_logs)


@bot.client.on_message(filters.incoming & filters.command(["eval"]))
async def _(client, message):
    await event_handler(message, eval_message, require_args=True)


@bot.client.on_message(filters.incoming & filters.command(["bash"]))
async def _(client, message):
    await event_handler(message, bash, require_args=True)


@bot.client.on_message(filters.incoming & filters.command("enka"))
async def _(client, message):
    await event_handler(message, enka_handler, require_args=True)


@bot.client.on_message(filters.incoming & filters.command("weapon"))
async def _(client, message):
    await event_handler(message, weapon_handler, require_args=True)


@bot.client.on_message(filters.incoming & filters.command("rchallenge"))
async def _(client, message):
    await event_handler(message, random_challenge)


@bot.client.on_message(filters.incoming & filters.command("ping"))
async def _(client, message):
    await event_handler(message, up)


@bot.client.on_message(filters.incoming & filters.command("events"))
async def _(client, message):
    await event_handler(message, get_events)


@bot.client.on_message(filters.incoming & filters.command("meme"))
async def _(client, message):
    await event_handler(message, getmeme)


@bot.client.on_message(filters.incoming & filters.command("codes"))
async def _(client, message):
    await event_handler(message, getgiftcodes)


@bot.client.on_message(filters.incoming & filters.command("rss"))
async def _(client, message):
    await event_handler(message, rss_handler, require_args=True)


@bot.client.on_message(filters.incoming & filters.command("update"))
async def _(client, message):
    await event_handler(message, update_handler)


@bot.client.on_message(filters.incoming & filters.command("restart"))
async def _(client, message):
    await event_handler(message, restart_handler)


########### Start ############


async def start_bot():
    try:
        async with bot.client:
            bot.client.loop.run_until_complete(on_startup())
            LOGS.info("Bot has started.")
            bot.client.loop.run_forever()
    except Exception:
        LOGS.critical(traceback.format_exc())
        LOGS.critical("Cannot recover from error, exiting…")
        exit()


asyncio.run(start_bot())
