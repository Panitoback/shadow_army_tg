// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// Resource display config
const RESOURCES = [
    { key: "wood",  label: "Wood",  icon: "assets/wood.png",  fallback: "🪵" },
    { key: "stone", label: "Stone", icon: "assets/stone.png", fallback: "🪨" },
    { key: "water", label: "Water", icon: "assets/water.png", fallback: "💧" },
    { key: "food",  label: "Food",  icon: "assets/food.png",  fallback: "🌾" },
];

let myUserId = null;
let inventoryCache = {};
let statusCache = {};
let countdownInterval = null;
let pollInterval = null;

// ── Tabs ───────────────────────────────────────────────────

function initTabs() {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
        });
    });
}

// ── Helpers ────────────────────────────────────────────────

function formatTime(seconds) {
    if (seconds >= 3600) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return `${h}h ${m}m`;
    }
    if (seconds >= 60) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}m ${s}s`;
    }
    return `${seconds}s`;
}

function showToast(message, color = "#4caf50") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.style.background = color;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 2800);
}

// ── Render ─────────────────────────────────────────────────

function renderProfile(profile) {
    myUserId = profile.id;
    document.getElementById("player-name").textContent = profile.username;
    document.getElementById("player-level").textContent = `Lv. ${profile.level}`;
    document.getElementById("gold-amount").textContent = profile.inventory.gold;

    const pct = Math.min((profile.experience / profile.xp_needed) * 100, 100);
    document.getElementById("xp-bar").style.width = `${pct}%`;
    document.getElementById("xp-text").textContent =
        `${profile.experience} / ${profile.xp_needed} XP`;

    inventoryCache = profile.inventory;
}

function renderResources(status) {
    const grid = document.getElementById("resources-grid");
    grid.innerHTML = "";

    RESOURCES.forEach(({ key, label, icon, fallback }) => {
        const state  = status[key];
        const amount = inventoryCache[key] ?? 0;

        let btnLabel, btnClass;
        if (state === "idle") {
            btnLabel = "Start";
            btnClass = "btn-idle";
        } else if (state === "ready") {
            btnLabel = "Collect!";
            btnClass = "btn-ready";
        } else {
            btnLabel = formatTime(state);
            btnClass = "btn-waiting";
        }

        const card = document.createElement("div");
        card.className = "resource-card";
        card.innerHTML = `
            <img class="resource-icon" src="${icon}" alt="${label}"
                 onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
            <span class="resource-icon-fallback" style="display:none">${fallback}</span>
            <span class="resource-name">${label}</span>
            <span class="resource-amount">${amount}</span>
            <button class="resource-btn ${btnClass}" data-resource="${key}" data-state="${state}">
                ${btnLabel}
            </button>
        `;
        grid.appendChild(card);
    });

    // Attach click handlers
    grid.querySelectorAll(".resource-btn").forEach(btn => {
        btn.addEventListener("click", () => handleResourceClick(btn));
    });
}

function renderRanking(ranking) {
    const list = document.getElementById("ranking-list");
    list.innerHTML = "";

    const medals = ["🥇", "🥈", "🥉"];
    ranking.forEach(({ username, level, experience }, i) => {
        const item = document.createElement("div");
        item.className = "ranking-item";
        item.innerHTML = `
            <span class="rank-pos">${medals[i] ?? i + 1}</span>
            <span class="rank-username">${username}</span>
            <span class="rank-level">Lv.${level} · ${experience} XP</span>
        `;
        list.appendChild(item);
    });
}

function renderMarket(offers) {
    const list = document.getElementById("market-list");
    list.innerHTML = "";

    if (offers.length === 0) {
        list.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No active offers.</p>`;
        return;
    }

    const LABELS = { wood: "Wood", stone: "Stone", water: "Water", food: "Food" };

    offers.forEach(({ id, seller, resource, amount, price_gold, is_mine }) => {
        const label = LABELS[resource] ?? resource;
        const item = document.createElement("div");
        item.className = "market-item";
        item.innerHTML = `
            <div class="market-item-info">
                <div class="market-item-title">${label} x${amount}</div>
                <div class="market-item-sub">by ${seller}</div>
            </div>
            <span class="market-price">${price_gold}g</span>
            ${is_mine
                ? `<button class="btn-cancel-offer" data-offer-id="${id}">Cancel</button>`
                : `<button class="btn-buy" data-offer-id="${id}">Buy</button>`
            }
        `;
        list.appendChild(item);
    });

    list.querySelectorAll(".btn-buy").forEach(btn => {
        btn.addEventListener("click", () => handleBuy(btn));
    });
    list.querySelectorAll(".btn-cancel-offer").forEach(btn => {
        btn.addEventListener("click", () => handleCancelOffer(btn));
    });
}

function renderPowerRanking(ranking) {
    const list = document.getElementById("power-ranking-list");
    list.innerHTML = "";

    if (ranking.length === 0) {
        list.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No players yet.</p>`;
        return;
    }

    ranking.forEach(({ user_id, username, level, power }, i) => {
        const isMe = user_id === myUserId;
        const item = document.createElement("div");
        item.className = "power-item";
        item.innerHTML = `
            <span class="power-rank">${i + 1}</span>
            <div class="power-info">
                <div class="power-username">${username}${isMe ? " (You)" : ""}</div>
                <div class="power-score">Lv.${level} · ⚔️ ${power} power</div>
            </div>
            <button class="btn-attack" data-username="${username}" ${isMe ? "disabled" : ""}>
                ${isMe ? "You" : "Attack"}
            </button>
        `;
        list.appendChild(item);
    });

    list.querySelectorAll(".btn-attack:not([disabled])").forEach(btn => {
        btn.addEventListener("click", () => handleAttack(btn));
    });
}

function renderBattleHistory(history) {
    const list = document.getElementById("battle-history-list");
    list.innerHTML = "";

    if (history.length === 0) {
        list.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No battles yet.</p>`;
        return;
    }

    history.forEach(battle => {
        const won = battle.winner_id === myUserId;
        const item = document.createElement("div");
        item.className = "battle-item";
        item.innerHTML = `
            <div class="battle-item-header">
                <span class="${won ? "battle-outcome-win" : "battle-outcome-lose"}">${won ? "WIN" : "LOSS"}</span>
                <span>${battle.attacker} ⚔️ ${battle.defender}</span>
            </div>
            <div class="battle-item-sub">
                Power: ${battle.attacker_power} vs ${battle.defender_power} ·
                Stolen: ${battle.resources_stolen} resources
            </div>
        `;
        list.appendChild(item);
    });
}

// ── Actions ────────────────────────────────────────────────

async function handleResourceClick(btn) {
    const resource = btn.dataset.resource;
    const state    = btn.dataset.state;

    if (state !== "idle" && state !== "ready") return;

    btn.disabled = true;

    try {
        if (state === "idle") {
            await Api.startCollection(resource);
            showToast(`${resource} collection started!`);
        } else {
            const result = await Api.collectResource(resource);
            if (result.collected) {
                showToast(`+${result.amount} ${resource}! (+${result.xp} XP)`);
                if (result.leveled_up) {
                    setTimeout(() =>
                        showToast(`Level up! Now level ${result.new_level}! 🎉`, "#e94560"), 1000);
                }
            }
        }
        await refresh();
    } catch (err) {
        console.error(err);
        btn.disabled = false;
    }
}

async function handleBuy(btn) {
    const offerId = btn.dataset.offerId;
    btn.disabled = true;
    try {
        const result = await Api.buyOffer(offerId);
        const LABELS = { wood: "Wood", stone: "Stone", water: "Water", food: "Food" };
        showToast(`Bought ${result.amount} ${LABELS[result.resource] ?? result.resource} for ${result.price_gold}g!`);
        await refresh();
    } catch (err) {
        showToast(err.message || "Purchase failed", "#e94560");
        btn.disabled = false;
    }
}

async function handleCancelOffer(btn) {
    const offerId = btn.dataset.offerId;
    btn.disabled = true;
    try {
        await Api.cancelOffer(offerId);
        showToast("Offer cancelled. Resources returned.");
        await refresh();
    } catch (err) {
        showToast(err.message || "Cancel failed", "#e94560");
        btn.disabled = false;
    }
}

async function handleAttack(btn) {
    const username = btn.dataset.username;
    btn.disabled = true;
    try {
        const result = await Api.attackPlayer(username);
        const won = result.winner_id === myUserId;
        const stolen = result.resources_stolen;
        if (won) {
            showToast(`Victory! Stole ${stolen} resources from ${username}!`);
        } else {
            showToast(`Defeat! ${username} stole ${stolen} resources from you.`, "#e94560");
        }
        await refresh();
    } catch (err) {
        showToast(err.message || "Attack failed", "#e94560");
        btn.disabled = false;
    }
}

async function handleSell() {
    const resource   = document.getElementById("sell-resource").value;
    const amount     = parseInt(document.getElementById("sell-amount").value);
    const price_gold = parseInt(document.getElementById("sell-price").value);

    if (!amount || !price_gold || amount <= 0 || price_gold <= 0) {
        showToast("Enter a valid amount and price.", "#e94560");
        return;
    }

    const btn = document.getElementById("sell-btn");
    btn.disabled = true;
    try {
        const result = await Api.sellOffer(resource, amount, price_gold);
        document.getElementById("sell-amount").value = "";
        document.getElementById("sell-price").value = "";
        showToast(`Offer #${result.offer_id} created!`);
        await refresh();
    } catch (err) {
        showToast(err.message || "Could not create offer", "#e94560");
    } finally {
        btn.disabled = false;
    }
}

// ── Data loading ───────────────────────────────────────────

async function refresh() {
    const [profile, status, ranking, offers, powerRanking, battleHistory] = await Promise.all([
        Api.getProfile(),
        Api.getResourceStatus(),
        Api.getRanking(),
        Api.getMarket(),
        Api.getPowerRanking(),
        Api.getBattleHistory(),
    ]);
    renderProfile(profile);
    statusCache = status;
    renderResources(statusCache);
    renderRanking(ranking);
    renderMarket(offers);
    renderPowerRanking(powerRanking);
    renderBattleHistory(battleHistory);
}

function tickCountdown() {
    let stateChanged = false;
    for (const key in statusCache) {
        if (typeof statusCache[key] === "number" && statusCache[key] > 0) {
            statusCache[key] -= 1;
            if (statusCache[key] <= 0) {
                statusCache[key] = "ready";
                stateChanged = true;
            }
        }
    }
    if (stateChanged) {
        // Full re-render only when a timer just turned "ready"
        renderResources(statusCache);
    } else {
        // Lightweight: only update the button text, images stay untouched
        document.querySelectorAll(".resource-btn.btn-waiting").forEach(btn => {
            const val = statusCache[btn.dataset.resource];
            if (typeof val === "number") {
                btn.textContent = formatTime(val);
                btn.dataset.state = val;
            }
        });
    }
}

async function init() {
    try {
        initTabs();
        document.getElementById("sell-btn").addEventListener("click", handleSell);
        await refresh();
        // Decrement timers locally every second (no server request)
        countdownInterval = setInterval(tickCountdown, 1000);
        // Sync with server every 10s to catch real state changes
        pollInterval = setInterval(async () => {
            const status = await Api.getResourceStatus();
            statusCache = status;
            renderResources(statusCache);
        }, 10000);
    } catch (err) {
        console.error("Failed to load game data:", err);
        document.getElementById("player-name").textContent = "Error loading";
    }
}

init();
