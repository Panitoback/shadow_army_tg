from apscheduler.schedulers.asyncio import AsyncIOScheduler


def setup_scheduler(app) -> AsyncIOScheduler:
    """
    Configures and returns the background task scheduler.
    Pending: notify users when their collection timer is ready.
    """
    scheduler = AsyncIOScheduler()
    # TODO: add notification jobs here
    scheduler.start()
    return scheduler
