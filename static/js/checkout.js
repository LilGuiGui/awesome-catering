// Load and display cart data on page load
function loadCheckoutData() {
    fetch('/api/cart')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayCheckoutItems(data.cart, data.addons, data.total);
        } else {
            // Redirect to menu if cart is empty
            window.location.href = '/menu';
        }
    })
    .catch(error => {
        console.error('Error loading cart:', error);
        window.location.href = '/menu';
    });
}

function displayCheckoutItems(cart, addons, total) {
    const cartItemsDisplay = document.getElementById('cart-items-display');
    const addonsDisplay = document.getElementById('addons-display');
    const totalsBreakdown = document.getElementById('totals-breakdown');
    
    // Display main items
    let cartHtml = '';
    let cartTotal = 0;
    
    if (cart && cart.length > 0) {
        cart.forEach(item => {
            cartHtml += `
                <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                    <div>${item.name}</div>
                    <div>$Rp ${item.price} x Rp ${item.quantity} = Rp ${item.total}</div>
                </div>
            `;
            cartTotal += item.total;
        });
    } else {
        cartHtml = '<div style="color: #666; font-style: italic;">No main items</div>';
    }
    cartItemsDisplay.innerHTML = cartHtml;
    
    // Display addons
    let addonsHtml = '';
    let addonsTotal = 0;
    
    if (addons && addons.length > 0) {
        addons.forEach(addon => {
            addonsHtml += `
                <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                    <div>${addon.name}</div>
                    <div>$Rp ${addon.price} x Rp ${addon.quantity} = Rp ${addon.total}</div>
                </div>
            `;
            addonsTotal += addon.total;
        });
    } else {
        addonsHtml = '<div style="color: #666; font-style: italic;">No add-ons</div>';
    }
    addonsDisplay.innerHTML = addonsHtml;
    
    // Display totals breakdown
    const grandTotal = cartTotal + addonsTotal;
    let totalsHtml = '';
    
    if (cartTotal > 0) {
        totalsHtml += `<div style="display: flex; justify-content: space-between;"><span>Main Items:</span><span>Rp ${cartTotal}</span></div>`;
    }
    if (addonsTotal > 0) {
        totalsHtml += `<div style="display: flex; justify-content: space-between;"><span>Add-ons:</span><span>Rp ${addonsTotal}</span></div>`;
    }
    totalsHtml += `<div style="display: flex; justify-content: space-between; font-size: 18px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;"><span>Total:</span><span>Rp ${grandTotal}</span></div>`;
    
    totalsBreakdown.innerHTML = totalsHtml;
}

// Load checkout data when page loads
loadCheckoutData();

document.getElementById('checkout-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        phone: document.getElementById('phone').value,
        notes: document.getElementById('notes').value
    };
    
    const submitBtn = document.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    
    // Declare functions first to avoid hoisting issues
    function resetButton() {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
    
    function saveOrderToLocalStorage(orderId) {
        const orderData = {
            order_id: orderId,
            expiry: new Date().getTime() + (24 * 60 * 60 * 1000) // 24 hours from now
        };
        localStorage.setItem('tracking_order', JSON.stringify(orderData));
    }
    
    function handleSaveFallback(orderId) {
        saveOrderToLocalStorage(orderId);
        alert(`Payment successful! Your order ID is: ${orderId}\n\nPlease save this ID to track your order. You'll be redirected to the tracking page.`);
        window.location.href = '/track?order_id=' + orderId;
    }
    
    function handleSaveRetry(orderId, transactionId, retryCount) {
        const maxRetries = 3;
        
        if (retryCount >= maxRetries) {
            handleSaveFallback(orderId);
            return;
        }
        
        submitBtn.textContent = `Retrying save... (${retryCount + 1}/${maxRetries})`;
        
        setTimeout(() => {
            fetch('/api/payment-success', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order_id: orderId,
                    transaction_id: transactionId
                })
            })
            .then(response => response.json())
            .then(saveResult => {
                if (saveResult.success) {
                    saveOrderToLocalStorage(orderId);
                    submitBtn.textContent = 'Redirecting...';
                    setTimeout(() => {
                        window.location.href = '/order-success/' + orderId;
                    }, 1000);
                } else if (saveResult.retry && retryCount < maxRetries - 1) {
                    handleSaveRetry(orderId, transactionId, retryCount + 1);
                } else {
                    handleSaveFallback(orderId);
                }
            })
            .catch(error => {
                console.error('Retry error:', error);
                if (retryCount < maxRetries - 1) {
                    handleSaveRetry(orderId, transactionId, retryCount + 1);
                } else {
                    handleSaveFallback(orderId);
                }
            });
        }, 2000); // 2 second delay between retries
    }
    
    fetch('/api/create-payment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Open Midtrans Snap payment
            snap.pay(data.snap_token, {
                onSuccess: function(result) {
                    console.log('Payment success:', result);
                    
                    // Show loading message
                    submitBtn.textContent = 'Saving order...';
                    
                    // Send payment success to backend
                    fetch('/api/payment-success', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            order_id: data.order_id,
                            transaction_id: result.transaction_id
                        })
                    })
                    .then(response => response.json())
                    .then(saveResult => {
                        if (saveResult.success) {
                            // Save order to localStorage for tracking
                            if (saveResult.save_for_tracking) {
                                saveOrderToLocalStorage(data.order_id);
                            }
                            
                            // Add small delay to ensure database write completes
                            submitBtn.textContent = 'Redirecting...';
                            setTimeout(() => {
                                window.location.href = '/order-success/' + data.order_id;
                            }, 1000); // 1 second delay
                            
                        } else if (saveResult.retry) {
                            // Backend suggests retry
                            handleSaveRetry(data.order_id, result.transaction_id, 0);
                        } else {
                            // Payment successful but saving failed permanently
                            handleSaveFallback(data.order_id);
                        }
                    })
                    .catch(error => {
                        console.error('Error saving order:', error);
                        handleSaveFallback(data.order_id);
                    });
                },
                
                onPending: function(result) {
                    console.log('Payment pending:', result);
                    alert('Payment pending. Please complete the payment.');
                    resetButton();
                },
                
                onError: function(result) {
                    console.log('Payment error:', result);
                    alert('Payment failed. Please try again.');
                    resetButton();
                },
                
                onClose: function() {
                    console.log('Payment popup closed');
                    resetButton();
                }
            });
        } else {
            alert('Error creating payment: ' + data.error);
            resetButton();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error);
        resetButton();
    });
});