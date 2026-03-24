# ResourceWars — Telegram Game

A resource trading Telegram bot built with Python. Designed with scalable modules for future player-to-player trading and a battle system.

> Portfolio project — built to demonstrate clean architecture, layered design, and async Python.

---

## Tech Stack

- **Python 3.11+**
- **python-telegram-bot 20.7** (async)
- **PostgreSQL** via psycopg2
- **APScheduler** for background tasks
- **python-dotenv** for environment config

---

## Project Structure

```
juego_telegram/
├── bot.py                      # Entry point — registers all handlers and starts polling
├── config.py                   # Environment variables and game constants
├── database.py                 # DB connection and schema initialization
├── scheduler.py                # Background task scheduler (APScheduler)
│
├── handlers/                   # Telegram command layer (no business logic)
│   ├── jugador.py              # /start  /profile  /ranking
│   ├── recursos.py             # /collect  /inventory + inline keyboard callbacks
│   ├── comercio.py             # [PENDING] /market  /sell  /buy  /cancel
│   └── batalla.py              # [PENDING] /attack  /defense  /history
│
└── services/                   # Business logic layer (no Telegram)
    ├── jugador_service.py      # User registration, XP, level-up, ranking
    ├── recursos_service.py     # Collection timers, resource gathering
    ├── comercio_service.py     # [PENDING] Market offers, transfers
    └── batalla_service.py      # [PENDING] Combat resolution, power calculation
```

**Architecture rule:** handlers only translate Telegram input → call services → return response. They never touch the database directly.

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
- Each resource has a cooldown timer before it can be collected
- Collecting grants XP

| Resource | Cooldown | Amount | XP |
|----------|----------|--------|----|
| Wood     | 1h       | 10     | 5  |
| Stone    | 2h       | 5      | 8  |
| Water    | 30m      | 20     | 3  |
| Food     | 1.5h     | 15     | 6  |

### Leveling
- XP threshold per level: `level × 100`
- Level up is automatic when threshold is reached

### Commands
| Command      | Description                        |
|--------------|------------------------------------|
| `/start`     | Register and start playing         |
| `/collect`   | Open resource collection menu      |
| `/inventory` | View current resources and gold    |
| `/profile`   | View level, XP bar                 |
| `/ranking`   | Top 10 players by level            |

---

## Planned Modules

### Trading (next)
- Players post sell offers with a resource + gold price
- Other players browse `/market` and accept with `/buy`
- Transfers recorded in `transactions`

### Battle System (future)
- Attack power derived from level + inventory
- Winner steals a portion of loser's resources
- Results recorded in `battles`

---

## Setup

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in BOT_TOKEN and DATABASE_URL

# 4. Run
python bot.py
```

`.env` format:
```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/resourcewars
```

---

## Current Status

- [x] Project architecture defined
- [x] Database schema with all tables
- [x] User registration and profile system
- [x] Resource collection with timers and inline keyboards
- [x] XP and leveling system
- [x] Player ranking
- [ ] Trading module
- [ ] Battle module
- [ ] Collection ready notifications (scheduler)
