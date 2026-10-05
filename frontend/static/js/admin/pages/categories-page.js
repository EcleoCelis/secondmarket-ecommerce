(function () {
    function renderCategoriesPage() {
        const disabled = this.actionDisabledAttribute();
        const categoryRows = this.state.categories.map((category) => `
            <tr>
                <td>
                    <strong>${this.escapeHtml(category.name)}</strong>
                    <div class="admin-muted">${this.escapeHtml(category.description || "No description provided.")}</div>
                </td>
                <td>${this.escapeHtml(category.slug)}</td>
                <td>${category.product_count || 0}</td>
                <td>${this.statusBadge(category.is_active ? "available" : "hidden", category.is_active ? "Active" : "Inactive")}</td>
                <td>${category.sort_order}</td>
                <td>
                    <div class="admin-inline-actions">
                        <label class="admin-row-control">
                            <span>Status</span>
                            <select data-admin-action onchange="adminApp.setCategoryStatus('${this.escapeAttribute(category.slug)}', this.value)" ${disabled}>
                                <option value="true" ${category.is_active ? "selected" : ""}>Active</option>
                                <option value="false" ${!category.is_active ? "selected" : ""}>Inactive</option>
                            </select>
                        </label>
                        <form class="admin-row-control" onsubmit="adminApp.setCategorySortOrder(event, '${this.escapeAttribute(category.slug)}')">
                            <span>Sort</span>
                            <div class="admin-quantity-action">
                                <input data-admin-action name="sort_order" type="number" min="0" step="1" value="${category.sort_order}" ${disabled}>
                                <button data-admin-action type="submit" ${disabled}>Save</button>
                            </div>
                        </form>
                    </div>
                </td>
            </tr>
        `).join("") || this.emptyTableRow("No categories are available yet.", 6);

        return this.renderPageTemplate("categories", {
            categoryCount: this.state.categories.length,
            categoryStatus: this.renderInventoryStatus("Categories are loading."),
            categoryActionDisabled: disabled,
            categoryRows,
        });
    }

    window.SecondMarketAdminPages = window.SecondMarketAdminPages || {};
    window.SecondMarketAdminPages.renderCategoriesPage = renderCategoriesPage;
})();
