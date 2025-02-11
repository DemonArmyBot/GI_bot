import asyncio
import itertools
from inspect import getdoc

from feedparser import parse as feedparse

from bot import bot, rss_dict_lock
from bot.utils.bot_utils import list_to_str, split_text
from bot.utils.db_utils import save2db2
from bot.utils.log_utils import logger
from bot.utils.msg_utils import (
    avoid_flood,
    event_handler,
    get_args,
    get_user_info,
    try_delete,
    user_is_allowed,
    user_is_owner,
    user_is_privileged,
    user_is_sudoer,
)
from bot.utils.os_utils import re_x, updater
from bot.utils.rss_utils import schedule_rss, scheduler


async def restart_handler(event, args, client):
    """Restarts bot. (To avoid issues use /update instead.)"""
    if not user_is_privileged(event.from_user.id):
        return
    try:
        rst = await event.reply("**Restarting Please Wait…**")
        await bot.requests.close()
        message = str(rst.chat.id) + ":" + str(rst.id)
        re_x("restart", message)
    except Exception:
        await event.reply("An Error Occurred")
        await logger(Exception)


async def update_handler(event, args, client):
    """Fetches latest update for bot"""
    try:
        if not user_is_privileged(event.from_user.id):
            return
        upt_mess = "Updating…"
        reply = await event.reply(f"`{upt_mess}`")
        await bot.requests.close()
        updater(reply)
    except Exception:
        await logger(Exception)


async def pause_handler(event, args, client):
    """
    Pauses bot/ bot ignores Non-owner queries
    Arguments:
        -: on/enable <str> pauses bot
        -: off/disable <str> unpauses bot
        -: no argument <str> checks state
    """
    try:
        if not user_is_owner(event.from_user.id):
            return
        if not args:
            msg = f"Bot is currently {'paused' if bot.paused else 'unpaused'}."
            return await event.reply(msg)
        if args.casefold() in ("on", "enable"):
            if bot.paused:
                return await event.reply("Bot already paused.")
            bot.paused = True
            return await event.reply("Bot has been paused.")
        elif args.casefold() in ("off", "disable"):
            if not bot.paused:
                return await event.reply("Bot already unpaused.")
            bot.paused = False
            return await event.reply("Bot has been unpaused.")
    except Exception:
        await log(Exception)


async def rss_handler(event, args, client):
    """
    Base command for rss:
        *Arguments:
            -d (TITLE): To delete already an subscribed feed.
            -e (TITLE): To edit configurations for already subscribed rss feed.
            -g (TITLE, AMOUNT): To get previous feeds for given TITLE. (Amount corresponds to AMOUNT)
            -l (NO REQUIRED ARGS) To list subscribed feeds.
            -s (TITLE, LINK): To subscribe an rss feed.

        for additional help send the above arguments with -h/--help or without additional params.
        *listed in the order priority.
    """
    if not user_is_privileged(event.from_user.id):
        return await try_delete(event)
    arg, args = get_args(
        ["-d", "store_true"],
        ["-e", "store_true"],
        ["-g", "store_true"],
        ["-l", "store_true"],
        ["-s", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not (arg.d or arg.e or arg.g or arg.l or arg.s):
        return await avoid_flood(event.reply, f"`{rss_handler.__doc__}`")
    if arg.d:
        await event_handler(
            event, del_rss, client, True, default_args=args, use_default_args=True
        )
    elif arg.e:
        await event_handler(event, rss_editor, client, True, default_args=args)
    elif arg.g:
        await event_handler(event, rss_get, client, True, default_args=args)
    elif arg.l:
        await event_handler(event, rss_list, client, default_args=args)
    elif arg.s:
        await event_handler(event, rss_sub, client, True, default_args=args)


async def rss_list(event, args, client):
    """
    Get list of subscribed rss feeds
        Args:
            None.
        Returns:
            List of subscribed rss feeds.
    """
    if not user_is_privileged(event.from_user.id):
        return
    if not bot.rss_dict:
        return await event.reply(
            "**No subscriptions!**",
        )
    list_feed = str()
    pre_event = event

    def parse_filter(ftr: str):
        if not ftr:
            return None
        return ", ".join(["(" + ", ".join(map(str, sublist)) + ")" for sublist in ftr])

    async with rss_dict_lock:
        for i, (title, data) in zip(itertools.count(1), list(bot.rss_dict.items())):
            list_feed += (
                f"\n\n{i}. **Title:** `{title}`\n**Feed Url: **`{data['link']}`\n"
            )
            list_feed += f"**Chat:** `{list_to_str(data['chat']) or 'Default'}`\n"
            list_feed += f"**Include filter:** `{parse_filter(data['inf'])}`\n"
            list_feed += f"**Exclude filter:** `{parse_filter(data['exf'])}`\n"
            list_feed += f"**Paused:** `{data['paused']}`"

    lmsg = split_text(list_feed.strip("\n"), "\n\n", True)
    for i, msg in zip(itertools.count(1), lmsg):
        msg = f"**Your subscriptions** #{i}" + msg
        pre_event = await avoid_flood(pre_event.reply, msg, quote=True)
        await asyncio.sleep(1)


async def rss_get(event, args, client):
    """
    Get the links of titles in rss:
    Arguments:
        [Title] - Title used in subscribing rss
        -a [Amount] - Amount of links to grab
    """
    if not user_is_privileged(event.from_user.id):
        return
    arg, args = get_args(
        "-a",
        ["-g", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not arg.a:
        if len(args.split()) != 2:
            return await event.reply(f"`{rss_get.__doc__}`")
        args, arg.a = args.split()
    if not arg.a.isdigit():
        return await event.reply("Second argument must be a digit.")

    title = args
    count = int(arg.a)
    data = bot.rss_dict.get(title)
    if not (data and count > 0):
        return await event.reply(f"`{rss_get.__doc__}`")
    try:
        imsg = await event.reply(
            f"Getting the last **{count}** item(s) from {title}...",
            quote=True,
        )
        pre_event = imsg
        rss_d = feedparse(data["link"])
        item_info = ""
        for item_num in range(count):
            try:
                link = rss_d.entries[item_num]["links"][1]["href"]
            except IndexError:
                link = rss_d.entries[item_num]["link"]
            item_info += f"**Name:** `{rss_d.entries[item_num]['title'].replace('>', '').replace('<', '')}`\n"
            item_info += f"**Link:** `{link}`\n\n"
        for msg in split_text(item_info, "\n\n"):
            pre_event = await avoid_flood(pre_event.reply, msg, quote=True)
            await asyncio.sleep(2)
        await avoid_flood(
            imsg.edit,
            f"Here are the last **{count}** item(s) from {title}:",
        )
    except IndexError:
        await avoid_flood(
            imsg.edit, "Parse depth exceeded. Try again with a lower value."
        )
    except Exception as e:
        await logger(Exception)
        await avoid_flood(event.reply, f"error! - `{str(e)}`")


async def rss_editor(event, args, client):
    """
    Edit subscribed rss feeds!
    simply pass the rss title with the following arguements:
        Additional args:
            --exf (what_to_exclude): keyword of words to fiter out*
            --inf (what_to_include): keywords to include*
            --chat (chat_id) chat to send rss overides RSS_CHAT pass 'default' to reset.
            -p () to pause the rss feed
            -r () to resume the rss feed

        *format = "x or y|z"
        *to unset pass 'disable' or 'off'
        where:
            or - means either of both values
            | - means and
        Returns:
            success message on successfully editing the rss configuration
    """
    if not user_is_privileged(event.from_user.id):
        return
    arg, args = get_args(
        "-l",
        "--exf",
        "--inf",
        "--chat",
        ["-e", "store_true"],
        ["-p", "store_true"],
        ["-r", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not args:
        return await event.reply(f"Please pass the title of the rss item to edit")
    if not (data := bot.rss_dict.get(args)):
        return await event.reply(f"Could not find rss with title - {args}.")
    if not (arg.l or arg.exf or arg.inf or arg.p or arg.r or arg.chat):
        return await event.reply("Please supply at least one additional arguement.")
    if arg.chat:
        for chat in arg.chat.split():
            chat = chat.split(":")[0]
            if not (chat.lstrip("-").isdigit() or chat.casefold() in ("default", ".")):
                return await avoid_flood(
                    event.reply,
                    f"Chat must be a Telegram chat id (with -100 if a group or channel) or default\nNot '{chat}'",
                )
    if arg.l:
        data["link"] = arg.l
    if arg.chat:
        _default = False
        data["chat"] = []
        for chat in arg.chat.split():
            chat = str(event.chat.id) if chat == "." else chat
            if chat.casefold() != "default":
                data["chat"].append(chat)
            else:
                if _default:
                    continue
                data["chat"].append(None)
                _default = True
    if arg.exf:
        exf_lists = []
        if arg.exf.casefold() not in ("disable", "off"):
            filters_list = arg.exf.split("|")
            for x in filters_list:
                y = x.split(" or ")
                exf_lists.append(y)
        data["exf"] = exf_lists
    if arg.inf:
        inf_lists = []
        if arg.inf.casefold() not in ("disable", "off"):
            filters_list = arg.inf.split("|")
            for x in filters_list:
                y = x.split(" or ")
                inf_lists.append(y)
        data["inf"] = inf_lists
    if arg.p:
        data["paused"] = True
    elif arg.r:
        data["allow_rss_spam"] = True
        data["paused"] = False
        if scheduler.state == 2:
            scheduler.resume()
        elif not scheduler.running:
            schedule_rss()
            scheduler.start()
    await save2db2(bot.rss_dict, "rss")
    await event.reply(
        f"Edited rss configurations for rss feed with title - `{args}` successfully!"
    )


async def del_rss(event, args, client):
    """
    Removes feed with designated title from list of subscribed feeds
        Args:
            TITLE (str): subscribed rss feed title to remove


        Returns:
            Success message on successfull removal
            Not found message if TITLE passed was not found
    """
    if not user_is_privileged(event.from_user.id):
        return
    if not bot.rss_dict.get(args):
        return await event.reply(f"'{args}' not found in list of subscribed rss feeds!")
    bot.rss_dict.pop(args)
    msg = f"Succesfully removed '{args}' from subscribed feeds!"
    await save2db2(bot.rss_dict, "rss")
    await event.reply(msg)
    await logger(e=msg)


async def rss_sub(event, args, client):
    """
    Subscribe rss feeds!
    simply pass the rss link with the following arguements:
        Args:
            -t (TITLE): New Title of the subscribed rss feed [Required]
            --exf (what_to_exclude): keyword of words to fiter out*
            --inf (what_to_include): keywords to include*
            -p () to pause the rss feed
            -r () to resume the rss feed
            --chat (chat_id) chat to send feeds

        *format = "x or y|z"
        where:
            or - means either of both values
            | - means and
        *only leech and qbleech commands are passed
        Returns:
            success message on successfully subscribing to an rss feed
    """
    if not user_is_privileged(event.from_user.id):
        return
    arg, args = get_args(
        "-t",
        "--exf",
        "--inf",
        "--chat",
        ["-p", "store_true"],
        ["-s", "store_true"],
        to_parse=args,
        get_unknown=True,
    )
    if not (arg.t and args):
        return await event.reply(f"`{rss_sub.__doc__}`")
    feed_link = args
    title = arg.t

    if arg.chat:
        for chat in arg.chat.split():
            chat = chat.split(":")[0]
            if not (chat.lstrip("-").isdigit() or chat.casefold() in ("default", ".")):
                return await avoid_flood(
                    event.reply,
                    f"Chat must be a Telegram chat id (with -100 if a group or channel)\nNot '{chat}'",
                )
    if bot.rss_dict.get(title):
        return await avoid_flood(
            event.reply,
            f"This title **{title}** has already been subscribed!. **Please choose another title!**",
        )
    chat = []
    if arg.chat:
        _current = False
        _default = False
        for chat_ in arg.chat.split():
            if chat_ == ".":
                if _current:
                    continue
                chat_ = str(event.chat.id)
                _current = True
            if chat_.casefold() != "default":
                chat.append(chat_)
            else:
                if _default:
                    continue
                chat.append(None)
                _default = True
    inf_lists = []
    exf_lists = []
    if arg.inf:
        filters_list = arg.inf.split("|")
        for x in filters_list:
            y = x.split(" or ")
            inf_lists.append(y)
    if arg.exf:
        filters_list = arg.exf.split("|")
        for x in filters_list:
            y = x.split(" or ")
            exf_lists.append(y)
    msg = str()
    try:
        rss_d = feedparse(feed_link)
        last_title = rss_d.entries[0]["title"]
        msg += "**Subscribed!**"
        msg += f"\n**Title:** `{title}`\n**Feed Url:** {feed_link}"
        msg += f"\n**latest record for** {rss_d.feed.title}:"
        msg += f"\nName: `{last_title.replace('>', '').replace('<', '')}`"
        try:
            last_link = rss_d.entries[0]["links"][1]["href"]
        except IndexError:
            last_link = rss_d.entries[0]["link"]
        msg += f"\nLink:- `{last_link}`"
        msg += f"\n**Chat:-** `{arg.chat or 'Default'}`"
        msg += f"\n**Filters:-**\ninf: `{arg.inf}`\nexf: `{arg.exf}`"
        msg += f"\n**Paused:-** `{arg.p}`"
        async with rss_dict_lock:
            bot.rss_dict[title] = {
                "link": feed_link,
                "last_feed": last_link,
                "last_title": last_title,
                "chat": chat,
                "inf": inf_lists,
                "exf": exf_lists,
                "paused": arg.p,
            }
        await logger(
            e="Rss Feed Added:"
            f"\nby:- {event.from_user.id}"
            f"\ntitle:- {title}"
            f"\nlink:- {feed_link}"
            f"\nchat:- {arg.chat}"
            f"\ninclude filter:- {arg.inf}"
            f"\nexclude filter:- {arg.exf}"
            f"\npaused:- {arg.p}"
        )
    except (IndexError, AttributeError) as e:
        emsg = f"The link: {feed_link} doesn't seem to be a RSS feed or it's region-blocked!"
        await avoid_flood(event.reply, emsg + "\nError: " + str(e))
    except Exception as e:
        await logger(Exception)
        return await avoid_flood(event.reply, str(e))
    await save2db2(bot.rss_dict, "rss")
    if msg:
        await avoid_flood(event.reply, msg, quote=True)
    if arg.p:
        return
    if scheduler.state == 2:
        scheduler.resume()
    elif not scheduler.running:
        schedule_rss()
        scheduler.start()


async def ban(event, args, client):
    """
    Ban the user from using the bot:
    Argument:
        *user_id/@mentions
        or reply to the user's message

    *user_id: user's telegram id
    """
    user = event.from_user.id
    if not user_is_owner(user):
        return
    try:
        if args and (" " in args or not (args.startswith("@") or args.isdigit())):
            return await event.reply("**Please supply a valid id to ban**")
        elif not (args or event.reply_to_message):
            return await event.reply(
                "**Reply to a message or supply an id to ban the user from using the bot.**"
            )

        ban_id = args or event.reply_to_message.from_user.id
        ban_info = await get_user_info(ban_id)
        ban_id = str(ban_info.id)
        if not ban_info:
            return await event.reply("**Invalid user_id**")
        if user_is_owner(ban_id):
            return await event.reply("**Why?**")
        if user_is_sudoer(ban_id):
            return await event.reply(f"{ban_info.mention()} **is a Sudoer.**")
        if not user_is_allowed(ban_id):
            return await event.reply(
                f"@{ban_info.mention()} **has already been banned from using the bot.**"
            )
        bot.user_dict.setdefault(ban_id, {}).update(banned=True)
        await save2db2(bot.user_dict, "users")
        return await event.reply(
            f"{ban_info.mention()} **has been banned from using the bot.**"
        )
    except Exception:
        await logger(Exception)


async def unban(event, args, client):
    """
    Unban previously banned user:
    Argument:
        *user_id/@mentions
        or reply to the user's message

    *user_id: user's telegram id
    """
    user = event.from_user.id
    if not user_is_owner(user):
        return
    try:
        if args and (" " in args or not (args.startswith("@") or args.isdigit())):
            return await event.reply("**Please supply a valid id to unban**")
        elif not (args or event.reply_to_message):
            return await event.reply(
                "**Reply to a message or supply an id to unban the user from using the bot.**"
            )
        ban_id = args or event.reply_to_message.from_user.id
        ban_info = await get_user_info(ban_id)
        if not ban_info:
            return await event.reply("**Invalid user_id**")
        ban_id = str(ban_info.id)
        if user_is_owner(ban_id):
            return await event.reply("**Why?**")
        if user_is_sudoer(ban_id):
            return await event.reply(f"{ban_info.mention()} **is a Sudoer.**")
        if user_is_allowed(ban_id):
            return await event.reply(
                f"{ban_info.mention()} **was never banned from using the bot.**"
            )
        bot.user_dict.setdefault(ban_id, {}).update(banned=False)
        await save2db2(bot.user_dict, "users")
        return await event.reply(f"{ban_info.mention()}'s *ban has been lifted.*")
    except Exception:
        await logger(Exception)


async def disable(event, args, client):
    "Disable bot replies in a group chat."
    if event.chat.type.value == "private":
        return
    try:
        user = event.from_user.id
        user_info = await event.chat.get_member(user)
        if not user_is_privileged(user):
            if not user_info.privileges:
                return await event.reply("`You're not allowed to do this.`")
        chat_id = str(event.chat.id)
        chat_name = event.chat.title
        if not chat_is_allowed(event):
            return await event.reply(
                "Bot has already been disabled in this Group chat."
            )
        bot.group_dict.setdefault(chat_id, {}).update(disabled=True)
        await save2db2(bot.group_dict, "groups")
        await event.reply(
            f"Successfully disabled bot replies in group: **{chat_name}**"
        )
    except Exception:
        await logger(Exception)


async def enable(event, args, client):
    "Enable bot replies in a group chat."
    if not event.chat.is_group:
        return
    try:
        user = event.from_user.id
        user_info = await event.chat.get_member(user)
        if not user_is_privileged(user):
            if not user_info.privileges:
                return await event.reply("`You're not allowed to do this.`")
        chat_id = str(event.chat.id)
        chat_name = event.chat.title
        if chat_is_allowed(event):
            return await event.reply("Bot is already enabled in this Group chat.")
        bot.group_dict.setdefault(chat_id, {}).update(disabled=False)
        await save2db2(bot.group_dict, "groups")
        await event.reply(f"Successfully enabled bot replies in group: **{chat_name}**")
    except Exception:
        await logger(Exception)


async def list_sudoers(event, args, client):
    "Lists the sudoers."
    msg = str()
    for user in bot.user_dict.keys():
        if not bot.user_dict.get(user, {}).get("sudoer", False):
            continue
        info = await get_user_info(user)
        name = info.first_name
        msg += f"\n**⁍** `{name}`"
    if not msg:
        resp = "**No sudoers found.*"
    else:
        resp = f"**List of sudoers:**{msg}"

    for text in split_text(resp):
        event = await event.reply(text)


async def sudoers(event, args, client):
    """
    Modify sudoers
    Arguments:
        -a: Add user to sudoers
        -rm Remove user from sudoers
        {user_id}: ID* of user of user to add to sudoers (can also be specified through a tag); Replying the user message also works

    *ID: user's phone number with country code without spaces or the initial '+'
    """
    user = event.from_user.id
    if not user_is_owner(user):
        return
    try:
        if not args:
            return await list_sudoers(event, args, client)
        arg, args = get_args(
            ["-a", "store_true"],
            ["-rm", "store_true"],
            to_parse=args,
            get_unknown=True,
        )
        if arg.a:
            msg1 = "**Please supply a valid id to add to sudoers*"
            msg2 = "**Reply to a message or supply an id to add the user to sudoers.*"
        elif arg.rm:
            msg1 = "**Please supply a valid id to remove from sudoers*"
            msg2 = (
                "**Reply to a message or supply an id to remove the user from sudoers.*"
            )
        else:
            return await event.reply(getdoc(sudoers))
        if args and (" " in args or not (args.startswith("@") or args.isdigit())):
            return await event.reply(msg1)
        elif not (args or event.reply_to_message):
            return await event.reply(msg2)
        _id = args or event.reply_to_message.from_user.id
        _info = await get_user_info(_id)
        if not _info:
            return await event.reply("**Invalid user_id**")
        _id = str(_info.id)
        if user_is_owner(_id):
            return await event.reply("**Why?**")
        if arg.a:
            if user_is_sudoer(_id):
                return await event.reply(f"{_info.mention()} **is already a Sudoer.**")
            bot.user_dict.setdefault(_id, {}).update(sudoer=True)
        if arg.rm:
            if not user_is_sudoer(_id):
                return await event.reply(f"{_id} **is not a Sudoer.**")
            bot.user_dict.setdefault(_id, {}).update(sudoer=False)
        await save2db2(bot.user_dict, "users")
        await event.reply(
            f"{_id} **has been successfully {'added to' if arg.a else 'removed from'} sudoers.**"
        )
    except Exception:
        await logger(Exception)
