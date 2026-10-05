(function () {
    const BASE_URL = "/api/v1/marketplace";

    function conditionLabel(condition) {
        const labels = {
            new_other: "New Other",
            like_new: "Like New",
            good: "Good",
            fair: "Fair",
            for_repair: "For Repair"
        };
        return labels[condition] || "Secondhand";
    }

    async function request(path, options = {}) {
        const response = await fetch(`${BASE_URL}${path}`, {
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
                ...(options.headers || {})
            },
            ...options
        });
        const payload = await response.json().catch(() => ({}));

        if (!response.ok || payload.success === false) {
            const error = new Error(payload.error?.message || "Marketplace request failed.");
            error.status = response.status;
            error.details = payload.error?.details || {};
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

    function normalizeCategory(category) {
        return {
            id: category.id,
            name: category.name,
            slug: category.slug,
            description: category.description || "",
            productCount: category.product_count || 0
        };
    }

    function normalizeProduct(product) {
        const primaryImage = product.primary_image || product.images?.[0] || null;
        const images = product.images?.length
            ? product.images.map((image) => image.url)
            : [primaryImage?.url].filter(Boolean);

        return {
            id: product.slug,
            apiId: product.id,
            slug: product.slug,
            title: product.title,
            category: product.category?.name || "Marketplace",
            categorySlug: product.category?.slug || "",
            price: product.price?.amount || 0,
            priceCents: product.price?.amount_cents || 0,
            currency: product.price?.currency || "PHP",
            description: product.description || "",
            condition: product.condition,
            conditionLabel: conditionLabel(product.condition),
            status: product.status,
            quantity: product.quantity || 0,
            inStock: product.status === "available" && (product.quantity || 0) > 0,
            badge: conditionLabel(product.condition),
            image: primaryImage?.url || "/static/productImages/headphones/m502t0016_13june22_headphone_03.jpg",
            imageAlt: primaryImage?.alt_text || product.title,
            gallery: images.length ? images : [primaryImage?.url].filter(Boolean),
            colors: product.color ? [product.color] : ["As shown"],
            sizes: product.dimensions ? [product.dimensions] : ["Standard"],
            rating: "New",
            reviewsCount: 0,
            originalPrice: null,
            seller: product.seller || null,
            specs: {
                material: product.material || "Secondhand item",
                dimensions: product.dimensions || "See listing details",
                weight: "Not specified",
                origin: product.brand || "SecondMarket"
            }
        };
    }

    async function listCategories() {
        const payload = await request("/categories");
        return payload.data.map(normalizeCategory);
    }

    async function listProducts(filters = {}) {
        const payload = await request(`/products${buildQueryString(filters)}`);
        return {
            products: payload.data.map(normalizeProduct),
            count: payload.meta?.count || payload.data.length
        };
    }

    async function getProduct(slug) {
        const payload = await request(`/products/${encodeURIComponent(slug)}`);
        return normalizeProduct(payload.data);
    }

    async function listWishlist() {
        const payload = await request("/wishlist");
        return {
            products: payload.data.map(normalizeProduct),
            slugs: payload.data.map((product) => product.slug),
            count: payload.meta?.count || payload.data.length
        };
    }

    async function addWishlistItem(productSlug) {
        const payload = await request("/wishlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_slug: productSlug })
        });
        return normalizeProduct(payload.data);
    }

    async function removeWishlistItem(productSlug) {
        const payload = await request(`/wishlist/${encodeURIComponent(productSlug)}`, {
            method: "DELETE"
        });
        return payload.data;
    }

    function formatError(error) {
        return error?.message || "The marketplace is temporarily unavailable.";
    }

    window.SecondMarketMarketplaceAPI = {
        listCategories,
        listProducts,
        getProduct,
        listWishlist,
        addWishlistItem,
        removeWishlistItem,
        buildQueryString,
        formatError
    };
})();
