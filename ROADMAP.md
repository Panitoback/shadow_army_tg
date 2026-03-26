# ResourceWars — Roadmap

Estado a fecha 2026-03-26. Cada fase depende de la anterior.

---

## Fase 1 — Núcleo jugable ✅ COMPLETA

Todo lo de esta fase está implementado y funcionando.

- [x] Servidor FastAPI con webhook de Telegram
- [x] Esquema de base de datos (6 tablas: users, inventory, collection_timers, transactions, battles, market_offers)
- [x] Autenticación de initData de Telegram (HMAC-SHA256)
- [x] Registro de usuario al enviar `/start`
- [x] Comandos de bot: `/start`, `/profile`, `/ranking`, `/collect`, `/inventory`
- [x] Recolección de 4 recursos con temporizadores (Wood, Stone, Water, Food)
- [x] Sistema de XP y subida de nivel automática
- [x] Ranking de jugadores (top 10)
- [x] Mini App frontend (HTML/CSS/JS vanilla, sin build step)
- [x] Modo polling alternativo (`bot.py`) para desarrollo sin ngrok

---

## Fase 2 — Notificaciones de temporizador ✅ COMPLETA

**Objetivo:** avisar al jugador cuando su recurso está listo para recolectar, sin que tenga que abrir el juego.

- [x] Columna `notified BOOLEAN DEFAULT FALSE` añadida a `collection_timers` (con `ALTER TABLE ADD COLUMN IF NOT EXISTS` para tablas existentes)
- [x] `services/scheduler.py` — job que corre cada minuto, consulta `ends_at <= now AND notified = FALSE`, envía mensaje de Telegram, marca `notified = TRUE`; maneja usuarios que bloquearon el bot sin romper
- [x] Scheduler integrado en el `lifespan` de `main.py` — arranca tras el bot, se apaga limpiamente en shutdown
- [x] `scheduler.py` de la raíz eliminado (era un stub sin lógica ni imports)

---

## Fase 3 — Sistema de comercio (Trading) ✅ COMPLETA

**Objetivo:** los jugadores pueden publicar ofertas de venta y comprar recursos de otros.

- [x] `services/trading_service.py` — 4 funciones con transacciones atómicas:
  - `create_offer` — valida stock, descuenta inventario, inserta en `market_offers`
  - `cancel_offer` — devuelve recurso al inventario, marca como `cancelled`
  - `get_active_offers` — lista todas las ofertas activas con username del vendedor
  - `buy_offer` — valida gold, transfiere recursos y gold entre jugadores, registra en `transactions`, marca como `sold`
- [x] `handlers/trading.py` — `/market`, `/sell <recurso> <cantidad> <precio>`, `/buy <id>`, `/cancel <id>`
- [x] `api/routes/market.py` — `GET /api/market`, `POST /api/market/sell`, `POST /api/market/buy/{id}`, `DELETE /api/market/{id}`
- [x] Frontend: pestaña "Market" con formulario de venta, lista de ofertas activas, botón Buy/Cancel según si es tuya o ajena

**Mejoras de frontend implementadas también en esta fase:**
- [x] Navegación por tabs (Resources / Market / Ranking) — elimina el scroll largo
- [x] Countdown client-side sin parpadeo: `tickCountdown()` actualiza solo el texto del botón; re-render completo solo al pasar a "ready"
- [x] Server poll cada 10s solo para sincronizar estado real; countdown local cada 1s sin requests

---

## Fase 4 — Sistema de batallas (Battle) ⬜ PENDIENTE

**Objetivo:** los jugadores pueden atacar a otros, el ganador roba recursos.

**Archivos a completar:**
- `services/battle_service.py` — lógica completa
- `handlers/battle.py` — comandos de bot
- `api/routes/` — endpoints REST para la webapp

**Pasos:**
1. **`services/battle_service.py`**
   - `calculate_power(user_id)` — poder de ataque/defensa basado en nivel e inventario
   - `resolve_battle(attacker_id, defender_id)` — compara poderes, determina ganador
   - `apply_loot(winner_id, loser_id)` — transfiere un porcentaje de recursos al ganador
   - `record_battle(attacker_id, defender_id, winner_id, power, loot)` — guarda en `battles`
   - `get_battle_history(user_id)` — historial de batallas del jugador

2. **`handlers/battle.py`**
   - `/attack <username>` — atacar a otro jugador
   - `/defense` — ver tu poder de defensa actual
   - `/history` — ver historial de tus batallas

3. **API REST (webapp)**
   - `POST /api/battle/attack` — iniciar ataque
   - `GET /api/battle/history` — historial
   - `GET /api/battle/power` — poder actual del jugador

4. **Frontend**
   - Pestaña "Battle" en la webapp con ranking de poder, botón de ataque e historial

---

## Fase 5 — Limpieza y calidad ⬜ PENDIENTE

**Objetivo:** dejar el proyecto listo para publicar como portfolio o para producción.

**Pasos:**
1. Eliminar o integrar `modules/` (actualmente sin uso)
2. ~~Eliminar `scheduler.py` de la raíz~~ ✅ Ya hecho en Fase 2
3. Crear `.env.example` con todas las variables requeridas
4. Añadir manejo de errores global en FastAPI (handlers de excepciones)
5. Revisar que todas las rutas API devuelvan mensajes de error consistentes
6. Añadir validación de parámetros en los endpoints REST (Pydantic models — ya en market, extender a resources)
7. Añadir índices a la base de datos (`user_id` en `collection_timers`, `market_offers`)
8. Añadir sistema de migraciones (Alembic) para gestionar cambios de esquema en producción

---

## Fase 6 — Despliegue en producción ⬜ FUTURO

**Objetivo:** pasar de ngrok/local a un servidor real.

**Pasos:**
1. Elegir hosting (Railway, Render, VPS, etc.)
2. Configurar PostgreSQL en producción (o usar Supabase/Neon)
3. Crear `Dockerfile` o configuración de despliegue
4. Configurar variables de entorno en el proveedor de hosting
5. Configurar `PUBLIC_URL` con el dominio definitivo
6. Registrar el webhook con la URL de producción
7. Añadir logs persistentes y monitorización básica

---

## Resumen de estado

| Fase | Descripción              | Estado       |
|------|--------------------------|--------------|
| 1    | Núcleo jugable           | ✅ Completa   |
| 2    | Notificaciones scheduler | ✅ Completa   |
| 3    | Sistema de comercio      | ✅ Completa   |
| 4    | Sistema de batallas      | ⬜ Pendiente  |
| 5    | Limpieza y calidad       | ⬜ Pendiente  |
| 6    | Despliegue producción    | ⬜ Futuro     |
