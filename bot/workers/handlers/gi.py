import asyncio
import io
import itertools

import requests
from bs4 import BeautifulSoup
from PIL import Image

from bot.utils.gi_utils import (
    enka_update,
    get_enka_card,
    get_enka_card2,
    get_enka_profile,
    get_enka_profile2,
    get_gi_info,
)
from bot.utils.log_utils import log, logger
from bot.utils.msg_utils import (
    clean_reply,
    get_args,
    pm_is_allowed,
    user_is_allowed,
    user_is_owner,
)
from bot.utils.os_utils import s_remove


async def enka_handler(event, args, client):
    """
    Get a players's character build card from enka
    Requires character build for the specified uid to be public

    Arguments:
    uid: {genshin player uid} (Required)
    -c or --card {character name}: use quotes if the name has spaces eg:- "Hu tao"; Also supports lookups
    -cs or --cards {characters} same as -c but for multiple characters; delimited by commas
    -t <int> {template}: card generation template; currently only two templates exist; default 1
    Flags:
    -v2: Get cards in new template
    -d or --dump: Dump all character build from the given uid
    -p or --profile: To get player card instead
    --hide_uid: Hide uid in card
    --no_top: Remove akasha ranking from card
    --update: update library

    Examples:
    123454697855 -c "Hu tao" -t 2 --hide_uid
        - retrieves the current build for Hu tao from the given uid with uid hidden while using the second template
    123456789 -p -t 2
        - retrieves profile card using the second template for the given uid
    12345678900 -c xq
        - retrieves the current build for whatever matches the character name provided; in this case Xingqui
    """
    error = None
    status = None
    user = event.from_user.id
    if not user_is_owner(user):
        if not pm_is_allowed(event):
            return
        if not user_is_allowed(user):
            return
    try:
        arg, args = get_args(
            ["--hide_uid", "store_true"],
            ["--no_top", "store_false"],
            ["--update", "store_true"],
            "-c",
            "-cs",
            "--card",
            "--cards",
            ["-d", "store_true"],
            ["--dump", "store_true"],
            ["-p", "store_true"],
            ["--profile", "store_true"],
            ["-v2", "store_true"],
            "-t",
            to_parse=args,
            get_unknown=True,
        )
        card = arg.c or arg.card
        cards = arg.cs or arg.cards
        dump = arg.d or arg.dump
        prof = arg.p or arg.profile
        akasha = arg.no_top
        reply = event.reply_to_message
        if arg.update:
            u_reply = await event.reply("`Updating enka assets…`")
            await enka_update()
            if not (card or cards or dump or prof):
                return await u_reply.edit("Updated enka assets.")
            await u_reply.delete()
        if not (card or cards or dump or prof):
            return await event.reply(f"```{enka_handler.__doc__}```")
        if arg.t not in ("1", "2"):
            arg.t = 1
        profile, error = await get_enka_profile(args)
        if error:
            result = profile
            return
        status = await event.reply("`Fetching card(s), Please Wait…`")
        if prof:
            cprofile, error = (
                await get_enka_profile(args, card=True, template=arg.t)
                if not arg.v2
                else await get_enka_profile2(args, huid=arg.hide_uid)
            )
            if error:
                return
            caption = f"{profile.player.name}'s profile"
            file_name = caption + ".png"
            path = "enka/" + file_name
            cprofile.card.save(path)
            await clean_reply(
                event, reply, "reply_photo", photo=path, caption=f"**{caption}**"
            )
            return s_remove(path)
        if card:
            info = await get_gi_info(query=card)
            if not info:
                return await event.reply(
                    f"**Character not found.**\nYou searched for {card}.\nNot what you searched for?\nTry again with double quotes"
                )
            char_id = info.get("id")
            result, error = (
                await get_enka_card(
                    args, char_id, akasha=akasha, huid=arg.hide_uid, template=arg.t
                )
                if not arg.v2
                else await get_enka_card2(args, char_id, arg.hide_uid)
            )
            if error:
                return
            caption = f"{profile.player.name}'s current {info.get('name')} build"
            file_name = caption + ".png"
            path = "enka/" + file_name
            if not result.card:
                error = f"**{card} not found in showcase!**"
                return
            result.card[0].card.save(path)
            await clean_reply(
                event, reply, "reply_photo", photo=path, caption=f"**{caption}**"
            )
            return s_remove(path)
        if cards:
            ids = str()
            errors = str()
            for name in cards.split(","):
                name = name.strip()
                info = await get_gi_info(query=name)
                if not info:
                    errors += f"{name}, "
                    continue
                char_id = info.get("id")
                ids += f"{char_id},"
            errors = errors.strip(", ")
            error_txt = f"**Character(s) not found.**\nYou searched for {errors}.\nNot what you searched for?\nTry again with double quotes"
            if not ids:
                return await event.reply(error_txt)
            ids = ids.strip(",")
            result, error = (
                await get_enka_card(
                    args, ids, akasha=akasha, huid=arg.hide_uid, template=arg.t
                )
                if not arg.v2
                else await get_enka_card2(args, ids, huid=arg.hide_uid)
            )
            if error:
                return

            if errors:
                await event.reply(error_txt)
            return await send_multi_cards(event, reply, result, profile)
        if dump:
            result, error = (
                await get_enka_card(
                    args, None, akasha=akasha, huid=arg.hide_uid, template=arg.t
                )
                if not arg.v2
                else await get_enka_card2(args, str(), huid=arg.hide_uid)
            )
            if error:
                return
            return await send_multi_cards(event, reply, result, profile)
    except Exception:
        await logger(Exception)
    finally:
        if status:
            return await status.delete()
        if error:
            return await event.reply(f"**Error:**\n{result}")


async def send_multi_cards(event, reply, results, profile):
    chain = event
    for card in results.card:
        print(card.name)  # best debugger?
        caption = f"{profile.player.name}'s current {card.name} build"
        file_name = caption + ".png"
        path = "enka/" + file_name
        card.card.save(path)
        chain = await clean_reply(
            chain, reply, "reply_photo", photo=path, caption=f"**{caption}**"
        )
        reply = None
        await asyncio.sleep(3)
        s_remove(path)


async def weapon_handler(event, args, client):
    """
    Fetch specified genshin weapon details;
    Args:
        Name of weapon.
    """
    user = event.from_user.id
    if not user_is_owner(user):
        if not pm_is_allowed(event):
            return
        if not user_is_allowed(user):
            return
    try:
        reply = event.reply_to_message
        weapon = await get_gi_info("weapons", args)
        if not weapon:
            return await event.reply(
                f"**Weapon not found.**\nYou searched for `{args}`."
            )
        weapon_stats = await get_gi_info("weapons", args, stats=True)
        pic, caption = fetch_weapon_detail(weapon, weapon_stats)
        await clean_reply(event, reply, "reply_photo", photo=pic, caption=caption)
    except Exception:
        await logger(Exception)


def fetch_weapon_detail(weapon: dict, weapon_stats: dict) -> tuple:
    name = weapon.get("name")
    des = weapon.get("description")
    rarity = weapon.get("rarity")
    max_level = "90" if rarity > 2 else "70"
    typ = weapon.get("weaponText")
    base_atk = round(weapon.get("baseAtkValue"))
    main_stat = weapon.get("mainStatText", str())
    base_stat = weapon.get("baseStatText", str())
    effect_name = weapon.get("effectName", str())
    effects = weapon.get("effectTemplateRaw", str())
    if effects:
        effects = BeautifulSoup(effects, "html.parser").text
        r1 = weapon["r1"]["values"] if weapon.get("r1") else []
        r2 = weapon["r2"]["values"] if weapon.get("r2") else []
        r3 = weapon["r3"]["values"] if weapon.get("r3") else []
        r4 = weapon["r4"]["values"] if weapon.get("r4") else []
        r5 = weapon["r5"]["values"] if weapon.get("r5") else []
        key = [f"{a}/{b}/{c}/{d}/{e}".split("/None", maxsplit=1)[0] for a, b, c, d, e in itertools.zip_longest(r1, r2, r3, r4, r5)]
        effects = effects.format(*key)
    img_suf = weapon["images"]["filename_gacha"]
    img = add_background(img_suf, rarity, name)
    max_stats = weapon_stats[max_level]
    max_base_atk = round(max_stats.get("attack"))
    max_main_stat = max_stats.get("specialized")
    if main_stat:
        if max_main_stat > 1:
            max_main_stat = round(max_main_stat)
        else:
            max_main_stat = f"{(round(max_main_stat) * 100)}%"
    caption = f"**{name}**\n"
    caption += f"{'⭐' * rarity}\n\n"
    caption += f"**Rarity:** `{'★' * rarity}`\n"
    caption += f"**Type:** `{typ}`\n"
    caption += f"**Base ATK:** `{base_atk}` ➜ `{max_base_atk}` __(Lvl {max_level})__\n"
    if main_stat:
        caption += f"**{main_stat}:** `{base_stat}` ➜ `{max_main_stat}` __(Lvl {max_level})__\n"
    caption += f"`{(des[:2000] + '…') if len(des) > 2000 else des}`\n\n"
    if effects:
        log(e=effects)
        caption += f"**{effect_name}** +\n"
        caption += f"```{effects}```"

    return img, caption


def add_background(image_suf: str, rarity: int, name: str = "weapon"):
    """Fetches image and adds a background.

    Args:
        image_suf: identifier for image.
        rarity: rarity of item
    """
    # Dict for associating rarity with background color
    color = {
        1: (126, 126, 128, 255),
        2: (78, 126, 110, 255),
        3: (84, 134, 169, 255),
        4: (127, 103, 161, 255),
        5: (176, 112, 48, 255),
    }

    # Download the image
    image_url = f"https://gi.yatta.moe/assets/UI/{image_suf}.png"
    response = requests.get(image_url, stream=True)
    response.raise_for_status()

    # Create an Image object from the downloaded content
    img = Image.open(response.raw)

    # Create a gold/purple/blue/green/white background image with the same
    # size as the input image
    background = Image.new("RGBA", img.size, color.get(rarity))  # color with alpha

    # Paste the input image onto the background
    background.paste(img, (0, 0), img)

    # Save the output image
    output = io.BytesIO()
    background.save(output, format="png")
    output.name = f"{name}.png"
    return output
