from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.database import DatabaseManager
from services.auth import verify_admin_credentials, require_admin

admin_bp = Blueprint('admin', __name__)
db_manager = DatabaseManager()

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_admin_credentials(username, password):
            session['admin'] = True
            session.modified = True
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
def logout():
    """Admin logout"""
    session.pop('admin', None)
    session.modified = True
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin')
@require_admin
def dashboard():
    """Admin dashboard"""
    try:
        # Get all active orders and group them by status
        all_orders = db_manager.get_active_orders_for_admin()
        
        preparing_orders = [order for order in all_orders if order.get('order_status') == 'preparing']
        ready_orders = [order for order in all_orders if order.get('order_status') == 'ready']
        
        return render_template('admin_dashboard.html', 
                             preparing_orders=preparing_orders,
                             ready_orders=ready_orders)
    except Exception as e:
        print(f"Admin dashboard error: {str(e)}")  # Debug print
        return render_template('admin_dashboard.html', 
                             error=str(e),
                             preparing_orders=[],
                             ready_orders=[])

@admin_bp.route('/admin/orders')
@require_admin
def orders():
    """Admin orders page"""
    try:
        status_filter = request.args.get('status')
        orders = db_manager.get_orders_for_admin(status_filter)
        return render_template('admin_orders.html', orders=orders, current_filter=status_filter)
    except Exception as e:
        return render_template('admin_orders.html', orders=[], error=str(e))

@admin_bp.route('/admin/menu')
@require_admin
def menu():
    """Admin menu management page"""
    try:
        items = db_manager.get_menu_items()
        return render_template('admin_menu.html', items=items)
    except Exception as e:
        return render_template('admin_menu.html', items=[], error=str(e))

@admin_bp.route('/admin/addons')
@require_admin
def addons():
    """Admin addons management page"""
    try:
        addons = db_manager.get_addons()
        return render_template('admin_addons.html', addons=addons)
    except Exception as e:
        return render_template('admin_addons.html', addons=[], error=str(e))

@admin_bp.route('/admin/api/update-order-status', methods=['POST'])
@require_admin
def update_order_status():
    """API endpoint to update order status"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not order_id or not new_status:
            return jsonify({'success': False, 'error': 'Order ID and status are required'})
        
        # Allow all valid statuses including 'done'
        if new_status not in ['preparing', 'ready', 'done']:
            return jsonify({'success': False, 'error': 'Invalid status'})
        
        # Verify order exists
        order = db_manager.get_order(order_id)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'})
        
        # Update status
        db_manager.update_order_tracking_status(order_id, new_status, notes if notes else None)
        
        return jsonify({
            'success': True, 
            'message': f'Order {order_id} status updated to {new_status}'
        })
    
    except Exception as e:
        print(f"Update order status error: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/get-order-details/<order_id>')
@require_admin
def get_order_details(order_id):
    """Get detailed order information"""
    try:
        order = db_manager.get_order(order_id)
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'})
        
        return jsonify({'success': True, 'order': order})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/get-orders')
@require_admin
def get_admin_orders():
    """Get orders for admin dashboard"""
    try:
        status_filter = request.args.get('status')  # 'preparing', 'ready', or None for all active
        
        if status_filter and status_filter in ['preparing', 'ready']:
            # Get orders with specific status only
            orders = db_manager.get_orders_for_admin(status_filter)
        else:
            # Get all active orders (preparing + ready, but not done)
            orders = db_manager.get_active_orders_for_admin()
        
        return jsonify({'success': True, 'orders': orders})
        
    except Exception as e:
        print(f"Get admin orders error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Menu Management Routes
@admin_bp.route('/admin/api/add-menu-item', methods=['POST'])
@require_admin
def add_menu_item():
    """Add new menu item"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'price', 'image_url', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'})
        
        # Create menu item
        menu_item = {
            'name': data['name'],
            'description': data['description'],
            'price': int(data['price']),
            'image_url': data['image_url'],
            'category': data['category'],
            'available': data.get('available', True)
        }
        
        db_manager.add_menu_item(menu_item)
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Add menu item error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/update-menu-item/<item_id>', methods=['PUT'])
@require_admin
def update_menu_item(item_id):
    """Update menu item"""
    try:
        data = request.get_json()
        
        # Verify item exists
        item = db_manager.get_menu_item(item_id)
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'})
        
        # Update only provided fields
        update_data = {}
        allowed_fields = ['name', 'description', 'price', 'image_url', 'category', 'available']
        
        for field in allowed_fields:
            if field in data:
                if field == 'price':
                    update_data[field] = int(data[field])
                elif field == 'available':
                    update_data[field] = bool(data[field])
                else:
                    update_data[field] = data[field]
        
        if update_data:
            db_manager.update_menu_item(item_id, update_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Update menu item error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/delete-menu-item/<item_id>', methods=['DELETE'])
@require_admin
def delete_menu_item(item_id):
    """Delete menu item"""
    try:
        # Verify item exists
        item = db_manager.get_menu_item(item_id)
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'})
        
        db_manager.delete_menu_item(item_id)
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Delete menu item error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/toggle-item-availability/<item_id>', methods=['POST'])
@require_admin
def toggle_item_availability(item_id):
    """Toggle menu item availability"""
    try:
        # Verify item exists
        item = db_manager.get_menu_item(item_id)
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'})
        
        # Toggle availability
        new_availability = not item.get('available', True)
        db_manager.update_menu_item(item_id, {'available': new_availability})
        
        return jsonify({
            'success': True, 
            'available': new_availability,
            'message': f'Item {"enabled" if new_availability else "disabled"}'
        })
        
    except Exception as e:
        print(f"Toggle availability error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Addon Management Routes
@admin_bp.route('/admin/api/add-addon', methods=['POST'])
@require_admin
def add_addon():
    """Add new addon"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'})
        
        # Create addon
        addon = {
            'name': data['name'],
            'price': int(data['price']),
            'available': data.get('available', True)
        }
        
        db_manager.add_addon(addon)
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Add addon error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/update-addon/<addon_id>', methods=['PUT'])
@require_admin
def update_addon(addon_id):
    """Update addon"""
    try:
        data = request.get_json()
        
        # Verify addon exists
        addon = db_manager.get_addon(addon_id)
        if not addon:
            return jsonify({'success': False, 'error': 'Addon not found'})
        
        # Update only provided fields
        update_data = {}
        allowed_fields = ['name', 'price', 'available']
        
        for field in allowed_fields:
            if field in data:
                if field == 'price':
                    update_data[field] = int(data[field])
                elif field == 'available':
                    update_data[field] = bool(data[field])
                else:
                    update_data[field] = data[field]
        
        if update_data:
            db_manager.update_addon(addon_id, update_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Update addon error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/delete-addon/<addon_id>', methods=['DELETE'])
@require_admin
def delete_addon(addon_id):
    """Delete addon"""
    try:
        # Verify addon exists
        addon = db_manager.get_addon(addon_id)
        if not addon:
            return jsonify({'success': False, 'error': 'Addon not found'})
        
        db_manager.delete_addon(addon_id)
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Delete addon error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/admin/api/toggle-addon-availability/<addon_id>', methods=['POST'])
@require_admin
def toggle_addon_availability(addon_id):
    """Toggle addon availability"""
    try:
        # Verify addon exists
        addon = db_manager.get_addon(addon_id)
        if not addon:
            return jsonify({'success': False, 'error': 'Addon not found'})
        
        # Toggle availability
        new_availability = not addon.get('available', True)
        db_manager.update_addon(addon_id, {'available': new_availability})
        
        return jsonify({
            'success': True, 
            'available': new_availability,
            'message': f'Addon {"enabled" if new_availability else "disabled"}'
        })
        
    except Exception as e:
        print(f"Toggle addon availability error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})