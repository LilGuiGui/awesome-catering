import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '98ru90yo8n&R%#^Yvc5ey56ce435XZ#2rd3cghJGK8nho8M*H&GN^d>:>"Z>Fvrsg31@RWTVhb9M9mHybfdVretsdhGIu&8&^%7534%@wEBNM<kpl.:<po[o]'
    
    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Midtrans configuration (sandbox)
    MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY') or 'Mid-server-puL0S3m0HVRpjEjV831DRs1k'
    MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY') or 'Mid-client-VBCau5iMI5VdsY0Y'
    MIDTRANS_BASE_URL = 'https://api.sandbox.midtrans.com/v2'
    MIDTRANS_SNAP_URL = 'https://app.sandbox.midtrans.com/snap/v1/transactions'
    MIDTRANS_STATUS_URL = 'https://api.sandbox.midtrans.com/v2'
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH = 'serviceAccountKey.json'