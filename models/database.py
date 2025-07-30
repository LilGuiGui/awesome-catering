import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from config import Config

class DatabaseManager:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()
    
    def get_menu_items(self):
        """Get all menu items"""
        menu_items = self.db.collection('menu').stream()
        items = []
        for item in menu_items:
            data = item.to_dict()
            data['id'] = item.id
            items.append(data)
        return items
    
    def get_menu_item(self, item_id):
        """Get single menu item"""
        item_ref = self.db.collection('menu').document(item_id)
        item = item_ref.get()
        if item.exists:
            data = item.to_dict()
            data['id'] = item.id
            return data
        return None
    
    # NEW ADDON METHODS
    def get_addons(self):
        """Get all addons"""
        addons = self.db.collection('addons').stream()
        addon_list = []
        for addon in addons:
            data = addon.to_dict()
            data['id'] = addon.id
            addon_list.append(data)
        return addon_list
    
    def get_available_addons(self):
        """Get only available addons"""
        addons = self.db.collection('addons').where('available', '==', True).stream()
        addon_list = []
        for addon in addons:
            data = addon.to_dict()
            data['id'] = addon.id
            addon_list.append(data)
        return addon_list
    
    def get_addon(self, addon_id):
        """Get single addon"""
        addon_ref = self.db.collection('addons').document(addon_id)
        addon = addon_ref.get()
        if addon.exists:
            data = addon.to_dict()
            data['id'] = addon.id
            return data
        return None
    
    def add_addon(self, addon_data):
        """Add new addon"""
        addon_data['created_at'] = firestore.SERVER_TIMESTAMP
        self.db.collection('addons').add(addon_data)
    
    def update_addon(self, addon_id, data):
        """Update addon"""
        self.db.collection('addons').document(addon_id).update(data)
    
    def delete_addon(self, addon_id):
        """Delete addon"""
        self.db.collection('addons').document(addon_id).delete()
    
    def get_rice_addon(self):
        """Get rice addon specifically"""
        rice_query = self.db.collection('addons').where('name', '==', 'Rice').limit(1).stream()
        for rice in rice_query:
            data = rice.to_dict()
            data['id'] = rice.id
            return data
        return None
    
    # EXISTING METHODS (unchanged)
    def save_order(self, order_data):
        """Save order to database with tracking status"""
        # Use Firestore server timestamp for consistency
        order_data['created_at'] = firestore.SERVER_TIMESTAMP
        order_data['status'] = order_data.get('status', 'paid')
        order_data['order_status'] = order_data.get('order_status', 'preparing')  # Set default tracking status
        order_data['status_updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Debug print
        print(f"Saving order: {order_data['order_id']} with status: {order_data['order_status']}")
        
        self.db.collection('orders').document(order_data['order_id']).set(order_data)
    
    def get_order(self, order_id):
        """Get order by ID"""
        try:
            order_ref = self.db.collection('orders').document(order_id)
            order = order_ref.get()
            if order.exists:
                data = order.to_dict()
                print(f"Retrieved order: {order_id}, status: {data.get('order_status', 'unknown')}")  # Debug print
                return data
            else:
                print(f"Order not found: {order_id}")  # Debug print
                return None
        except Exception as e:
            print(f"Error retrieving order {order_id}: {str(e)}")
            return None
    
    def get_orders_by_phone(self, phone_number):
        """Get orders by customer phone number (excluding completed orders)"""
        try:
            # Query orders where customer.phone matches (without order_by to avoid composite index)
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('customer.phone', '==', phone_number)
            
            orders = query.limit(50).stream()
            order_list = []
            
            for order in orders:
                data = order.to_dict()
                data['id'] = order.id
                
                # Only include active orders (not completed) - filter in Python
                order_status = data.get('order_status', 'preparing')
                if order_status != 'done':
                    order_list.append(data)
            
            # Sort by created_at in Python (newest first)
            order_list.sort(key=lambda x: x.get('created_at', 0), reverse=True)
            
            print(f"Found {len(order_list)} active orders for phone: {phone_number}")  # Debug print
            return order_list
            
        except Exception as e:
            print(f"Error getting orders by phone {phone_number}: {str(e)}")
            return []
    
    def get_recent_orders(self, limit=50):
        """Get recent orders for admin"""
        orders = self.db.collection('orders').order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit).stream()
        order_list = []
        for order in orders:
            data = order.to_dict()
            data['id'] = order.id
            order_list.append(data)
        return order_list
    
    def add_menu_item(self, menu_item):
        """Add new menu item"""
        menu_item['created_at'] = firestore.SERVER_TIMESTAMP
        self.db.collection('menu').add(menu_item)
    
    def update_menu_item(self, item_id, data):
        """Update menu item"""
        self.db.collection('menu').document(item_id).update(data)
    
    def delete_menu_item(self, item_id):
        """Delete menu item"""
        self.db.collection('menu').document(item_id).delete()
    
    def update_order_status(self, order_id, status, transaction_status=None):
        """Update order payment status"""
        update_data = {
            'status': status,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        if transaction_status:
            update_data['transaction_status'] = transaction_status
        
        print(f"Updating order {order_id} payment status to: {status}")  # Debug print
        self.db.collection('orders').document(order_id).update(update_data)
    
    def update_order_tracking_status(self, order_id, order_status, notes=None):
        """Update order tracking status (preparing/ready)"""
        update_data = {
            'order_status': order_status,
            'status_updated_at': firestore.SERVER_TIMESTAMP
        }
        if notes:
            update_data['admin_notes'] = notes
        
        print(f"Updating order {order_id} tracking status to: {order_status}")  # Debug print
        self.db.collection('orders').document(order_id).update(update_data)
    
    def get_orders_for_admin(self, status_filter=None):
        """Get orders for admin with optional status filter"""
        try:
            query = self.db.collection('orders').order_by('created_at', direction=firestore.Query.DESCENDING)
            
            orders = query.limit(200).stream()
            order_list = []
            
            for order in orders:
                data = order.to_dict()
                data['id'] = order.id
                
                order_status = data.get('order_status', 'preparing')
                
                # Filter logic
                if status_filter:
                    # Specific status requested
                    if order_status == status_filter:
                        order_list.append(data)
                else:
                    # No filter - return all orders (including done for admin overview)
                    order_list.append(data)
                
                if len(order_list) >= 100:
                    break
            
            return order_list
            
        except Exception as e:
            print(f"Error getting orders for admin: {str(e)}")
            return []
    
    def get_active_orders_for_admin(self):
        """Get active orders for admin dashboard (preparing and ready only)"""
        try:
            # Get all orders first, then filter in Python to avoid needing composite index
            orders_ref = self.db.collection('orders')
            query = orders_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            orders = query.limit(200).stream()  # Get more to account for filtering
            order_list = []
            
            for order in orders:
                data = order.to_dict()
                data['id'] = order.id
                
                # Filter for active orders only
                order_status = data.get('order_status', 'preparing')
                if order_status in ['preparing', 'ready']:
                    order_list.append(data)
                
                # Limit to 100 active orders
                if len(order_list) >= 100:
                    break
            
            return order_list
            
        except Exception as e:
            print(f"Error getting active orders for admin: {str(e)}")
            return []