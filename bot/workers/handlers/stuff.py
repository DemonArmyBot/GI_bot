from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from bot import bot
from bot.utils.bot_utils import get_json
from bot.utils.log_utils import logger
from bot.utils.msg_utils import pm_is_allowed, user_is_allowed, user_is_owner

meme_list = []


async def gen_meme(link):
    i = 1
    while True:
        result = await get_json(link)
        _id = result.get("ups")
        title = result.get("title")
        author = result.get("author")
        pl = result.get("postLink")
        if i > 20:
            raise Exception("Request Timeout!")
        i += 1
        if pl in meme_list:
            continue
        if len(meme_list) > 100:
            meme_list.clear()
        meme_list.append(pl)
        sb = result.get("subreddit")
        nsfw = result.get("nsfw")
        nsfw_text = "**🔞 NSFW**\n"
        caption = f"{nsfw_text if nsfw else str()}**{title.strip()}**\n{pl}\n\nBy u/{author} in r/{sb}"
        url = result.get("url")
        filename = f"{_id}.{url.split('.')[-1]}"
        break
    return caption, url, filename, nsfw


async def getmeme(event, args, client, edit=False, user=None):
    """
    Fetches a random meme from reddit
    Uses meme-api.com

    Arguments:
    subreddit - custom subreddit
    """
    user = user or event.from_user.id
    if not user_is_owner(user):
        if not pm_is_allowed(event):
            return
        if not user_is_allowed(user):
            return
    link = "https://meme-api.com/gimme"
    try:
        ref_button = InlineKeyboardButton(
            text="Refresh", callback_data=f"refmeme {user}{'_'+args if args else str()}"
        )
        reply_markup = InlineKeyboardMarkup([[ref_button]])
        if args:
            link += f"/{args}" if not args.isdigit() else str()
        caption, url, filename, nsfw = await gen_meme(link)
        if not edit:
            return await event.reply_photo(
                caption=caption, photo=url, has_spoiler=nsfw, reply_markup=reply_markup
            )
        photo = InputMediaPhoto(media=url, caption=caption, has_spoiler=nsfw)
        return await event.edit_media(photo, reply_markup=reply_markup)
        # time.sleep(3)
    except Exception as e:
        await logger(Exception)
        return await event.reply(f"*Error:*\n{e}")


async def refmeme(client, query):
    try:
        data, info = query.data.split(maxsplit=1)
        usearg = info.split("_", maxsplit=1)
        user, args = usearg if len(usearg) == 2 else (usearg[0], None)
        if not query.from_user.id == int(user):
            return await query.answer(
                "You're not allowed to do this!", show_alert=False
            )
        await query.answer("Refreshing…", show_alert=False)
        return await getmeme(query.message, args, None, True, user)
    except Exception:
        await logger(Exception)


async def hello(event, args, client):
    try:
        await event.reply("Hi!")
    except Exception:
        await logger(Exception)


bot.client.add_handler(CallbackQueryHandler(refmeme, filters=regex("^refmeme")))
