import random

from psycopg2 import sql

from database import get_connection

LOOT_PERCENTAGE = 0.20
POWER_RANDOMNESS = 0.20  # ±20% random factor applied to each side

# How much each resource unit contributes to power
RESOURCE_POWER_WEIGHTS = {
    "wood": 1,
    "stone": 2,
    "water": 1,
    "food": 1,
}


def calculate_power(user_id: int) -> int:
    """
    Calculate a player's combat power.
    Formula: level * 10 + (weighted resource sum) // 2
    Returns 0 if the user does not exist.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT level FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            return 0
        level = row[0]

        cur.execute(
            "SELECT wood, stone, water, food FROM inventory WHERE user_id = %s",
            (user_id,),
        )
        inv = cur.fetchone()
        if not inv:
            return level * 10

        wood, stone, water, food = inv
        resource_power = (
            wood * RESOURCE_POWER_WEIGHTS["wood"]
            + stone * RESOURCE_POWER_WEIGHTS["stone"]
            + water * RESOURCE_POWER_WEIGHTS["water"]
            + food * RESOURCE_POWER_WEIGHTS["food"]
        )
        return level * 10 + resource_power // 2
    finally:
        cur.close()
        conn.close()


def resolve_battle(attacker_id: int, defender_id: int) -> dict:
    """
    Resolve a battle between two players atomically.
    - Applies ±20% random factor to each side's power.
    - Winner steals LOOT_PERCENTAGE of each of the loser's resources.
    - Records the battle in the battles table.

    Returns dict with keys:
        battle_id, winner_id, loser_id, attacker_power, defender_power,
        resources_stolen, loot {resource: amount}
    On error: {error: str}
    """
    if attacker_id == defender_id:
        return {"error": "You cannot attack yourself"}

    attacker_power = calculate_power(attacker_id)
    defender_power = calculate_power(defender_id)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE id = %s", (defender_id,))
        if not cur.fetchone():
            return {"error": "Target player not found"}

        eff_attacker = attacker_power * random.uniform(
            1 - POWER_RANDOMNESS, 1 + POWER_RANDOMNESS
        )
        eff_defender = defender_power * random.uniform(
            1 - POWER_RANDOMNESS, 1 + POWER_RANDOMNESS
        )

        if eff_attacker >= eff_defender:
            winner_id = attacker_id
            loser_id = defender_id
        else:
            winner_id = defender_id
            loser_id = attacker_id

        loot, resources_stolen = _apply_loot(cur, winner_id, loser_id)
        battle_id = _record_battle(
            cur, attacker_id, defender_id, winner_id,
            attacker_power, defender_power, resources_stolen,
        )
        conn.commit()

        return {
            "battle_id": battle_id,
            "winner_id": winner_id,
            "loser_id": loser_id,
            "attacker_power": attacker_power,
            "defender_power": defender_power,
            "resources_stolen": resources_stolen,
            "loot": loot,
        }
    finally:
        cur.close()
        conn.close()


def _apply_loot(cur, winner_id: int, loser_id: int) -> tuple[dict, int]:
    """
    Transfer LOOT_PERCENTAGE of each resource from loser to winner.
    Runs within the caller's transaction (shares cursor).
    Returns (loot_dict, total_stolen).
    """
    cur.execute(
        "SELECT wood, stone, water, food FROM inventory WHERE user_id = %s",
        (loser_id,),
    )
    row = cur.fetchone()
    if not row:
        return {}, 0

    wood, stone, water, food = row
    loot = {
        "wood": int(wood * LOOT_PERCENTAGE),
        "stone": int(stone * LOOT_PERCENTAGE),
        "water": int(water * LOOT_PERCENTAGE),
        "food": int(food * LOOT_PERCENTAGE),
    }
    total_stolen = sum(loot.values())

    for resource, amount in loot.items():
        if amount > 0:
            cur.execute(
                sql.SQL(
                    "UPDATE inventory SET {col} = {col} - %s WHERE user_id = %s"
                ).format(col=sql.Identifier(resource)),
                (amount, loser_id),
            )
            cur.execute(
                sql.SQL(
                    "UPDATE inventory SET {col} = {col} + %s WHERE user_id = %s"
                ).format(col=sql.Identifier(resource)),
                (amount, winner_id),
            )

    return loot, total_stolen


def _record_battle(
    cur,
    attacker_id: int,
    defender_id: int,
    winner_id: int,
    attacker_power: int,
    defender_power: int,
    resources_stolen: int,
) -> int:
    """Insert the battle row and return the new battle id."""
    cur.execute(
        """
        INSERT INTO battles
            (attacker_id, defender_id, winner_id, attacker_power, defender_power, resources_stolen)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (attacker_id, defender_id, winner_id, attacker_power, defender_power, resources_stolen),
    )
    return cur.fetchone()[0]


def get_battle_history(user_id: int) -> list:
    """
    Return the last 20 battles where the user was attacker or defender.
    Each row: (id, attacker_username, defender_username, winner_id,
               attacker_power, defender_power, resources_stolen, created_at)
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                b.id,
                ua.username AS attacker_username,
                ud.username AS defender_username,
                b.winner_id,
                b.attacker_power,
                b.defender_power,
                b.resources_stolen,
                b.created_at
            FROM battles b
            JOIN users ua ON ua.id = b.attacker_id
            JOIN users ud ON ud.id = b.defender_id
            WHERE b.attacker_id = %s OR b.defender_id = %s
            ORDER BY b.created_at DESC
            LIMIT 20
            """,
            (user_id, user_id),
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()
