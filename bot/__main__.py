from . import LOGS, bot

from .startup.after import on_startup



@bot.client.on_message(filters.incoming & filters.command(["start", "help"]))
async def _(bot.client, message):
    await hello(message)


@bot.client.on_message(filters.incoming & filters.command(["pause"]))
async def _(bot.client, message):
    await passwd(message)


@bot.client.on_message(filters.incoming & filters.command(["logs"]))
async def _(bot.client, message):
    await send_logs(message)


@bot.client.on_message(filters.incoming & filters.command(["eval"]))
async def _(bot.client, message):
    if message.from_user:
        if str(message.from_user.id) not in SUDO:
            return await message.delete()
    else:
        if ALLOWED_CHANNELS == "0":
            pass
        elif str(message.chat.id) not in ALLOWED_CHANNELS:
            return await message.delete()
    await anime_arch(message)


@bot.client.on_message(filters.incoming & filters.command("enka"))
async def _(bot.client, message):
    await generate(message)


########### Start ############

try:
    with bot.client:
        bot.client.loop.run_until_complete(startup())
        LOGS.info("bot.client has started.")
        bot.client.loop.run_forever()
except Exception:
    LOGS.critical(traceback.format_exc())
    LOGS.critical("Cannot recover from error, exiting…")
    exit()