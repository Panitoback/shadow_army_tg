from database import get_connection


def get_xp_for_level(level: int) -> int:
    return level * 100


def register_user(user_id: int, username: str) -> bool:
    """Register a new user. Returns True if new, False if already exists."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if cur.fetchone():
            return False

        cur.execute(
            "INSERT INTO users (id, username) VALUES (%s, %s)",
            (user_id, username)
        )
        cur.execute(
            "INSERT INTO inventory (user_id) VALUES (%s)",
            (user_id,)
        )
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()


def get_user(user_id: int):
    """Returns (id, username, level, experience) or None."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username, level, experience FROM users WHERE id = %s",
            (user_id,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def get_user_by_username(username: str):
    """Returns (id, username, level, experience) or None. Case-insensitive lookup."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username, level, experience FROM users WHERE LOWER(username) = LOWER(%s)",
            (username,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def get_inventory(user_id: int):
    """Returns (wood, stone, water, food, gold) or None."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT wood, stone, water, food, gold FROM inventory WHERE user_id = %s",
            (user_id,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def add_experience(user_id: int, amount: int) -> tuple[bool, int]:
    """
    Add experience to a user and level up if threshold is reached.
    Returns (leveled_up, new_level).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT level, experience FROM users WHERE id = %s",
            (user_id,)
        )
        level, experience = cur.fetchone()
        new_xp = experience + amount
        new_level = level

        while new_xp >= get_xp_for_level(new_level):
            new_xp -= get_xp_for_level(new_level)
            new_level += 1

        cur.execute(
            "UPDATE users SET level = %s, experience = %s WHERE id = %s",
            (new_level, new_xp, user_id)
        )
        conn.commit()
        return new_level > level, new_level
    finally:
        cur.close()
        conn.close()


def get_ranking(limit: int = 10) -> list:
    """Returns list of (username, level, experience) ordered by ranking."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT username, level, experience
               FROM users
               ORDER BY level DESC, experience DESC
               LIMIT %s""",
            (limit,)
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()
