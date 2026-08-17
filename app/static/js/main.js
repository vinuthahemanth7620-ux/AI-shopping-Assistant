/**
 * Global Centralized Price Formatter
 * Formats raw numeric/string values into clean Indian Rupee (₹) currency display.
 * Safely handles null, undefined, empty string, NaN, and invalid numbers.
 */
function priceFmt(value) {
    if (value === null || value === undefined || value === '') {
        return 'Price unavailable';
    }
    let num = Number(value);
    if (isNaN(num) || !isFinite(num)) {
        let s = String(value).trim();
        if (s.startsWith('₹') || s.startsWith('$')) {
            return s;
        }
        return 'Price unavailable';
    }
    try {
        return '₹' + num.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } catch (e) {
        return '₹' + num.toFixed(2);
    }
}
window.priceFmt = priceFmt;

document.addEventListener('DOMContentLoaded', () => {
    console.log("AI Shopping Assistant Client initialized.");

    // Auto-dismiss alert banners after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });

    // Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Fetch initial Wishlist status for heart icon highlighting if authenticated
    fetch('/wishlist/status')
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (data && data.success && data.wishlist_ids) {
                updateWishlistIcons(data.wishlist_ids);
                updateWishlistBadgeCount(data.wishlist_count);
            }
        })
        .catch(() => {});

    // Delegated click handler for Wishlist toggle buttons
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.wishlist-toggle-btn, [title*="Wishlist"]');
        if (!btn) return;

        // Skip standard form submit buttons inside wishlist view
        if (btn.type === 'submit' && btn.closest('form[action*="/wishlist/remove"]')) return;

        e.preventDefault();
        const productId = btn.getAttribute('data-product-id') || btn.closest('[data-product-id]')?.getAttribute('data-product-id');
        if (!productId) return;

        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

        fetch(`/wishlist/toggle/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => {
            if (res.status === 401 || res.redirected) {
                window.location.href = '/auth/login';
                return null;
            }
            return res.json();
        })
        .then(data => {
            if (!data) return;
            if (data.success) {
                const icon = btn.querySelector('i');
                if (icon) {
                    if (data.is_wishlisted) {
                        icon.className = 'fa-solid fa-heart text-danger';
                    } else {
                        icon.className = 'fa-regular fa-heart text-danger';
                    }
                }
                updateWishlistBadgeCount(data.wishlist_count);
                showMainToast(data.message, data.is_wishlisted ? 'success' : 'info');
            }
        })
        .catch(err => console.error("Wishlist toggle error:", err));
    });

    function updateWishlistIcons(wishlistIds) {
        const wishSet = new Set(wishlistIds);
        const btns = document.querySelectorAll('.wishlist-toggle-btn, [title*="Wishlist"]');
        btns.forEach(btn => {
            const pId = parseInt(btn.getAttribute('data-product-id'));
            const icon = btn.querySelector('i');
            if (pId && icon) {
                if (wishSet.has(pId)) {
                    icon.className = 'fa-solid fa-heart text-danger';
                } else {
                    icon.className = 'fa-regular fa-heart text-danger';
                }
            }
        });
    }

    function updateWishlistBadgeCount(count) {
        const badges = document.querySelectorAll('.wishlist-badge-count');
        badges.forEach(b => b.textContent = count);
    }

    function showMainToast(msg, type) {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1090';
            document.body.appendChild(container);
        }

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'info'} border-0 shadow-lg`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body font-semibold small">${msg}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        container.appendChild(toastEl);
        const bsToast = new bootstrap.Toast(toastEl, { delay: 3500 });
        bsToast.show();
    }
});
