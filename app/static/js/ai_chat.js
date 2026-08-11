/**
 * AI Shopping Assistant - Frontend Chat Module
 * Handles AJAX chat submission, CSRF token validation, message bubble rendering,
 * product card layout, loading indicators, and chip selection.
 */

document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const csrfTokenInput = document.getElementById('csrfToken');
    const suggestedChips = document.querySelectorAll('.suggested-chip');
    const charCounter = document.getElementById('charCounter');

    const MAX_LENGTH = 500;

    // Character counter listener
    if (chatInput && charCounter) {
        chatInput.addEventListener('input', function () {
            const len = chatInput.value.length;
            charCounter.textContent = `${len} / ${MAX_LENGTH}`;
            if (len > MAX_LENGTH) {
                charCounter.classList.add('text-danger');
            } else {
                charCounter.classList.remove('text-danger');
            }
        });
    }

    // Suggested Questions Chip Clicks
    suggestedChips.forEach(chip => {
        chip.addEventListener('click', function () {
            const questionText = this.textContent.trim();
            chatInput.value = questionText;
            if (charCounter) charCounter.textContent = `${questionText.length} / ${MAX_LENGTH}`;
            submitUserQuestion(questionText);
        });
    });

    // Clear Chat Button Click
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', function () {
            chatMessages.innerHTML = `
                <div class="d-flex gap-3 mb-4 message-wrapper ai-message">
                    <div class="avatar-icon bg-warning text-dark rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center shadow-sm" style="width: 40px; height: 40px;">
                        <i class="fa-solid fa-robot"></i>
                    </div>
                    <div class="message-content-wrapper flex-grow-1">
                        <div class="p-3 rounded-4 shadow-sm bg-white border border-light-subtle text-dark">
                            <p class="fw-semibold text-primary mb-1 small"><i class="fa-solid fa-sparkles me-1"></i> AI Shopping Assistant</p>
                            <p class="mb-0">Chat history cleared! Ask me anything about products in our catalog.</p>
                        </div>
                    </div>
                </div>
            `;
        });
    }

    // Form Submit Listener
    if (chatForm) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;
            if (message.length > MAX_LENGTH) {
                alert(`Message exceeds maximum limit of ${MAX_LENGTH} characters.`);
                return;
            }
            submitUserQuestion(message);
        });
    }

    /**
     * Submit user question via fetch() AJAX POST
     */
    function submitUserQuestion(questionText) {
        // 1. Render User Message Bubble
        appendUserMessage(questionText);

        // 2. Clear input
        chatInput.value = '';
        if (charCounter) charCounter.textContent = `0 / ${MAX_LENGTH}`;

        // 3. Show Loading Indicator
        const loadingId = appendLoadingIndicator();

        // 4. Disable Input & Button while processing
        setFormState(true);

        // 5. Get CSRF Token
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

        // 6. Send AJAX Request to /ai/chat
        fetch('/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ message: questionText })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            removeLoadingIndicator(loadingId);
            setFormState(false);

            if (data && data.success) {
                appendAIMessage(data.ai_response, data.recommended_products);
            } else {
                appendErrorMessage(data.ai_response || 'Failed to get recommendation. Please try again.');
            }
        })
        .catch(err => {
            removeLoadingIndicator(loadingId);
            setFormState(false);
            console.error('Chat AJAX error:', err);
            const errorMsg = (err && err.ai_response) ? err.ai_response : 'Network error or server unavailable. Please try again.';
            appendErrorMessage(errorMsg);
        });
    }

    /**
     * Append User Message Bubble
     */
    function appendUserMessage(text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'd-flex gap-3 mb-4 justify-content-end message-wrapper user-message animate-fade-in';
        wrapper.innerHTML = `
            <div class="message-content-wrapper max-w-75">
                <div class="p-3 rounded-4 shadow-sm bg-primary text-white">
                    <p class="mb-0">${escapeHTML(text)}</p>
                </div>
            </div>
            <div class="avatar-icon bg-secondary text-white rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center shadow-sm" style="width: 40px; height: 40px;">
                <i class="fa-regular fa-user"></i>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        scrollToBottom();
    }

    /**
     * Append Loading Indicator Bubble
     */
    function appendLoadingIndicator() {
        const id = 'loading_' + Date.now();
        const wrapper = document.createElement('div');
        wrapper.id = id;
        wrapper.className = 'd-flex gap-3 mb-4 message-wrapper ai-loading-wrapper';
        wrapper.innerHTML = `
            <div class="avatar-icon bg-warning text-dark rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center shadow-sm" style="width: 40px; height: 40px;">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content-wrapper flex-grow-1">
                <div class="p-3 rounded-4 shadow-sm bg-white border border-light-subtle text-muted d-inline-block">
                    <div class="d-flex align-items-center gap-2">
                        <div class="spinner-border spinner-border-sm text-warning" role="status"></div>
                        <span class="small fw-semibold">Searching catalog & generating recommendation...</span>
                    </div>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        scrollToBottom();
        return id;
    }

    function removeLoadingIndicator(id) {
        const elem = document.getElementById(id);
        if (elem) elem.remove();
    }

    /**
     * Append AI Response Bubble + Recommended Product Cards Grid
     */
    function appendAIMessage(responseText, products) {
        const wrapper = document.createElement('div');
        wrapper.className = 'd-flex gap-3 mb-4 message-wrapper ai-message animate-fade-in';

        let productsHTML = '';
        if (products && Array.isArray(products) && products.length > 0) {
            productsHTML = `
                <div class="mt-3">
                    <h6 class="fw-bold text-dark mb-3"><i class="fa-solid fa-boxes-packing text-primary me-1"></i> Recommended Products (${products.length})</h6>
                    <div class="row row-cols-1 row-cols-md-2 g-3">
                        ${products.map(p => renderProductCardHTML(p)).join('')}
                    </div>
                </div>
            `;
        }

        wrapper.innerHTML = `
            <div class="avatar-icon bg-warning text-dark rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center shadow-sm" style="width: 40px; height: 40px;">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content-wrapper flex-grow-1" style="max-width: 85%;">
                <div class="p-3 rounded-4 shadow-sm bg-white border border-light-subtle text-dark">
                    <p class="fw-semibold text-primary mb-2 small"><i class="fa-solid fa-sparkles me-1"></i> AI Shopping Assistant</p>
                    <div class="ai-formatted-text mb-0">${formatMarkdownText(responseText)}</div>
                    ${productsHTML}
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        scrollToBottom();
    }

    /**
     * Render Single Product Card HTML snippet for chat recommendations
     */
    function renderProductCardHTML(product) {
        const ratingVal = product.rating ? (product.rating.value || product.rating) : '0.0';
        const imgUrl = product.image_url || '/static/images/placeholder_product.png';
        const detailUrl = `/products/${product.id}`;
        const prodName = escapeHTML(product.name);

        return `
            <div class="col">
                <div class="card h-100 border shadow-sm rounded-3 overflow-hidden bg-white hover-shadow transition-all">
                    <div class="row g-0 align-items-center p-2">
                        <div class="col-4 text-center bg-light p-2 rounded-2" style="height: 100px;">
                            <a href="${detailUrl}">
                                <img src="${imgUrl}" alt="${prodName}" class="img-fluid rounded h-100 object-fit-contain" onerror="this.src='https://via.placeholder.com/150';">
                            </a>
                        </div>
                        <div class="col-8 ps-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge bg-light text-primary border me-1 small">${escapeHTML(product.brand || 'Brand')}</span>
                                <span class="badge bg-warning text-dark small fw-bold"><i class="fa-solid fa-star me-1"></i>${ratingVal}</span>
                            </div>
                            <h6 class="card-title fs-6 mb-1 mt-1 text-truncate" title="${prodName}">
                                <a href="${detailUrl}" class="text-dark text-decoration-none fw-bold">${prodName}</a>
                            </h6>
                            <div class="fw-bold text-success mb-2">${product.price_formatted || ('₹' + (product.price_raw || 0))}</div>
                            <div class="d-flex gap-1">
                                <button type="button" class="btn btn-sm btn-primary rounded-pill flex-fill py-1 fw-semibold add-to-cart-ai-btn" data-product-id="${product.id}" data-product-name="${prodName}">
                                    <i class="fa-solid fa-cart-shopping me-1"></i> Cart
                                </button>
                                <a href="${detailUrl}" class="btn btn-sm btn-outline-secondary rounded-pill py-1 px-2 fw-semibold text-center" title="View Details">
                                    <i class="fa-solid fa-chevron-right"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Attach delegated click listener for AI product card "Add to Cart" buttons
    if (chatMessages) {
        chatMessages.addEventListener('click', function (e) {
            const btn = e.target.closest('.add-to-cart-ai-btn');
            if (!btn) return;

            e.preventDefault();
            const productId = btn.getAttribute('data-product-id');
            const productName = btn.getAttribute('data-product-name') || 'Product';
            const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span> Adding...`;

            fetch(`/cart/add/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ quantity: 1 })
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
                btn.disabled = false;
                btn.className = 'btn btn-sm btn-success rounded-pill flex-fill py-1 fw-semibold add-to-cart-ai-btn';
                btn.innerHTML = `<i class="fa-solid fa-check me-1"></i> Added!`;
                
                setTimeout(() => {
                    btn.className = 'btn btn-sm btn-primary rounded-pill flex-fill py-1 fw-semibold add-to-cart-ai-btn';
                    btn.innerHTML = `<i class="fa-solid fa-cart-shopping me-1"></i> Cart`;
                }, 2000);

                if (data.success) {
                    updateNavbarCartCount(data.cart_count);
                    showToastNotification(`"${productName.slice(0, 30)}" added to cart successfully! <a href="/cart/" class="text-white text-decoration-underline ms-1">View Cart</a>`, 'success');
                } else {
                    showToastNotification(data.message || 'Failed to add item to cart.', 'danger');
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-cart-shopping me-1"></i> Cart`;
                console.error("AI Add to Cart AJAX Error:", err);
            });
        });
    }

    function updateNavbarCartCount(count) {
        const badges = document.querySelectorAll('.nav-link[href*="/cart"] .badge');
        badges.forEach(b => {
            b.textContent = count;
            if (count > 0) {
                b.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-warning text-dark';
            }
        });
    }

    function showToastNotification(htmlContent, type) {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0 show shadow-lg rounded-3 mb-2`;
        toast.role = 'alert';
        toast.innerHTML = `
            <div class="d-flex p-2 align-items-center">
                <div class="toast-body small fw-semibold flex-grow-1">${htmlContent}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
            </div>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            if (toast) toast.remove();
        }, 4000);
    }

    /**
     * Append Error Message Bubble
     */
    function appendErrorMessage(errorText) {
        const wrapper = document.createElement('div');
        wrapper.className = 'd-flex gap-3 mb-4 message-wrapper ai-error-message animate-fade-in';
        wrapper.innerHTML = `
            <div class="avatar-icon bg-danger text-white rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center shadow-sm" style="width: 40px; height: 40px;">
                <i class="fa-solid fa-circle-exclamation"></i>
            </div>
            <div class="message-content-wrapper flex-grow-1">
                <div class="p-3 rounded-4 shadow-sm bg-danger-subtle border border-danger-subtle text-danger">
                    <p class="fw-semibold mb-1 small"><i class="fa-solid fa-triangle-exclamation me-1"></i> Notice</p>
                    <p class="mb-0">${escapeHTML(errorText)}</p>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        scrollToBottom();
    }

    function setFormState(disabled) {
        chatInput.disabled = disabled;
        sendBtn.disabled = disabled;
        if (disabled) {
            sendBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status"></span> Thinking...`;
        } else {
            sendBtn.innerHTML = `<span>Send</span> <i class="fa-solid fa-paper-plane ms-1"></i>`;
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatMarkdownText(text) {
        if (!text) return '';
        let formatted = escapeHTML(text);
        
        // Bold: **text**
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic: *text*
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Bullet points
        formatted = formatted.replace(/^•\s+(.*)$/gm, '<li class="ms-3">$1</li>');
        formatted = formatted.replace(/^-\s+(.*)$/gm, '<li class="ms-3">$1</li>');

        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }
});
