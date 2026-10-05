(function () {
    function renderAuthView(state) {
        return `
            <section class="auth-shell" aria-labelledby="auth-title">
                <div class="auth-panel text-center">
                    <h1 id="auth-title" class="font-serif text-2xl font-semibold text-[#4E4638] text-center mb-2">Customer Portal</h1>
                    <p class="text-xs text-[#776B56] text-center mb-6">Access your buyer account for saved items, checkout, and orders.</p>
                    <div class="auth-page-links">
                        <a class="btn-primary" href="/login.html">Sign In</a>
                        <a class="btn-outline" href="/register.html">Create Buyer Account</a>
                    </div>
                </div>
            </section>
        `;
    }

    function renderAccountRequiredView() {
        return `
            <section class="auth-shell" aria-labelledby="account-required-title">
                <div class="auth-panel text-center space-y-4">
                    <h1 id="account-required-title" class="font-serif text-2xl font-semibold text-[#4E4638]">Sign In Required</h1>
                    <p class="text-sm text-[#776B56]">Please sign in or create a buyer account to view your account details.</p>
                    <a href="/login.html" class="btn-primary w-full py-3 text-xs uppercase tracking-widest">Go to Customer Portal</a>
                </div>
            </section>
        `;
    }

    function renderCheckoutAuthRequiredView() {
        return `
            <section class="auth-shell" aria-labelledby="checkout-auth-title">
                <div class="auth-panel text-center space-y-4">
                    <h1 id="checkout-auth-title" class="font-serif text-2xl font-semibold text-[#4E4638]">Sign In To Checkout</h1>
                    <p class="text-sm text-[#776B56]">Use your buyer account before placing an order.</p>
                    <a href="/login.html" class="btn-primary w-full py-3 text-xs uppercase tracking-widest">Go to Customer Portal</a>
                </div>
            </section>
        `;
    }

    function renderAccountView(state, formatPrice) {
        if (!state.user) {
            return renderAccountRequiredView();
        }

        if (state.user.role === "admin") {
            window.location.href = "/admin";
            return `
                <section class="auth-shell" aria-labelledby="admin-redirect-title">
                    <div class="auth-panel text-center space-y-4">
                        <h1 id="admin-redirect-title" class="font-serif text-2xl font-semibold text-[#4E4638]">Redirecting To Admin</h1>
                        <p class="text-sm text-[#776B56]">Admin seller accounts are managed in the admin workspace.</p>
                        <a href="/admin" class="btn-primary w-full py-3 text-xs uppercase tracking-widest">Open Admin Workspace</a>
                    </div>
                </section>
            `;
        }

        return `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <h1 class="font-serif text-3xl font-semibold text-[#4E4638] mb-2">Welcome, ${state.user.name}</h1>
                <p class="text-xs text-[#776B56] mb-4">${state.user.email} | ${state.user.role} account | ${state.user.status}</p>
                <div class="account-actions">
                    <button onclick="app.handleLogout()" class="btn-outline py-2 text-xs uppercase tracking-widest">Sign Out</button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div class="space-y-4">
                        <div class="bg-white p-6 border border-[#D7CEC1] rounded">
                            <h3 class="font-serif text-lg font-semibold text-[#4E4638] mb-2">Profile</h3>
                            <p class="text-xs text-[#776B56] leading-relaxed">
                                ${state.user.name}<br>
                                ${state.user.email}<br>
                                ${state.user.phone}
                            </p>
                        </div>
                    </div>

                    <div class="md:col-span-2 bg-white p-6 border border-[#D7CEC1] rounded space-y-4">
                        <h3 class="font-serif text-lg font-semibold text-[#4E4638]">Order History</h3>
                        ${state.user.orders.length === 0 ? `
                            <p class="text-sm text-[#776B56]">No orders yet.</p>
                        ` : `<div class="divide-y divide-[#D7CEC1]">
                            ${state.user.orders.map((order) => `
                                <div class="py-3 flex justify-between items-center text-xs">
                                    <div>
                                        <p class="font-bold text-[#4E4638]">${order.id}</p>
                                        <p class="text-[#776B56]">${order.date}</p>
                                    </div>
                                    <div class="text-right">
                                        <span class="badge badge-new">${order.status}</span>
                                        <p class="font-bold text-[#4E4638] mt-1">${formatPrice(order.total)}</p>
                                    </div>
                                </div>
                            `).join("")}
                        </div>`}
                    </div>
                </div>
            </div>
        `;
    }

    window.SecondMarketAuthViews = {
        renderAccountRequiredView,
        renderAccountView,
        renderAuthView,
        renderCheckoutAuthRequiredView,
    };
})();
