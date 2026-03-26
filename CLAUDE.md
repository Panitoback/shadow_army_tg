# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language conventions

All code must be in English: variable names, function names, file names, comments, and any in-code strings or identifiers. CLI responses to the user must be in Spanish.

## Comandos principales

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar con webhook (modo principal)
python main.py
# Escucha en 0.0.0.0:8000, monta la webapp como archivos estáticos

# Ejecutar con polling (alternativa, sin webhook)
python bot.py

# ngrok (binario en la raíz del proyecto)
.\ngrok.exe http 8000
# Copiar la URL https resultante en PUBLIC_URL del .env antes de correr main.py
```

No hay sistema de tests automatizados ni linter configurado en este proyecto.

## Variables de entorno requeridas (.env)

```
BOT_TOKEN=<telegram_bot_token>
DATABASE_URL=postgresql://user:password@localhost:5432/resourcewars
PUBLIC_URL=https://xxxx.ngrok.io  # URL pública para el webhook y la webapp
```

El esquema de base de datos se crea automáticamente al iniciar la app mediante `init_db()` en `database.py`. Las columnas añadidas después de la creación inicial usan `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

## Arquitectura

### Capas del sistema

```
handlers/ (comandos Telegram) ──┐
                                 ├──→ services/ (lógica de negocio) ──→ database.py (PostgreSQL)
api/routes/ (REST API webapp)  ──┘
```

- **`handlers/`**: Comandos del bot.
  - `player.py`: registra `/start`, `/profile`, `/ranking`
  - `resources.py`: registra `/collect`, `/inventory` y un `CallbackQueryHandler` para los patrones `collect_start:*`, `collect_take:*`, `collect_wait:*`
  - `trading.py`: registra `/market`, `/sell`, `/buy`, `/cancel`
  - `battle.py`: stub vacío, `get_handlers()` retorna `[]`

- **`api/routes/`**: Endpoints REST usados por la webapp. Toda petición protegida requiere el header `x-init-data` con el initData de Telegram, validado por HMAC-SHA256 en `api/auth.py`. **Excepciones:** `GET /api/ranking` es público sin autenticación. `GET /api/player/me` auto-registra al usuario si no existe.
  - `player.py`: `GET /api/player/me`, `GET /api/ranking`
  - `resources.py`: `GET /api/resources/status`, `POST /api/resources/{resource}/start`, `POST /api/resources/{resource}/collect` (este último también llama a `add_experience`)
  - `market.py`: `GET /api/market`, `POST /api/market/sell` (body: `SellRequest` Pydantic), `POST /api/market/buy/{offer_id}`, `DELETE /api/market/{offer_id}`

- **`services/`**: Lógica pura sin dependencias de HTTP ni Telegram.
  - `player_service.py`: `register_user`, `get_user`, `get_inventory`, `add_experience` (soporta múltiples level-ups en bucle while), `get_ranking`
  - `resources_service.py`: `get_resource_status`, `start_collection`, `collect_resource`. Usa `psycopg2.sql.Identifier` para inyectar el nombre de columna del recurso de forma segura en las queries UPDATE.
  - `trading_service.py`: `create_offer`, `cancel_offer`, `get_active_offers`, `buy_offer`. Todas las transferencias de recursos/gold son atómicas. Usa `sql.Identifier` para columnas de recurso. `get_active_offers` retorna `(id, seller_id, username, resource, amount, price_gold)`.
  - `scheduler.py`: `setup_scheduler(bot)` — configura `AsyncIOScheduler` con job `notify_ready_timers` cada 1 minuto. El job consulta `collection_timers WHERE ends_at <= now AND notified = FALSE`, envía mensaje por Telegram, marca `notified = TRUE`. Falla silenciosamente si el usuario bloqueó el bot.
  - `battle_service.py`: stub de comentarios, pendiente de implementar.
  - `game_service.py`: archivo vacío reservado.

- **`config.py`**: Centraliza tiempos de recolección (`COLLECTION_TIMES`) y cantidades por recurso (`COLLECTION_AMOUNTS`).

- **`main.py`**: Entry point principal. Inicializa DB, registra todos los handlers, configura webhook, arranca el scheduler (`setup_scheduler(bot_app.bot)`) en el `lifespan`, monta `webapp/` como archivos estáticos. El mount estático va después de todos los endpoints para evitar que capture rutas API. En shutdown llama a `scheduler.shutdown()` antes de `bot_app.stop()`.

- **`bot.py`**: Modo polling. Idéntico a `main.py` en registro de handlers, sin webhook ni FastAPI ni scheduler. Útil para desarrollo local sin ngrok.

### Frontend (webapp/)

Vanilla JS sin build step. Navegación por tabs: **Resources** (castillo + gold + grid de recursos), **Market** (formulario de venta + lista de ofertas), **Ranking**.

Cuando se cambia el contenido visible hay que incrementar el parámetro `?v=N` en los `<script>` y `<link>` del `index.html` para forzar que Telegram invalide su caché agresiva.

- `api.js`: Objeto `Api` con **9 métodos** que adjuntan `window.Telegram.WebApp.initData` como header `x-init-data`: `getProfile`, `getRanking`, `getResourceStatus`, `startCollection`, `collectResource`, `getMarket`, `sellOffer`, `buyOffer`, `cancelOffer`.
- `app.js`:
  - Al iniciar llama `Promise.all([getProfile, getResourceStatus, getRanking, getMarket])` en paralelo.
  - **Countdown client-side**: `tickCountdown()` corre cada **1 segundo** — solo actualiza `.textContent` de los botones `.btn-waiting` sin reconstruir el DOM (evita parpadeo de iconos). Re-render completo solo cuando un timer transiciona a `"ready"`.
  - **Server sync**: `pollInterval` cada **10 segundos** llama `getResourceStatus` y actualiza `statusCache` + re-renderiza.
  - `statusCache` almacena el estado actual de recursos localmente entre syncs.
  - En cada acción del usuario (start/collect/buy/sell/cancel) hace un `refresh()` completo de los 4 endpoints.
  - Toast de level-up en rojo (#e94560), toast de colección/compra en verde (#4caf50), desaparece a los 2.8s.
  - `initTabs()` gestiona la navegación por tabs via `data-tab` attributes.

### Base de datos

6 tablas — esquema creado con `CREATE TABLE IF NOT EXISTS`, sin migraciones:

| Tabla | Campos relevantes | Notas |
|-------|-------------------|-------|
| `users` | id BIGINT PK, username, level=1, experience=0, created_at | — |
| `inventory` | user_id FK, wood=0, stone=0, water=0, food=0, gold=**100** | gold arranca en 100, no en 0 |
| `collection_timers` | (user_id, resource) PK, ends_at TIMESTAMP, notified BOOLEAN DEFAULT FALSE | `notified` añadido en Fase 2 vía `ALTER TABLE ADD COLUMN IF NOT EXISTS` |
| `transactions` | sender_id, receiver_id, resource, amount, status='completed', created_at | Registra compras del mercado |
| `battles` | attacker_id, defender_id, winner_id, attacker_power, defender_power, resources_stolen=0 | — |
| `market_offers` | seller_id, resource, amount, price_gold, status='active', created_at | status: active → sold/cancelled |

Las consultas usan psycopg2 con parámetros posicionales (`%s`) para evitar SQL injection. No hay ORM.

### Sistema de niveles

XP necesario para subir de nivel = `nivel_actual × 100`. Los recursos otorgan XP al ser recolectados (madera=5, piedra=8, agua=3, comida=6). `add_experience()` soporta múltiples level-ups consecutivos en una sola llamada.

### Autenticación API

`api/auth.py` implementa la validación oficial de Telegram:
1. Parsea el `initData` URL-encoded, extrae y elimina el campo `hash`.
2. Construye el `data_check_string` con los campos restantes ordenados alfabéticamente.
3. Genera `secret_key = HMAC-SHA256(key="WebAppData", msg=BOT_TOKEN)`.
4. Computa `HMAC-SHA256(key=secret_key, msg=data_check_string)` y compara con `hash` usando `hmac.compare_digest` (timing-safe).
5. Retorna el dict del campo `user` parseado desde JSON. Si no hay campo `user`, retorna `{}`.

## Dependencias (requirements.txt)

| Paquete | Versión | Uso real |
|---------|---------|----------|
| python-telegram-bot | 20.7 | Bot + WebApp button + handlers |
| psycopg2-binary | 2.9.9 | PostgreSQL |
| python-dotenv | 1.0.0 | Carga .env |
| APScheduler | 3.10.4 | Scheduler de notificaciones — **activo en main.py** |
| fastapi | 0.109.0 | REST API + webhook server |
| uvicorn | 0.27.0 | ASGI server |
| python-multipart | 0.0.9 | Requerido por FastAPI |
| httpx | 0.25.2 | **Instalado, no usado en el código actual** |

## .gitignore — cobertura actual

Cubre: `.env`, `.env.*`, `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`.

**Ausente:** `ngrok.exe` (binario en la raíz), `.claude/` (configuración local).

## Módulos pendientes

- `handlers/battle.py` y `services/battle_service.py` — stubs de comentarios sin lógica. Siguiente fase.
- `services/game_service.py` — archivo vacío reservado para lógica cross-domain futura.
- `modules/` (`player.py`, `resources.py`, `__init__.py`) — los tres archivos están vacíos, no son importados en ningún lugar del código activo. Candidatos a eliminar en Fase 5.
