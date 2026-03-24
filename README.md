# ResourceWars — Telegram Mini App Game

A resource trading game built as a Telegram Mini App. Players manage a castle, collect resources, level up, and compete on a leaderboard. Designed with scalable modules for player-to-player trading and a battle system.

> Portfolio project — demonstrates clean layered architecture, REST API, async Python, and Telegram Mini App integration.

---

## Tech Stack

- **Python 3.11+**
- **FastAPI 0.109** — REST API + webhook server
- **python-telegram-bot 20.7** — bot commands and WebApp button
- **PostgreSQL** via psycopg2
- **APScheduler** — background tasks
- **httpx** — async HTTP client
- **Vanilla JS / HTML / CSS** — frontend (no build step)
- **Telegram WebApp SDK** — native Mini App integration

---

## Project Structure

```
juego_telegram/
├── main.py                     # Entry point — FastAPI app + webhook + static files
├── config.py                   # Environment variables and game constants
├── database.py                 # DB connection and schema initialization
├── scheduler.py                # Background task scheduler (APScheduler)
│
├── api/                        # REST API layer
│   ├── auth.py                 # Telegram initData validation (HMAC-SHA256)
│   └── routes/
│       ├── player.py           # GET /api/player/me  GET /api/ranking
│       └── resources.py        # GET /api/resources/status
│                               # POST /api/resources/{resource}/start
│                               # POST /api/resources/{resource}/collect
│
├── handlers/                   # Telegram bot command layer
│   ├── player.py               # /start (sends WebApp button)  /profile  /ranking
│   ├── resources.py            # /collect  /inventory (fallback commands)
│   ├── trading.py              # [PENDING] /market  /sell  /buy  /cancel
│   └── battle.py               # [PENDING] /attack  /defense  /history
│
├── services/                   # Business logic (no Telegram, no HTTP)
│   ├── player_service.py       # User registration, XP, level-up, ranking
│   ├── resources_service.py    # Collection timers, resource gathering
│   ├── trading_service.py      # [PENDING] Market offers, transfers
│   └── battle_service.py       # [PENDING] Combat resolution
│
└── webapp/                     # Frontend Mini App
    ├── index.html              # Main UI
    ├── css/style.css           # Dark medieval theme
    ├── js/
    │   ├── api.js              # API calls with Telegram auth headers
    │   └── app.js              # UI rendering, timers, interactions
    └── assets/                 # Your PNG files go here (castle, resources)
```

**Architecture rule:** handlers translate Telegram input → call services. API routes validate initData → call services. Services never touch Telegram or HTTP.

---

## How It Works

```
User opens Telegram → sends /start
  → Bot sends "Play ResourceWars" button
    → Telegram opens webapp/index.html inside the app
      → JS calls /api/... with Telegram initData header
        → FastAPI validates initData (HMAC-SHA256) → calls services → DB
```

---

## Database Schema

```sql
users               -- id, username, level, experience
inventory           -- wood, stone, water, food, gold (starts at 100)
collection_timers   -- active timers per user/resource
transactions        -- resource transfers (status: pending | completed | cancelled)
battles             -- combat log (attacker, defender, winner, power, resources_stolen)
market_offers       -- player sell offers (status: active | sold | cancelled)
```

---

## Game Mechanics (implemented)

### Resource Collection
- 4 resources: Wood, Stone, Water, Food
- Each resource has a cooldown before it can be collected
- Collecting grants XP and updates the UI in real time

| Resource | Cooldown | Amount | XP |
|----------|----------|--------|----|
| Wood     | 1h       | 10     | 5  |
| Stone    | 2h       | 5      | 8  |
| Water    | 30m      | 20     | 3  |
| Food     | 1.5h     | 15     | 6  |

### Leveling
- XP threshold per level: `level × 100`
- Level up is automatic, shown as a toast notification in the UI

### Bot Commands
| Command      | Description                           |
|--------------|---------------------------------------|
| `/start`     | Register and open the Mini App        |
| `/profile`   | View level and XP (text fallback)     |
| `/ranking`   | Top 10 players (text fallback)        |

---

## Setup

### 1. Clone and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```

`.env` format:
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

### 5. Add your assets
Place PNG files in `webapp/assets/`:
- `castle.png` — main castle (400×300 px recommended)
- `wood.png`, `stone.png`, `water.png`, `food.png` — resource icons (64×64 px)

The app shows emoji fallbacks automatically if files are missing.

---

## Planned Modules

### Trading (next)
- Players post sell offers with a resource + gold price
- Other players browse `/market` and accept with `/buy`
- Full UI in the Mini App

### Battle System (future)
- Attack power derived from level + inventory
- Winner steals a portion of loser's resources
- Battle history visible in the Mini App

---

## Current Status

- [x] Project architecture defined
- [x] Database schema with all tables
- [x] FastAPI server with webhook
- [x] Telegram Mini App frontend (HTML/CSS/JS)
- [x] Telegram initData authentication (HMAC-SHA256)
- [x] User registration and profile system
- [x] Resource collection with timers
- [x] XP and leveling system with toast notifications
- [x] Player ranking
- [ ] Trading module
- [ ] Battle module
- [ ] Push notifications when collection is ready (scheduler)
