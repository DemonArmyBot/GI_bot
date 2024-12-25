import argparse
import io
import itertools
import re
from functools import partial

from bs4 import BeautifulSoup
from pyrogram.types import InputMediaPhoto, InputMediaVideo

from bot import pyro_errors
from bot.config import bot, conf
from bot.fun.quips import enquip3
from bot.others.exceptions import ArgumentParserError

from .bot_utils import convert_gif_2_mp4, gfn, post_to_tgph
from .gi_utils import async_dl
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


def get_msg_from_codes(codes: list, auto: bool = False):
    msg = "**Genshin Impact Redeem Codes**\n\n"
    for code, no in zip(codes, itertools.count(1)):
        link = f"https://genshin.hoyoverse.com/en/gift?code={code.get('code')}"
        msg += f"**{no}.** **{link}**\n**Reward:** `{code.get('rewards')}`"
        msg += "\n\n"
    msg += (
        ">__I'm a bot and this action was performed automatically.__" if auto else str()
    )
    return msg


async def download_media_to_memory(*pics):
    in_mem = []
    for pic in pics:
        try:
            name = pic.split("/")[-1]
            response = await async_dl(pic)
            media = await response.content.read()
            if name.endswith(".gif"):
                media = await convert_gif_2_mp4(media)
                name = name[:-3] + "mp4"
            img = io.BytesIO(media)
            img.name = name
            in_mem.append(img)
        except Exception:
            await logger(Exception)
    return in_mem


def build_media(caption, pics):
    if len(pics) < 2:
        return None
    media = []
    medias = []
    for pic in pics:
        caption_ = caption if str(len(media)).endswith("1") else None
        if pic.name.endswith(".mp4"):
            media.append(InputMediaVideo(pic, caption=caption_))
        else:
            media.append(InputMediaPhoto(pic, caption=caption_))
        if len(media) == 10:
            medias.append(media)
            media = []
    if media:
        medias.append(media)
    return medias


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
        pics = await download_media_to_memory(*pic)
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
            tgh_link = (await post_to_tgph(title, content))["url"]
            caption += f"\n\n>**[Telegraph]({tgh_link})** __({author})__"
        medias = build_media(caption, pics)
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
            await send_rss(caption, chat, medias, pics, top_id)
    except Exception:
        await logger(Exception)


async def send_rss(caption, chat, medias, pics, top_id):
    try:
        if medias:
            for media in medias:
                await avoid_flood(
                    bot.client.send_media_group,
                    chat,
                    media,
                    reply_to_message_id=top_id,
                )
        elif pics:
            send_media = bot.client.send_photo
            if pics[0].name.endswith(".mp4"):
                send_media = bot.client.send_animation
            await avoid_flood(
                send_media,
                chat,
                pics[0],
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
