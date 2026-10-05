(function () {
    function renderPDPView(productId) {
        const product = this.getProductById(productId);
        if (this.state.productDetailLoading) {
            return `
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12" aria-live="polite">
                        <div class="aspect-4/3 rounded skeleton"></div>
                        <div class="space-y-4">
                            <div class="h-4 skeleton rounded w-1/3"></div>
                            <div class="h-10 skeleton rounded"></div>
                            <div class="h-5 skeleton rounded w-1/2"></div>
                            <div class="h-24 skeleton rounded"></div>
                        </div>
                    </div>
                    <p class="sr-only">Product details are loading.</p>
                </div>
            `;
        }
        if (!product) {
            return `
                <div class="max-w-3xl mx-auto px-4 py-16 text-center">
                    <h1 class="font-serif text-3xl font-semibold text-[#4E4638]">Product Not Found</h1>
                    <p class="text-sm text-[#776B56] mt-3">This item may no longer be available.</p>
                    <button onclick="app.navigate('shop')" class="btn-primary mt-6 text-xs uppercase tracking-widest">Back To Catalog</button>
                </div>
            `;
        }

        const activeImage = this.state.pdpImage || product.gallery[0];
        const selectedColor = this.state.pdpColor || product.colors[0];
        const selectedSize = this.state.pdpSize || product.sizes[0];
        const quantitySelected = this.state.pdpQty || 1;
        const galleryButtons = product.gallery.map((image) => `
            <button onclick="app.state.pdpImage = '${image}'; app.render();" class="w-20 h-20 rounded border-2 ${activeImage === image ? 'border-[#9A8B74]' : 'border-transparent'} overflow-hidden flex-shrink-0">
                <img src="${image}" class="w-full h-full object-cover" alt="${product.title}">
            </button>
        `).join('');
        const colorButtons = product.colors.map((color) => `
            <button onclick="app.state.pdpColor = '${color}'; app.render();" class="px-3 py-1.5 border text-xs rounded ${selectedColor === color ? 'border-[#9A8B74] bg-[#9A8B74] text-white font-semibold' : 'border-[#D7CEC1] text-[#4E4638]'}">
                ${color}
            </button>
        `).join('');
        const sizeButtons = product.sizes.map((size) => `
            <button onclick="app.state.pdpSize = '${size}'; app.render();" class="px-3 py-1.5 border text-xs rounded ${selectedSize === size ? 'border-[#9A8B74] bg-[#9A8B74] text-white font-semibold' : 'border-[#D7CEC1] text-[#4E4638]'}">
                ${size}
            </button>
        `).join('');

        return this.renderPageTemplate('product-detail', {
            categorySlug: product.categorySlug,
            categoryName: product.category,
            title: product.title,
            activeImage,
            galleryButtons,
            price: this.formatPrice(product.price),
            conditionLabel: product.conditionLabel,
            quantity: product.quantity,
            description: product.description,
            selectedColor,
            selectedSize,
            colorButtons,
            sizeButtons,
            quantitySelected,
            productId: product.id,
            lineTotal: this.formatPrice(product.price * quantitySelected),
            material: product.specs.material,
            brand: product.specs.origin,
            dimensions: product.specs.dimensions,
            sellerName: product.seller?.name || 'SecondMarket seller',
        });
    }

    window.SecondMarketMarketplacePages = window.SecondMarketMarketplacePages || {};
    window.SecondMarketMarketplacePages.renderPDPView = renderPDPView;
})();
