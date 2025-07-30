# payment_routes.py - Fixed routes without /api prefix
from flask import Blueprint, request, jsonify, session, url_for
from models.database import DatabaseManager
from services.cart import CartService
from services.payment import PaymentService
import time

payment_api_bp = Blueprint('payment_api', __name__)
db_manager = DatabaseManager()
payment_service = PaymentService()

@payment_api_bp.route('/create-payment', methods=['POST'])  # REMOVED /api prefix
def create_payment():
    """Create payment transaction"""
    if 'session_key' not in session:
        return jsonify({'success': False, 'error': 'Session not initialized'})
    
    try:
        data = request.get_json()
        
        # Get cart data (including addons)
        all_cart_items = CartService.get_all_cart_items()
        total = CartService.get_cart_total()
        
        if not all_cart_items or total <= 0:
            return jsonify({'success': False, 'error': 'Cart is empty'})
        
        # Customer data
        customer_data = {
            'name': data.get('name', '').strip(),
            'phone': data.get('phone', '').strip(),
            'email': data.get('email', 'customer@example.com')
        }
        
        # Validate customer data
        if not customer_data['name'] or not customer_data['phone']:
            return jsonify({'success': False, 'error': 'Name and phone are required'})
        
        # Store customer phone in session for order tracking
        session['customer_phone'] = customer_data['phone']
        
        # Create payment with Midtrans
        base_url = request.url_root.rstrip('/')
        payment_result = payment_service.create_payment(all_cart_items, customer_data, base_url)
        
        if not payment_result['success']:
            return jsonify(payment_result)
        
        # Store pending order data in session for fallback
        pending_order_data = {
            'order_id': payment_result['order_id'],
            'cart': all_cart_items,
            'total': total,
            'customer': customer_data,
            'notes': data.get('notes', ''),
            'created_at': time.time()
        }
        session['pending_order'] = pending_order_data
        session.modified = True
        
        return jsonify({
            'success': True,
            'snap_token': payment_result['snap_token'],
            'order_id': payment_result['order_id']
        })
        
    except Exception as e:
        print(f"Create payment error: {str(e)}")
        return jsonify({'success': False, 'error': 'Payment creation failed'})

@payment_api_bp.route('/payment-success', methods=['POST'])  # REMOVED /api prefix
def payment_success():
    """Handle successful payment callback"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        transaction_id = data.get('transaction_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID required'})
        
        # Get pending order from session
        pending_order = session.get('pending_order')
        if not pending_order or pending_order['order_id'] != order_id:
            return jsonify({'success': False, 'error': 'Order data not found'})
        
        # Prepare order data for database
        order_data = {
            'order_id': order_id,
            'items': pending_order['cart'],
            'total': pending_order['total'],
            'customer': pending_order['customer'],
            'notes': pending_order.get('notes', ''),
            'status': 'paid',
            'order_status': 'preparing',  # Initial tracking status
            'payment_method': 'midtrans',
            'transaction_id': transaction_id
        }
        
        # Save to database with retry logic
        max_retries = 3
        save_success = False
        
        for attempt in range(max_retries):
            try:
                db_manager.save_order(order_data)
                save_success = True
                print(f"Order {order_id} saved successfully on attempt {attempt + 1}")
                break
            except Exception as save_error:
                print(f"Save attempt {attempt + 1} failed for order {order_id}: {str(save_error)}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait 1 second before retry
        
        if save_success:
            # Clear cart after successful save
            CartService.clear_cart()
            
            # Clean up session
            session.pop('pending_order', None)
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': 'Order saved successfully',
                'save_for_tracking': True  # Indicate to frontend to save for tracking
            })
        else:
            # Saving failed - suggest retry
            return jsonify({
                'success': False,
                'retry': True,
                'error': 'Failed to save order, retrying...'
            })
    
    except Exception as e:
        print(f"Payment success handling error: {str(e)}")
        return jsonify({
            'success': False,
            'retry': True,
            'error': 'Error processing payment success'
        })

@payment_api_bp.route('/verify-payment/<order_id>')  # REMOVED /api prefix
def verify_payment(order_id):
    """Verify payment status with Midtrans"""
    try:
        # First check if order exists in database
        order = db_manager.get_order(order_id)
        if order:
            return jsonify({
                'success': True,
                'paid': True,
                'order_status': order.get('order_status', 'preparing')
            })
        
        # If not in database, check with Midtrans
        is_paid = payment_service.verify_payment_status(order_id)
        
        return jsonify({
            'success': True,
            'paid': is_paid,
            'in_database': False
        })
        
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@payment_api_bp.route('/session-init', methods=['POST'])  # REMOVED /api prefix
def init_session():
    """Initialize session for cart functionality"""
    try:
        if 'session_key' not in session:
            session['session_key'] = f"session_{int(time.time())}"
            session.modified = True
        
        return jsonify({
            'success': True,
            'session_key': session['session_key']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})