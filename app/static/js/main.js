// Main JavaScript for Shalabi Verse Financial System

document.addEventListener('DOMContentLoaded', function() {
    // Fix select dropdown rendering on desktop browsers
    const selectElements = document.querySelectorAll('select.form-select, select');
    selectElements.forEach(function(select) {
        // Force single selection dropdown behavior unless explicitly multiple
        if (!select.hasAttribute('multiple')) {
            select.removeAttribute('size');
        }
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من الحذف؟')) {
                e.preventDefault();
            }
        });
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
});

// Show/hide custom date range based on period selection
function toggleCustomDateRange() {
    const periodSelect = document.getElementById('periodSelect');
    if (periodSelect) {
        const customRange = document.getElementById('customDateRange');
        const customRangeEnd = document.getElementById('customDateRangeEnd');

        periodSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                if (customRange) customRange.style.display = 'block';
                if (customRangeEnd) customRangeEnd.style.display = 'block';
            } else {
                if (customRange) customRange.style.display = 'none';
                if (customRangeEnd) customRangeEnd.style.display = 'none';
            }
        });

        // Initialize on page load
        if (periodSelect.value === 'custom') {
            if (customRange) customRange.style.display = 'block';
            if (customRangeEnd) customRangeEnd.style.display = 'block';
        }
    }
}

// Call on page load
toggleCustomDateRange();
