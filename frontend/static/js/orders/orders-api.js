(function () {
    const BASE_URL = "/api/v1/orders";

    async function request(path = "", options = {}) {
        const response = await fetch(`${BASE_URL}${path}`, {
            credentials: "include",
            headers: {
                Accept: "application/json",
                ...(options.headers || {}),
            },
            ...options,
        });
        const payload = await response.json().catch(() => ({
            success: false,
            message: "The server returned an unreadable response.",
            error: { details: {} },
        }));

        if (!response.ok || payload.success === false) {
            const error = new Error(payload.message || "Order request failed.");
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    function buildQueryString(params = {}) {
        const query = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value === undefined || value === null || value === "" || value === "all") return;
            query.set(key, value);
        });

        const queryString = query.toString();
        return queryString ? `?${queryString}` : "";
    }

    async function listOrders(filters = {}) {
        const payload = await request(buildQueryString(filters));
        return {
            orders: payload.data,
            count: payload.meta?.count || payload.data.length,
        };
    }

    async function getOrder(orderNumber) {
        const payload = await request(`/${encodeURIComponent(orderNumber)}`);
        return payload.data;
    }

    async function cancelOrder(orderNumber) {
        const payload = await request(`/${encodeURIComponent(orderNumber)}/cancel`, {
            method: "PATCH",
        });
        return payload.data;
    }

    function formatError(error) {
        const details = error?.payload?.error?.details || {};
        const messages = Object.values(details).flat().filter(Boolean);
        return messages.length ? messages.join(" ") : error.message || "The order workspace is temporarily unavailable.";
    }

    window.SecondMarketOrdersAPI = {
        buildQueryString,
        cancelOrder,
        formatError,
        getOrder,
        listOrders,
    };
})();
