from datetime import datetime, timezone, timedelta
from psycopg2 import sql

from database import get_connection
from config import COLLECTION_TIMES, COLLECTION_AMOUNTS

XP_PER_RESOURCE = {
    "wood": 5,
    "stone": 8,
    "water": 3,
    "food": 6,
}


def get_timers(user_id: int) -> dict:
    """Returns a dict of {resource: ends_at} for active timers."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT resource, ends_at FROM collection_timers WHERE user_id = %s",
            (user_id,)
        )
        return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        cur.close()
        conn.close()


def get_resource_status(user_id: int) -> dict:
    """
    Returns the collection status for all resources.
    Possible values: 'idle' | 'ready' | seconds_remaining (int)
    """
    timers = get_timers(user_id)
    now = datetime.now(timezone.utc)
    status = {}

    for resource in COLLECTION_TIMES:
        if resource not in timers:
            status[resource] = "idle"
            continue

        ends_at = timers[resource]
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)

        if now >= ends_at:
            status[resource] = "ready"
        else:
            status[resource] = int((ends_at - now).total_seconds())

    return status


def start_collection(user_id: int, resource: str) -> dict:
    """
    Starts a collection timer for a resource.
    Returns dict with keys: started | already_running | ready_to_collect | error
    """
    if resource not in COLLECTION_TIMES:
        return {"error": "Invalid resource"}

    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now(timezone.utc)
        cur.execute(
            "SELECT ends_at FROM collection_timers WHERE user_id = %s AND resource = %s",
            (user_id, resource)
        )
        row = cur.fetchone()

        if row:
            ends_at = row[0]
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)
            if now < ends_at:
                return {"started": False, "already_running": True, "ends_at": ends_at}
            else:
                return {"started": False, "ready_to_collect": True}

        ends_at = now + timedelta(seconds=COLLECTION_TIMES[resource])
        cur.execute(
            "INSERT INTO collection_timers (user_id, resource, ends_at) VALUES (%s, %s, %s)",
            (user_id, resource, ends_at)
        )
        conn.commit()
        return {"started": True, "ends_at": ends_at}
    finally:
        cur.close()
        conn.close()


def collect_resource(user_id: int, resource: str) -> dict:
    """
    Collects a resource if the timer has finished.
    Returns dict with keys: collected | time_left | no_timer | error
    """
    if resource not in COLLECTION_TIMES:
        return {"error": "Invalid resource"}

    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now(timezone.utc)
        cur.execute(
            "SELECT ends_at FROM collection_timers WHERE user_id = %s AND resource = %s",
            (user_id, resource)
        )
        row = cur.fetchone()

        if not row:
            return {"collected": False, "no_timer": True}

        ends_at = row[0]
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)

        if now < ends_at:
            time_left = int((ends_at - now).total_seconds())
            return {"collected": False, "time_left": time_left}

        amount = COLLECTION_AMOUNTS[resource]
        xp = XP_PER_RESOURCE[resource]

        # Use sql.Identifier to safely inject column name
        cur.execute(
            sql.SQL("UPDATE inventory SET {col} = {col} + %s WHERE user_id = %s").format(
                col=sql.Identifier(resource)
            ),
            (amount, user_id)
        )
        cur.execute(
            "DELETE FROM collection_timers WHERE user_id = %s AND resource = %s",
            (user_id, resource)
        )
        conn.commit()
        return {"collected": True, "amount": amount, "xp": xp}
    finally:
        cur.close()
        conn.close()
