from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.player_service import get_user
from services.trading_service import buy_offer, cancel_offer, create_offer, get_active_offers

RESOURCE_NAMES = {
    "wood": "Wood",
    "stone": "Stone",
    "water": "Water",
    "food": "Food",
}


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offers = get_active_offers()
    if not offers:
        await update.message.reply_text("No active offers in the market.")
        return

    lines = ["Market — Active Offers\n"]
    for offer_id, _seller_id, username, resource, amount, price_gold in offers:
        name = RESOURCE_NAMES.get(resource, resource.capitalize())
        lines.append(f"#{offer_id} | {name} x{amount} → {price_gold} gold  (by {username})")

    lines.append("\nUse /buy <id> to purchase.")
    await update.message.reply_text("\n".join(lines))


async def cmd_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Register first with /start")
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            "Usage: /sell <resource> <amount> <price>\nExample: /sell wood 10 50"
        )
        return

    resource = context.args[0].lower()
    try:
        amount = int(context.args[1])
        price_gold = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Amount and price must be whole numbers.")
        return

    result = create_offer(user_id, resource, amount, price_gold)
    if result.get("created"):
        name = RESOURCE_NAMES.get(resource, resource.capitalize())
        await update.message.reply_text(
            f"Offer #{result['offer_id']} created!\n{name} x{amount} for {price_gold} gold."
        )
    else:
        await update.message.reply_text(f"Error: {result['error']}")


async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Register first with /start")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /buy <offer_id>\nExample: /buy 3")
        return

    try:
        offer_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Offer ID must be a number.")
        return

    result = buy_offer(user_id, offer_id)
    if result.get("bought"):
        name = RESOURCE_NAMES.get(result["resource"], result["resource"].capitalize())
        await update.message.reply_text(
            f"Purchase complete!\nYou got {result['amount']} {name} for {result['price_gold']} gold."
        )
    else:
        await update.message.reply_text(f"Error: {result['error']}")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Register first with /start")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /cancel <offer_id>\nExample: /cancel 3")
        return

    try:
        offer_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Offer ID must be a number.")
        return

    result = cancel_offer(user_id, offer_id)
    if result.get("cancelled"):
        await update.message.reply_text(
            f"Offer #{offer_id} cancelled. Resources returned to your inventory."
        )
    else:
        await update.message.reply_text(f"Error: {result['error']}")


def get_handlers():
    return [
        CommandHandler("market", cmd_market),
        CommandHandler("sell", cmd_sell),
        CommandHandler("buy", cmd_buy),
        CommandHandler("cancel", cmd_cancel),
    ]
