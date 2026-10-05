from flask import Blueprint

from backend.app.api.admin import admin_bp
from backend.app.api.auth import auth_bp
from backend.app.api.cart import cart_bp
from backend.app.api.checkout import checkout_bp
from backend.app.api.health import health_bp
from backend.app.api.marketplace import marketplace_bp
from backend.app.api.orders import admin_orders_bp, orders_bp
from backend.app.api.system import system_bp


api_bp = Blueprint("api", __name__)
api_bp.register_blueprint(admin_bp)
api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(cart_bp)
api_bp.register_blueprint(checkout_bp)
api_bp.register_blueprint(health_bp)
api_bp.register_blueprint(marketplace_bp)
api_bp.register_blueprint(orders_bp)
api_bp.register_blueprint(admin_orders_bp)
api_bp.register_blueprint(system_bp, url_prefix="/system")
