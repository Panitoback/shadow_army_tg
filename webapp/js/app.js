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

let inventoryCache = {};
let pollInterval = null;

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

// ── Data loading ───────────────────────────────────────────

async function refresh() {
    const [profile, status, ranking] = await Promise.all([
        Api.getProfile(),
        Api.getResourceStatus(),
        Api.getRanking(),
    ]);
    renderProfile(profile);
    renderResources(status);
    renderRanking(ranking);
}

async function init() {
    try {
        await refresh();
        // Poll every 10s to update timers automatically
        pollInterval = setInterval(async () => {
            const status = await Api.getResourceStatus();
            renderResources(status);
        }, 10000);
    } catch (err) {
        console.error("Failed to load game data:", err);
        document.getElementById("player-name").textContent = "Error loading";
    }
}

init();
