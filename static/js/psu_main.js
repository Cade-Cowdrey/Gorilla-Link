/**
 * PSU Connect - Main JavaScript
 * Modern, interactive functionality for PSU Connect platform
 */

// Global PSU namespace
const PSU = {
    init: function() {
        this.initTooltips();
        this.initAnimations();
        this.initFormValidation();
        this.initNotifications();
        this.initSearch();
    },
    
    // Initialize tooltips
    initTooltips: function() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(el => {
            el.classList.add('psu-tooltip');
            const text = el.getAttribute('data-tooltip');
            const span = document.createElement('span');
            span.className = 'psu-tooltip-text';
            span.textContent = text;
            el.appendChild(span);
        });
    },
    
    // Initialize scroll animations
    initAnimations: function() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.psu-card, .psu-section').forEach(el => {
            observer.observe(el);
        });
    },
    
    // Form validation
    initFormValidation: function() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                let isValid = true;
                const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
                
                inputs.forEach(input => {
                    if (!input.value.trim()) {
                        isValid = false;
                        input.style.borderColor = 'var(--psu-error)';
                        PSU.showError(input, 'This field is required');
                    } else {
                        input.style.borderColor = 'var(--psu-success)';
                        PSU.clearError(input);
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    PSU.showAlert('Please fill in all required fields', 'error');
                }
            });
        });
    },
    
    // Show/hide notifications
    initNotifications: function() {
        const bellIcon = document.querySelector('.fa-bell');
        if (bellIcon) {
            bellIcon.addEventListener('click', function(e) {
                e.preventDefault();
                PSU.toggleNotifications();
            });
        }
    },
    
    toggleNotifications: function() {
        const dropdown = document.getElementById('notifications-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    },
    
    // Search functionality
    initSearch: function() {
        const searchInput = document.querySelector('input[data-search]');
        if (searchInput) {
            searchInput.addEventListener('input', PSU.debounce(function(e) {
                const query = e.target.value;
                if (query.length >= 3) {
                    PSU.performSearch(query);
                }
            }, 300));
        }
    },
    
    performSearch: function(query) {
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                PSU.displaySearchResults(data);
            })
            .catch(error => {
                console.error('Search error:', error);
            });
    },
    
    displaySearchResults: function(results) {
        const container = document.getElementById('search-results');
        if (!container) return;
        
        container.innerHTML = results.map(item => `
            <div class="search-result-item">
                <a href="${item.url}">${item.title}</a>
                <p>${item.description}</p>
            </div>
        `).join('');
    },
    
    // Alert system
    showAlert: function(message, type = 'info') {
        const alertClass = `psu-alert-${type}`;
        const iconClass = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        }[type] || 'info-circle';
        
        const alert = document.createElement('div');
        alert.className = `psu-alert ${alertClass} fade-in`;
        alert.innerHTML = `
            <i class="fas fa-${iconClass}"></i>
            <span>${message}</span>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alert, container.firstChild);
            
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }, 5000);
        }
    },
    
    // Form error handling
    showError: function(input, message) {
        let errorEl = input.nextElementSibling;
        if (!errorEl || !errorEl.classList.contains('error-message')) {
            errorEl = document.createElement('div');
            errorEl.className = 'error-message';
            errorEl.style.color = 'var(--psu-error)';
            errorEl.style.fontSize = '0.875rem';
            errorEl.style.marginTop = '0.25rem';
            input.parentNode.insertBefore(errorEl, input.nextSibling);
        }
        errorEl.textContent = message;
    },
    
    clearError: function(input) {
        const errorEl = input.nextElementSibling;
        if (errorEl && errorEl.classList.contains('error-message')) {
            errorEl.remove();
        }
    },
    
    // Utility: Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Loading spinner
    showLoading: function(container) {
        const spinner = document.createElement('div');
        spinner.className = 'psu-spinner';
        spinner.id = 'loading-spinner';
        container.appendChild(spinner);
    },
    
    hideLoading: function() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) spinner.remove();
    },
    
    // API call helper
    api: {
        get: async function(url) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                return await response.json();
            } catch (error) {
                console.error('API GET error:', error);
                throw error;
            }
        },
        
        post: async function(url, data) {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch (error) {
                console.error('API POST error:', error);
                throw error;
            }
        },
        
        put: async function(url, data) {
            try {
                const response = await fetch(url, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch (error) {
                console.error('API PUT error:', error);
                throw error;
            }
        },
        
        delete: async function(url) {
            try {
                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                return await response.json();
            } catch (error) {
                console.error('API DELETE error:', error);
                throw error;
            }
        }
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    PSU.init();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PSU;
}
