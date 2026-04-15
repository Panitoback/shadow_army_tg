// Attaches Telegram WebApp initData to every request for authentication
const API_BASE = "";

const Api = {
    _initData() {
        return window.Telegram?.WebApp?.initData || "";
    },

    async _request(method, path, body = null) {
        const options = {
            method,
            headers: {
                "Content-Type": "application/json",
                "x-init-data": this._initData(),
            },
        };
        if (body) options.body = JSON.stringify(body);

        const res = await fetch(`${API_BASE}${path}`, options);
        if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
        return res.json();
    },

    getProfile()              { return this._request("GET",    "/api/player/me"); },
    getRanking()              { return this._request("GET",    "/api/ranking"); },
    getResourceStatus()       { return this._request("GET",    "/api/resources/status"); },
    startCollection(resource) { return this._request("POST",   `/api/resources/${resource}/start`); },
    collectResource(resource) { return this._request("POST",   `/api/resources/${resource}/collect`); },
    getMarket()               { return this._request("GET",    "/api/market"); },
    sellOffer(resource, amount, price_gold) {
        return this._request("POST", "/api/market/sell", { resource, amount, price_gold });
    },
    buyOffer(id)              { return this._request("POST",   `/api/market/buy/${id}`); },
    cancelOffer(id)           { return this._request("DELETE", `/api/market/${id}`); },
    getPowerRanking()         { return this._request("GET",    "/api/battle/power"); },
    getBattleHistory()        { return this._request("GET",    "/api/battle/history"); },
    attackPlayer(username)    { return this._request("POST",   "/api/battle/attack", { username }); },
};
