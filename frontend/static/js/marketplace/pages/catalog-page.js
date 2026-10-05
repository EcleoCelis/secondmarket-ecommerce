(function () {
    function renderShopView() {
        const category = this.state.viewParams.category || this.state.filterState.category;
        const filtered = this.state.products;
        const categoryOptions = [{ name: 'All', slug: 'all', productCount: this.state.products.length }, ...this.state.categories];
        const conditionOptions = [
            { label: 'All Conditions', value: 'all' },
            { label: 'New Other', value: 'new_other' },
            { label: 'Like New', value: 'like_new' },
            { label: 'Good', value: 'good' },
            { label: 'Fair', value: 'fair' },
            { label: 'For Repair', value: 'for_repair' }
        ];
        const sortOptions = [
            { label: 'Featured First', value: 'featured' },
            { label: 'Price: Low to High', value: 'price-low' },
            { label: 'Price: High to Low', value: 'price-high' },
            { label: 'Title: A to Z', value: 'title' }
        ];
        const categoryOptionsHtml = categoryOptions.map((cat) => `
            <li>
                <button onclick="app.applyMarketplaceFilters({category: '${cat.slug}'})" class="w-full text-left py-1 hover:text-[#9A8B74] ${category === cat.slug ? 'font-bold text-[#9A8B74]' : 'text-[#776B56]'}">
                    ${cat.name} (${cat.productCount})
                </button>
            </li>
        `).join('');
        const conditionOptionsHtml = conditionOptions.map((option) => `
            <option value="${option.value}" ${this.state.filterState.condition === option.value ? 'selected' : ''}>${option.label}</option>
        `).join('');
        const sortOptionsHtml = sortOptions.map((option) => `
            <option value="${option.value}" ${this.state.filterState.sortBy === option.value ? 'selected' : ''}>${option.label}</option>
        `).join('');
        const productGrid = filtered.length ? `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                ${filtered.map((product) => this.renderProductCard(product)).join('')}
            </div>
        ` : '';
        const emptyState = !this.state.marketplaceLoading && !this.state.marketplaceError && filtered.length === 0 ? `
            <div class="text-center py-16 bg-white rounded border border-[#D7CEC1]/50">
                <p class="text-sm text-[#776B56]">No marketplace products match your active filter criteria.</p>
                <button onclick="app.resetMarketplaceFilters()" class="btn-outline mt-4 text-xs py-2">Reset All Filters</button>
            </div>
        ` : '';

        return this.renderPageTemplate('catalog', {
            categoryName: this.categoryName(category),
            productCount: filtered.length,
            sortOptions: sortOptionsHtml,
            searchQuery: this.state.searchQuery,
            clearSearchButton: this.state.searchQuery ? '<button type="button" onclick="app.clearCatalogSearch()" class="btn-outline text-xs uppercase tracking-widest">Clear</button>' : '',
            categoryOptions: categoryOptionsHtml,
            priceMax: this.state.filterState.priceMax,
            priceMinLabel: this.formatPrice(0),
            priceMaxLabel: this.formatPrice(this.state.filterState.priceMax),
            conditionOptions: conditionOptionsHtml,
            catalogStatus: this.renderMarketplaceStatus(filtered, 'Marketplace products are loading.'),
            emptyState,
            productGrid,
        });
    }

    window.SecondMarketMarketplacePages = window.SecondMarketMarketplacePages || {};
    window.SecondMarketMarketplacePages.renderShopView = renderShopView;
})();
