

// Update coordinate count and button states
function updateCoordinateCount() {
    const count = parseInt(document.getElementById('coord-count').textContent);
    const predictAllBtn = document.getElementById('predict-all-btn');
    if (predictAllBtn) {
        predictAllBtn.disabled = count === 0 || count > 30;
    }
    updateClearButton();
}

// Update clear button state
function updateClearButton() {
    const count = parseInt(document.getElementById('coord-count').textContent);
    const clearBtn = document.getElementById('clear-all-btn');
    if (clearBtn) {
        clearBtn.disabled = count === 0;
    }
}

// Predict all coordinates
function predictAll() {
    if ({{ session.coordinates|length }} > 30) {
        alert('Maximum 30 coordinates allowed for bulk prediction');
        return;
    }
    window.location.href = "{{ url_for('predict_all') }}";
}

// Predict single coordinate
function predictCoordinate() {
    const form = document.getElementById('coord-form');
    const lat = form.elements['lat'].value;
    const lon = form.elements['lon'].value;
    
    if (!lat || !lon) {
        alert('Please enter both latitude and longitude');
        return;
    }
    
    const tempForm = document.createElement('form');
    tempForm.method = 'POST';
    tempForm.action = "{{ url_for('prediction') }}";
    
    const latInput = document.createElement('input');
    latInput.type = 'hidden';
    latInput.name = 'lat';
    latInput.value = lat;
    
    const lonInput = document.createElement('input');
    lonInput.type = 'hidden';
    lonInput.name = 'lon';
    lonInput.value = lon;
    
    tempForm.appendChild(latInput);
    tempForm.appendChild(lonInput);
    document.body.appendChild(tempForm);
    tempForm.submit();
}

// Handle CSV form submission
document.getElementById('csv-form').addEventListener('submit', function(e) {
    const fileInput = document.getElementById('csv_file');
    if (fileInput.files[0].size > 102400) { // 100KB limit
        alert('File size too large. Maximum 100KB allowed.');
        e.preventDefault();
        return;
    }
    
    const coordCount = parseInt(document.getElementById('coord-count').textContent);
    if (coordCount > 0) {
        if (!confirm('Uploading a new CSV will clear all existing coordinates. Do you want to proceed?')) {
            e.preventDefault();
            return;
        }
    }
});

// Handle Clear Coordinates form submission
$('#clear-coordinates-form').on('submit', function(e) {
    e.preventDefault();
    const button = this.querySelector('#clear-all-btn');
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing...';
    button.disabled = true;

    $.ajax({
        url: $(this).attr('action'),
        type: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        success: (response) => {
            // Show success message
            showFlashMessage(response.message, 'success');
            // Redirect to map page to refresh
            window.location.href = "{{ url_for('map') }}";
        },
        error: (xhr) => {
            button.innerHTML = '<i class="fas fa-eraser"></i> Clear All Coordinates';
            button.disabled = false;
            showFlashMessage(xhr.responseJSON?.message || 'Error clearing coordinates', 'error');
        }
    });
});

// Initialize button states on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCoordinateCount();
});
