import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_connection

logger = logging.getLogger(__name__)

RESOURCE_LABELS = {
    "wood": "Wood",
    "stone": "Stone",
    "water": "Water",
    "food": "Food",
}


async def notify_ready_timers(bot) -> None:
    """Check for expired timers and notify each user once via Telegram."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now(timezone.utc)
        cur.execute(
            """
            SELECT user_id, resource FROM collection_timers
            WHERE ends_at <= %s AND notified = FALSE
            """,
            (now,),
        )
        rows = cur.fetchall()

        for user_id, resource in rows:
            label = RESOURCE_LABELS.get(resource, resource.capitalize())
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"Your {label} is ready to collect! Use /collect",
                )
                cur.execute(
                    """
                    UPDATE collection_timers SET notified = TRUE
                    WHERE user_id = %s AND resource = %s
                    """,
                    (user_id, resource),
                )
            except Exception:
                # User may have blocked the bot — skip silently
                logger.warning("Could not notify user %s for %s", user_id, resource)

        conn.commit()
    finally:
        cur.close()
        conn.close()


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notify_ready_timers,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="notify_timers",
    )
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler
