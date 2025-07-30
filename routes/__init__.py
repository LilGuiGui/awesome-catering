from flask import Blueprint

def register_blueprints(app):
    """Register all blueprints with the app"""
    from .main import main_bp
    from .api import api_bp
    from .admin import admin_bp
    from .payment_routes import payment_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payment_bp, url_prefix='/api')