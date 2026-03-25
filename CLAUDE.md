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
PUBLIC_URL=https://xxxx.ngrok.io  # URL pública para el webhook
```

El esquema de base de datos se crea automáticamente al iniciar la app mediante `init_db()` en `database.py`.

## Arquitectura

### Capas del sistema

```
handlers/ (comandos Telegram) ──┐
                                 ├──→ services/ (lógica de negocio) ──→ database.py (PostgreSQL)
api/routes/ (REST API webapp)  ──┘
```

- **`handlers/`**: Comandos del bot (`/start`, `/profile`, `/ranking`). Llaman a los services.
- **`api/routes/`**: Endpoints REST usados por la webapp (`/api/player/me`, `/api/resources/*`). Toda petición requiere el header `x-init-data` con el initData de Telegram, validado por HMAC-SHA256 en `api/auth.py`.
- **`services/`**: Lógica pura sin dependencias de HTTP ni Telegram. Los módulos `trading_service.py` y `battle_service.py` son stubs pendientes de implementar. `game_service.py` existe pero está vacío. `scheduler.py` tiene el setup de APScheduler pero aún no conecta jobs reales.
- **`config.py`**: Centraliza tiempos de recolección y cantidades por recurso.
- **`scheduler.py`** (raíz): Setup alternativo de APScheduler — no importado por `main.py`, pendiente de integrar.
- **`main.py`**: Entry point principal. Inicializa DB, registra handlers, configura webhook, monta `webapp/` como archivos estáticos.
- **`bot.py`**: Modo polling (alternativa sin webhook). Útil para desarrollo local sin ngrok.

### Frontend (webapp/)

Vanilla JS sin build step. `app.js` hace polling a `/api/resources/status` cada 10 segundos para actualizar los temporizadores. La autenticación usa `window.Telegram.WebApp.initData` que se envía en `x-init-data`.

### Base de datos

6 tablas: `users`, `inventory`, `collection_timers`, `transactions`, `battles`, `market_offers`. Las consultas usan psycopg2 con parámetros para evitar SQL injection. No hay ORM.

### Sistema de niveles

XP necesario para subir de nivel = `nivel_actual × 100`. Los recursos otorgan XP al ser recolectados (madera=5, piedra=8, agua=3, comida=6).

## Módulos pendientes

- `handlers/trading.py`, `handlers/battle.py` y sus services respectivos son stubs sin implementación.
- `scheduler.py` (raíz) y `services/scheduler.py` existen pero no están integrados en `main.py` — las notificaciones de timer siguen pendientes.
- `services/game_service.py` es un archivo vacío.
- `modules/` (con `player.py` y `resources.py`) no es importado en ningún lugar del código activo.
