let currentFilter = 'all';

// Load orders on page load
window.addEventListener('load', function() {
    loadOrders();
    // Auto-refresh every 30 seconds
    setInterval(loadOrders, 30000);
});

function loadOrders() {
    const url = currentFilter === 'all' ? '/admin/api/get-orders' : `/admin/api/get-orders?status=${currentFilter}`;
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayOrders(data.orders);
        } else {
            showError(data.error);
        }
    })
    .catch(error => {
        console.error('Error loading orders:', error);
        showError('Error loading orders: ' + error.message);
    });
}

function displayOrders(orders) {
    const container = document.getElementById('orders-container');
    
    if (!orders || orders.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #6c757d;"><h3>No active orders found</h3></div>';
        return;
    }

    let html = '';
    orders.forEach(order => {
        html += createOrderCard(order);
    });
    
    container.innerHTML = html;
}

function createOrderCard(order) {
    // Handle different date formats
    let createdDate = 'Unknown';
    if (order.created_at) {
        if (order.created_at._seconds) {
            createdDate = new Date(order.created_at._seconds * 1000);
        } else if (typeof order.created_at === 'string') {
            createdDate = new Date(order.created_at);
        } else {
            createdDate = new Date(order.created_at);
        }
        createdDate = createdDate.toLocaleDateString() + ' ' + createdDate.toLocaleTimeString();
    }
    
    const statusInfo = getStatusInfo(order.order_status);
    
    let itemsList = '';
    if (order.items && order.items.length > 0) {
        itemsList = order.items.map(item => 
            `<li>${item.name || 'Item'} x ${item.quantity || 1} = $${item.total || item.price || 0}</li>`
        ).join('');
    }
    
    return `
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3>Order #${order.order_id}</h3>
                <div style="background: ${statusInfo.color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                    ${statusInfo.icon} ${statusInfo.text}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <p><strong>Customer:</strong> ${order.customer?.name || 'N/A'}</p>
                    <p><strong>Phone:</strong> ${order.customer?.phone || 'N/A'}</p>
                    <p><strong>Notes:</strong> ${order.customer?.notes || 'None'}</p>
                    <p><strong>Ordered:</strong> ${createdDate}</p>
                    <p><strong>Total:</strong> $${order.total || 0}</p>
                </div>
                
                <div>
                    <h4>Items:</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        ${itemsList}
                    </ul>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">Update Status:</h4>
                <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                    <button onclick="updateOrderStatus('${order.order_id}', 'preparing')" 
                            style="padding: 8px 15px; background: #ffc107; color: black; border: none; border-radius: 4px; cursor: pointer;">
                        👨‍🍳 Preparing
                    </button>
                    <button onclick="updateOrderStatus('${order.order_id}', 'ready')" 
                            style="padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        ✅ Ready
                    </button>
                    <button onclick="updateOrderStatus('${order.order_id}', 'done')" 
                            style="padding: 8px 15px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        ✓ Done
                    </button>
                    <input type="text" id="notes-${order.order_id}" placeholder="Add kitchen notes..." 
                           style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 200px;">
                </div>
                ${order.admin_notes ? `<p style="margin-top: 10px; font-style: italic;"><strong>Kitchen notes:</strong> ${order.admin_notes}</p>` : ''}
            </div>
        </div>
    `;
}

function getStatusInfo(status) {
    const statusMap = {
        'preparing': { text: 'Preparing', color: '#ffc107', icon: '👨‍🍳' },
        'ready': { text: 'Ready for Pickup', color: '#28a745', icon: '✅' },
        'done': { text: 'Completed', color: '#6c757d', icon: '✓' }
    };
    return statusMap[status] || { text: status, color: '#6c757d', icon: '?' };
}

function updateOrderStatus(orderId, newStatus) {
    const notesInput = document.getElementById(`notes-${orderId}`);
    const notes = notesInput ? notesInput.value.trim() : '';
    
    const confirmMessage = newStatus === 'done' ? 
        'Mark this order as DONE? It will be removed from customer tracking.' : 
        `Update order status to ${newStatus.toUpperCase()}?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    fetch('/admin/api/update-order-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            order_id: orderId,
            status: newStatus,
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear notes input
            if (notesInput) {
                notesInput.value = '';
            }
            
            // Show success message
            showSuccess(`Order ${orderId} updated to ${newStatus}`);
            
            // Reload orders
            setTimeout(loadOrders, 1000);
        } else {
            showError(data.error);
        }
    })
    .catch(error => {
        console.error('Error updating order:', error);
        showError('Error updating order: ' + error.message);
    });
}

function filterOrders(filter) {
    currentFilter = filter;
    
    // Update button styles
    document.querySelectorAll('[id^="filter-"]').forEach(btn => {
        btn.style.background = '#6c757d';
    });
    document.getElementById(`filter-${filter}`).style.background = '#007bff';
    
    loadOrders();
}

function refreshOrders() {
    loadOrders();
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.innerHTML = `<div style="color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; border: 1px solid #f5c6cb;">
        <strong>Error:</strong> ${message}
    </div>`;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorDiv.innerHTML = '';
    }, 5000);
}

function showSuccess(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.innerHTML = `<div style="color: #155724; background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0; border: 1px solid #c3e6cb;">
        <strong>Success:</strong> ${message}
    </div>`;
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        errorDiv.innerHTML = '';
    }, 3000);
}