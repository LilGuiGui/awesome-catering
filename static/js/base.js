let cart = [];
let addons = [];
let availableAddons = [];

function updateCartDisplay() {
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0) + 
                      addons.reduce((sum, addon) => sum + addon.quantity, 0);
    document.getElementById('cart-count').textContent = totalItems;
}

function loadAvailableAddons() {
    fetch('/api/addons')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            availableAddons = data.addons;
        }
    });
}

function addToCart(itemId, name, price) {
    fetch('/api/add-to-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            addons = data.addons;
            updateCartDisplay();
            alert('Item added to cart!');
        } else {
            alert('Error adding item to cart: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function addAddonToCart(addonId) {
    fetch('/api/add-addon-to-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            addon_id: addonId,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addons = data.addons;
            updateCartDisplay();
            displayCart();
        } else {
            alert('Error adding addon: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}

function showCart() {
    fetch('/api/cart')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            addons = data.addons;
            displayCart();
            document.getElementById('cart-modal').style.display = 'block';
        }
    });
}

function hideCart() {
    document.getElementById('cart-modal').style.display = 'none';
}

function displayCart() {
    const cartItems = document.getElementById('cart-items');
    const cartAddons = document.getElementById('cart-addons');
    const availableAddonsDiv = document.getElementById('available-addons');
    const cartTotal = document.getElementById('cart-total');
    
    if (cart.length === 0 && addons.length === 0) {
        cartItems.innerHTML = '<p>Your cart is empty</p>';
        cartAddons.innerHTML = '';
        availableAddonsDiv.innerHTML = '';
        cartTotal.innerHTML = '';
        document.getElementById('checkout-btn').style.display = 'none';
        return;
    }

    document.getElementById('checkout-btn').style.display = 'inline-block';
    
    // Display main items
    let mainItemsHtml = '';
    if (cart.length > 0) {
        mainItemsHtml += '<h4 style="margin-bottom: 10px; color: #666;">Main Items</h4>';
        cart.forEach(item => {
            mainItemsHtml += `
                <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${item.name}</strong><br>
                            Rp ${item.price} x ${item.quantity} = Rp ${item.total}
                        </div>
                        <div>
                            <button onclick="updateCartItem('${item.id}', ${item.quantity - 1})" style="background: #dc3545; color: white; border: none; padding: 5px 10px; margin-right: 5px;">-</button>
                            <span style="margin: 0 10px;">${item.quantity}</span>
                            <button onclick="updateCartItem('${item.id}', ${item.quantity + 1})" style="background: #28a745; color: white; border: none; padding: 5px 10px;">+</button>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    cartItems.innerHTML = mainItemsHtml;

    // Display available addons (only if cart has items)
    let availableAddonsHtml = '';
    if (cart.length > 0) {
        availableAddons.forEach(addon => {
            const alreadyInCart = addons.find(a => a.id === addon.id);
            if (!alreadyInCart) {
                availableAddonsHtml += `
                    <button onclick="addAddonToCart('${addon.id}')" 
                            style="background: #28a745; color: white; border: none; padding: 8px 12px; margin: 2px; border-radius: 4px; font-size: 12px;">
                        Add ${addon.name} (Rp ${addon.price})
                    </button>
                `;
            }
        });
    }
    availableAddonsDiv.innerHTML = availableAddonsHtml;

    // Display cart addons
    let cartAddonsHtml = '';
    if (addons.length > 0) {
        cartAddonsHtml += '<h5 style="margin: 15px 0 10px 0; color: #666;">In Cart:</h5>';
        addons.forEach(addon => {
            cartAddonsHtml += `
                <div style="border-bottom: 1px solid #eee; padding: 8px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${addon.name}</strong><br>
                            Rp ${addon.price} x ${addon.quantity} = Rp ${addon.total}
                        </div>
                        <div>
                            <button onclick="updateAddonItem('${addon.id}', ${addon.quantity - 1})" style="background: #dc3545; color: white; border: none; padding: 5px 10px; margin-right: 5px;">-</button>
                            <span style="margin: 0 10px;">${addon.quantity}</span>
                            <button onclick="updateAddonItem('${addon.id}', ${addon.quantity + 1})" style="background: #28a745; color: white; border: none; padding: 5px 10px;">+</button>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    cartAddons.innerHTML = cartAddonsHtml;
    
    // Calculate and display total
    const mainTotal = cart.reduce((sum, item) => sum + item.total, 0);
    const addonTotal = addons.reduce((sum, addon) => sum + addon.total, 0);
    const grandTotal = mainTotal + addonTotal;
    
    cartTotal.innerHTML = `
        <div style="text-align: right;">
            ${mainTotal > 0 ? `<div>Main Items: Rp ${mainTotal}</div>` : ''}
            ${addonTotal > 0 ? `<div>Add-ons: Rp ${addonTotal}</div>` : ''}
            <div style="font-size: 18px; font-weight: bold; margin-top: 5px;">Total: Rp ${grandTotal}</div>
        </div>
    `;
}

function updateCartItem(itemId, quantity) {
    fetch('/api/update-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
            displayCart();
        }
    });
}

function updateAddonItem(addonId, quantity) {
    fetch('/api/update-addon-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            addon_id: addonId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addons = data.addons;
            updateCartDisplay();
            displayCart();
        }
    });
}

function goToCheckout() {
    window.location.href = '/checkout';
}

// Initialize session and load cart data
function initializeApp() {
    // First initialize session
    fetch('/api/session-init', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Then load cart and addons
            loadCartData();
            loadAvailableAddons();
        }
    })
    .catch(error => {
        console.error('Session init error:', error);
        // Try to load data anyway
        loadCartData();
        loadAvailableAddons();
    });
}

function loadCartData() {
    fetch('/api/cart')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            addons = data.addons;
            updateCartDisplay();
        }
    });
}

// Initialize app on page load
initializeApp();