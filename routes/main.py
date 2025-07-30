# main.py - Simplified approach without order_recovery.html
from flask import Blueprint, render_template, session, request, redirect, url_for
from models.database import DatabaseManager
from services.cart import CartService
import time

main_bp = Blueprint('main', __name__)
db_manager = DatabaseManager()

@main_bp.route('/')
def index():
    # Check if this is a payment redirect from Midtrans
    order_id = request.args.get('order_id')
    status_code = request.args.get('status_code')
    transaction_status = request.args.get('transaction_status')
    
    if order_id and status_code == '200' and transaction_status == 'settlement':
        return redirect(url_for('main.order_success', order_id=order_id))
    
    # Try to show user's orders on home page
    phone_number = session.get('customer_phone')
    orders = []
    if phone_number:
        try:
            orders = db_manager.get_orders_by_phone(phone_number)
        except Exception as e:
            print(f"Error fetching orders: {e}")
    return render_template('index.html', orders=orders)

@main_bp.route('/menu')
def menu():
    try:
        items = db_manager.get_menu_items()
        return render_template('menu.html', items=items)
    except Exception as e:
        return render_template('menu.html', items=[], error=str(e))

@main_bp.route('/checkout')
def checkout():
    cart = CartService.get_cart()
    if not cart:
        return redirect(url_for('main.menu'))
    
    total = CartService.get_cart_total()
    return render_template('checkout.html', cart=cart, total=total)

@main_bp.route('/order-success/<order_id>')
def order_success(order_id):
    """Order success page - try database first, then session fallback"""
    
    # Try to get from database with retries
    order = None
    for attempt in range(3):
        try:
            order = db_manager.get_order(order_id)
            if order:
                break
            if attempt < 2:  # Don't sleep on last attempt
                time.sleep(1)
        except Exception as e:
            print(f"Database error attempt {attempt + 1}: {str(e)}")
            if attempt < 2:
                time.sleep(1)
    
    # If no order from database, try session fallback
    if not order:
        pending_order = session.get('pending_order')
        if pending_order and pending_order['order_id'] == order_id:
            # Create order structure from session data
            order = {
                'order_id': order_id,
                'items': pending_order['cart'],
                'total': pending_order['total'],
                'customer': pending_order['customer'],
                'status': 'paid',
                'payment_method': 'midtrans'
            }
            print(f"Using session fallback for order {order_id}")
    
    # If still no order, create minimal structure to prevent template errors
    if not order:
        order = {
            'order_id': order_id,
            'items': [],  # Ensure this is always a list
            'total': 0,
            'customer': {'name': 'Unknown', 'phone': 'Unknown'},
            'status': 'processing'
        }
        print(f"Using minimal fallback for order {order_id}")
    
    # CRITICAL: Ensure order data types are correct
    if order:
        # Convert items to list if it's not already
        if not isinstance(order.get('items', []), list):
            print(f"WARNING: Converting items from {type(order.get('items'))} to list")
            order['items'] = []
        
        # Ensure customer is a dict
        if not isinstance(order.get('customer', {}), dict):
            order['customer'] = {'name': 'Unknown', 'phone': 'Unknown'}
        
        # Ensure total is a number
        if not isinstance(order.get('total', 0), (int, int)):
            order['total'] = 0
    
    return render_template('order_success.html', order=order)