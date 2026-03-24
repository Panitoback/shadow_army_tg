import logging

from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN
from database import init_db
from handlers.jugador import get_handlers as player_handlers
from handlers.recursos import get_handlers as resource_handlers
from handlers.comercio import get_handlers as trading_handlers
from handlers.batalla import get_handlers as battle_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    for handler in [
        *player_handlers(),
        *resource_handlers(),
        *trading_handlers(),
        *battle_handlers(),
    ]:
        app.add_handler(handler)

    logging.info("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
