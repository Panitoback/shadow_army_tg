import psycopg2
from config import DATABASE_URL


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id BIGINT REFERENCES users(id),
            wood INTEGER DEFAULT 0,
            stone INTEGER DEFAULT 0,
            water INTEGER DEFAULT 0,
            food INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 100,
            PRIMARY KEY (user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS collection_timers (
            user_id BIGINT REFERENCES users(id),
            resource TEXT,
            ends_at TIMESTAMP,
            PRIMARY KEY (user_id, resource)
        )
    """)

    # status: pending | completed | cancelled
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            sender_id BIGINT REFERENCES users(id),
            receiver_id BIGINT REFERENCES users(id),
            resource TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            id SERIAL PRIMARY KEY,
            attacker_id BIGINT REFERENCES users(id),
            defender_id BIGINT REFERENCES users(id),
            winner_id BIGINT REFERENCES users(id),
            attacker_power INTEGER,
            defender_power INTEGER,
            resources_stolen INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # status: active | sold | cancelled
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_offers (
            id SERIAL PRIMARY KEY,
            seller_id BIGINT REFERENCES users(id),
            resource TEXT,
            amount INTEGER,
            price_gold INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
