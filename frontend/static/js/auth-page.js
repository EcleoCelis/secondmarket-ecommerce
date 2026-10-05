(function () {
    const form = document.querySelector("[data-auth-form]");
    const message = document.querySelector("[data-auth-message]");

    function setMessage(text, type = "error") {
        if (!message) return;

        message.textContent = text;
        message.className = `auth-message is-visible is-${type}`;
    }

    function setLoading(isLoading) {
        const submitButton = form?.querySelector("button[type='submit']");
        if (!submitButton) return;

        submitButton.disabled = isLoading;
        submitButton.dataset.originalText = submitButton.dataset.originalText || submitButton.textContent;
        submitButton.textContent = isLoading ? "Please wait..." : submitButton.dataset.originalText;
    }

    function redirectAuthenticatedUser(user) {
        if (user?.role === "admin") {
            window.location.href = "/admin";
            return;
        }

        sessionStorage.setItem("secondmarket:nextView", "account");
        window.location.href = form?.dataset.authSuccessUrl || "/";
    }

    async function rejectUnexpectedRole(requiredRole, actualRole) {
        await window.SecondMarketAuthAPI.logout().catch(() => {});
        throw new Error(
            requiredRole === "admin"
                ? "Use an admin seller account to access the admin workspace."
                : "Admin seller accounts must use the admin sign-in page."
        );
    }

    async function handleSubmit(event) {
        event.preventDefault();
        if (!form || !window.SecondMarketAuthAPI) return;

        const formData = new FormData(form);
        const mode = form.dataset.authForm;
        setLoading(true);

        try {
            let payload;
            if (mode === "register") {
                payload = await window.SecondMarketAuthAPI.register({
                    email: formData.get("email"),
                    password: formData.get("password"),
                    first_name: formData.get("first_name"),
                    last_name: formData.get("last_name"),
                    phone: formData.get("phone"),
                    role: "buyer",
                });
                setMessage("Your buyer account is ready.", "success");
            } else {
                payload = await window.SecondMarketAuthAPI.login({
                    email: formData.get("email"),
                    password: formData.get("password"),
                });
                setMessage("You are now signed in.", "success");
            }

            const user = payload?.data?.user;
            const requiredRole = form.dataset.authRequiredRole;
            if (requiredRole && user?.role !== requiredRole) {
                await rejectUnexpectedRole(requiredRole, user?.role);
            }

            redirectAuthenticatedUser(user);
        } catch (error) {
            setMessage(window.SecondMarketAuthAPI.formatError(error), "error");
            setLoading(false);
        }
    }

    if (form) {
        form.addEventListener("submit", handleSubmit);
    }
})();
