import traceback

from bot import LOGS, bot, conf


async def group_logger(Exception: Exception, e: str):
    if not conf.LOG_GROUP:
        return
    try:
        error = e or traceback.format_exc()
        gc = conf.LOG_GROUP.split(":")
        chat, top_id = map(int, gc) if len(gc) > 1 else (int(gc[0]), None)
        msg = await bot.client.send_message(
            chat,
            f"*#ERROR*\n\n*Summary of what happened:*\n> {error}\n\n*To restict error messages to logs unset the* `conf.LOG_GROUP` *env var*.",
            reply_to_message_id=top_id,
        )
        return msg
    except Exception:
        LOGS.warning(traceback.format_exc())


def log(Exception: Exception = None, e: str = None, critical=False):
    trace = e or traceback.format_exc()
    LOGS.info(trace) if not critical else LOGS.critical(trace)


async def logger(Exception: Exception = None, e: str = None, critical=False):
    log(Exception, e, critical)
    await group_logger(Exception, e)
