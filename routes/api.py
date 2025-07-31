from flask import Blueprint, jsonify, request, session
from models.database import DatabaseManager
from services.cart import CartService
import time
from datetime import datetime

api_bp = Blueprint('api', __name__)
db_manager = DatabaseManager()

@api_bp.route('/ping')
def ping():
    """Simple ping endpoint for health checks and keeping app alive"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': True
    }), 200

@api_bp.route('/health')
def health():
    """More detailed health check endpoint"""
    try:
        db_manager.get_menu_items()
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'services': {
            'cart': 'ok',
            'session': 'ok' if 'session_key' in session else 'no_session'
        }
    }), 200

@api_bp.route('/menu')
def menu():
    try:
        items = db_manager.get_menu_items()
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/addons')
def addons():
    """Get available addons"""
    try:
        addons = db_manager.get_available_addons()
        return jsonify({'success': True, 'addons': addons})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    # Remove session verification - just check if session exists
    if 'session_key' not in session:
        return jsonify({'success': False, 'error': 'Session not initialized'})
    
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))
    
    try:
        item_data = db_manager.get_menu_item(item_id)
        if not item_data:
            return jsonify({'success': False, 'error': 'Item not found'})
        
        cart = CartService.add_to_cart(item_data, quantity)
        addons = CartService.get_addons()
        
        return jsonify({
            'success': True, 
            'cart': cart,
            'addons': addons,
            'total': CartService.get_cart_total()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/add-addon-to-cart', methods=['POST'])
def add_addon_to_cart():
    """Add addon to cart"""
    if 'session_key' not in session:
        return jsonify({'success': False, 'error': 'Session not initialized'})
    
    data = request.get_json()
    addon_id = data.get('addon_id')
    quantity = int(data.get('quantity', 1))
    
    try:
        addon_data = db_manager.get_addon(addon_id)
        if not addon_data:
            return jsonify({'success': False, 'error': 'Addon not found'})
        
        if not addon_data.get('available', True):
            return jsonify({'success': False, 'error': 'Addon not available'})
        
        addons = CartService.add_addon_to_cart(addon_data, quantity)
        
        return jsonify({
            'success': True, 
            'addons': addons,
            'total': CartService.get_cart_total()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/cart')
def cart():
    return jsonify({
        'success': True, 
        'cart': CartService.get_cart(),
        'addons': CartService.get_addons(),
        'total': CartService.get_cart_total()
    })

@api_bp.route('/update-cart', methods=['POST'])
def update_cart():
    # Remove session verification - just check if session exists
    if 'session_key' not in session:
        return jsonify({'success': False, 'error': 'Session not initialized'})
    
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 0))
    
    cart = CartService.update_cart_item(item_id, quantity)
    return jsonify({
        'success': True, 
        'cart': cart,
        'total': CartService.get_cart_total()
    })

@api_bp.route('/update-addon-cart', methods=['POST'])
def update_addon_cart():
    """Update addon quantity in cart"""
    if 'session_key' not in session:
        return jsonify({'success': False, 'error': 'Session not initialized'})
    
    data = request.get_json()
    addon_id = data.get('addon_id')
    quantity = int(data.get('quantity', 0))
    
    addons = CartService.update_addon_item(addon_id, quantity)
    return jsonify({
        'success': True, 
        'addons': addons,
        'total': CartService.get_cart_total()
    })

@api_bp.route('/check-order-status/<order_id>')
def check_order_status(order_id):
    try:
        order = db_manager.get_order(order_id)
        if order:
            return jsonify({
                'success': True, 
                'exists': True,
                'status': order.get('status')
            })
        else:
            return jsonify({'success': True, 'exists': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
