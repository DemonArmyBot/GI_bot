from . import LOGS, bot, filters
from .startup.after import on_startup
from .utils.msg_utils import event_handler
from .workers.handlers.dev import bash, eval_message, get_logs
from .workers.handlers.gi import enka_handler
from .workers.handlers.manage import pause_handler, restart_handler, update_handler
from .workers.handlers.stuff import getmeme, hello


@bot.client.on_message(filters.incoming & filters.command(["start", "help"]))
async def _(client, message):
    await event_handler(message, hello)


@bot.client.on_message(filters.incoming & filters.command(["pause"]))
async def _(client, message):
    await event_handler(message, pause_handler)


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


@bot.client.on_message(filters.incoming & filters.command("meme"))
async def _(client, message):
    await event_handler(message, getmeme)


@bot.client.on_message(filters.incoming & filters.command("update"))
async def _(client, message):
    await event_handler(message, update_handler)


@bot.client.on_message(filters.incoming & filters.command("restart"))
async def _(client, message):
    await event_handler(message, restart_handler)


########### Start ############

try:
    with bot.client:
        bot.client.loop.run_until_complete(on_startup())
        LOGS.info("Bot has started.")
        bot.client.loop.run_forever()
except Exception:
    LOGS.critical(traceback.format_exc())
    LOGS.critical("Cannot recover from error, exiting…")
    exit()
