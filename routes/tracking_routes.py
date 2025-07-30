# tracking_routes.py - Remove session verification
from flask import Blueprint, render_template, request, jsonify, session
from models.database import DatabaseManager
# Remove this import: from services.auth import verify_session_key

tracking_bp = Blueprint('tracking', __name__)
db_manager = DatabaseManager()

@tracking_bp.route('/track')
def track_order():
    """Order tracking page"""
    return render_template('track_order.html')

@tracking_bp.route('/api/track-order', methods=['POST'])
def api_track_order():
    """API endpoint to get order status by phone number"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '').strip()
        
        print(f"Tracking request for phone: {phone_number}")
        
        if not phone_number:
            return jsonify({'success': False, 'error': 'Phone number is required'})
        
        # Get orders by phone number (only non-completed orders)
        orders = db_manager.get_orders_by_phone(phone_number)
        
        print(f"Database returned {len(orders)} orders")
        
        if not orders:
            return jsonify({'success': False, 'error': 'No active orders found for this phone number'})
        
        # Save phone to session for easier future tracking
        session['customer_phone'] = phone_number
        session.modified = True
        
        return jsonify({'success': True, 'orders': orders})
    
    except Exception as e:
        print(f"Track order API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@tracking_bp.route('/api/save-order-to-session', methods=['POST'])
def save_order_to_session():
    """Save order ID to session for persistence"""
    # Remove session verification - just check if session exists
    if 'session_key' not in session:
        return jsonify({'success': False, 'error': 'Session not initialized'})
    
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID is required'})
        
        # Verify order exists
        order = db_manager.get_order(order_id)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'})
        
        # Save to session for server-side tracking
        session['current_order_id'] = order_id
        
        # Also save customer phone if available
        if order.get('customer', {}).get('phone'):
            session['customer_phone'] = order['customer']['phone']
        
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Order saved to session',
            'expires_in': 86400  # 24 hours in seconds
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@tracking_bp.route('/api/get-session-order')
def get_session_order():
    """Get current order from session"""
    try:
        order_id = session.get('current_order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'No order in session'})
        
        order = db_manager.get_order(order_id)
        
        if not order:
            # Clear invalid order from session
            session.pop('current_order_id', None)
            session.modified = True
            return jsonify({'success': False, 'error': 'Order not found'})
        
        # Don't show completed orders in session tracking
        if order.get('order_status') == 'done':
            session.pop('current_order_id', None)
            session.modified = True
            return jsonify({'success': False, 'error': 'Order completed'})
        
        tracking_info = {
            'order_id': order['order_id'],
            'order_status': order.get('order_status', 'preparing'),
            'status_updated_at': order.get('status_updated_at'),
            'created_at': order.get('created_at'),
            'items': order.get('items', []),
            'total': order.get('total', 0),
            'customer': order.get('customer', {}),
            'admin_notes': order.get('admin_notes', '')
        }
        
        return jsonify({'success': True, 'order': tracking_info})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})