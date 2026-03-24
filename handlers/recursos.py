from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from services.recursos_service import get_resource_status, start_collection, collect_resource
from services.jugador_service import add_experience, get_user, get_inventory

RESOURCE_NAMES = {
    "wood": "Wood",
    "stone": "Stone",
    "water": "Water",
    "food": "Food",
}


def format_time(seconds: int) -> str:
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"
    elif seconds >= 60:
        m = seconds // 60
        s = seconds % 60
        return f"{m}m {s}s"
    return f"{seconds}s"


def build_resource_keyboard(user_id: int) -> InlineKeyboardMarkup:
    status = get_resource_status(user_id)
    buttons = []

    for resource, state in status.items():
        name = RESOURCE_NAMES[resource]

        if state == "idle":
            label = f"{name} — Start"
            callback = f"collect_start:{resource}"
        elif state == "ready":
            label = f"{name} — Ready!"
            callback = f"collect_take:{resource}"
        else:
            label = f"{name} — {format_time(state)}"
            callback = f"collect_wait:{resource}"

        buttons.append([InlineKeyboardButton(label, callback_data=callback)])

    return InlineKeyboardMarkup(buttons)


async def cmd_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not get_user(user.id):
        await update.message.reply_text("You must register first with /start")
        return

    keyboard = build_resource_keyboard(user.id)
    await update.message.reply_text(
        "Resource Collection\nSelect a resource:",
        reply_markup=keyboard,
    )


async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user(user_id)

    if not user_data:
        await update.message.reply_text("You must register first with /start")
        return

    inv = get_inventory(user_id)
    _, username, level, _ = user_data
    wood, stone, water, food, gold = inv

    await update.message.reply_text(
        f"Inventory: {username} (Level {level})\n\n"
        f"Wood:  {wood}\n"
        f"Stone: {stone}\n"
        f"Water: {water}\n"
        f"Food:  {food}\n"
        f"Gold:  {gold}"
    )


async def callback_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, resource = query.data.split(":")
    user_id = query.from_user.id

    if action == "collect_wait":
        status = get_resource_status(user_id)
        time_left = status.get(resource)
        if isinstance(time_left, int):
            await query.answer(f"{format_time(time_left)} remaining", show_alert=True)
        return

    if action == "collect_start":
        result = start_collection(user_id, resource)
        name = RESOURCE_NAMES[resource]

        if result.get("started"):
            await query.answer(f"{name} collection started!", show_alert=True)
        elif result.get("already_running"):
            await query.answer("Collection already in progress.", show_alert=True)
        elif result.get("ready_to_collect"):
            await query.answer("Already ready to collect! Use the Ready button.", show_alert=True)

    elif action == "collect_take":
        result = collect_resource(user_id, resource)
        name = RESOURCE_NAMES[resource]

        if result.get("collected"):
            amount = result["amount"]
            xp = result["xp"]
            leveled_up, new_level = add_experience(user_id, xp)
            msg = f"Collected {amount} {name}! (+{xp} XP)"
            if leveled_up:
                msg += f"\nLevel up! You are now level {new_level}!"
            await query.answer(msg, show_alert=True)

        elif result.get("time_left"):
            await query.answer(
                f"{format_time(result['time_left'])} remaining", show_alert=True
            )
        elif result.get("no_timer"):
            await query.answer("No active collection.", show_alert=True)

    # Refresh the keyboard with updated status
    keyboard = build_resource_keyboard(user_id)
    try:
        await query.edit_message_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


def get_handlers():
    return [
        CommandHandler("collect", cmd_collect),
        CommandHandler("inventory", cmd_inventory),
        CallbackQueryHandler(callback_collect, pattern="^collect_"),
    ]
