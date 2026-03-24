from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.jugador_service import (
    register_user,
    get_user,
    get_xp_for_level,
    get_ranking,
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = register_user(user.id, user.username or user.first_name)

    if is_new:
        await update.message.reply_text(
            f"Welcome to ResourceWars, {user.first_name}!\n\n"
            "Your adventure begins with 100 gold.\n\n"
            "Available commands:\n"
            "/collect — gather resources\n"
            "/inventory — view your resources\n"
            "/profile — view your profile\n"
            "/ranking — view top players"
        )
    else:
        await update.message.reply_text(
            f"Welcome back, {user.first_name}!\n"
            "Use /inventory to check your resources."
        )


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)

    if not data:
        await update.message.reply_text("You must register first with /start")
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

    medals = ["1.", "2.", "3."]
    lines = ["Player Ranking\n"]

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
