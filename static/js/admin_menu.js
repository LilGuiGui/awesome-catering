function showAddForm() {
    document.getElementById('add-form-modal').style.display = 'block';
}

function hideAddForm() {
    document.getElementById('add-form-modal').style.display = 'none';
    document.getElementById('add-item-form').reset();
    document.getElementById('item-available').checked = true;
}

function showEditForm() {
    document.getElementById('edit-form-modal').style.display = 'block';
}

function hideEditForm() {
    document.getElementById('edit-form-modal').style.display = 'none';
    document.getElementById('edit-item-form').reset();
}

document.getElementById('add-item-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('item-name').value,
        description: document.getElementById('item-description').value,
        price: parseFloat(document.getElementById('item-price').value),
        image_url: document.getElementById('item-image').value,
        category: document.getElementById('item-category').value,
        available: document.getElementById('item-available').checked
    };
    
    fetch('/admin/api/add-menu-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Menu item added successfully!');
            location.reload();
        } else {
            alert('Error adding menu item: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
});

document.getElementById('edit-item-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const itemId = document.getElementById('edit-item-id').value;
    const formData = {
        name: document.getElementById('edit-item-name').value,
        description: document.getElementById('edit-item-description').value,
        price: parseFloat(document.getElementById('edit-item-price').value),
        image_url: document.getElementById('edit-item-image').value,
        category: document.getElementById('edit-item-category').value,
        available: document.getElementById('edit-item-available').checked
    };
    
    fetch(`/admin/api/update-menu-item/${itemId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Menu item updated successfully!');
            location.reload();
        } else {
            alert('Error updating menu item: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
});

function editItem(itemId, name, description, price, imageUrl, category, available) {
    document.getElementById('edit-item-id').value = itemId;
    document.getElementById('edit-item-name').value = name;
    document.getElementById('edit-item-description').value = description;
    document.getElementById('edit-item-price').value = price;
    document.getElementById('edit-item-image').value = imageUrl;
    document.getElementById('edit-item-category').value = category;
    document.getElementById('edit-item-available').checked = (available === 'true');
    showEditForm();
}

function deleteItem(itemId, itemName) {
    if (confirm(`Are you sure you want to delete "${itemName}"?`)) {
        fetch(`/admin/api/delete-menu-item/${itemId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Menu item deleted successfully!');
                location.reload();
            } else {
                alert('Error deleting menu item: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    }
}

function toggleItemAvailability(itemId) {
    fetch(`/admin/api/toggle-item-availability/${itemId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error toggling availability: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
}