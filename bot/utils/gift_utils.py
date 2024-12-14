import asyncio

from bot.config import bot, conf

from .bot_utils import get_json
from .db_utils import save2db2
from .log_utils import log
from .msg_utils import get_msg_from_codes, send_rss


async def gift_code_monitor():
    try:
        if not bot.gift_dict["chats"]:
            return
        response = await get_json("https://hoyo-codes.seria.moe/codes?game=genshin")
        new_codes = []
        _to_db = []
        for codes in response.get("codes"):
            if codes.get("id") == 43:
                continue
            if codes.get("code") in bot.gift_dict["codes"]:
                continue
            _to_db.append(codes.get("code"))
            new_codes.append(codes)
        if not new_codes:
            return
        msg = get_msg_from_codes(new_codes, auto=True)
        expanded_chat = []
        for chat in bot.gift_dict["chats"]:
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
            try:

                await send_rss(msg, chat, None, [], top_id)
                await asyncio.sleep(5)
            except Exception:
                log(Exception)
        bot.gift_dict["codes"].extend(_to_db)
        await save2db2(bot.gift_dict, "gift")
        log(e="Found and sent new codes to chat!")
    except Exception:
        log(Exception)
