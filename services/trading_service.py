from psycopg2 import sql

from database import get_connection

VALID_RESOURCES = {"wood", "stone", "water", "food"}


def create_offer(user_id: int, resource: str, amount: int, price_gold: int) -> dict:
    """
    Create a sell offer. Deducts the resource from the seller's inventory immediately.
    Returns: {created: True, offer_id} | {error: str}
    """
    if resource not in VALID_RESOURCES:
        return {"error": "Invalid resource"}
    if amount <= 0 or price_gold <= 0:
        return {"error": "Amount and price must be positive"}

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            sql.SQL("SELECT {col} FROM inventory WHERE user_id = %s").format(
                col=sql.Identifier(resource)
            ),
            (user_id,),
        )
        row = cur.fetchone()
        if not row or row[0] < amount:
            return {"error": "Not enough resources"}

        cur.execute(
            sql.SQL("UPDATE inventory SET {col} = {col} - %s WHERE user_id = %s").format(
                col=sql.Identifier(resource)
            ),
            (amount, user_id),
        )
        cur.execute(
            """
            INSERT INTO market_offers (seller_id, resource, amount, price_gold)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (user_id, resource, amount, price_gold),
        )
        offer_id = cur.fetchone()[0]
        conn.commit()
        return {"created": True, "offer_id": offer_id}
    finally:
        cur.close()
        conn.close()


def cancel_offer(user_id: int, offer_id: int) -> dict:
    """
    Cancel the user's own offer and return the resource to their inventory.
    Returns: {cancelled: True} | {error: str}
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT seller_id, resource, amount, status FROM market_offers WHERE id = %s",
            (offer_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Offer not found"}

        seller_id, resource, amount, status = row
        if seller_id != user_id:
            return {"error": "That offer is not yours"}
        if status != "active":
            return {"error": "Offer is no longer active"}

        cur.execute(
            sql.SQL("UPDATE inventory SET {col} = {col} + %s WHERE user_id = %s").format(
                col=sql.Identifier(resource)
            ),
            (amount, user_id),
        )
        cur.execute(
            "UPDATE market_offers SET status = 'cancelled' WHERE id = %s",
            (offer_id,),
        )
        conn.commit()
        return {"cancelled": True}
    finally:
        cur.close()
        conn.close()


def get_active_offers() -> list:
    """
    Returns all active offers.
    Each row: (id, seller_id, username, resource, amount, price_gold)
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT mo.id, mo.seller_id, u.username, mo.resource, mo.amount, mo.price_gold
            FROM market_offers mo
            JOIN users u ON u.id = mo.seller_id
            WHERE mo.status = 'active'
            ORDER BY mo.created_at ASC
            """
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def buy_offer(buyer_id: int, offer_id: int) -> dict:
    """
    Buy an active offer. Transfers resources and gold atomically.
    Returns: {bought: True, resource, amount, price_gold} | {error: str}
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT seller_id, resource, amount, price_gold, status FROM market_offers WHERE id = %s",
            (offer_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Offer not found"}

        seller_id, resource, amount, price_gold, status = row

        if status != "active":
            return {"error": "Offer is no longer available"}
        if seller_id == buyer_id:
            return {"error": "You cannot buy your own offer"}

        cur.execute("SELECT gold FROM inventory WHERE user_id = %s", (buyer_id,))
        gold_row = cur.fetchone()
        if not gold_row or gold_row[0] < price_gold:
            return {"error": "Not enough gold"}

        # Transfer gold: buyer → seller
        cur.execute(
            "UPDATE inventory SET gold = gold - %s WHERE user_id = %s",
            (price_gold, buyer_id),
        )
        cur.execute(
            "UPDATE inventory SET gold = gold + %s WHERE user_id = %s",
            (price_gold, seller_id),
        )

        # Transfer resource: market → buyer
        cur.execute(
            sql.SQL("UPDATE inventory SET {col} = {col} + %s WHERE user_id = %s").format(
                col=sql.Identifier(resource)
            ),
            (amount, buyer_id),
        )

        cur.execute(
            "UPDATE market_offers SET status = 'sold' WHERE id = %s",
            (offer_id,),
        )
        cur.execute(
            """
            INSERT INTO transactions (sender_id, receiver_id, resource, amount, status)
            VALUES (%s, %s, %s, %s, 'completed')
            """,
            (seller_id, buyer_id, resource, amount),
        )
        conn.commit()
        return {"bought": True, "resource": resource, "amount": amount, "price_gold": price_gold}
    finally:
        cur.close()
        conn.close()
