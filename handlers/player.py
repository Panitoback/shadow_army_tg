from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from config import PUBLIC_URL
from services.player_service import register_user, get_user, get_xp_for_level, get_ranking


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or user.first_name)

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="Play ResourceWars",
            web_app=WebAppInfo(url=f"{PUBLIC_URL}/")
        )
    ]])

    await update.message.reply_text(
        f"Welcome to ResourceWars, {user.first_name}!\n"
        "Tap the button below to open the game.",
        reply_markup=keyboard,
    )


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)

    if not data:
        await update.message.reply_text("Register first with /start")
        return

    _, username, level, experience = data
    xp_needed = get_xp_for_level(level)
    progress = int((experience / xp_needed) * 10)
    bar = "█" * progress + "░" * (10 - progress)

    await update.message.reply_text(
        f"Profile: {username}\n\n"
        f"Level: {level}\n"
        f"XP: {experience}/{xp_needed}\n"
        f"[{bar}]"
    )


async def cmd_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = get_ranking()

    if not ranking:
        await update.message.reply_text("No players in the ranking yet.")
        return

    lines = ["Player Ranking\n"]
    medals = ["1.", "2.", "3."]

    for i, (username, level, experience) in enumerate(ranking):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {username} — Level {level} ({experience} XP)")

    await update.message.reply_text("\n".join(lines))


def get_handlers():
    return [
        CommandHandler("start", cmd_start),
        CommandHandler("profile", cmd_profile),
        CommandHandler("ranking", cmd_ranking),
    ]
