function showAddForm() {
        document.getElementById('add-form-modal').style.display = 'block';
    }

function hideAddForm() {
    document.getElementById('add-form-modal').style.display = 'none';
    document.getElementById('add-addon-form').reset();
    document.getElementById('addon-available').checked = true;
}

function showEditForm() {
    document.getElementById('edit-form-modal').style.display = 'block';
}

function hideEditForm() {
    document.getElementById('edit-form-modal').style.display = 'none';
    document.getElementById('edit-addon-form').reset();
}

document.getElementById('add-addon-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('addon-name').value,
        price: parseFloat(document.getElementById('addon-price').value),
        available: document.getElementById('addon-available').checked
    };
    
    fetch('/admin/api/add-addon', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Addon added successfully!');
            location.reload();
        } else {
            alert('Error adding addon: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
});

document.getElementById('edit-addon-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const addonId = document.getElementById('edit-addon-id').value;
    const formData = {
        name: document.getElementById('edit-addon-name').value,
        price: parseFloat(document.getElementById('edit-addon-price').value),
        available: document.getElementById('edit-addon-available').checked
    };
    
    fetch(`/admin/api/update-addon/${addonId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Addon updated successfully!');
            location.reload();
        } else {
            alert('Error updating addon: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error: ' + error);
    });
});

function editAddon(addonId, name, price, available) {
    document.getElementById('edit-addon-id').value = addonId;
    document.getElementById('edit-addon-name').value = name;
    document.getElementById('edit-addon-price').value = price;
    document.getElementById('edit-addon-available').checked = (available === 'true');
    showEditForm();
}

function deleteAddon(addonId, addonName) {
    if (confirm(`Are you sure you want to delete "${addonName}"?`)) {
        fetch(`/admin/api/delete-addon/${addonId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Addon deleted successfully!');
                location.reload();
            } else {
                alert('Error deleting addon: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    }
}

function toggleAddonAvailability(addonId) {
    fetch(`/admin/api/toggle-addon-availability/${addonId}`, {
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