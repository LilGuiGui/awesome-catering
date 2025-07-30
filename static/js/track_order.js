function trackOrder() {
    const phoneNumber = document.getElementById('phone-input').value.trim();
    
    if (!phoneNumber) {
        showError('Please enter your phone number');
        return;
    }
    
    clearError();
    
    const button = document.getElementById('track-btn');
    const originalText = button.textContent;
    button.textContent = 'Tracking...';
    button.disabled = true;
    
    fetch('/api/track-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            phone_number: phoneNumber
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayOrders(data.orders);
        } else {
            showError(data.error || 'No active orders found');
        }
    })
    .catch(error => {
        console.error('Track order error:', error);
        showError('Error tracking order: ' + error.message);
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
}

function displayOrders(orders) {
    const container = document.getElementById('orders-container');
    
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No active orders found for this phone number.</p>';
        return;
    }
    
    let html = '<h2>Your Orders:</h2>';
    
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
            
            <p><strong>Ordered:</strong> ${createdDate}</p>
            <p><strong>Customer:</strong> ${order.customer?.name || 'N/A'}</p>
            <p><strong>Notes:</strong> ${order.customer?.notes || 'N/A'}</p>
            <p><strong>Total:</strong> $${order.total || 0}</p>
            
            ${order.admin_notes ? `<p><strong>Kitchen Notes:</strong> ${order.admin_notes}</p>` : ''}
            
            <details style="margin-top: 10px;">
                <summary style="cursor: pointer; font-weight: bold;">View Items</summary>
                <ul style="margin-top: 10px;">
                    ${itemsList}
                </ul>
            </details>
            
            <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                <h4 style="margin: 0 0 10px 0;">Order Progress:</h4>
                <div style="display: flex; justify-content: space-between; position: relative;">
                    ${createProgressSteps(order.order_status)}
                </div>
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

function createProgressSteps(currentStatus) {
    const steps = [
        { key: 'preparing', label: 'Preparing', icon: '👨‍🍳' },
        { key: 'ready', label: 'Ready', icon: '✅' }
    ];
    
    let html = '';
    steps.forEach((step, index) => {
        const isActive = step.key === currentStatus || 
                        (currentStatus === 'ready' && step.key === 'preparing');
        const isCurrent = step.key === currentStatus;
        
        const bgColor = isActive ? (isCurrent ? '#007bff' : '#28a745') : '#e9ecef';
        const textColor = isActive ? 'white' : '#6c757d';
        
        html += `
            <div style="text-align: center; flex: 1;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: ${bgColor}; color: ${textColor}; 
                            display: flex; align-items: center; justify-content: center; margin: 0 auto 5px; font-size: 18px;">
                    ${step.icon}
                </div>
                <small style="color: ${textColor}; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                    ${step.label}${isCurrent ? ' (Now)' : ''}
                </small>
            </div>
        `;
        
        // Add connector line (except for last item)
        if (index < steps.length - 1) {
            const lineColor = currentStatus === 'ready' ? '#28a745' : '#e9ecef';
            html += `
                <div style="flex: 1; height: 2px; background: ${lineColor}; align-self: center; margin: 0 10px; margin-top: -20px;"></div>
            `;
        }
    });
    
    return html;
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.innerHTML = `<div style="color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <strong>Error:</strong> ${message}
    </div>`;
}

function clearError() {
    document.getElementById('error-message').innerHTML = '';
}

// Allow Enter key to trigger search
document.getElementById('phone-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        trackOrder();
    }
});