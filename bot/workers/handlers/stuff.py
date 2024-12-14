import asyncio

from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from bot import bot, pyro_errors
from bot.utils.bot_utils import get_json, list_to_str
from bot.utils.db_utils import save2db2
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    get_msg_from_codes,
    pm_is_allowed,
    user_is_allowed,
    user_is_owner,
)

meme_list = []


async def gen_meme(link, pm=False):
    i = 1
    while True:
        result = await get_json(link)
        _id = result.get("ups")
        title = result.get("title")
        if not title:
            return None, None, None, None
        author = result.get("author")
        pl = result.get("postLink")
        if i > 100:
            raise Exception("Request Timeout!")
        i += 1
        if pl in meme_list:
            continue
        if len(meme_list) > 10000:
            meme_list.clear()
        nsfw = result.get("nsfw")
        if bot.block_nsfw and nsfw and not pm:
            return None, None, None, True
        meme_list.append(pl)
        sb = result.get("subreddit")
        nsfw_text = "*🔞 NSFW*\n"
        caption = f"{nsfw_text if nsfw else str()}*{title.strip()}*\n{pl}\n\nBy u/{author} in r/{sb}"
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
        caption, url, filename, nsfw = await gen_meme(
            link, (event.chat.type.value == "private")
        )
        if not url:
            if nsfw:
                return await event.reply("**NSFW is blocked!**")
            return await event.reply("**Request Failed!**")
        if not edit:
            return await event.reply_photo(
                caption=caption, photo=url, has_spoiler=nsfw, reply_markup=reply_markup
            )
        photo = InputMediaPhoto(media=url, caption=caption, has_spoiler=nsfw)
        return await event.edit_media(photo, reply_markup=reply_markup)
        # time.sleep(3)
    except pyro_errors.BadRequest as e:
        if e.ID == "MEDIA_EMPTY":
            return await getmeme(event, args, client, edit, user)
        await logger(Exception)
        return await event.reply(f"**Error:**\n`{e}`")
    except Exception as e:
        await logger(Exception)
        return await event.reply(f"**Error:**\n`{e}`")


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


async def manage_autogift_chat(event, args, client):
    user = event.from_user.id
    if not user_is_owner(user):
        return
    try:
        msg = str()
        arg = args.split(maxsplit=1)
        if len(arg) == 1:
            if arg[0] != "-g":
                return
            if not bot.gift_dict["chats"]:
                msg = "No chat set!"
                return
            msg = list_to_str(bot.gift_dict["chats"], sep=", ")
            return
        else:
            if not arg[0] in ("-add", "-rm"):
                return
        if not arg[1].split(":")[0].isdigit():
            if arg[1].casefold() not in ("default", "."):
                msg = "**Invalid chat!**"
                return
            arg[1] = None if arg[1] != "." else event.chat.id
        if arg[0] == "-add":
            if arg[1] in bot.gift_dict["chats"]:
                msg = "**Chat already added!**"
                return
            bot.gift_dict["chats"].append(arg[1])
            await save2db2(bot.gift_dict, "gift")
            msg = f"**{arg[1] or 'default'}** has been added."
            return
        if arg[0] == "-rm":
            if not arg[1] in bot.gift_dict["chats"]:
                msg = "**Given chat was never added!**"
                return
            bot.gift_dict["chats"].remove(arg[1])
            await save2db2(bot.gift_dict, "gift")
            msg = f"**{arg[1] or 'default'}** has been removed."
            return
    except Exception:
        await logger(Exception)
    finally:
        if msg:
            await event.reply(msg)


async def getgiftcodes(event, args, client):
    """
    Fetches a lastest genshin giftcodes
    Uses hoyo-codes.seria.moe

    Arguments:
        -add
        -rm
        -get
     add, remove and get chats for auto giftcodes
    """
    if args:
        return await manage_autogift_chat(event, args, client)
    user = event.from_user.id
    if not user_is_owner(user):
        if not pm_is_allowed(event):
            return
        if not user_is_allowed(user):
            return
    link = "https://hoyo-codes.seria.moe/codes?game=genshin"
    try:
        reply = await event.reply("**Fetching latest giftcodes…**")
        result = await get_json(link)
        msg = get_msg_from_codes(result.get("codes"))
        await event.reply(msg)
        await asyncio.sleep(5)
        await reply.delete()
    except Exception as e:
        await logger(Exception)
        return await event.reply(f"**Error:**\n{e}")


async def hello(event, args, client):
    try:
        await event.reply("Hi!")
    except Exception:
        await logger(Exception)


bot.client.add_handler(CallbackQueryHandler(refmeme, filters=regex("^refmeme")))
