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
```

No hay sistema de tests automatizados ni linter configurado en este proyecto.

## Variables de entorno requeridas (.env)

```
BOT_TOKEN=<telegram_bot_token>
DATABASE_URL=postgresql://user:password@localhost:5432/resourcewars
PUBLIC_URL=https://xxxx.ngrok.io  # URL pública para el webhook y la webapp
```

El esquema de base de datos se crea automáticamente al iniciar la app mediante `init_db()` en `database.py`.

## Arquitectura

### Capas del sistema

```
handlers/ (comandos Telegram) ──┐
                                 ├──→ services/ (lógica de negocio) ──→ database.py (PostgreSQL)
api/routes/ (REST API webapp)  ──┘
```

- **`handlers/`**: Comandos del bot. Registra `/start`, `/profile`, `/ranking` (player.py) y `/collect`, `/inventory` (resources.py). resources.py también registra un `CallbackQueryHandler` para el teclado inline de recolección con los patrones `collect_start:*`, `collect_take:*`, `collect_wait:*`.
- **`api/routes/`**: Endpoints REST usados por la webapp. Toda petición protegida requiere el header `x-init-data` con el initData de Telegram, validado por HMAC-SHA256 en `api/auth.py`. **Excepción:** `GET /api/ranking` es público, sin autenticación. `GET /api/player/me` auto-registra al usuario si no existe (permite abrir la webapp sin haber ejecutado `/start`).
- **`services/`**: Lógica pura sin dependencias de HTTP ni Telegram. `resources_service.py` usa `psycopg2.sql.Identifier` para inyectar el nombre de columna del recurso de forma segura en las queries UPDATE. `player_service.add_experience()` soporta múltiples level-ups en una sola llamada (bucle while). Los módulos `trading_service.py` y `battle_service.py` son stubs de comentarios pendientes de implementar. `game_service.py` es un archivo vacío reservado.
- **`config.py`**: Centraliza tiempos de recolección (`COLLECTION_TIMES`) y cantidades por recurso (`COLLECTION_AMOUNTS`).
- **`main.py`**: Entry point principal. Inicializa DB, registra todos los handlers (incluidos los stubs vacíos de trading y battle), configura webhook, monta `webapp/` como archivos estáticos. El mount estático va después del endpoint `/webhook` para evitar que capture esa ruta.
- **`bot.py`**: Modo polling. Idéntico a main.py en registro de handlers, sin webhook ni FastAPI. Útil para desarrollo local sin ngrok.
- **`scheduler.py`** (raíz): Define `setup_scheduler()` con APScheduler pero **no es importado por nadie**. Pendiente de integrar en `main.py`.

### Frontend (webapp/)

Vanilla JS sin build step. Una sola página con secciones: header (nombre + nivel + barra XP), castillo con fallback emoji, gold, recursos (grid 2 columnas), ranking.

- `api.js`: Objeto `Api` con 5 métodos que adjuntan `window.Telegram.WebApp.initData` como header `x-init-data`.
- `app.js`: Al iniciar llama `Promise.all([getProfile, getResourceStatus, getRanking])` en paralelo. Hace polling a `getResourceStatus` cada **10 segundos** para actualizar temporizadores. En cada acción del usuario (start/collect) hace un refresh completo de los 3 endpoints. Toast de level-up en rojo (#e94560), toast de colección en verde (#4caf50), desaparece a los 2.8s.

### Base de datos

6 tablas — esquema creado con `CREATE TABLE IF NOT EXISTS`, sin migraciones:

| Tabla | Campos relevantes | Notas |
|-------|-------------------|-------|
| `users` | id BIGINT PK, username, level=1, experience=0, created_at | — |
| `inventory` | user_id FK, wood=0, stone=0, water=0, food=0, gold=**100** | gold arranca en 100, no en 0 |
| `collection_timers` | (user_id, resource) PK, ends_at TIMESTAMP | Sin columna `notified` — scheduler aún no implementado |
| `transactions` | sender_id, receiver_id, resource, amount, status='completed' | status default es 'completed', no 'pending' |
| `battles` | attacker_id, defender_id, winner_id, attacker_power, defender_power, resources_stolen=0 | — |
| `market_offers` | seller_id, resource, amount, price_gold, status='active' | — |

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
| APScheduler | 3.10.4 | **Instalado, no inicializado** |
| fastapi | 0.109.0 | REST API + webhook server |
| uvicorn | 0.27.0 | ASGI server |
| python-multipart | 0.0.9 | Requerido por FastAPI, sin endpoints de form data activos |
| httpx | 0.25.2 | **Instalado, no usado en el código actual** |

## .gitignore — cobertura actual

Cubre: `.env`, `.env.*`, `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`.

**Ausente:** `ngrok.exe` (binario en la raíz), `.claude/` (configuración local).

## Módulos pendientes

- `handlers/trading.py` y `services/trading_service.py` — stubs de comentarios sin lógica.
- `handlers/battle.py` y `services/battle_service.py` — stubs de comentarios sin lógica.
- `scheduler.py` (raíz) y `services/scheduler.py` — APScheduler setup sin jobs ni integración en `main.py`.
- `services/game_service.py` — archivo vacío reservado.
- `modules/` (`player.py`, `resources.py`, `__init__.py`) — los tres archivos tienen 1 línea vacía, no son importados en ningún lugar del código activo. Candidatos a eliminar.
