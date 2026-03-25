# ResourceWars — Telegram Mini App Game

A resource trading game built as a Telegram Mini App. Players manage a castle, collect resources, level up, and compete on a leaderboard. Designed with scalable modules for player-to-player trading and a battle system.

> Portfolio project — demonstrates clean layered architecture, REST API, async Python, and Telegram Mini App integration.

---

## Tech Stack

- **Python 3.11+**
- **FastAPI 0.109** — REST API + webhook server
- **python-telegram-bot 20.7** — bot commands, inline keyboards, and WebApp button
- **PostgreSQL** via psycopg2 (no ORM)
- **APScheduler 3.10.4** — background task scheduler (installed, pending integration)
- **httpx 0.25.2** — async HTTP client (installed, not yet used)
- **Vanilla JS / HTML / CSS** — frontend (no build step)
- **Telegram WebApp SDK** — native Mini App integration

---

## Project Structure

```
juego_telegram/
├── main.py                     # Entry point — FastAPI app + webhook + static files
├── bot.py                      # Polling alternative (development without ngrok)
├── config.py                   # Environment variables and game constants
├── database.py                 # DB connection and schema initialization (6 tables)
├── scheduler.py                # [NOT CONNECTED] APScheduler setup at root — not imported
│
├── api/                        # REST API layer
│   ├── auth.py                 # Telegram initData validation (HMAC-SHA256)
│   └── routes/
│       ├── player.py           # GET /api/player/me (auth required, auto-registers)
│       │                       # GET /api/ranking   (public, no auth)
│       └── resources.py        # GET  /api/resources/status        (auth required)
│                               # POST /api/resources/{resource}/start   (auth required)
│                               # POST /api/resources/{resource}/collect (auth required)
│
├── handlers/                   # Telegram bot command layer
│   ├── player.py               # /start  /profile  /ranking
│   ├── resources.py            # /collect  /inventory
│   │                           # CallbackQueryHandler: collect_start:* collect_take:* collect_wait:*
│   ├── trading.py              # [PENDING] /market  /sell  /buy  /cancel
│   └── battle.py               # [PENDING] /attack  /defense  /history
│
├── services/                   # Business logic (no Telegram, no HTTP)
│   ├── player_service.py       # register_user, get_user, get_inventory, add_experience, get_ranking
│   ├── resources_service.py    # get_resource_status, start_collection, collect_resource
│   ├── scheduler.py            # [NOT CONNECTED] APScheduler setup — not imported by main.py
│   ├── game_service.py         # [EMPTY] Reserved for future cross-domain logic
│   ├── trading_service.py      # [PENDING] Market offers, resource transfers
│   └── battle_service.py       # [PENDING] Combat resolution, loot calculation
│
├── modules/                    # [UNUSED] Three empty files — not imported anywhere
│
└── webapp/                     # Frontend Mini App (single scrollable page)
    ├── index.html              # Header, castle, gold, resource grid, ranking
    ├── css/style.css           # Dark medieval theme (CSS variables, mobile-first 480px)
    ├── js/
    │   ├── api.js              # Api object — 5 methods, attaches x-init-data header
    │   └── app.js              # Render, timers, click handlers, 10s polling loop
    └── assets/                 # PNG files — emoji fallback if missing
        └── README.md           # Documents required assets and recommended sizes
```

**Architecture rule:** handlers translate Telegram input → call services. API routes validate initData → call services. Services never touch Telegram or HTTP.

**Note:** `api/routes/resources.py` imports from both `resources_service` and `player_service` (to grant XP on collect). This is intentional — both the bot handler and the API route correctly grant XP through the same service call.

---

## How It Works

```
User opens Telegram → sends /start
  → Bot registers user, sends "Play ResourceWars" button
    → Telegram opens webapp/index.html inside the app
      → JS calls Promise.all([/api/player/me, /api/resources/status, /api/ranking])
        → FastAPI validates initData (HMAC-SHA256) → calls services → DB
          → UI renders: header, castle, gold, resource cards, ranking
            → Every 10s: polls /api/resources/status to refresh timers
```

---

## Database Schema

```sql
users               -- id BIGINT PK, username, level=1, experience=0, created_at
inventory           -- user_id FK, wood=0, stone=0, water=0, food=0, gold=100
collection_timers   -- (user_id, resource) PK, ends_at TIMESTAMP
transactions        -- sender_id, receiver_id, resource, amount, status='completed'
battles             -- attacker_id, defender_id, winner_id, attacker_power, defender_power, resources_stolen=0
market_offers       -- seller_id, resource, amount, price_gold, status='active'
```

Key details:
- `inventory.gold` starts at **100** (not 0) for every new player
- `transactions.status` defaults to `'completed'` (trading module may change this to `'pending'`)
- `collection_timers` has no `notified` column yet (needed for scheduler notifications)
- Schema is created with `CREATE TABLE IF NOT EXISTS` — no migration system

---

## Game Mechanics (implemented)

### Resource Collection
- 4 resources: Wood, Stone, Water, Food
- Start a timer via bot (`/collect`) or webapp button → wait → collect

| Resource | Cooldown | Amount | XP |
|----------|----------|--------|----|
| Wood     | 1h       | 10     | 5  |
| Stone    | 2h       | 5      | 8  |
| Water    | 30m      | 20     | 3  |
| Food     | 1.5h     | 15     | 6  |

### Leveling
- XP threshold per level: `current_level × 100`
- `add_experience()` handles multiple simultaneous level-ups in a single call
- Level up shown as a red toast notification in the webapp

### Authentication
- All API endpoints except `GET /api/ranking` require the `x-init-data` header
- `GET /api/ranking` is public (no auth needed)
- `GET /api/player/me` auto-registers the user if they open the webapp without `/start` first

### Bot Commands
| Command      | Description                                            |
|--------------|--------------------------------------------------------|
| `/start`     | Register user and open the Mini App (WebApp button)    |
| `/profile`   | View level, XP, and progress bar (text fallback)       |
| `/ranking`   | Top 10 players (text fallback)                         |
| `/collect`   | Open inline keyboard to start/collect resources        |
| `/inventory` | View current resource and gold amounts                 |

### Inline Keyboard (bot)
`/collect` sends an inline keyboard with one button per resource. Buttons show:
- **"Start"** — idle resource, starts a timer
- **"Ready!"** — timer finished, collects the resource and grants XP
- **"Xh Ym"** — countdown while timer is active (shows alert on tap, no action)

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
ngrok http 8000
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

### Trading (next)
- Players post sell offers with a resource + gold price
- Other players browse `/market` and accept with `/buy`
- Full CRUD: `/sell`, `/buy`, `/cancel`
- UI panel in the Mini App

### Battle System (future)
- Attack power derived from level + inventory
- Winner steals a portion of loser's resources
- Battle history visible in the Mini App

### Scheduler notifications (next)
- Notify players via Telegram message when their collection timer finishes
- Requires: adding `notified` column to `collection_timers`, integrating `services/scheduler.py` into `main.py`

---

## Current Status

- [x] Project architecture defined
- [x] Database schema with all 6 tables
- [x] FastAPI server with webhook
- [x] Telegram Mini App frontend (HTML/CSS/JS, single-page)
- [x] Telegram initData authentication (HMAC-SHA256, timing-safe)
- [x] User registration (via /start and auto-register on webapp open)
- [x] Resource collection with timers (bot inline keyboard + webapp buttons)
- [x] XP and leveling system (multi-level-up supported)
- [x] Player ranking (public endpoint)
- [x] Gold inventory (starts at 100 per player)
- [ ] Scheduler notifications (APScheduler installed, not connected)
- [ ] Trading module
- [ ] Battle module
- [ ] Push notifications when collection is ready
