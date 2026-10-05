(function () {
    function renderHomeView() {
        const featuredProducts = this.state.products.slice(0, 3);
        const categoryTiles = this.state.categories.slice(0, 4);
        const categoryTileHtml = categoryTiles.map((cat, index) => `
            <div onclick="app.navigate('shop', {category: '${cat.slug}'})" class="group relative h-80 rounded overflow-hidden cursor-pointer shadow-subtle">
                <img src="${this.categoryImage(index)}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" alt="${cat.name}">
                <div class="absolute inset-0 bg-gradient-to-t from-[#4E4638]/80 via-transparent to-transparent"></div>
                <div class="absolute bottom-6 left-6 text-white">
                    <h3 class="font-serif text-xl">${cat.name}</h3>
                    <p class="text-xs text-[#B9A995] uppercase tracking-wider mt-1 group-hover:underline">${cat.productCount} available</p>
                </div>
            </div>
        `).join('');
        const featuredProductsHtml = featuredProducts.length ? `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                ${featuredProducts.map((product) => this.renderProductCard(product)).join('')}
            </div>
        ` : '';

        return this.renderPageTemplate('home', {
            categoryTiles: categoryTileHtml,
            featuredStatus: this.renderMarketplaceStatus(featuredProducts, 'Featured products are loading.'),
            featuredProducts: featuredProductsHtml,
        });
    }

    window.SecondMarketMarketplacePages = window.SecondMarketMarketplacePages || {};
    window.SecondMarketMarketplacePages.renderHomeView = renderHomeView;
})();
