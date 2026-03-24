import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN, PUBLIC_URL
from database import init_db
from handlers.jugador import get_handlers as player_handlers
from handlers.recursos import get_handlers as resource_handlers
from handlers.comercio import get_handlers as trading_handlers
from handlers.batalla import get_handlers as battle_handlers
from api.routes import player, resources

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

bot_app = ApplicationBuilder().token(BOT_TOKEN).build()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()

    for handler in [
        *player_handlers(),
        *resource_handlers(),
        *trading_handlers(),
        *battle_handlers(),
    ]:
        bot_app.add_handler(handler)

    await bot_app.initialize()
    await bot_app.bot.set_webhook(url=f"{PUBLIC_URL}/webhook")
    await bot_app.start()
    logging.info("Bot started with webhook.")

    yield

    # Shutdown
    await bot_app.stop()
    logging.info("Bot stopped.")


app = FastAPI(lifespan=lifespan)

# REST API routes
app.include_router(player.router, prefix="/api")
app.include_router(resources.router, prefix="/api")

# Serve the frontend
app.mount("/", StaticFiles(directory="webapp", html=True), name="webapp")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
