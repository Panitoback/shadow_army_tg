from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.battle_service import calculate_power, get_battle_history, resolve_battle
from services.player_service import get_user, get_user_by_username

RESOURCE_NAMES = {
    "wood": "Wood",
    "stone": "Stone",
    "water": "Water",
    "food": "Food",
}


async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attacker_id = update.effective_user.id

    if not get_user(attacker_id):
        await update.message.reply_text("Register first with /start")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /attack <username>\nExample: /attack playerX")
        return

    target_username = context.args[0].lstrip("@")
    target = get_user_by_username(target_username)
    if not target:
        await update.message.reply_text(f"Player '{target_username}' not found.")
        return

    defender_id = target[0]
    result = resolve_battle(attacker_id, defender_id)

    if result.get("error"):
        await update.message.reply_text(f"Error: {result['error']}")
        return

    attacker_data = get_user(attacker_id)
    attacker_username = attacker_data[1] if attacker_data else "You"

    won = result["winner_id"] == attacker_id
    outcome_line = "Victory! You won the battle." if won else "Defeat. You lost the battle."

    loot_lines = []
    if won and result.get("loot"):
        stolen = {r: a for r, a in result["loot"].items() if a > 0}
        if stolen:
            parts = [f"{a} {RESOURCE_NAMES.get(r, r)}" for r, a in stolen.items()]
            loot_lines.append(f"Loot stolen: {', '.join(parts)}")
        else:
            loot_lines.append("The defender had no resources to steal.")
    elif not won and result.get("loot"):
        stolen = {r: a for r, a in result["loot"].items() if a > 0}
        if stolen:
            parts = [f"{a} {RESOURCE_NAMES.get(r, r)}" for r, a in stolen.items()]
            loot_lines.append(f"Resources lost: {', '.join(parts)}")

    lines = [
        outcome_line,
        "",
        f"vs {target[1]}",
        f"Your power: {result['attacker_power']}  |  Their power: {result['defender_power']}",
    ] + loot_lines

    await update.message.reply_text("\n".join(lines))


async def cmd_defense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)

    if not data:
        await update.message.reply_text("Register first with /start")
        return

    _, username, level, _ = data
    power = calculate_power(user_id)
    base_power = level * 10
    resource_contribution = power - base_power

    await update.message.reply_text(
        f"Defense stats for {username}\n\n"
        f"Combat power: {power}\n"
        f"  Level bonus:     {base_power}  (level {level} × 10)\n"
        f"  Resource bonus:  {resource_contribution}  (weighted resources // 2)\n\n"
        "Stone counts double. Higher power = better odds.\n"
        "Note: each battle applies a ±20% random factor."
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not get_user(user_id):
        await update.message.reply_text("Register first with /start")
        return

    battles = get_battle_history(user_id)
    if not battles:
        await update.message.reply_text("You have no battle history yet.")
        return

    lines = ["Battle History (last 20)\n"]
    for row in battles:
        battle_id, attacker_username, defender_username, winner_id, \
            attacker_power, defender_power, resources_stolen, created_at = row

        you_won = winner_id == user_id
        result_tag = "W" if you_won else "L"
        date_str = created_at.strftime("%m/%d %H:%M") if created_at else "?"

        lines.append(
            f"[{result_tag}] #{battle_id} {attacker_username} vs {defender_username} "
            f"({attacker_power}v{defender_power}) stolen:{resources_stolen}  {date_str}"
        )

    await update.message.reply_text("\n".join(lines))


def get_handlers():
    return [
        CommandHandler("attack", cmd_attack),
        CommandHandler("defense", cmd_defense),
        CommandHandler("history", cmd_history),
    ]
