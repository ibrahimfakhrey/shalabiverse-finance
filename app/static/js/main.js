// Main JavaScript for Shalabi Verse Financial System

// Custom Dropdown Implementation
function createCustomDropdown(selectElement) {
    // Don't replace multiple selects
    if (selectElement.hasAttribute('multiple')) return;

    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'custom-select-wrapper';

    // Create custom select display
    const customSelect = document.createElement('div');
    customSelect.className = 'custom-select form-select';
    if (selectElement.hasAttribute('required')) {
        customSelect.setAttribute('required', 'required');
    }

    // Create dropdown menu
    const dropdown = document.createElement('div');
    dropdown.className = 'custom-select-dropdown';

    // Function to update display
    function updateDisplay() {
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        customSelect.textContent = selectedOption ? selectedOption.text : '';
        customSelect.classList.toggle('placeholder', selectElement.selectedIndex === 0);
    }

    // Populate dropdown with options
    Array.from(selectElement.options).forEach((option, index) => {
        const item = document.createElement('div');
        item.className = 'custom-select-option';
        item.textContent = option.text;
        item.dataset.value = option.value;

        if (index === selectElement.selectedIndex) {
            item.classList.add('selected');
        }

        item.addEventListener('click', function(e) {
            e.stopPropagation();
            selectElement.selectedIndex = index;
            selectElement.dispatchEvent(new Event('change', { bubbles: true }));
            updateDisplay();

            // Update selected state
            dropdown.querySelectorAll('.custom-select-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            item.classList.add('selected');

            // Close dropdown
            wrapper.classList.remove('open');
        });

        dropdown.appendChild(item);
    });

    // Toggle dropdown
    customSelect.addEventListener('click', function(e) {
        e.stopPropagation();
        // Close all other dropdowns
        document.querySelectorAll('.custom-select-wrapper.open').forEach(w => {
            if (w !== wrapper) w.classList.remove('open');
        });
        wrapper.classList.toggle('open');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function() {
        wrapper.classList.remove('open');
    });

    // Initial display
    updateDisplay();

    // Insert wrapper before select
    selectElement.parentNode.insertBefore(wrapper, selectElement);
    wrapper.appendChild(customSelect);
    wrapper.appendChild(dropdown);

    // Hide original select
    selectElement.style.display = 'none';
    wrapper.appendChild(selectElement);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Shalabi Verse: Initializing custom dropdowns...');

    // Replace all select elements with custom dropdowns
    const selectElements = document.querySelectorAll('select.form-select, select');
    console.log('Found ' + selectElements.length + ' select elements');

    selectElements.forEach(function(select) {
        createCustomDropdown(select);
        console.log('Replaced select:', select.name || select.id || 'unnamed');
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
