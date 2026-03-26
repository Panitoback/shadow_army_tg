# ResourceWars — Telegram Mini App Game

A resource trading game built as a Telegram Mini App. Players manage a castle, collect resources, trade with each other, level up, and compete on a leaderboard. Designed with scalable modules for a full battle system.

> Portfolio project — demonstrates clean layered architecture, REST API, async Python, and Telegram Mini App integration.

---

## Tech Stack

- **Python 3.11+**
- **FastAPI 0.109** — REST API + webhook server
- **python-telegram-bot 20.7** — bot commands, inline keyboards, and WebApp button
- **PostgreSQL** via psycopg2 (no ORM)
- **APScheduler 3.10.4** — background scheduler for timer notifications
- **httpx 0.25.2** — async HTTP client (installed, not yet used in active code)
- **Vanilla JS / HTML / CSS** — frontend (no build step)
- **Telegram WebApp SDK** — native Mini App integration

---

## Project Structure

```
juego_telegram/
├── main.py                     # Entry point — FastAPI app + webhook + static files + scheduler
├── bot.py                      # Polling alternative (development without ngrok)
├── config.py                   # Environment variables and game constants
├── database.py                 # DB connection and schema initialization (6 tables)
│
├── api/                        # REST API layer
│   ├── auth.py                 # Telegram initData validation (HMAC-SHA256)
│   └── routes/
│       ├── player.py           # GET /api/player/me (auth, auto-registers)
│       │                       # GET /api/ranking   (public, no auth)
│       ├── resources.py        # GET  /api/resources/status
│       │                       # POST /api/resources/{resource}/start
│       │                       # POST /api/resources/{resource}/collect
│       └── market.py           # GET    /api/market
│                               # POST   /api/market/sell
│                               # POST   /api/market/buy/{offer_id}
│                               # DELETE /api/market/{offer_id}
│
├── handlers/                   # Telegram bot command layer
│   ├── player.py               # /start  /profile  /ranking
│   ├── resources.py            # /collect  /inventory
│   │                           # CallbackQueryHandler: collect_start:* collect_take:* collect_wait:*
│   ├── trading.py              # /market  /sell  /buy  /cancel
│   └── battle.py               # [PENDING] /attack  /defense  /history
│
├── services/                   # Business logic (no Telegram, no HTTP)
│   ├── player_service.py       # register_user, get_user, get_inventory, add_experience, get_ranking
│   ├── resources_service.py    # get_resource_status, start_collection, collect_resource
│   ├── trading_service.py      # create_offer, cancel_offer, get_active_offers, buy_offer
│   ├── scheduler.py            # setup_scheduler() — notify_ready_timers job (every 1 min)
│   ├── game_service.py         # [EMPTY] Reserved for future cross-domain logic
│   └── battle_service.py       # [PENDING] Combat resolution, loot calculation
│
├── modules/                    # [UNUSED] Three empty files — not imported anywhere
│
└── webapp/                     # Frontend Mini App (tab-based single page)
    ├── index.html              # Header + tab nav (Resources / Market / Ranking)
    ├── css/style.css           # Dark medieval theme (CSS variables, mobile-first 480px)
    ├── js/
    │   ├── api.js              # Api object — 9 methods, attaches x-init-data header
    │   └── app.js              # Tabs, render, client-side countdown, click handlers
    └── assets/                 # PNG files — emoji fallback if missing
        └── README.md           # Documents required assets and recommended sizes
```

**Architecture rule:** handlers translate Telegram input → call services. API routes validate initData → call services. Services never touch Telegram or HTTP.

---

## How It Works

```
User opens Telegram → sends /start
  → Bot registers user, sends "Play ResourceWars" button
    → Telegram opens webapp/index.html inside the app
      → JS calls Promise.all([/api/player/me, /api/resources/status, /api/ranking, /api/market])
        → FastAPI validates initData (HMAC-SHA256) → calls services → DB
          → UI renders: header, tab nav, resource cards, market offers, ranking
            → Every 1s:  client-side countdown decrements timer buttons (no server request)
            → Every 10s: polls /api/resources/status to sync real state from server
            → APScheduler: every 1 min checks collection_timers, sends Telegram message when ready
```

---

## Database Schema

```sql
users               -- id BIGINT PK, username, level=1, experience=0, created_at
inventory           -- user_id FK, wood=0, stone=0, water=0, food=0, gold=100
collection_timers   -- (user_id, resource) PK, ends_at TIMESTAMP, notified BOOLEAN DEFAULT FALSE
transactions        -- sender_id, receiver_id, resource, amount, status='completed', created_at
battles             -- attacker_id, defender_id, winner_id, attacker_power, defender_power, resources_stolen=0
market_offers       -- seller_id, resource, amount, price_gold, status='active', created_at
```

Key details:
- `inventory.gold` starts at **100** (not 0) for every new player
- `collection_timers.notified` prevents duplicate notifications — set to TRUE after the scheduler sends the message, deleted when the player collects
- `transactions.status` defaults to `'completed'`
- Schema is created with `CREATE TABLE IF NOT EXISTS` — `ALTER TABLE ADD COLUMN IF NOT EXISTS` handles columns added after initial creation
- No ORM — raw psycopg2 with `%s` positional parameters; `psycopg2.sql.Identifier` for safe column name injection

---

## Game Mechanics

### Resource Collection
- 4 resources: Wood, Stone, Water, Food
- Start a timer via bot (`/collect`) or webapp button → wait → collect

| Resource | Cooldown | Amount | XP |
|----------|----------|--------|----|
| Wood     | 1h       | 10     | 5  |
| Stone    | 2h       | 5      | 8  |
| Water    | 30m      | 20     | 3  |
| Food     | 1.5h     | 15     | 6  |

When a timer expires, the APScheduler job sends a Telegram notification to the player.

### Trading
- Any player can create a sell offer: `/sell wood 10 50` (10 wood for 50 gold)
- The resource is deducted from inventory immediately when the offer is created
- Other players browse `/market` or the Market tab and buy with `/buy <id>`
- Gold transfers atomically: buyer loses gold, seller gains gold, buyer gains resource
- Transactions are recorded in the `transactions` table
- Sellers can cancel their own active offers (`/cancel <id>`) to recover the resource

### Leveling
- XP threshold per level: `current_level × 100`
- `add_experience()` handles multiple simultaneous level-ups in a single call
- Level up shown as a red toast notification in the webapp

### Authentication
- All API endpoints except `GET /api/ranking` require the `x-init-data` header
- `GET /api/ranking` is public (no auth needed)
- `GET /api/player/me` auto-registers the user if they open the webapp without `/start` first

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register user and open the Mini App |
| `/profile` | View level, XP, and progress bar |
| `/ranking` | Top 10 players |
| `/collect` | Inline keyboard to start/collect resources |
| `/inventory` | View current resource and gold amounts |
| `/market` | List all active sell offers |
| `/sell <resource> <amount> <price>` | Create a sell offer |
| `/buy <offer_id>` | Buy an active offer |
| `/cancel <offer_id>` | Cancel your own offer |

---

## Setup

### 1. Clone and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/resourcewars
PUBLIC_URL=https://xxxx.ngrok.io
```

### 3. Expose your local server (development)
```bash
.\ngrok.exe http 8000
# Copy the https URL into PUBLIC_URL in your .env
```

### 4. Run
```bash
python main.py
```

> **Alternative (no ngrok):** `python bot.py` uses polling instead of webhook — no `PUBLIC_URL` needed, but the webapp won't be served.

### 5. Add your assets
Place PNG files in `webapp/assets/`:
- `castle.png` — main castle image (400×300 px recommended)
- `wood.png`, `stone.png`, `water.png`, `food.png` — resource icons (64×64 px)

The app shows emoji fallbacks automatically if files are missing.

---

## Planned Modules

### Battle System (next)
- Attack power derived from level + inventory
- Winner steals a portion of loser's resources
- Bot commands: `/attack <username>`, `/defense`, `/history`
- Battle tab in the Mini App with power ranking, attack button, and history

---

## Current Status

- [x] Project architecture defined
- [x] Database schema with all 6 tables
- [x] FastAPI server with webhook
- [x] Telegram Mini App frontend (HTML/CSS/JS, tab-based)
- [x] Telegram initData authentication (HMAC-SHA256, timing-safe)
- [x] User registration (via /start and auto-register on webapp open)
- [x] Resource collection with timers (bot inline keyboard + webapp buttons)
- [x] Client-side countdown (1s visual update, 10s server sync, no flicker)
- [x] XP and leveling system (multi-level-up supported)
- [x] Player ranking (public endpoint)
- [x] Gold inventory (starts at 100 per player)
- [x] APScheduler notifications when collection timer expires
- [x] Trading module (create/cancel/list/buy offers, atomic transfers)
- [ ] Battle module
