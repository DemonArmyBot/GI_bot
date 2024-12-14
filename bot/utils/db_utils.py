from pymongo.errors import ServerSelectionTimeoutError

from bot import asyncio, bot_id
from bot.config import bot, conf
from bot.startup.before import miscdb, pickle, rssdb, userdb

from .bot_utils import list_to_str, sync_to_async
from .local_db_utils import save2db_lcl2

# i suck at using database -_-'
# But hey if it works don't touch it
# wanna fix this?
# PRs are welcome

_filter = {"_id": bot_id}

database = conf.DATABASE_URL


async def save2db(db, update, retries=3):
    while retries:
        try:
            await sync_to_async(db.update_one, _filter, {"$set": update}, upsert=True)
            break
        except ServerSelectionTimeoutError as e:
            retries -= 1
            if not retries:
                raise e
            await asyncio.sleep(0.5)


async def save2db2(data: dict | str = False, db: str = None):
    if not database:
        if data is False or db in ("gift", "rss"):
            await sync_to_async(save2db_lcl2, db)
        return
    if data is False:
        busers = list_to_str(bot.banned)
        data = pickle.dumps(busers)
        _update = {"banned_users": data}
        await save2db(userdb, _update)
        return
    p_data = pickle.dumps(data)
    _update = {db: p_data}
    if db == "rss":
        await save2db(rssdb, _update)
        return
    if db == "gift":
        await save2db(miscdb, _update)
        return
