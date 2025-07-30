from flask import session
from models.database import DatabaseManager

class CartService:
    @staticmethod
    def get_cart():
        """Get current cart from session"""
        return session.get('cart', [])
    
    @staticmethod
    def get_addons():
        """Get current addons from session"""
        return session.get('addons', [])
    
    @staticmethod
    def add_to_cart(item_data, quantity=1):
        """Add item to cart and auto-add rice if it's the first main course item"""
        if 'cart' not in session:
            session['cart'] = []
        if 'addons' not in session:
            session['addons'] = []
        
        cart_item = {
            'id': item_data['id'],
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': quantity,
            'total': item_data['price'] * quantity
        }
        
        # Check if item already in cart
        existing_item = None
        for i, existing_cart_item in enumerate(session['cart']):
            if existing_cart_item['id'] == item_data['id']:
                existing_item = i
                break
        
        # Check if this is the first main course item being added
        is_first_main_item = len(session['cart']) == 0
        
        if existing_item is not None:
            session['cart'][existing_item]['quantity'] += quantity
            session['cart'][existing_item]['total'] = session['cart'][existing_item]['price'] * session['cart'][existing_item]['quantity']
        else:
            session['cart'].append(cart_item)
        
        # Auto-add rice with quantity 1 if this is the first item added
        if is_first_main_item:
            CartService._auto_add_rice()
        
        session.modified = True
        return session['cart']
    
    @staticmethod
    def _auto_add_rice():
        """Auto-add rice addon when first main course item is added"""
        try:
            db_manager = DatabaseManager()
            rice_addon = db_manager.get_rice_addon()
            
            if rice_addon and rice_addon.get('available', True):
                # Check if rice is already in addons
                rice_exists = False
                for addon in session['addons']:
                    if addon['id'] == rice_addon['id']:
                        rice_exists = True
                        break
                
                if not rice_exists:
                    rice_cart_item = {
                        'id': rice_addon['id'],
                        'name': rice_addon['name'],
                        'price': rice_addon['price'],
                        'quantity': 1,
                        'total': rice_addon['price']
                    }
                    session['addons'].append(rice_cart_item)
                    print(f"Auto-added rice addon: {rice_addon['name']}")
        
        except Exception as e:
            print(f"Error auto-adding rice: {str(e)}")
    
    @staticmethod
    def update_cart_item(item_id, quantity):
        """Update cart item quantity"""
        cart = session.get('cart', [])
        for i, item in enumerate(cart):
            if item['id'] == item_id:
                if quantity <= 0:
                    cart.pop(i)
                else:
                    cart[i]['quantity'] = quantity
                    cart[i]['total'] = cart[i]['price'] * quantity
                break
        
        session['cart'] = cart
        session.modified = True
        return cart
    
    @staticmethod
    def add_addon_to_cart(addon_data, quantity=1):
        """Add addon to cart"""
        if 'addons' not in session:
            session['addons'] = []
        
        addon_item = {
            'id': addon_data['id'],
            'name': addon_data['name'],
            'price': addon_data['price'],
            'quantity': quantity,
            'total': addon_data['price'] * quantity
        }
        
        # Check if addon already in cart
        existing_addon = None
        for i, existing_addon_item in enumerate(session['addons']):
            if existing_addon_item['id'] == addon_data['id']:
                existing_addon = i
                break
        
        if existing_addon is not None:
            session['addons'][existing_addon]['quantity'] += quantity
            session['addons'][existing_addon]['total'] = session['addons'][existing_addon]['price'] * session['addons'][existing_addon]['quantity']
        else:
            session['addons'].append(addon_item)
        
        session.modified = True
        return session['addons']
    
    @staticmethod
    def update_addon_item(addon_id, quantity):
        """Update addon item quantity"""
        addons = session.get('addons', [])
        for i, addon in enumerate(addons):
            if addon['id'] == addon_id:
                if quantity <= 0:
                    addons.pop(i)
                else:
                    addons[i]['quantity'] = quantity
                    addons[i]['total'] = addons[i]['price'] * quantity
                break
        
        session['addons'] = addons
        session.modified = True
        return addons
    
    @staticmethod
    def clear_cart():
        """Clear the cart and addons"""
        session['cart'] = []
        session['addons'] = []
        session.modified = True
    
    @staticmethod
    def get_cart_total():
        """Calculate total cart value including addons"""
        cart = session.get('cart', [])
        addons = session.get('addons', [])
        
        cart_total = sum(item['total'] for item in cart)
        addons_total = sum(addon['total'] for addon in addons)
        
        return cart_total + addons_total
    
    @staticmethod
    def get_all_cart_items():
        """Get combined cart items and addons for order processing"""
        cart = session.get('cart', [])
        addons = session.get('addons', [])
        
        # Mark items with type for clarity in orders
        all_items = []
        
        for item in cart:
            item_copy = item.copy()
            item_copy['type'] = 'menu'
            all_items.append(item_copy)
        
        for addon in addons:
            addon_copy = addon.copy()
            addon_copy['type'] = 'addon'
            all_items.append(addon_copy)
        
        return all_items