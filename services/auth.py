import secrets
import hashlib
import time
from config import Config

def generate_session_key():
    """Generate tamper-proof session key"""
    timestamp = str(int(time.time()))
    random_data = secrets.token_hex(16)
    raw_key = f"{timestamp}:{random_data}"
    session_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return session_key, timestamp

def verify_session_key(session_key, timestamp):
    """Verify session key hasn't been tampered with"""
    try:
        # Check if timestamp is within reasonable range (24 hours)
        current_time = int(time.time())
        session_time = int(timestamp)
        if current_time - session_time > 86400:  # 24 hours
            return False
        return True
    except:
        return False

def verify_admin_credentials(username, password):
    """Verify admin login credentials"""
    return username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD

def require_admin(func):
    """Decorator to require admin authentication"""
    from functools import wraps
    from flask import session, redirect, url_for, jsonify, request
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            if request.is_json:
                return jsonify({'success': False, 'error': 'Unauthorized'})
            return redirect(url_for('admin.login'))
        return func(*args, **kwargs)
    return wrapper