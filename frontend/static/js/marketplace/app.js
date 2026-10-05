class SecondMarketApp {
            constructor() {
                this.state = {
                    currentView: 'home',
                    viewParams: {},
                    cart: [],
                    wishlist: [],
                    currency: { code: 'PHP', rate: 1, symbol: '₱' },
                    searchQuery: '',
                    filterState: { category: 'all', condition: 'all', priceMax: 5000, sortBy: 'featured' },
                    categories: [],
                    products: [],
                    searchResults: [],
                    productDetails: {},
                    marketplaceLoading: true,
                    marketplaceError: '',
                    searchLoading: false,
                    wishlistLoading: false,
                    productDetailLoading: false,
                    user: null,
                    authMode: 'login',
                    authLoading: false,
                    checkoutStep: 1,
                    quickViewProduct: null
                };

                this.init();
            }

            init() {
                this.render();
                this.updateCounters();
                this.setupKeyboardListeners();
                this.loadCurrentUser();
                this.loadMarketplaceData();
            }

            async loadMarketplaceData() {
                if (!window.SecondMarketMarketplaceAPI) {
                    this.state.marketplaceLoading = false;
                    this.state.marketplaceError = 'Marketplace client is unavailable.';
                    this.render();
                    return;
                }

                this.state.marketplaceLoading = true;
                this.state.marketplaceError = '';
                this.render();

                try {
                    const [categories, productResult] = await Promise.all([
                        window.SecondMarketMarketplaceAPI.listCategories(),
                        window.SecondMarketMarketplaceAPI.listProducts(this.marketplaceQueryParams())
                    ]);
                    this.state.categories = categories;
                    this.state.products = productResult.products;
                    this.state.marketplaceLoading = false;
                    this.render();
                } catch (error) {
                    this.state.marketplaceLoading = false;
                    this.state.marketplaceError = window.SecondMarketMarketplaceAPI.formatError(error);
                    this.render();
                }
            }

            async refreshMarketplaceProducts() {
                if (!window.SecondMarketMarketplaceAPI) return;

                this.state.marketplaceLoading = true;
                this.state.marketplaceError = '';
                this.render();

                try {
                    const productResult = await window.SecondMarketMarketplaceAPI.listProducts(this.marketplaceQueryParams());
                    this.state.products = productResult.products;
                } catch (error) {
                    this.state.marketplaceError = window.SecondMarketMarketplaceAPI.formatError(error);
                } finally {
                    this.state.marketplaceLoading = false;
                    this.render();
                }
            }

            marketplaceQueryParams(overrides = {}) {
                const category = overrides.category ?? this.state.filterState.category;
                const condition = overrides.condition ?? this.state.filterState.condition;
                const sortBy = overrides.sortBy ?? this.state.filterState.sortBy;
                const priceMax = overrides.priceMax ?? this.state.filterState.priceMax;
                const searchQuery = overrides.q ?? this.state.searchQuery;
                const sortMap = {
                    featured: 'recent',
                    'price-low': 'price_asc',
                    'price-high': 'price_desc',
                    title: 'title_asc'
                };

                return {
                    q: searchQuery.trim(),
                    category,
                    condition,
                    sort: sortMap[sortBy] || 'recent',
                    max_price_cents: priceMax ? priceMax * 100 : ''
                };
            }

            applyMarketplaceFilters(nextFilters = {}) {
                this.state.filterState = {
                    ...this.state.filterState,
                    ...nextFilters
                };
                if (Object.prototype.hasOwnProperty.call(nextFilters, 'category')) {
                    this.state.viewParams.category = nextFilters.category;
                }
                this.refreshMarketplaceProducts();
            }

            applyCatalogSearch(event) {
                event.preventDefault();
                const form = new FormData(event.currentTarget);
                this.state.searchQuery = (form.get('q') || '').toString();
                this.refreshMarketplaceProducts();
            }

            clearCatalogSearch() {
                this.state.searchQuery = '';
                this.refreshMarketplaceProducts();
            }

            resetMarketplaceFilters() {
                this.state.searchQuery = '';
                this.state.filterState = { category: 'all', condition: 'all', priceMax: 5000, sortBy: 'featured' };
                this.state.viewParams = {};
                this.refreshMarketplaceProducts();
            }

            async loadProductDetail(productSlug) {
                if (!window.SecondMarketMarketplaceAPI || this.state.productDetails[productSlug]) return;

                this.state.productDetailLoading = true;
                this.render();

                try {
                    const product = await window.SecondMarketMarketplaceAPI.getProduct(productSlug);
                    this.state.productDetails[productSlug] = product;
                    const productIndex = this.state.products.findIndex((item) => item.id === productSlug);
                    if (productIndex > -1) {
                        this.state.products[productIndex] = product;
                    }
                } catch (error) {
                    this.showToast(window.SecondMarketMarketplaceAPI.formatError(error), 'error');
                } finally {
                    this.state.productDetailLoading = false;
                    this.render();
                }
            }

            getProductById(productId) {
                return this.state.productDetails[productId] || this.state.products.find((product) => product.id === productId) || null;
            }

            categoryName(categorySlug) {
                if (!categorySlug || categorySlug === 'all') return 'All Secondhand Finds';
                return this.state.categories.find((category) => category.slug === categorySlug)?.name || categorySlug;
            }

            categoryImage(index) {
                const images = [
                    '/static/productImages/headphones/m502t0016_13june22_headphone_03.jpg',
                    '/static/productImages/shirts/men-rsquo-s-black-short-sleeve-shirt-casual-apparel.jpg',
                    '/static/productImages/smartphones/330788-P9NVVS-165.jpg',
                    '/static/productImages/bags/young-girl-with-gray-student-backpack.jpg'
                ];
                return images[index % images.length];
            }

            renderMarketplaceStatus(products, loadingMessage) {
                if (this.state.marketplaceLoading) {
                    return `
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6" aria-live="polite">
                            ${[1, 2, 3].map(() => `
                                <div class="bg-white border border-[#D7CEC1]/60 rounded overflow-hidden">
                                    <div class="h-56 skeleton"></div>
                                    <div class="p-5 space-y-3">
                                        <div class="h-3 skeleton rounded"></div>
                                        <div class="h-5 skeleton rounded"></div>
                                        <div class="h-3 skeleton rounded w-1/2"></div>
                                    </div>
                                </div>
                            `).join('')}
                            <p class="sr-only">${loadingMessage}</p>
                        </div>
                    `;
                }

                if (this.state.marketplaceError) {
                    return `
                        <div class="text-center py-12 bg-white rounded border border-[#D7CEC1]/50">
                            <p class="text-sm text-[#776B56]">${this.state.marketplaceError}</p>
                            <button onclick="app.loadMarketplaceData()" class="btn-outline mt-4 text-xs py-2">Try Again</button>
                        </div>
                    `;
                }

                if (!products.length && this.state.products.length === 0) {
                    return `
                        <div class="text-center py-12 bg-white rounded border border-[#D7CEC1]/50">
                            <p class="text-sm text-[#776B56]">No products are available right now.</p>
                        </div>
                    `;
                }

                return '';
            }

            loadPageTemplate(templateName) {
                this.templateCache = this.templateCache || {};
                if (this.templateCache[templateName]) {
                    return this.templateCache[templateName];
                }

                const request = new XMLHttpRequest();
                request.open('GET', `/marketplace/pages/${templateName}.html`, false);
                request.send(null);

                if (request.status < 200 || request.status >= 300) {
                    return `
                        <section class="max-w-3xl mx-auto px-4 py-16 text-center">
                            <h1 class="font-serif text-3xl font-semibold text-[#4E4638]">Page Template Missing</h1>
                            <p class="text-sm text-[#776B56] mt-3">${templateName} could not be loaded.</p>
                        </section>
                    `;
                }

                this.templateCache[templateName] = request.responseText;
                return this.templateCache[templateName];
            }

            renderPageTemplate(templateName, replacements = {}) {
                return Object.entries(replacements).reduce(
                    (html, [key, value]) => html.replaceAll(`{{${key}}}`, value ?? ''),
                    this.loadPageTemplate(templateName)
                );
            }

            normalizeApiUser(user) {
                if (!user) return null;

                return {
                    id: user.id,
                    name: `${user.first_name} ${user.last_name}`.trim(),
                    firstName: user.first_name,
                    lastName: user.last_name,
                    email: user.email,
                    phone: user.phone || 'Not provided',
                    role: user.role,
                    status: user.status,
                    addresses: [],
                    orders: []
                };
            }

            async loadCurrentUser() {
                if (!window.SecondMarketAuthAPI) return;

                try {
                    const payload = await window.SecondMarketAuthAPI.me();
                    this.state.user = payload.data.authenticated ? this.normalizeApiUser(payload.data.user) : null;
                    const nextView = sessionStorage.getItem('secondmarket:nextView');
                    if (this.state.user && nextView) {
                        sessionStorage.removeItem('secondmarket:nextView');
                        this.navigate(nextView);
                        this.loadWishlist();
                        return;
                    }
                    if (this.state.currentView === 'account' || this.state.currentView === 'auth') {
                        this.render();
                    }
                    if (this.state.user) {
                        this.loadWishlist();
                        this.loadCart();
                    }
                } catch (error) {
                    this.state.user = null;
                }
            }

            normalizeCartItem(item) {
                return {
                    product: {
                        id: item.product.slug,
                        title: item.product.title,
                        price: item.unit_price.amount,
                        image: item.product.primary_image?.url || '/static/productImages/bags/young-girl-with-gray-student-backpack.jpg',
                        imageAlt: item.product.primary_image?.alt_text || item.product.title,
                        condition: item.product.condition,
                        category: item.product.category?.name || 'Secondhand item',
                    },
                    quantity: item.quantity,
                    maxQuantity: item.max_quantity,
                };
            }

            syncCartFromApi(cart) {
                this.state.cart = (cart?.items || []).map((item) => this.normalizeCartItem(item));
                this.updateCounters();
                if (!document.getElementById('cart-drawer')?.classList.contains('translate-x-full')) {
                    this.renderCartDrawer();
                }
            }

            async loadCart() {
                if (!this.state.user || !window.SecondMarketCheckoutAPI) return;

                try {
                    const cart = await window.SecondMarketCheckoutAPI.getCart();
                    this.syncCartFromApi(cart);
                } catch (error) {
                    this.showToast(window.SecondMarketCheckoutAPI.formatError(error), 'error');
                }
            }

            async loadWishlist() {
                if (!this.state.user || !window.SecondMarketMarketplaceAPI) return;

                this.state.wishlistLoading = true;
                try {
                    const wishlist = await window.SecondMarketMarketplaceAPI.listWishlist();
                    this.state.wishlist = wishlist.slugs;
                    wishlist.products.forEach((product) => {
                        this.state.productDetails[product.id] = product;
                    });
                    this.updateCounters();
                    if (this.state.currentView === 'wishlist') {
                        this.render();
                    }
                } catch (error) {
                    this.showToast(window.SecondMarketMarketplaceAPI.formatError(error), 'error');
                } finally {
                    this.state.wishlistLoading = false;
                }
            }

            formatPrice(priceAmount) {
                const converted = priceAmount * this.state.currency.rate;
                return `${this.state.currency.symbol}${converted.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
            }

            setCurrency(code, rate, symbol) {
                this.state.currency = { code, rate, symbol };
                document.getElementById('current-currency').textContent = `${code} (${symbol})`;
                this.render();
                this.showToast(`Currency changed to ${code}`, 'info');
            }

            updateCounters() {
                const cartCount = this.state.cart.reduce((acc, item) => acc + item.quantity, 0);
                document.getElementById('cart-counter').textContent = cartCount;
                document.getElementById('drawer-cart-count').textContent = `(${cartCount} items)`;
                document.getElementById('wishlist-counter').textContent = this.state.wishlist.length;
            }

            showToast(message, type = 'success') {
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = `p-4 rounded shadow-lg bg-[#4E4638] text-white text-xs flex items-center justify-between gap-3 fade-in border-l-4 ${type === 'error' ? 'border-red-500' : 'border-[#9A8B74]'} pointer-events-auto`;
                toast.innerHTML = `
                    <span>${message}</span>
                    <button onclick="this.parentElement.remove()" class="text-[#B9A995] hover:text-white">&times;</button>
                `;
                container.appendChild(toast);
                setTimeout(() => toast.remove(), 4000);
            }

            navigate(viewName, params = {}) {
                this.state.currentView = viewName;
                this.state.viewParams = params;
                if (viewName === 'shop') {
                    this.state.filterState.category = params.category || 'all';
                    this.refreshMarketplaceProducts();
                }
                if (viewName === 'pdp' && params.id) {
                    this.state.pdpImage = null;
                    this.state.pdpColor = null;
                    this.state.pdpSize = null;
                    this.loadProductDetail(params.id);
                }
                window.scrollTo({ top: 0, behavior: 'smooth' });
                this.render();
            }

            setAuthMode(mode) {
                this.state.authMode = mode;
                this.render();
            }

            async handleLogin(event) {
                event.preventDefault();
                const form = new FormData(event.currentTarget);
                this.state.authLoading = true;
                this.render();

                try {
                    const payload = await window.SecondMarketAuthAPI.login({
                        email: form.get('email'),
                        password: form.get('password')
                    });
                    this.state.user = this.normalizeApiUser(payload.data.user);
                    this.state.authLoading = false;
                    await this.loadWishlist();
                    this.showToast('You are now signed in.');
                    this.navigate('account');
                } catch (error) {
                    this.showToast(window.SecondMarketAuthAPI.formatError(error), 'error');
                    this.state.authLoading = false;
                    this.render();
                }
            }

            async handleRegister(event) {
                event.preventDefault();
                const form = new FormData(event.currentTarget);
                this.state.authLoading = true;
                this.render();

                try {
                    const payload = await window.SecondMarketAuthAPI.register({
                        email: form.get('email'),
                        password: form.get('password'),
                        first_name: form.get('first_name'),
                        last_name: form.get('last_name'),
                        role: 'buyer',
                        phone: form.get('phone')
                    });
                    this.state.user = this.normalizeApiUser(payload.data.user);
                    this.state.authLoading = false;
                    await this.loadWishlist();
                    this.showToast('Your buyer account is ready.');
                    this.navigate('account');
                } catch (error) {
                    this.showToast(window.SecondMarketAuthAPI.formatError(error), 'error');
                    this.state.authLoading = false;
                    this.render();
                }
            }

            async handleLogout() {
                try {
                    await window.SecondMarketAuthAPI.logout();
                } catch (error) {
                    this.showToast(window.SecondMarketAuthAPI.formatError(error), 'error');
                }

                this.state.user = null;
                this.state.wishlist = [];
                this.showToast('You have been signed out.', 'info');
                this.navigate('auth');
            }

            async toggleCartDrawer() {
                const drawer = document.getElementById('cart-drawer');
                const backdrop = document.getElementById('cart-drawer-backdrop');
                const isOpen = !drawer.classList.contains('translate-x-full');
                
                if (isOpen) {
                    drawer.classList.add('translate-x-full');
                    backdrop.classList.add('hidden');
                } else {
                    await this.loadCart();
                    this.renderCartDrawer();
                    drawer.classList.remove('translate-x-full');
                    backdrop.classList.remove('hidden');
                }
            }

            toggleMobileMenu() {
                const menu = document.getElementById('mobile-menu');
                const backdrop = document.getElementById('mobile-menu-backdrop');
                const isOpen = !menu.classList.contains('-translate-x-full');
                
                if (isOpen) {
                    menu.classList.add('-translate-x-full');
                    backdrop.classList.add('hidden');
                } else {
                    menu.classList.remove('-translate-x-full');
                    backdrop.classList.remove('hidden');
                }
            }

            toggleSearchModal() {
                const modal = document.getElementById('search-modal');
                modal.classList.toggle('hidden');
                if (!modal.classList.contains('hidden')) {
                    document.getElementById('search-input').focus();
                }
            }

            async handleSearchInput(query) {
                const container = document.getElementById('search-results');
                if (!query.trim()) {
                    container.innerHTML = '<p class="text-xs text-[#776B56] italic">Start typing to see live inventory results...</p>';
                    return;
                }

                container.innerHTML = '<p class="text-xs text-[#776B56] italic">Searching marketplace inventory...</p>';

                try {
                    const result = await window.SecondMarketMarketplaceAPI.listProducts({ q: query.trim(), sort: 'recent' });
                    this.state.searchResults = result.products;
                } catch (error) {
                    container.innerHTML = `<p class="text-xs text-[#776B56]">${window.SecondMarketMarketplaceAPI.formatError(error)}</p>`;
                    return;
                }

                if (this.state.searchResults.length === 0) {
                    container.innerHTML = '<p class="text-xs text-[#776B56]">No matching products found in marketplace inventory.</p>';
                    return;
                }

                container.innerHTML = this.state.searchResults.map(p => `
                    <div onclick="app.toggleSearchModal(); app.navigate('pdp', {id: '${p.id}'})" class="flex items-center gap-4 p-2 hover:bg-[#D7CEC1]/30 rounded cursor-pointer transition">
                        <img src="${p.image}" class="w-12 h-12 object-cover rounded" alt="${p.title}">
                        <div>
                            <p class="text-sm font-semibold text-[#4E4638]">${p.title}</p>
                            <p class="text-xs text-[#776B56]">${p.category} | ${this.formatPrice(p.price)}</p>
                        </div>
                    </div>
                `).join('');
            }

            quickSearch(term) {
                document.getElementById('search-input').value = term;
                this.handleSearchInput(term);
            }

            setupKeyboardListeners() {
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape') {
                        document.getElementById('search-modal').classList.add('hidden');
                        if (!document.getElementById('cart-drawer').classList.contains('translate-x-full')) {
                            this.toggleCartDrawer();
                        }
                    }
                });
            }

            async addToCart(productId, selectedColor = null, selectedSize = null, quantity = 1) {
                const product = this.getProductById(productId);
                if (!product || !product.inStock) {
                    this.showToast('Sorry, this product is currently out of stock.', 'error');
                    return;
                }

                if (!this.state.user) {
                    sessionStorage.setItem('secondmarket:nextView', 'shop');
                    this.showToast('Please sign in as a buyer to save items to your cart.', 'info');
                    window.location.href = '/login.html';
                    return;
                }

                if (!window.SecondMarketCheckoutAPI) {
                    this.showToast('Cart service is temporarily unavailable.', 'error');
                    return;
                }

                try {
                    const cart = await window.SecondMarketCheckoutAPI.addItem(product.slug || product.id, quantity);
                    this.syncCartFromApi(cart);
                    this.showToast(`Added ${product.title} to your bag.`);
                    this.toggleCartDrawer();
                } catch (error) {
                    this.showToast(window.SecondMarketCheckoutAPI.formatError(error), 'error');
                }
            }

            async updateCartQuantity(index, newQty) {
                const item = this.state.cart[index];
                if (!item || !window.SecondMarketCheckoutAPI) return;

                try {
                    const cart = newQty <= 0
                        ? await window.SecondMarketCheckoutAPI.removeItem(item.product.id)
                        : await window.SecondMarketCheckoutAPI.updateItem(item.product.id, newQty);
                    this.syncCartFromApi(cart);
                } catch (error) {
                    this.showToast(window.SecondMarketCheckoutAPI.formatError(error), 'error');
                }
            }

            async toggleWishlist(productId) {
                const idx = this.state.wishlist.indexOf(productId);

                if (this.state.user && window.SecondMarketMarketplaceAPI) {
                    try {
                        if (idx > -1) {
                            await window.SecondMarketMarketplaceAPI.removeWishlistItem(productId);
                            this.state.wishlist.splice(idx, 1);
                            this.showToast('Removed item from your wishlist.', 'info');
                        } else {
                            await window.SecondMarketMarketplaceAPI.addWishlistItem(productId);
                            this.state.wishlist.push(productId);
                            this.showToast('Saved item to your wishlist.');
                        }
                    } catch (error) {
                        this.showToast(window.SecondMarketMarketplaceAPI.formatError(error), 'error');
                        return;
                    }
                } else if (idx > -1) {
                    this.state.wishlist.splice(idx, 1);
                    this.showToast('Removed temporary wishlist item.', 'info');
                } else {
                    this.state.wishlist.push(productId);
                    this.showToast('Saved temporarily. Sign in to keep your wishlist.');
                }

                this.updateCounters();
                this.render();
            }

            render() {
                const main = document.getElementById('main-content');
                main.innerHTML = '';

                switch (this.state.currentView) {
                    case 'home':
                        main.innerHTML = this.renderHomeView();
                        break;
                    case 'shop':
                        main.innerHTML = this.renderShopView();
                        break;
                    case 'pdp':
                        main.innerHTML = this.renderPDPView(this.state.viewParams.id || this.state.products[0]?.id);
                        break;
                    case 'cart':
                        main.innerHTML = this.renderCartView();
                        break;
                    case 'checkout':
                        main.innerHTML = this.renderCheckoutView();
                        break;
                    case 'order-confirmation':
                        main.innerHTML = this.renderOrderConfirmationView();
                        break;
                    case 'auth':
                        main.innerHTML = this.renderAuthView();
                        break;
                    case 'account':
                        main.innerHTML = this.renderAccountView();
                        break;
                    case 'wishlist':
                        main.innerHTML = this.renderWishlistView();
                        break;
                    default:
                        main.innerHTML = this.renderHomeView();
                }
            }

            renderHomeView() {
                return window.SecondMarketMarketplacePages.renderHomeView.call(this);
            }

            renderProductCard(product) {
                return window.SecondMarketMarketplaceComponents.renderProductCard.call(this, product);
            }

            renderShopView() {
                return window.SecondMarketMarketplacePages.renderShopView.call(this);
            }

            renderPDPView(productId) {
                return window.SecondMarketMarketplacePages.renderPDPView.call(this, productId);
            }

            renderCartDrawer() {
                const itemsContainer = document.getElementById('cart-drawer-items');
                if (!itemsContainer) return;

                if (this.state.cart.length === 0) {
                    itemsContainer.innerHTML = `
                        <div class="text-center py-12 space-y-3">
                            <p class="text-sm text-[#776B56]">Your selection bag is currently empty.</p>
                            <button onclick="app.toggleCartDrawer(); app.navigate('shop');" class="btn-outline text-xs py-2">Explore Studio Catalog</button>
                        </div>
                    `;
                    document.getElementById('cart-drawer-subtotal').textContent = this.formatPrice(0);
                    return;
                }

                let subtotal = 0;
                itemsContainer.innerHTML = this.state.cart.map((item, idx) => {
                    const itemTotal = item.product.price * item.quantity;
                    subtotal += itemTotal;
                    return `
                        <div class="flex gap-4 p-3 bg-white rounded border border-[#D7CEC1]/60">
                            <img src="${item.product.image}" class="w-16 h-16 object-cover rounded" alt="${item.product.title}">
                            <div class="flex-grow space-y-1">
                                <h4 class="text-xs font-semibold text-[#4E4638] line-clamp-1">${item.product.title}</h4>
                                <p class="text-[10px] text-[#776B56]">${item.product.category} | ${item.product.condition}</p>
                                <div class="flex justify-between items-center pt-1">
                                    <div class="flex items-center border border-[#D7CEC1] rounded text-[10px]">
                                        <button onclick="app.updateCartQuantity(${idx}, ${item.quantity - 1})" class="px-2 py-0.5 text-[#776B56]">-</button>
                                        <span class="px-2 font-semibold">${item.quantity}</span>
                                        <button onclick="app.updateCartQuantity(${idx}, ${item.quantity + 1})" class="px-2 py-0.5 text-[#776B56]">+</button>
                                    </div>
                                    <span class="text-xs font-bold text-[#4E4638]">${this.formatPrice(itemTotal)}</span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');

                document.getElementById('cart-drawer-subtotal').textContent = this.formatPrice(subtotal);
            }

            renderCartView() {
                const subtotal = this.state.cart.reduce((acc, i) => acc + (i.product.price * i.quantity), 0);
                const shipping = subtotal > 300 ? 0 : 45;

                return `
                    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                        <h1 class="font-serif text-3xl font-semibold text-[#4E4638] mb-8">Shopping Bag Overview</h1>
                        
                        ${this.state.cart.length === 0 ? `
                            <div class="text-center py-16 bg-white rounded border border-[#D7CEC1]">
                                <p class="text-sm text-[#776B56]">Your bag is empty.</p>
                                <button onclick="app.navigate('shop')" class="btn-primary mt-4 text-xs">Continue Shopping</button>
                            </div>
                        ` : `
                            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                <div class="lg:col-span-2 space-y-4">
                                    ${this.state.cart.map((item, idx) => `
                                        <div class="flex flex-col sm:flex-row items-center justify-between p-4 bg-white border border-[#D7CEC1] rounded gap-4">
                                            <div class="flex items-center gap-4 w-full sm:w-auto">
                                                <img src="${item.product.image}" class="w-20 h-20 object-cover rounded" alt="${item.product.title}">
                                                <div>
                                                    <h3 class="font-serif text-base font-semibold text-[#4E4638]">${item.product.title}</h3>
                                                    <p class="text-xs text-[#776B56]">${item.product.category} | ${item.product.condition}</p>
                                                    <span class="text-xs font-bold text-[#4E4638] mt-1 block">${this.formatPrice(item.product.price)}</span>
                                                </div>
                                            </div>

                                            <div class="flex items-center justify-between w-full sm:w-auto gap-6">
                                                <div class="flex items-center border border-[#D7CEC1] rounded bg-white">
                                                    <button onclick="app.updateCartQuantity(${idx}, ${item.quantity - 1})" class="px-3 py-1 text-xs">-</button>
                                                    <span class="px-3 text-xs font-semibold">${item.quantity}</span>
                                                    <button onclick="app.updateCartQuantity(${idx}, ${item.quantity + 1})" class="px-3 py-1 text-xs">+</button>
                                                </div>
                                                <button onclick="app.updateCartQuantity(${idx}, 0)" class="text-xs text-[#776B56] hover:text-red-600">Remove</button>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>

                                <!-- Summary Card -->
                                <div class="p-6 bg-white border border-[#D7CEC1] rounded space-y-4 h-fit">
                                    <h2 class="font-serif text-lg font-semibold text-[#4E4638]">Order Summary</h2>
                                    <div class="space-y-2 text-xs border-b border-[#D7CEC1] pb-4">
                                        <div class="flex justify-between text-[#776B56]">
                                            <span>Subtotal</span>
                                            <span class="font-bold text-[#4E4638]">${this.formatPrice(subtotal)}</span>
                                        </div>
                                        <div class="flex justify-between text-[#776B56]">
                                            <span>Estimated Express Shipping</span>
                                            <span class="font-bold text-[#4E4638]">${shipping === 0 ? 'Complimentary' : this.formatPrice(shipping)}</span>
                                        </div>
                                    </div>
                                    <div class="flex justify-between text-sm font-bold text-[#4E4638]">
                                        <span>Total</span>
                                        <span>${this.formatPrice(subtotal + shipping)}</span>
                                    </div>
                                    <button onclick="window.location.href='/checkout'" class="btn-primary w-full py-3 text-xs uppercase tracking-widest">Proceed to Checkout</button>
                                </div>
                            </div>
                        `}
                    </div>
                `;
            }

            renderCheckoutView() {
                if (!this.state.user) {
                    return window.SecondMarketAuthViews.renderCheckoutAuthRequiredView();
                }

                const subtotal = this.state.cart.reduce((acc, i) => acc + (i.product.price * i.quantity), 0);
                const defaultAddress = this.state.user.addresses[0] || { line1: '', city: '', state: '', zip: '' };

                return `
                    <div class="max-w-5xl mx-auto px-4 py-10">
                        <h1 class="font-serif text-3xl font-semibold text-[#4E4638] mb-8 text-center">Express Checkout</h1>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <!-- Step Form -->
                            <div class="md:col-span-2 space-y-6">
                                <form onsubmit="event.preventDefault(); app.navigate('order-confirmation');" class="bg-white p-6 border border-[#D7CEC1] rounded space-y-4">
                                    <h2 class="font-serif text-xl font-semibold text-[#4E4638]">Shipping & Delivery Address</h2>
                                    
                                    <div class="grid grid-cols-2 gap-4">
                                        <div>
                                            <label class="block text-xs font-semibold text-[#776B56] mb-1">First Name</label>
                                            <input type="text" required value="${this.state.user.name.split(' ')[0]}" class="form-input">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-[#776B56] mb-1">Last Name</label>
                                            <input type="text" required value="${this.state.user.name.split(' ')[1] || ''}" class="form-input">
                                        </div>
                                    </div>

                                    <div>
                                        <label class="block text-xs font-semibold text-[#776B56] mb-1">Street Address</label>
                                            <input type="text" required value="${defaultAddress.line1}" class="form-input">
                                    </div>

                                    <div class="grid grid-cols-3 gap-4">
                                        <div>
                                            <label class="block text-xs font-semibold text-[#776B56] mb-1">City</label>
                                            <input type="text" required value="${defaultAddress.city}" class="form-input">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-[#776B56] mb-1">State / Region</label>
                                            <input type="text" required value="${defaultAddress.state}" class="form-input">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-[#776B56] mb-1">Zip Code</label>
                                            <input type="text" required value="${defaultAddress.zip}" class="form-input">
                                        </div>
                                    </div>

                                    <h2 class="font-serif text-xl font-semibold text-[#4E4638] pt-4 border-t border-[#D7CEC1]">Payment Method</h2>
                                    <div class="p-3 border rounded border-[#9A8B74] bg-[#FAF8F5] text-xs font-semibold text-[#4E4638]">
                                        ðŸ’³ Credit Card (Encrypted Mock Authorization)
                                    </div>

                                    <button type="submit" class="btn-primary w-full py-3.5 text-xs uppercase tracking-widest mt-4">Place Order & Authorize Payment</button>
                                </form>
                            </div>

                            <!-- Order Summary Side Panel -->
                            <div class="bg-white p-6 border border-[#D7CEC1] rounded space-y-4 h-fit">
                                <h3 class="font-serif text-lg font-semibold text-[#4E4638]">Summary</h3>
                                <div class="space-y-3">
                                    ${this.state.cart.map(i => `
                                        <div class="flex justify-between text-xs">
                                            <span>${i.product.title} (x${i.quantity})</span>
                                            <span class="font-semibold">${this.formatPrice(i.product.price * i.quantity)}</span>
                                        </div>
                                    `).join('')}
                                </div>
                                <div class="pt-3 border-t border-[#D7CEC1] flex justify-between font-bold text-sm text-[#4E4638]">
                                    <span>Total Due</span>
                                    <span>${this.formatPrice(subtotal)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

            renderOrderConfirmationView() {
                const orderNum = 'AUR-' + Math.floor(100000 + Math.random() * 900000);
                this.state.cart = []; // Empty bag on order placement
                this.updateCounters();

                return `
                    <div class="max-w-3xl mx-auto px-4 py-16 text-center space-y-6">
                        <div class="w-16 h-16 bg-[#EDF6F1] text-[#3F7A54] rounded-full flex items-center justify-center mx-auto text-2xl font-bold">âœ“</div>
                        <h1 class="font-serif text-4xl font-semibold text-[#4E4638]">Order Confirmed</h1>
                        <p class="text-sm text-[#776B56]">Thank you for your order. Reference Number: <span class="font-bold text-[#4E4638]">${orderNum}</span></p>
                        <p class="text-xs text-[#776B56] max-w-md mx-auto">A confirmation receipt and courier tracking details have been dispatched to your email address.</p>
                        <button onclick="app.navigate('home')" class="btn-primary py-3 px-8 text-xs uppercase tracking-widest">Return to Home Studio</button>
                    </div>
                `;
            }

            renderAuthView() {
                return window.SecondMarketAuthViews.renderAuthView(this.state);
                const isRegister = this.state.authMode === 'register';
                const submitText = this.state.authLoading ? 'Please wait...' : (isRegister ? 'Create Buyer Account' : 'Sign In');
// login
                return `
                    <section class="auth-shell" aria-labelledby="auth-title">
                        <div class="auth-panel">
                            <h1 id="auth-title" class="font-serif text-2xl font-semibold text-[#4E4638] text-center mb-2">Customer Portal</h1>
                            <p class="text-xs text-[#776B56] text-center mb-6">Access your buyer account for saved items, checkout, and orders.</p>

                            <div class="auth-tabs" role="tablist" aria-label="Authentication mode">
                                <button type="button" onclick="app.setAuthMode('login')" class="auth-tab ${!isRegister ? 'is-active' : ''}" aria-selected="${!isRegister}">Sign In</button>
                                <button type="button" onclick="app.setAuthMode('register')" class="auth-tab ${isRegister ? 'is-active' : ''}" aria-selected="${isRegister}">Register</button>
                            </div>

                            <form onsubmit="${isRegister ? 'app.handleRegister(event)' : 'app.handleLogin(event)'}" class="auth-grid" novalidate>
                                ${isRegister ? `
                                    <div class="auth-grid two-columns">
                                        <div class="auth-field">
                                            <label for="register-first-name">First Name</label>
                                            <input id="register-first-name" name="first_name" type="text" required autocomplete="given-name" class="form-input">
                                        </div>
                                        <div class="auth-field">
                                            <label for="register-last-name">Last Name</label>
                                            <input id="register-last-name" name="last_name" type="text" required autocomplete="family-name" class="form-input">
                                        </div>
                                    </div>
                                    <div class="auth-field">
                                        <label for="register-phone">Phone</label>
                                        <input id="register-phone" name="phone" type="tel" autocomplete="tel" class="form-input">
                                    </div>
                                ` : ''}
                                <div class="auth-field">
                                    <label for="${isRegister ? 'register-email' : 'login-email'}">Email Address</label>
                                    <input id="${isRegister ? 'register-email' : 'login-email'}" name="email" type="email" required autocomplete="email" class="form-input">
                                </div>
                                <div class="auth-field">
                                    <label for="${isRegister ? 'register-password' : 'login-password'}">Password</label>
                                    <input id="${isRegister ? 'register-password' : 'login-password'}" name="password" type="password" required autocomplete="${isRegister ? 'new-password' : 'current-password'}" minlength="8" class="form-input">
                                </div>
                                <button type="submit" class="btn-primary w-full py-3 text-xs uppercase tracking-widest" ${this.state.authLoading ? 'disabled' : ''}>${submitText}</button>
                            </form>
                        </div>
                    </section>
                `;
                return `
                    <div class="max-w-md mx-auto px-4 py-16">
                        <div class="bg-white p-8 border border-[#D7CEC1] rounded shadow-subtle space-y-6">
                            <h1 class="font-serif text-2xl font-semibold text-[#4E4638] text-center">Customer Portal</h1>
                            <form onsubmit="event.preventDefault(); app.navigate('account');" class="space-y-4">
                                <div>
                                    <label class="block text-xs font-semibold text-[#776B56] mb-1">Email Address</label>
                                    <input type="email" required value="elena.rostova@design.com" class="form-input">
                                </div>
                                <div>
                                    <label class="block text-xs font-semibold text-[#776B56] mb-1">Password</label>
                                    <input type="password" required value="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢" class="form-input">
                                </div>
                                <button type="submit" class="btn-primary w-full py-3 text-xs uppercase tracking-widest">Sign In</button>
                            </form>
                        </div>
                    </div>
                `;
            }

            renderAccountView() {
                return window.SecondMarketAuthViews.renderAccountView(this.state, this.formatPrice.bind(this));
                if (!this.state.user) {
                    return `
                        <section class="auth-shell" aria-labelledby="account-required-title">
                            <div class="auth-panel text-center space-y-4">
                                <h1 id="account-required-title" class="font-serif text-2xl font-semibold text-[#4E4638]">Sign In Required</h1>
                                <p class="text-sm text-[#776B56]">Please sign in or create a buyer account to view your account details.</p>
                                <button onclick="app.navigate('auth')" class="btn-primary w-full py-3 text-xs uppercase tracking-widest">Go to Customer Portal</button>
                            </div>
                        </section>
                    `;
                }

                return `
                    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                        <h1 class="font-serif text-3xl font-semibold text-[#4E4638] mb-2">Welcome, ${this.state.user.name}</h1>
                        <p class="text-xs text-[#776B56] mb-4">${this.state.user.email} | ${this.state.user.role} account | ${this.state.user.status}</p>
                        <div class="account-actions">
                            <button onclick="app.handleLogout()" class="btn-outline py-2 text-xs uppercase tracking-widest">Sign Out</button>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div class="space-y-4">
                                <div class="bg-white p-6 border border-[#D7CEC1] rounded">
                                    <h3 class="font-serif text-lg font-semibold text-[#4E4638] mb-2">Profile</h3>
                                    <p class="text-xs text-[#776B56] leading-relaxed">
                                        ${this.state.user.name}<br>
                                        ${this.state.user.email}<br>
                                        ${this.state.user.phone}
                                    </p>
                                </div>
                            </div>

                            <div class="md:col-span-2 bg-white p-6 border border-[#D7CEC1] rounded space-y-4">
                                <h3 class="font-serif text-lg font-semibold text-[#4E4638]">Order History</h3>
                                ${this.state.user.orders.length === 0 ? `
                                    <p class="text-sm text-[#776B56]">No orders yet.</p>
                                ` : `<div class="divide-y divide-[#D7CEC1]">
                                    ${this.state.user.orders.map(o => `
                                        <div class="py-3 flex justify-between items-center text-xs">
                                            <div>
                                                <p class="font-bold text-[#4E4638]">${o.id}</p>
                                                <p class="text-[#776B56]">${o.date}</p>
                                            </div>
                                            <div class="text-right">
                                                <span class="badge badge-new">${o.status}</span>
                                                <p class="font-bold text-[#4E4638] mt-1">${this.formatPrice(o.total)}</p>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>`}
                            </div>
                        </div>
                    </div>
                `;
                return `
                    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                        <h1 class="font-serif text-3xl font-semibold text-[#4E4638] mb-2">Welcome, ${this.state.user.name}</h1>
                        <p class="text-xs text-[#776B56] mb-8">${this.state.user.email} â€¢ Client ID: #CLIENT-90218</p>

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div class="space-y-4">
                                <div class="bg-white p-6 border border-[#D7CEC1] rounded">
                                    <h3 class="font-serif text-lg font-semibold text-[#4E4638] mb-2">Default Address</h3>
                                    <p class="text-xs text-[#776B56] leading-relaxed">
                                        ${this.state.user.addresses[0].line1}<br>
                                        ${this.state.user.addresses[0].city}, ${this.state.user.addresses[0].state} ${this.state.user.addresses[0].zip}
                                    </p>
                                </div>
                            </div>

                            <div class="md:col-span-2 bg-white p-6 border border-[#D7CEC1] rounded space-y-4">
                                <h3 class="font-serif text-lg font-semibold text-[#4E4638]">Order History</h3>
                                <div class="divide-y divide-[#D7CEC1]">
                                    ${this.state.user.orders.map(o => `
                                        <div class="py-3 flex justify-between items-center text-xs">
                                            <div>
                                                <p class="font-bold text-[#4E4638]">${o.id}</p>
                                                <p class="text-[#776B56]">${o.date}</p>
                                            </div>
                                            <div class="text-right">
                                                <span class="badge badge-new">${o.status}</span>
                                                <p class="font-bold text-[#4E4638] mt-1">${this.formatPrice(o.total)}</p>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

            renderWishlistView() {
                return window.SecondMarketMarketplacePages.renderWishlistView.call(this);
            }
        }

        // INITIALIZE APP INSTANCE ON WINDOW LOAD
        let app;
        window.addEventListener('DOMContentLoaded', () => {
            app = new SecondMarketApp();
        });



