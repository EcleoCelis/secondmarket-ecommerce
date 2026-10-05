(function () {
    const API_BASE_URL = "/api/v1/auth";

    async function request(path, options = {}) {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            ...options,
        });

        const payload = await response.json().catch(() => ({
            success: false,
            message: "The server returned an unreadable response.",
            error: { details: {} },
        }));

        if (!response.ok) {
            const error = new Error(payload.message || "Request failed.");
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    function register(data) {
        return request("/register", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    function login(data) {
        return request("/login", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    function logout() {
        return request("/logout", { method: "POST" });
    }

    function me() {
        return request("/me");
    }

    function formatError(error) {
        const details = error?.payload?.error?.details || {};
        const messages = Object.values(details).flat().filter(Boolean);
        return messages.length ? messages.join(" ") : error.message || "Something went wrong.";
    }

    window.SecondMarketAuthAPI = {
        formatError,
        login,
        logout,
        me,
        register,
    };
})();
