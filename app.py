# app.py - Main Flask application file

from flask import Flask, session
from services.auth import generate_session_key
from config import Config
import os
import firebase_admin
from firebase_admin import credentials

# Import blueprints
from routes.main import main_bp
from routes.api import api_bp
from routes.payment_routes import payment_api_bp
from routes.tracking_routes import tracking_bp  # New tracking routes
from routes.admin_routes import admin_bp        # New admin routes

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY  # Change this to a secure key

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(payment_api_bp, url_prefix='/api')
app.register_blueprint(tracking_bp)             # Tracking routes
app.register_blueprint(admin_bp)                # Admin routes

@app.before_request
def before_request():
    """Initialize session key if not present"""
    if 'session_key' not in session:
        session_key, timestamp = generate_session_key()
        session['session_key'] = session_key
        session['timestamp'] = timestamp
        session.modified = True

if not firebase_admin._apps:
    cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    firebase_admin.initialize_app(cred)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
