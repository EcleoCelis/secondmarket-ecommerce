(function () {
    function renderProductCard(product) {
                const isWishlisted = this.state.wishlist.includes(product.id);
                return `
                    <article class="group bg-white rounded border border-[#D7CEC1]/60 overflow-hidden shadow-subtle hover:shadow-medium transition duration-300 flex flex-col justify-between h-full">
                        <div class="relative marketplace-card-image bg-[#FAF8F5] overflow-hidden">
                            <img src="${product.image}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" alt="${product.title}">
                            
                            <!-- Badges -->
                            ${product.badge ? `
                                <div class="absolute top-3 left-3">
                                    <span class="badge ${product.badge === 'Sale' ? 'badge-sale' : product.badge === 'New' ? 'badge-new' : 'badge-out'}">${product.badge}</span>
                                </div>
                            ` : ''}

                            <!-- Wishlist Button -->
                            <button onclick="app.toggleWishlist('${product.id}')" class="absolute top-3 right-3 p-2 bg-white/80 hover:bg-white backdrop-blur-sm rounded-full text-[#4E4638] hover:text-[#9A8B74] transition shadow-sm" aria-label="Add to Wishlist">
                                <svg class="w-4 h-4 ${isWishlisted ? 'fill-[#9A8B74] text-[#9A8B74]' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.318 6.318a4.5 4.5 0 016.364 0L12 7.636l1.318-1.318a4.5 4.5 0 116.364 6.364L12 21.364l-7.682-7.682a4.5 4.5 0 010-6.364z"/></svg>
                            </button>

                            <!-- Quick Action Overlay -->
                            <div class="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-[#4E4638]/60 to-transparent opacity-0 group-hover:opacity-100 transition duration-300 flex gap-2">
                                <button onclick="app.navigate('pdp', {id: '${product.id}'})" class="btn-primary flex-1 py-2 text-xs">View Details</button>
                                <button onclick="app.addToCart('${product.id}')" class="btn-secondary py-2 px-3 text-xs" ${!product.inStock ? 'disabled' : ''}>Add</button>
                            </div>
                        </div>

                        <!-- Card Body -->
                        <div class="p-5 flex flex-col flex-grow justify-between">
                            <div>
                                <p class="text-[10px] uppercase tracking-widest text-[#776B56] font-semibold">${product.category}</p>
                                <h3 onclick="app.navigate('pdp', {id: '${product.id}'})" class="marketplace-card-title font-serif text-lg text-[#4E4638] font-medium hover:text-[#9A8B74] transition cursor-pointer mt-0.5">${product.title}</h3>
                                <p class="text-xs text-[#776B56] mt-2">${product.conditionLabel} | ${product.quantity} available</p>
                            </div>
                            <div class="mt-4 flex items-center justify-between pt-3 border-t border-[#FAF8F5]">
                                <div class="flex items-center gap-2">
                                    <span class="text-sm font-semibold text-[#4E4638]">${this.formatPrice(product.price)}</span>
                                    ${product.originalPrice ? `<span class="text-xs text-[#776B56] line-through">${this.formatPrice(product.originalPrice)}</span>` : ''}
                                </div>
                                <div class="flex items-center text-xs text-[#776B56]">
                                    <span>${product.inStock ? 'Available' : 'Unavailable'}</span>
                                </div>
                            </div>
                        </div>
                    </article>
                `;
            }
    window.SecondMarketMarketplaceComponents = window.SecondMarketMarketplaceComponents || {};
    window.SecondMarketMarketplaceComponents.renderProductCard = renderProductCard;
})();

