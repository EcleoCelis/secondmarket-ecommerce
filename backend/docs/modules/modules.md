# Module Development Roadmap

## Project

SecondMarket is a web-based secondhand e-commerce system built with HTML, CSS, JavaScript, and a Flask REST API.

## Roles

- Buyer: browses products, manages cart, places orders, tracks purchases, and reviews/report products.
- Admin as seller: manages categories, product listings, inventory status, orders, fulfillment, reports, and dashboard data.

## Implementation Sequence

| Module | Name | Purpose | Status |
| ---: | --- | --- | --- |
| 01 | System Foundation | Flask application structure, environment configuration, REST API architecture, frontend serving, shared response format, error handling, docs, and smoke tests. | Complete |
| 02 | Database & Core Domain Models | Users, roles, categories, secondhand products, product images, carts, orders, payments, shipping, reviews, and core relationships. | Complete |
| 03 | Authentication & Authorization | Buyer/admin registration, login, logout, password management, session handling, role-based authorization, and protected API routes. | Complete |
| 04 | Buyer Marketplace | Product catalog, category browsing, product details, search, filtering, sorting, wishlist, and responsive marketplace layout. | Complete |
| 05 | Admin Seller Management | Admin product lifecycle, category management, product images, availability, item condition, and secondhand inventory workflow. | Complete |
| 06 | Cart & Checkout | Cart persistence, item availability validation, order summary, address capture, payment method selection, and checkout confirmation. | Complete |
| 07 | Order & Fulfillment Management | Order creation, buyer order history, admin order list, status updates, cancellation rules, and fulfillment tracking. | Complete |
| 08 | Reviews, Reports & Moderation | Verified-purchase reviews, ratings, product reports, and admin moderation. | Planned |
| 09 | Notifications & Messaging | Account/order notifications and simple buyer-to-admin support messaging. | Planned |
| 10 | Admin Dashboard & Reports | Sales, orders, customers, products, inventory, revenue, exportable reports, and marketplace KPIs. | Planned |
| 11 | Security Hardening & QA | Input validation, CSRF/CORS policy, secure uploads, rate limiting, API tests, frontend checks, and regression testing. | Planned |
| 12 | Deployment & Monitoring | Production configuration, database migration, backups, logging, health checks, deployment, and operational verification. | Planned |

## Module 01 Acceptance Criteria

- Flask starts through an application factory.
- API endpoints are versioned under `/api/v1`.
- JSON responses use a consistent success/error envelope.
- Health and system metadata endpoints are available.
- The existing storefront is served by Flask at `/`.
- Environment configuration is centralized.
- Smoke tests cover the root page, health endpoint, metadata endpoint, and 404 response shape.

## Module 02 Implementation Sequence

### Step 1 - Database Foundation

Build and verify the database integration layer before adding domain tables.

- Files: `backend/app/extensions.py`, `backend/app/__init__.py`, `backend/app/core/config.py`, `.env.example`, `requirements.txt`, and `tests/test_database_foundation.py`.
- Purpose: initialize Flask-SQLAlchemy and Flask-Migrate from the app factory, centralize the PostgreSQL connection string, and confirm an isolated test database can be created.
- Verification: run `py -m pytest tests/test_database_foundation.py tests/test_foundation.py`.
- Database target: PostgreSQL is the development and production database. Tests use in-memory SQLite only for isolated, fast verification.

### Step 2 - Shared Model Conventions

Define timestamp, primary-key, and serialization patterns used by all models.

- Files: `backend/app/models/__init__.py`, `backend/app/models/base.py`, and `tests/test_identity_models.py`.
- Purpose: provide reusable integer primary keys, timestamp fields, and timezone helpers for current and future models.
- Verification: included with the identity model test suite.

### Step 3 - Identity Models

Define users and role fields required by later authentication and authorization.

- Files: `backend/app/models/identity.py`, `backend/app/__init__.py`, and `tests/test_identity_models.py`.
- Purpose: define the `users` and `auth_sessions` tables required by registration, login, logout, account status checks, and RBAC.
- Verification: run `py -m pytest tests/test_identity_models.py tests/test_auth_security.py tests/test_database_foundation.py tests/test_foundation.py`.

### Step 4 - Catalog Models

Define categories, secondhand products, product images, condition, availability, and ownership.

- Files: `backend/app/models/catalog.py` and `tests/test_catalog_models.py`.
- Purpose: define secondhand category, product, and product image records.
- Verification: run `py -m pytest tests/test_catalog_models.py`.

### Step 5 - Commerce Models

Define cart, cart items, orders, order items, payment records, and shipping records.

- Files: `backend/app/models/commerce.py` and `tests/test_commerce_models.py`.
- Purpose: define cart, order, payment, and fulfillment records used by checkout and admin order management.
- Verification: run `py -m pytest tests/test_commerce_models.py`.

### Step 6 - Trust and Moderation Models

Define reviews, ratings, product reports, and moderation status.

- Files: `backend/app/models/trust.py` and `tests/test_trust_models.py`.
- Purpose: define review and product report records used by buyer feedback and admin moderation.
- Verification: run `py -m pytest tests/test_trust_models.py`.

### Step 7 - Migration and Seed Workflow

Create database tables consistently and provide safe starter data for development.

- Files: `backend/app/cli.py`, `backend/app/seed.py`, and `tests/test_seed_workflow.py`.
- Purpose: provide guarded development commands for schema creation and starter categories/admin data.
- Verification: run `py -m pytest tests/test_seed_workflow.py`.
- Production note: direct table creation and development seeding are blocked in production; production schema changes should use Flask-Migrate migrations.

## Module 03 Implementation Sequence

### Step 1 - Authentication Security Foundation

Build reusable password and RBAC primitives before adding endpoints.

- Files: `backend/app/auth/__init__.py`, `backend/app/auth/security.py`, `backend/app/auth/rbac.py`, `tests/test_auth_security.py`, and `backend/docs/modules/modules.md`.
- Purpose: define supported roles, validate password strength, hash passwords securely, and verify password hashes.
- Verification: run `py -m pytest tests/test_auth_security.py tests/test_foundation.py tests/test_database_foundation.py`.
- Dependency note: database-backed registration and login require Module 02 identity models before API endpoints can be production-ready.

### Step 2 - Identity Model Prerequisite

Complete the Module 02 user/session tables required by authentication.

- Status: complete.
- Depends on Module 02 shared conventions and identity models.
- Verification: run `py -m pytest tests/test_identity_models.py tests/test_auth_security.py tests/test_database_foundation.py tests/test_foundation.py`.

### Step 3 - Auth API Contracts

Create request validation and endpoint skeletons for registration, login, logout, and current-user lookup.

- Files: `backend/app/auth/validation.py`, `backend/app/api/auth.py`, `backend/app/api/__init__.py`, and `tests/test_auth_api_contracts.py`.
- Purpose: define stable `/api/v1/auth` route contracts and request validation before wiring persistence.
- Verification: run `py -m pytest tests/test_auth_api_contracts.py tests/test_auth_security.py tests/test_foundation.py`.
- Status: complete.

### Step 4 - Database-Backed Auth Workflows

Persist users, verify credentials, create/revoke sessions, and protect account routes.

- Files: `backend/app/auth/service.py`, `backend/app/api/auth.py`, `backend/app/auth/validation.py`, `backend/app/core/config.py`, and `tests/test_auth_api_contracts.py`.
- Purpose: create buyer accounts, authenticate users, issue/revoke opaque HTTP-only session cookies, and load the current user from the session.
- Verification: run `py -m pytest tests/test_auth_api_contracts.py tests/test_auth_security.py tests/test_identity_models.py`.
- Status: complete.

### Step 5 - RBAC Middleware

Add reusable route guards for buyer-only, admin-only, and authenticated routes.

- Files: `backend/app/auth/decorators.py` and `tests/test_rbac_guards.py`.
- Purpose: protect future API endpoints with authentication and role checks.
- Verification: run `py -m pytest tests/test_rbac_guards.py tests/test_auth_api_contracts.py`.
- Status: complete.

### Step 6 - Frontend Auth Screens

Build semantic login/register/account UI and connect it to the API with loading, success, and error states.

- Files: `frontend/login.html`, `frontend/admin/login.html`, `frontend/register.html`, `frontend/index.html`, `frontend/static/js/auth-client.js`, `frontend/static/js/auth-page.js`, `frontend/static/js/auth-views.js`, `frontend/static/css/auth.css`, and `tests/test_frontend_auth_ui.py`.
- Purpose: provide separate buyer/admin login entry points plus buyer registration/account screens that use the `/api/v1/auth` endpoints with session-cookie support.
- Integration: `/login.html` is buyer-facing, `/admin/login.html` is admin-facing, both reuse the shared auth API client, successful login is role-aware, and admin accounts are redirected away from the buyer account interface into `/admin`.
- Verification: run `py -m pytest tests/test_frontend_auth_ui.py tests/test_auth_api_contracts.py tests/test_rbac_guards.py`.
- Status: complete.

## Module 04 Implementation Sequence

### Step 1 - Marketplace API and Product Image Foundation

Expose the buyer-facing read-only marketplace API before replacing the storefront mock data.

- Files: `backend/app/api/marketplace.py`, `backend/app/marketplace/service.py`, `backend/app/marketplace/serializers.py`, `backend/app/api/__init__.py`, `backend/app/seed.py`, `backend/app/__init__.py`, and `tests/test_marketplace_api.py`.
- Purpose: provide stable `/api/v1/marketplace/categories`, `/api/v1/marketplace/products`, and `/api/v1/marketplace/products/<slug>` endpoints using seeded secondhand products and local product images from `frontend/static/productImages`.
- Integration: marketplace routes are registered under `/api/v1`; product listing and detail responses return consistent JSON envelopes, category metadata, PHP price formatting, seller details, validation errors, and image URLs served by Flask from `/static/productImages`.
- Verification: run `py -m pytest tests/test_marketplace_api.py`.
- Status: complete.

### Step 2 - Storefront API Integration

Replace the storefront's inline mock product data with a dedicated marketplace frontend data client.

- Files: `frontend/index.html`, `frontend/static/js/marketplace-api.js`, and `tests/test_frontend_marketplace_ui.py`.
- Purpose: render real API-backed product listing, category browsing, search, sorting, filtering, product details, loading states, empty states, and error states.
- Verification: run `py -m pytest tests/test_marketplace_api.py tests/test_frontend_marketplace_ui.py tests/test_frontend_auth_ui.py`.
- Status: complete.

### Step 3 - Marketplace UI Polish and Responsive Verification

Polish the buyer marketplace interface and verify that the frontend remains responsive and API-backed.

- Files: `frontend/index.html`, `tests/test_frontend_marketplace_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: align storefront copy with the secondhand marketplace concept, improve product card sizing, add responsive catalog filter behavior, clean up old demo wording, and keep local product images visible in buyer-facing sections.
- Verification: run `py -m pytest tests/test_frontend_marketplace_ui.py tests/test_marketplace_api.py`, then serve seeded test data locally and confirm `/` and `/api/v1/marketplace/products` respond successfully.
- Status: complete.

### Step 4 - Marketplace Search and Filter API Integration

Move buyer search, category filtering, condition filtering, price filtering, and sorting onto the marketplace API contract.

- Files: `frontend/static/js/marketplace-api.js`, `frontend/index.html`, `backend/app/marketplace/service.py`, `tests/test_frontend_marketplace_ui.py`, `tests/test_marketplace_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: keep the browser storefront synchronized with `/api/v1/marketplace/products` query parameters instead of relying on local-only filtering logic.
- Integration: frontend filters now send `q`, `category`, `condition`, `sort`, and `max_price_cents`; backend validates supported sort and condition values before querying products.
- Verification: run `py -m pytest tests/test_marketplace_api.py tests/test_frontend_marketplace_ui.py`.
- Status: complete.

### Step 5 - Wishlist Persistence Preparation

Prepare buyer wishlist persistence before cart and checkout workflows depend on saved products.

- Files: `backend/app/models/catalog.py`, `backend/app/models/identity.py`, `backend/app/models/__init__.py`, `backend/app/marketplace/service.py`, `backend/app/api/marketplace.py`, `frontend/static/js/marketplace-api.js`, `frontend/index.html`, `tests/test_wishlist_api.py`, `tests/test_frontend_marketplace_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: store one wishlist record per buyer/product, expose authenticated wishlist list/add/remove API endpoints, and let the storefront sync wishlist state for logged-in buyers while keeping temporary guest behavior.
- Integration: buyer sessions protect `/api/v1/marketplace/wishlist`; wishlist items reference existing users and available products; frontend hearts call the wishlist API when authenticated.
- Verification: run `py -m pytest tests/test_wishlist_api.py tests/test_marketplace_api.py tests/test_frontend_marketplace_ui.py`.
- Status: complete.

### Step 6 - Marketplace Final Review and Module 04 Completion Check

Review the full buyer marketplace scope before marking Module 04 complete.

- Files: `migrations/versions/20261004_01_add_wishlist_items.py`, `tests/test_marketplace_module_completion.py`, `frontend/index.html`, `frontend/marketplace/pages/home.html`, `frontend/marketplace/pages/catalog.html`, `frontend/marketplace/pages/product-detail.html`, `frontend/marketplace/pages/wishlist.html`, `frontend/static/css/marketplace/base.css`, `frontend/static/js/marketplace/app.js`, `frontend/static/js/marketplace/components/product-card.js`, `frontend/static/js/marketplace/pages/home-page.js`, `frontend/static/js/marketplace/pages/catalog-page.js`, `frontend/static/js/marketplace/pages/product-detail-page.js`, `frontend/static/js/marketplace/pages/wishlist-page.js`, and `backend/docs/modules/modules.md`.
- Purpose: confirm the marketplace has API-backed category browsing, product listing, product detail, search, filtering, sorting, responsive frontend behavior, local product image usage, wishlist persistence, migration coverage, regression tests, and modular frontend page organization.
- Verification: run `py -m pytest tests/test_marketplace_module_completion.py tests/test_marketplace_api.py tests/test_frontend_marketplace_ui.py tests/test_wishlist_api.py`, then run the full suite with `py -m pytest`.
- Status: complete.

## Module 04 Frontend Structure

The buyer marketplace frontend is split into shell, page templates, shared styling, app behavior, page data binders, and reusable components.

- `frontend/index.html`: storefront shell, shared layout, modals, drawers, footer, and script/style imports.
- `frontend/marketplace/pages/home.html`: home page template for hero, category discovery, featured products, and marketplace promise sections.
- `frontend/marketplace/pages/catalog.html`: catalog page template for search, filters, sorting, empty state, and product grid regions.
- `frontend/marketplace/pages/product-detail.html`: product detail template for breadcrumbs, gallery, product metadata, variant controls, seller details, and cart action.
- `frontend/marketplace/pages/wishlist.html`: wishlist page template for saved buyer products.
- `frontend/static/css/marketplace/base.css`: marketplace design tokens, buttons, cards, skeleton states, and responsive layout helpers.
- `frontend/static/js/marketplace/app.js`: marketplace app state, routing, page-template loading, authentication integration, API refresh logic, wishlist syncing, cart drawer, and shared utilities.
- `frontend/static/js/marketplace/components/product-card.js`: reusable marketplace product card component.
- `frontend/static/js/marketplace/pages/home-page.js`: home page data binder for category tiles, featured product cards, and marketplace status.
- `frontend/static/js/marketplace/pages/catalog-page.js`: catalog page data binder for API search/filter/sort controls, empty state, and product grid.
- `frontend/static/js/marketplace/pages/product-detail-page.js`: product detail data binder for gallery buttons, selected variants, specs, seller details, and add-to-cart values.
- `frontend/static/js/marketplace/pages/wishlist-page.js`: wishlist page data binder for saved buyer product cards and empty/loading/error states.
- `frontend/static/js/marketplace-api.js`: marketplace API client for products, categories, search/filter query strings, product details, and wishlist persistence.

## Module 05 Implementation Sequence

### Step 1 - Admin Seller API Foundation

Create protected admin inventory endpoints before building the admin UI.

- Files: `backend/app/api/admin.py`, `backend/app/admin/__init__.py`, `backend/app/admin/service.py`, `backend/app/admin/serializers.py`, `backend/app/api/__init__.py`, `backend/app/core/responses.py`, `tests/test_admin_seller_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: expose admin-only category and product inventory data, including draft/non-buyer-visible products, product counts, images, seller metadata, filter validation, and RBAC protection.
- Integration: admin routes are registered under `/api/v1/admin`; all routes require the `admin` role through the existing session-cookie RBAC guard.
- Verification: run `py -m pytest tests/test_admin_seller_api.py tests/test_rbac_guards.py tests/test_marketplace_api.py`.
- Status: complete.

### Step 2 - Admin Frontend Folder and Page Foundation

Create the admin seller management frontend structure without mixing it into Module 4 marketplace files.

- Files: `backend/app/__init__.py`, `frontend/admin/index.html`, `frontend/admin/pages/dashboard.html`, `frontend/admin/pages/products.html`, `frontend/admin/pages/categories.html`, `frontend/static/css/admin/base.css`, `frontend/static/js/admin/admin-api.js`, `frontend/static/js/admin/app.js`, `frontend/static/js/admin/pages/dashboard-page.js`, `frontend/static/js/admin/pages/products-page.js`, `frontend/static/js/admin/pages/categories-page.js`, `tests/test_frontend_admin_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: provide a modular admin UI shell, separate page templates, shared admin styling, admin API client, route-aware app controller, and page-specific JavaScript data binders.
- Integration: Flask serves `/admin` from `frontend/admin/index.html`; admin page templates are loaded from `frontend/admin/pages`; the admin API client calls `/api/v1/admin`; the shell reuses the existing auth client to verify that the current session belongs to an admin user.
- Verification: run `py -m pytest tests/test_frontend_admin_ui.py tests/test_admin_seller_api.py`.
- Status: complete.

### Step 3 - Product Create and Edit API

Add validated admin product mutations after the admin frontend has a stable shell and read-only inventory foundation.

- Files: `backend/app/admin/validation.py`, `backend/app/admin/service.py`, `backend/app/api/admin.py`, `tests/test_admin_product_mutations.py`, and `backend/docs/modules/modules.md`.
- Purpose: allow admin sellers to create and edit product listings with validated category, price, condition, status, quantity, metadata, slug uniqueness, and image payloads.
- Integration: admin sellers can call `POST /api/v1/admin/products` and `PUT /api/v1/admin/products/<slug>`; the routes reuse the existing admin RBAC guard and return serialized admin product records.
- Verification: run `py -m pytest tests/test_admin_product_mutations.py tests/test_admin_seller_api.py`.
- Status: complete.

### Step 4 - Product Status and Inventory Workflow

Add focused admin controls for product status transitions and inventory quantity updates.

- Files: `backend/app/admin/validation.py`, `backend/app/admin/service.py`, `backend/app/api/admin.py`, `frontend/static/js/admin/admin-api.js`, `frontend/static/js/admin/app.js`, `frontend/static/js/admin/pages/products-page.js`, `frontend/static/css/admin/base.css`, `frontend/admin/pages/products.html`, `tests/test_admin_product_status_workflow.py`, `tests/test_frontend_admin_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: support draft, publish, hide, reserve, sold, and quantity update actions without requiring a full product edit form.
- Integration: admin sellers can call `PATCH /api/v1/admin/products/<slug>/status` and `PATCH /api/v1/admin/products/<slug>/inventory`; the products table exposes compact status and quantity controls backed by the admin API client.
- Verification: run `py -m pytest tests/test_admin_product_status_workflow.py tests/test_frontend_admin_ui.py`.
- Status: complete.

### Step 5 - Category Management Workflow

Add protected admin create/update/activate/deactivate workflows for product categories.

- Files: `backend/app/admin/validation.py`, `backend/app/admin/service.py`, `backend/app/api/admin.py`, `frontend/static/js/admin/admin-api.js`, `frontend/static/js/admin/app.js`, `frontend/static/js/admin/pages/categories-page.js`, `frontend/admin/pages/categories.html`, `tests/test_admin_category_management.py`, `tests/test_frontend_admin_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: allow admin sellers to manage category names, slugs, descriptions, active state, and sort order without directly editing seed data.
- Integration: admin sellers can call `POST /api/v1/admin/categories`, `PUT /api/v1/admin/categories/<slug>`, and `PATCH /api/v1/admin/categories/<slug>/status`; the admin category page exposes a create form plus active-state and sort-order controls.
- Verification: run `py -m pytest tests/test_admin_category_management.py tests/test_frontend_admin_ui.py`.
- Status: complete.

### Step 6 - Admin Frontend API Integration Review

Review and tighten the admin UI integration after product and category management workflows are available.

- Files: `frontend/static/js/admin/app.js`, `frontend/static/js/admin/pages/products-page.js`, `frontend/static/js/admin/pages/categories-page.js`, `frontend/admin/pages/products.html`, `frontend/admin/pages/categories.html`, `frontend/static/css/admin/base.css`, `tests/test_frontend_admin_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: verify loading, empty, error, validation, success, and refresh states across the admin seller pages before the Module 5 completion check.
- Integration: admin mutation controls now share a frontend action-loading guard, disable product/category controls while a request is in progress, validate quantity and sort values before calling the API, show toast errors for invalid values, and refresh inventory after successful mutations.
- Verification: run `py -m pytest tests/test_frontend_admin_ui.py tests/test_admin_seller_api.py tests/test_admin_product_mutations.py tests/test_admin_category_management.py`.
- Status: complete.

### Step 7 - Admin Seller Management Final Review and Module 05 Completion Check

Review the complete admin seller management scope before marking Module 05 complete.

- Files: `backend/app/api/admin.py`, `backend/app/admin/service.py`, `backend/app/admin/validation.py`, `backend/app/admin/serializers.py`, `frontend/admin/index.html`, `frontend/admin/pages/dashboard.html`, `frontend/admin/pages/products.html`, `frontend/admin/pages/categories.html`, `frontend/static/css/admin/base.css`, `frontend/static/js/admin/admin-api.js`, `frontend/static/js/admin/app.js`, `frontend/static/js/admin/pages/dashboard-page.js`, `frontend/static/js/admin/pages/products-page.js`, `frontend/static/js/admin/pages/categories-page.js`, `tests/test_admin_module_completion.py`, Module 05 admin tests, and `backend/docs/modules/modules.md`.
- Purpose: confirm admin RBAC, inventory reads, product mutations, status and quantity workflows, category management, frontend separation, loading/error/empty states, and regression coverage.
- Verification: run the Module 05 focused tests, then run the full suite with `py -m pytest`.
- Status: complete.

## Module 05 Frontend Structure

The admin seller frontend is separate from the buyer marketplace frontend.

- `frontend/admin/index.html`: admin seller shell, sidebar navigation, topbar, main render target, toast container, and script/style imports.
- `frontend/admin/pages/dashboard.html`: dashboard page template for inventory metrics and recent products.
- `frontend/admin/pages/products.html`: product listing page template for search, filters, table, status controls, quantity controls, and reserved full-product create action.
- `frontend/admin/pages/categories.html`: category listing page template for the category create form, category table, active-state controls, and sort-order controls.
- `frontend/static/css/admin/base.css`: admin layout, tables, forms, badges, buttons, states, and responsive behavior.
- `frontend/static/js/admin/admin-api.js`: admin API client for category management, products, status transitions, and inventory updates.
- `frontend/static/js/admin/app.js`: admin app state, auth gate, routing, template loading, inventory refresh, category actions, product filters, status/quantity actions, toast feedback, and shared rendering utilities.
- `frontend/static/js/admin/pages/dashboard-page.js`: dashboard data binder for metrics and recent inventory rows.
- `frontend/static/js/admin/pages/products-page.js`: product page data binder for filters and inventory table rows.
- `frontend/static/js/admin/pages/categories-page.js`: category page data binder for category table rows, active-state controls, and sort-order controls.

## Module 06 Implementation Sequence

### Step 1 - Cart API Foundation

Create buyer-only cart persistence endpoints before building checkout pages.

- Files: `backend/app/api/cart.py`, `backend/app/cart/__init__.py`, `backend/app/cart/service.py`, `backend/app/cart/serializers.py`, `backend/app/cart/validation.py`, `backend/app/api/__init__.py`, `tests/test_cart_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: allow authenticated buyers to view their active cart, add available products, update quantities, remove items, and receive validated cart totals.
- Integration: cart routes are registered under `/api/v1/cart`; all cart routes require the `buyer` role through the existing session-cookie RBAC guard; cart items reuse Module 02 `Cart` and `CartItem` models and validate against current product availability and stock.
- Verification: run `py -m pytest tests/test_cart_api.py tests/test_commerce_models.py tests/test_marketplace_api.py tests/test_rbac_guards.py`.
- Status: complete.

### Step 2 - Checkout Frontend Folder and Page Foundation

Create separated checkout frontend pages and assets without mixing checkout-specific code into marketplace or admin files.

- Files: `backend/app/__init__.py`, `frontend/checkout/index.html`, `frontend/checkout/pages/cart.html`, `frontend/checkout/pages/summary.html`, `frontend/static/css/checkout/base.css`, `frontend/static/js/checkout/checkout-api.js`, `frontend/static/js/checkout/app.js`, `frontend/static/js/checkout/pages/cart-page.js`, `frontend/static/js/checkout/pages/summary-page.js`, `tests/test_frontend_checkout_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: provide modular cart and checkout page shells that can be safely connected to the Cart API.
- Integration: Flask serves `/checkout` from `frontend/checkout/index.html`; checkout page templates are loaded from `frontend/checkout/pages`; checkout assets are isolated under `frontend/static/css/checkout` and `frontend/static/js/checkout`; the checkout shell reuses the existing auth client and calls the Module 06 Cart API through `/api/v1/cart`.
- Verification: run `py -m pytest tests/test_frontend_checkout_ui.py tests/test_cart_api.py tests/test_frontend_marketplace_ui.py`.
- Status: complete.

### Step 3 - Cart Frontend API Integration

Connect the cart page to the Cart API.

- Files: `frontend/static/js/checkout/checkout-api.js`, `frontend/static/js/checkout/app.js`, `frontend/static/js/checkout/pages/cart-page.js`, `frontend/static/css/checkout/base.css`, `frontend/index.html`, `frontend/static/js/marketplace/app.js`, `tests/test_frontend_checkout_ui.py`, `tests/test_frontend_marketplace_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: let buyers add products from marketplace pages, view persisted cart items, update quantities, remove items, and see loading/error/empty states.
- Integration: checkout cart controls call `/api/v1/cart/items`; marketplace add-to-cart and drawer quantity controls use the same cart API client; storefront checkout actions now route to `/checkout`.
- Verification: run `py -m pytest tests/test_frontend_checkout_ui.py tests/test_frontend_marketplace_ui.py tests/test_cart_api.py`.
- Status: complete.

### Step 4 - Checkout Validation and Order Draft API

Validate cart contents and prepare order summary data before final order placement.

- Files: `backend/app/api/checkout.py`, `backend/app/checkout/__init__.py`, `backend/app/checkout/service.py`, `backend/app/checkout/serializers.py`, `backend/app/checkout/validation.py`, `backend/app/api/__init__.py`, `tests/test_checkout_draft_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: calculate server-side subtotal/shipping/total values, reject unavailable cart items, and validate shipping and payment inputs.
- Integration: `POST /api/v1/checkout/draft` requires a buyer session, validates shipping address and payment method, rechecks every active cart item against current product stock/status, and returns an order-summary draft without creating the final order.
- Verification: run `py -m pytest tests/test_checkout_draft_api.py tests/test_cart_api.py tests/test_commerce_models.py`.
- Status: complete.

### Step 5 - Checkout Confirmation Workflow

Convert a valid cart into an order with order items, payment record, and shipping record.

- Files: `backend/app/api/checkout.py`, `backend/app/checkout/service.py`, `backend/app/checkout/serializers.py`, `tests/test_checkout_confirmation_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: create a confirmed order, snapshot purchased item data, reduce inventory safely, mark the cart checked out, and return a checkout confirmation.
- Integration: `POST /api/v1/checkout/confirm` reuses checkout draft validation, creates `Order`, `OrderItem`, `Payment`, and `ShippingRecord` records, deducts purchased quantities, marks zero-stock products as sold, and marks the active cart as checked out.
- Verification: run `py -m pytest tests/test_checkout_confirmation_api.py tests/test_checkout_draft_api.py tests/test_cart_api.py tests/test_commerce_models.py`.
- Status: complete.

### Step 6 - Module 06 Completion Check

Review the complete cart and checkout scope before marking Module 06 complete.

- Files: `frontend/static/js/checkout/checkout-api.js`, `frontend/static/js/checkout/app.js`, `frontend/static/js/checkout/pages/summary-page.js`, `frontend/checkout/pages/summary.html`, `frontend/static/css/checkout/base.css`, `tests/test_checkout_module_completion.py`, Module 06 focused tests, and `backend/docs/modules/modules.md`.
- Purpose: confirm cart persistence, availability validation, order summary, address capture, payment selection, checkout confirmation, frontend separation, and regression coverage.
- Integration: checkout summary form now submits to the checkout confirmation API, displays the returned order number and total, and the module completion guard verifies the route, API client, modular frontend structure, and roadmap status.
- Verification: run Module 06 focused tests, then run the full suite with `py -m pytest`.
- Status: complete.

## Module 06 Frontend Structure

The checkout frontend will be separate from buyer marketplace and admin seller files.

- `frontend/checkout/index.html`: checkout shell, route target, checkout-specific layout, and script/style imports.
- `frontend/checkout/pages/cart.html`: cart review page template for persisted cart items, quantity controls, empty state, and checkout entry action.
- `frontend/checkout/pages/summary.html`: checkout summary page template for shipping address, payment method, order totals, validation messages, and confirmation action.
- `frontend/static/css/checkout/base.css`: checkout-specific layout, forms, totals, states, and responsive behavior.
- `frontend/static/js/checkout/checkout-api.js`: checkout API client for cart, order summary, and checkout confirmation.
- `frontend/static/js/checkout/app.js`: checkout app state, auth gate, page-template loading, cart refresh logic, and shared utilities.
- `frontend/static/js/checkout/pages/cart-page.js`: cart page data binder for item rows, quantity updates, removal actions, and cart empty states.
- `frontend/static/js/checkout/pages/summary-page.js`: checkout summary page data binder for shipping/payment forms and order totals.

## Module 07 Implementation Sequence

### Step 1 - Order API Foundation

Create buyer and admin order read endpoints before building order management pages.

- Files: `backend/app/api/orders.py`, `backend/app/orders/__init__.py`, `backend/app/orders/service.py`, `backend/app/orders/serializers.py`, `backend/app/api/__init__.py`, `tests/test_order_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: allow buyers to list/view their own confirmed orders and allow admin sellers to list/view all marketplace orders with buyer, payment, shipping, and item details.
- Integration: buyer order routes are registered under `/api/v1/orders`; admin order routes are registered under `/api/v1/admin/orders`; both use the existing session-cookie RBAC guard and read orders created by Module 06 checkout confirmation.
- Verification: run `py -m pytest tests/test_order_api.py tests/test_checkout_confirmation_api.py tests/test_rbac_guards.py`.
- Status: complete.

### Step 2 - Buyer Order Frontend Folder and Page Foundation

Create separated buyer order history pages and assets without mixing order-specific code into marketplace or checkout files.

- Files: `backend/app/__init__.py`, `frontend/orders/index.html`, `frontend/orders/pages/history.html`, `frontend/orders/pages/detail.html`, `frontend/static/css/orders/base.css`, `frontend/static/js/orders/orders-api.js`, `frontend/static/js/orders/app.js`, `frontend/static/js/orders/pages/history-page.js`, `frontend/static/js/orders/pages/detail-page.js`, `tests/test_frontend_orders_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: provide modular buyer order history and order detail screens backed by the order API.
- Integration: Flask serves `/orders` from `frontend/orders/index.html`; buyer order templates are loaded from `frontend/orders/pages`; order assets are isolated under `frontend/static/css/orders` and `frontend/static/js/orders`; the shell reuses the auth client and targets `/api/v1/orders`.
- Verification: run `py -m pytest tests/test_frontend_orders_ui.py tests/test_order_api.py`.
- Status: complete.

### Step 3 - Buyer Order Frontend API Integration

Connect buyer order pages to the order API.

- Files: `frontend/static/js/orders/app.js`, `frontend/static/js/checkout/pages/summary-page.js`, `tests/test_frontend_orders_ui.py`, `tests/test_frontend_checkout_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: show placed orders after checkout, support direct order-detail links, and preserve API-backed order history/detail loading.
- Integration: checkout confirmation now links buyers to `/orders?order=<order_number>`; the buyer orders app reads the order query parameter, loads the matching order detail through `/api/v1/orders/<order_number>`, and keeps the browser URL synchronized when moving between history and detail views.
- Verification: run order API, checkout confirmation API, buyer order frontend, and checkout frontend tests.
- Status: complete.

### Step 4 - Admin Order Management Frontend Foundation

Add admin order pages to the existing admin seller workspace while keeping order-specific templates and JavaScript separate.

- Files: `frontend/admin/index.html`, `frontend/admin/pages/orders.html`, `frontend/static/js/admin/pages/orders-page.js`, `frontend/static/js/admin/admin-api.js`, `frontend/static/js/admin/app.js`, `frontend/static/css/admin/base.css`, `tests/test_frontend_admin_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: let admin sellers browse placed orders from the existing admin workspace before status mutation controls are added.
- Integration: the admin sidebar now includes an Orders view; the admin API client reads `/api/v1/admin/orders` and `/api/v1/admin/orders/<order_number>`; the admin app stores order filters, list state, and selected order detail; the orders page renders buyer, payment, shipping, item snapshot, loading, empty, and error-ready regions.
- Verification: run admin frontend and order API tests.
- Status: complete.

### Step 5 - Fulfillment Status Update API

Add protected admin status transitions for order, payment, and shipping workflows.

- Files: `backend/app/orders/validation.py`, `backend/app/orders/service.py`, `backend/app/api/orders.py`, `tests/test_order_fulfillment_api.py`, and `backend/docs/modules/modules.md`.
- Purpose: support admin-controlled processing, shipped, delivered, cancelled, payment updates, shipping updates, and tracking fields with validation.
- Integration: admin sellers can call `PATCH /api/v1/admin/orders/<order_number>/fulfillment`; the route uses the existing admin RBAC guard, validates supported statuses and allowed transitions, requires tracking before shipped/delivered shipping states, updates order/payment/shipping records atomically, and returns the serialized admin order detail.
- Verification: run fulfillment status tests and order API tests.
- Status: complete.

### Step 6 - Cancellation Rules and Buyer Tracking

Add buyer cancellation rules and fulfillment tracking behavior.

- Files: `backend/app/orders/validation.py`, `backend/app/orders/service.py`, `backend/app/api/orders.py`, `frontend/orders/pages/detail.html`, `frontend/static/js/orders/orders-api.js`, `frontend/static/js/orders/app.js`, `frontend/static/js/orders/pages/detail-page.js`, `frontend/static/css/orders/base.css`, `tests/test_buyer_order_tracking_api.py`, `tests/test_frontend_orders_ui.py`, and `backend/docs/modules/modules.md`.
- Purpose: allow safe buyer cancellation before fulfillment begins and expose clear tracking states after shipment.
- Integration: buyers can call `PATCH /api/v1/orders/<order_number>/cancel` only for their own pending/confirmed orders whose shipping status is still `not_ready`; successful cancellation restores product quantities and refreshes the buyer order detail UI. Buyer order detail now renders fulfillment tracking steps, tracking number visibility, and a guarded cancel button.
- Verification: run cancellation/tracking tests, buyer frontend order tests, fulfillment tests, and order API tests.
- Status: complete.

### Step 7 - Module 07 Completion Check

Review the complete order and fulfillment scope before marking Module 07 complete.

- Files: `tests/test_order_module_completion.py`, Module 07 backend/frontend files, and `backend/docs/modules/modules.md`.
- Purpose: confirm buyer order history, admin order list, status updates, cancellation rules, fulfillment tracking, frontend separation, and regression coverage.
- Integration: Module 07 now has guarded buyer and admin order APIs, admin fulfillment status updates, buyer cancellation rules, buyer tracking visibility, separated buyer order pages, separated admin order pages, and completion tests that verify the registered contracts and modular frontend structure.
- Verification: run Module 07 focused tests, then run the full suite with `py -m pytest`.
- Status: complete.

## Module 07 Frontend Structure

The buyer order frontend will be separate from marketplace and checkout files, while admin fulfillment views will extend the existing admin workspace using separate order templates and page binders.

- `frontend/orders/index.html`: buyer order shell, route target, main render area, and script/style imports.
- `frontend/orders/pages/history.html`: buyer order history template for placed order cards, filters, empty state, and detail navigation.
- `frontend/orders/pages/detail.html`: buyer order detail template for item snapshots, totals, payment status, shipping status, and fulfillment timeline.
- `frontend/static/css/orders/base.css`: buyer order layout, order cards, status badges, timelines, states, and responsive behavior.
- `frontend/static/js/orders/orders-api.js`: buyer order API client for order history and order detail.
- `frontend/static/js/orders/app.js`: buyer order app state, auth gate, page-template loading, order refresh logic, and shared utilities.
- `frontend/static/js/orders/pages/history-page.js`: buyer order history data binder.
- `frontend/static/js/orders/pages/detail-page.js`: buyer order detail data binder.
- `frontend/admin/pages/orders.html`: admin order list/detail template inside the admin seller workspace.
- `frontend/static/js/admin/pages/orders-page.js`: admin order management data binder.
