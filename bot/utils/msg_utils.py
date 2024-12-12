import argparse
import re
from functools import partial

from bs4 import BeautifulSoup
from pyrogram.types import InputMediaPhoto

from bot import pyro_errors
from bot.config import bot, conf
from bot.fun.quips import enquip3
from bot.others.exceptions import ArgumentParserError

from .bot_utils import gfn, post_to_tgph
from .log_utils import log, logger


def user_is_allowed(user: str | int):
    user = str(user)
    return user not in bot.banned


def user_is_owner(user: str | int):
    user = str(user)
    return user in conf.OWNER


def user_is_dev(user):
    user = int(user)
    return user == conf.DEV


def pm_is_allowed(event):
    if event.chat.type.value == "private":
        return not bot.ignore_pm
    return True


def build_media(caption, pics):
    if len(pics) < 2:
        return None
    media = []
    for pic in pics:
        media.append(InputMediaPhoto(pic, caption=caption))
        caption = None
    return media


def sanitize_text(text: str) -> str:
    if not text:
        return text
    text = BeautifulSoup(text, "html.parser").text
    return (text[:900] + "…") if len(text) > 900 else text


async def parse_and_send_rss(data: dict, chat_ids: list = None):
    try:
        author = data.get("author")
        chats = chat_ids or conf.RSS_CHAT.split()
        pic = data.get("pic")
        content = data.get("content")
        summary = sanitize_text(data.get("summary"))
        tgh_link = str()
        title = data.get("title")
        url = data.get("link")
        # auth_text = f" by {author}" if author else str()
        caption = f">**[{title}]({url})**"
        caption += f"\n`{summary or str()}`"
        if content:
            if len(content) > 65536:
                content = (
                    content[:65430]
                    + "<strong>...<strong><br><br><strong>(TRUNCATED DUE TO CONTENT EXCEEDING MAX LENGTH)<strong>"
                )
            tgh_link = (await post_to_tgph("Genshin_impact", content))["url"]
            caption += f"\n\n>**[Telegraph]({tgh_link})** __({author})__"
        media = build_media(caption, pic)
        expanded_chat = []
        for chat in chats:
            (
                expanded_chat.append(chat)
                if chat
                else expanded_chat.extend(conf.RSS_CHAT.split())
            )
        for chat in expanded_chat:
            top_chat = chat.split(":")
            chat, top_id = (
                map(int, top_chat) if len(top_chat) > 1 else (int(top_chat[0]), None)
            )
            await send_rss(caption, chat, media, pic, top_id)
    except Exception:
        await logger(Exception)


async def send_rss(caption, chat, media, pic, top_id):
    try:
        if media:
            await avoid_flood(
                bot.client.send_media_group,
                chat,
                media,
                reply_to_message_id=top_id,
            )
        elif pic:
            await avoid_flood(
                bot.client.send_photo,
                chat,
                pic[0],
                caption,
                reply_to_message_id=top_id,
            )
        else:
            await avoid_flood(
                bot.client.send_message,
                chat,
                caption,
                reply_to_message_id=top_id,
            )
    except Exception:
        await logger(Exception)


async def clean_reply(event, reply, func, *args, **kwargs):
    if reply:
        clas = reply
        try:
            await event.delete()
        except Exception:
            await logger(Exception)
    else:
        clas = event
    func = getattr(clas, func)
    return await avoid_flood(func, *args, **kwargs)


async def avoid_flood(func, *args, **kwargs):
    try:
        pfunc = partial(func, *args, **kwargs)
        return await pfunc()
    except pyro_errors.FloodWait as e:
        log(
            e=f"Sleeping for {e.value}s due to floodwait!"
            "\n"
            f"Caused by: {gfn(avoid_flood)}"
        )
        await asyncio.sleep(e.value)
        return await avoid_flood(func, *args, **kwargs)


async def try_delete(msg):
    try:
        await msg.delete()
    except pyro_errors.exceptions.forbidden_403.MessageDeleteForbidden:
        await msg.reply(f"`{enquip3()}`", quote=True)
    except Exception:
        await logger(Exception)


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def line_split(line):
    return [t.strip("\"'") for t in re.findall(r'[^\s"]+|"[^"]*"', line)]


def get_args(*args, to_parse: str, get_unknown=False):
    parser = ThrowingArgumentParser(
        description="parse command flags", exit_on_error=False, add_help=False
    )
    for arg in args:
        if isinstance(arg, list):
            parser.add_argument(arg[0], action=arg[1], required=False)
        else:
            parser.add_argument(arg, type=str, required=False)
    flag, unknowns = parser.parse_known_args(line_split(to_parse))
    if get_unknown:
        unknown = " ".join(map(str, unknowns))
        return flag, unknown
    return flag


async def reply_message(message, text, quote=True):
    """A function to reply messages with a loop in the event of FloodWait"""
    try:
        replied = await message.reply(text, quote=quote)
    except pyro_errors.FloodWait as e:
        log(
            e=f"Sleeping for {e.value}s due to floodwait!"
            "\n"
            f"Caused by: {gfn(reply_message)}"
        )
        await asyncio.sleep(e.value)
        return await reply_message(message, text, quote)


async def event_handler(
    event,
    function,
    client=None,
    require_args=False,
    disable_help=False,
    split_args=" ",
    default_args: str = False,
    use_default_args=False,
):
    args = (
        event.text.split(split_args, maxsplit=1)[1].strip()
        if len(event.text.split()) > 1
        else None
    )
    args = default_args if use_default_args and default_args is not False else args
    help_tuple = ("--help", "-h")
    if (
        (require_args and not args)
        or (args and args.casefold() in help_tuple)
        or (require_args and not (default_args or default_args is False))
        or (default_args in help_tuple)
    ):
        if disable_help:
            return
        return await reply_message(event, f"`{function.__doc__}`")
    await function(event, args, client)
