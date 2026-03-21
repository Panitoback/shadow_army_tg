import psycopg2
from config import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Inventory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id BIGINT REFERENCES users(id),
            wood INTEGER DEFAULT 0,
            stone INTEGER DEFAULT 0,
            water INTEGER DEFAULT 0,
            food INTEGER DEFAULT 0,
            PRIMARY KEY (user_id)
        )
    """)

    # Collection timers table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS collection_timers (
            user_id BIGINT REFERENCES users(id),
            resource TEXT,
            ends_at TIMESTAMP,
            PRIMARY KEY (user_id, resource)
        )
    """)

    # Transactions table (for future trading)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            sender_id BIGINT REFERENCES users(id),
            receiver_id BIGINT REFERENCES users(id),
            resource TEXT,
            amount INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Battles table (for future combat)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            id SERIAL PRIMARY KEY,
            attacker_id BIGINT REFERENCES users(id),
            defender_id BIGINT REFERENCES users(id),
            winner_id BIGINT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()