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

    getProfile()              { return this._request("GET",  "/api/player/me"); },
    getRanking()              { return this._request("GET",  "/api/ranking"); },
    getResourceStatus()       { return this._request("GET",  "/api/resources/status"); },
    startCollection(resource) { return this._request("POST", `/api/resources/${resource}/start`); },
    collectResource(resource) { return this._request("POST", `/api/resources/${resource}/collect`); },
};
