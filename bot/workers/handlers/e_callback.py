from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler

from bot import bot
from bot.utils.log_utils import logger

from .stuff import getmeme


async def refmeme(client, query):
    try:
        data, args = query.data.split("_", maxsplit=1)
        user = data.split(":")[-1]
        if not query.from_user.id == int(user):
            return await query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        await query.answer("Refreshing…", show_alert=False)
        return await getmeme(query.message, args, None, True)
    except Exception:
        await logger(Exception)


bot.client.add_handler(CallbackQueryHandler(refmeme, filters=regex("^refmeme")))
