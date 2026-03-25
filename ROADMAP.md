# ResourceWars — Roadmap

Estado a fecha 2026-03-24. Cada fase depende de la anterior.

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

## Fase 2 — Notificaciones de temporizador ⬜ PENDIENTE

**Objetivo:** avisar al jugador cuando su recurso está listo para recolectar, sin que tenga que abrir el juego.

**Archivos a modificar/completar:**
- `services/scheduler.py` — añadir el job que revise `collection_timers`
- `main.py` — inicializar y arrancar el scheduler en el `lifespan`
- `scheduler.py` (raíz) — puede eliminarse o fusionarse con `services/scheduler.py`

**Pasos:**
1. En `services/scheduler.py`, crear un job que se ejecute cada minuto
2. El job consulta `collection_timers` donde `ends_at <= now` y no se ha notificado
3. Envía mensaje de Telegram al usuario con `bot_app.bot.send_message()`
4. Añadir columna `notified` (boolean) a `collection_timers` para no notificar dos veces
5. Integrar el scheduler en `lifespan` de `main.py`

---

## Fase 3 — Sistema de comercio (Trading) ⬜ PENDIENTE

**Objetivo:** los jugadores pueden publicar ofertas de venta y comprar recursos de otros.

**Archivos a completar:**
- `services/trading_service.py` — lógica completa
- `handlers/trading.py` — comandos de bot
- `api/routes/` — endpoints REST para la webapp

**Pasos:**
1. **`services/trading_service.py`**
   - `create_offer(user_id, resource, amount, gold_price)` — valida que el jugador tenga suficiente recurso, descuenta del inventario, inserta en `market_offers`
   - `cancel_offer(user_id, offer_id)` — devuelve el recurso al inventario, marca oferta como `cancelled`
   - `get_active_offers()` — lista todas las ofertas activas
   - `buy_offer(buyer_id, offer_id)` — valida gold del comprador, transfiere recursos y gold, registra en `transactions`, marca oferta como `sold`

2. **`handlers/trading.py`**
   - `/market` — muestra lista de ofertas activas
   - `/sell <recurso> <cantidad> <precio_gold>` — crea una oferta
   - `/buy <offer_id>` — acepta una oferta
   - `/cancel <offer_id>` — cancela tu propia oferta

3. **API REST (webapp)**
   - `GET /api/market` — listar ofertas activas
   - `POST /api/market/sell` — crear oferta
   - `POST /api/market/buy/{offer_id}` — comprar
   - `DELETE /api/market/{offer_id}` — cancelar

4. **Frontend**
   - Pestaña "Market" en la webapp con listado de ofertas e interfaz de compra/venta

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
2. Eliminar `scheduler.py` de la raíz (duplicado de `services/scheduler.py`)
3. Crear `.env.example` con todas las variables requeridas
4. Añadir manejo de errores global en FastAPI (handlers de excepciones)
5. Revisar que todas las rutas API devuelvan mensajes de error consistentes
6. Añadir validación de parámetros en los endpoints REST (Pydantic models)
7. Añadir índices a la base de datos (`user_id` en `collection_timers`, `market_offers`)

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
| 2    | Notificaciones scheduler | ⬜ Pendiente  |
| 3    | Sistema de comercio      | ⬜ Pendiente  |
| 4    | Sistema de batallas      | ⬜ Pendiente  |
| 5    | Limpieza y calidad       | ⬜ Pendiente  |
| 6    | Despliegue producción    | ⬜ Futuro     |
