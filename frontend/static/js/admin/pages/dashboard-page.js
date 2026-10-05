(function () {
    function renderDashboardPage() {
        const products = this.state.products;
        const categories = this.state.categories;
        const availableCount = products.filter((product) => product.status === "available").length;
        const draftCount = products.filter((product) => product.status === "draft").length;
        const lowStockCount = products.filter((product) => product.quantity <= 1).length;
        const metricCards = [
            ["Total Products", products.length],
            ["Available", availableCount],
            ["Drafts", draftCount],
            ["Low Stock", lowStockCount],
        ].map(([label, value]) => `
            <article class="admin-metric-card">
                <span>${label}</span>
                <strong>${value}</strong>
            </article>
        `).join("");
        const recentProductRows = products.slice(0, 5).map((product) => `
            <tr>
                <td>${this.productCell(product)}</td>
                <td>${this.escapeHtml(product.category?.name || "Uncategorized")}</td>
                <td>${this.statusBadge(product.status)}</td>
                <td>${product.quantity}</td>
            </tr>
        `).join("") || this.emptyTableRow("No products are available yet.", 4);

        return this.renderPageTemplate("dashboard", {
            metricCards,
            recentProductRows,
            categoryCount: categories.length,
        });
    }

    window.SecondMarketAdminPages = window.SecondMarketAdminPages || {};
    window.SecondMarketAdminPages.renderDashboardPage = renderDashboardPage;
})();
