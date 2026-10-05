(function () {
    function optionList(options, selectedValue) {
        return options.map((option) => `
            <option value="${option.value}" ${option.value === selectedValue ? "selected" : ""}>${option.label}</option>
        `).join("");
    }

    function rowStatusOptions(product) {
        return optionList([
            { value: "draft", label: "Draft" },
            { value: "available", label: "Available" },
            { value: "reserved", label: "Reserved" },
            { value: "sold", label: "Sold" },
            { value: "hidden", label: "Hidden" },
        ], product.status);
    }

    function renderProductsPage() {
        const products = this.state.products;
        const disabled = this.actionDisabledAttribute();
        const statusOptions = optionList([
            { value: "all", label: "All Statuses" },
            { value: "draft", label: "Draft" },
            { value: "available", label: "Available" },
            { value: "reserved", label: "Reserved" },
            { value: "sold", label: "Sold" },
            { value: "hidden", label: "Hidden" },
        ], this.state.productFilters.status);
        const conditionOptions = optionList([
            { value: "all", label: "All Conditions" },
            { value: "new_other", label: "New Other" },
            { value: "like_new", label: "Like New" },
            { value: "good", label: "Good" },
            { value: "fair", label: "Fair" },
            { value: "for_repair", label: "For Repair" },
        ], this.state.productFilters.condition);
        const sortOptions = optionList([
            { value: "recent", label: "Recently Updated" },
            { value: "title_asc", label: "Title A to Z" },
            { value: "price_asc", label: "Price Low to High" },
            { value: "price_desc", label: "Price High to Low" },
            { value: "quantity_asc", label: "Quantity Low to High" },
            { value: "quantity_desc", label: "Quantity High to Low" },
        ], this.state.productFilters.sort);
        const productRows = products.map((product) => `
            <tr>
                <td>${this.productCell(product)}</td>
                <td>${this.escapeHtml(product.category?.name || "Uncategorized")}</td>
                <td>${this.conditionLabel(product.condition)}</td>
                <td>${this.statusBadge(product.status)}</td>
                <td>${product.quantity}</td>
                <td>${this.formatPrice(product.price)}</td>
                <td>
                    <div class="admin-inline-actions">
                        <label class="admin-row-control">
                            <span>Status</span>
                            <select data-admin-action onchange="adminApp.setProductStatus('${this.escapeAttribute(product.slug)}', this.value)" ${disabled}>
                                ${rowStatusOptions(product)}
                            </select>
                        </label>
                        <form class="admin-row-control" onsubmit="adminApp.setProductQuantity(event, '${this.escapeAttribute(product.slug)}')">
                            <span>Qty</span>
                            <div class="admin-quantity-action">
                                <input data-admin-action name="quantity" type="number" min="0" step="1" value="${product.quantity}" ${disabled}>
                                <button data-admin-action type="submit" ${disabled}>Save</button>
                            </div>
                        </form>
                    </div>
                </td>
            </tr>
        `).join("") || this.emptyTableRow("No products match the selected filters.", 7);

        return this.renderPageTemplate("products", {
            searchQuery: this.escapeAttribute(this.state.productFilters.q),
            statusOptions,
            conditionOptions,
            sortOptions,
            productCount: products.length,
            productStatus: this.renderInventoryStatus("Product inventory is loading."),
            productRows,
        });
    }

    window.SecondMarketAdminPages = window.SecondMarketAdminPages || {};
    window.SecondMarketAdminPages.renderProductsPage = renderProductsPage;
})();
