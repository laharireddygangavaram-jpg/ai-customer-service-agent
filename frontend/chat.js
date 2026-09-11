// =========================================================
// TECHSTORE AI CUSTOMER SUPPORT - FRONTEND
// =========================================================

let allProducts = [];
let cart = JSON.parse(localStorage.getItem("cart")) || [];

const API_URL = "http://127.0.0.1:5000/api";

// =========================================================
// DOM ELEMENTS
// =========================================================

const chatBox = document.getElementById("chat-messages");
const messageInput = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");

const loadProductsButton =
    document.getElementById("load-products-btn");

const cartContainer =
    document.getElementById("cart-items");

const cartSummary =
    document.querySelector(".cart-summary");

const cartTotalElement =
    document.getElementById("cart-total");

const cartCountElement =
    document.getElementById("cart-count");

const productsCountElement =
    document.getElementById("products-count");

const orderResult =
    document.getElementById("order-result");

const trackOrderNumber =
    document.getElementById("track-order-number");

const cancelOrderNumber =
    document.getElementById("cancel-order-number");

const refundOrderNumber =
    document.getElementById("refund-order-number");

const trackOrderButton =
    document.getElementById("track-order-btn");

const cancelOrderButton =
    document.getElementById("cancel-order-btn");

const refundOrderButton =
    document.getElementById("refund-order-btn");

const checkoutButton =
    document.getElementById("checkout-btn");

// =========================================================
// STORES
// =========================================================

const stores = [
    "Amazon",
    "Flipkart",
    "Meesho",
    "Myntra"
];

const storeContainers = {
    Amazon: "amazon-products",
    Flipkart: "flipkart-products",
    Meesho: "meesho-products",
    Myntra: "myntra-products"
};

// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// =========================================================
// PRODUCT ID
// =========================================================

function getProductId(product) {
    return String(
        product.id ??
        product.product_id ??
        ""
    );
}

// =========================================================
// STORE NAME
// =========================================================

function getStoreName(product) {

    if (product.store_name) {
        return String(product.store_name);
    }

    if (typeof product.store === "string") {
        return product.store;
    }

    if (
        product.store &&
        typeof product.store === "object" &&
        product.store.name
    ) {
        return String(product.store.name);
    }

    const storeId = Number(product.store_id);

    // Your database store IDs
    const storeMap = {
        1: "Amazon",
        2: "Flipkart",
        3: "Meesho",
        4: "Myntra"
    };

    return storeMap[storeId] || "Other Store";
}

// =========================================================
// PRODUCT IMAGE
// =========================================================

function getProductImage(product) {

    return (
        product.image_url ||
        product.image ||
        product.imageUrl ||
        "https://via.placeholder.com/200x150?text=Product"
    );
}

// =========================================================
// DELIVERY
// =========================================================

function getDelivery(product) {

    const delivery =
        product.delivery ??
        product.delivery_time;

    if (
        delivery !== undefined &&
        delivery !== null &&
        delivery !== ""
    ) {

        if (
            typeof delivery === "number" ||
            !isNaN(Number(delivery))
        ) {
            return `${Number(delivery)} days`;
        }

        return String(delivery);
    }

    return "2-3 days";
}

// =========================================================
// ADD CHAT MESSAGE
// =========================================================

function addMessage(message, type) {

    if (!chatBox) {
        return null;
    }

    const messageDiv =
        document.createElement("div");

    messageDiv.className = "message";

    if (type === "user") {
        messageDiv.classList.add("user");
    } else {
        messageDiv.classList.add("assistant");
    }

    const content =
        document.createElement("div");

    content.className = "message-content";
    content.textContent = message;

    messageDiv.appendChild(content);

    chatBox.appendChild(messageDiv);

    chatBox.scrollTop =
        chatBox.scrollHeight;

    return messageDiv;
}

// =========================================================
// SEND CHAT MESSAGE
// =========================================================

async function sendMessage() {

    if (!messageInput) {
        return;
    }

    const message =
        messageInput.value.trim();

    if (!message) {
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";

    if (sendButton) {
        sendButton.disabled = true;
        sendButton.textContent = "Thinking...";
    }

    const thinkingMessage =
        addMessage("Thinking... 🤖", "assistant");

    try {

        const response =
            await fetch(
                `${API_URL}/chat`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: message
                    })
                }
            );

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (thinkingMessage) {
            thinkingMessage.remove();
        }

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `HTTP Error: ${response.status}`
            );
        }

        const reply =
            data.response ||
            data.message ||
            data.reply ||
            "Sorry, I could not understand your request.";

        addMessage(reply, "assistant");

        // Load products for product-related questions
        const lowerMessage =
            message.toLowerCase();

        const productKeywords = [
            "product",
            "laptop",
            "computer",
            "phone",
            "mobile",
            "smartwatch",
            "smart watch",
            "watch",
            "headphone",
            "headphones",
            "keyboard",
            "mouse",
            "shirt",
            "shoe",
            "shoes",
            "camera",
            "tablet",
            "earbuds",
            "price",
            "buy",
            "compare"
        ];

        const isProductQuestion =
            productKeywords.some(
                keyword =>
                    lowerMessage.includes(keyword)
            );

        if (isProductQuestion) {

            if (allProducts.length === 0) {
                await loadProducts();
            }
        }

    } catch (error) {

        console.error("Chat Error:", error);

        if (thinkingMessage) {
            thinkingMessage.remove();
        }

        addMessage(
            "❌ Unable to connect to AI server. Please make sure the backend is running on port 5000.",
            "assistant"
        );

    } finally {

        if (sendButton) {
            sendButton.disabled = false;
            sendButton.textContent = "Send";
        }

        if (messageInput) {
            messageInput.focus();
        }
    }
}

// =========================================================
// LOAD PRODUCTS
// =========================================================

async function loadProducts() {

    if (loadProductsButton) {
        loadProductsButton.disabled = true;
        loadProductsButton.textContent = "Loading...";
    }

    const loading =
        document.getElementById("products-loading");

    if (loading) {
        loading.style.display = "block";
        loading.textContent = "Loading products... ⏳";
    }

    Object.values(storeContainers).forEach(id => {

        const container =
            document.getElementById(id);

        if (container) {
            container.innerHTML =
                "<p>Loading products... ⏳</p>";
        }
    });

    try {

        const response =
            await fetch(
                `${API_URL}/products`
            );

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `Products API Error: ${response.status}`
            );
        }

        if (Array.isArray(data)) {

            allProducts = data;

        } else if (Array.isArray(data.products)) {

            allProducts = data.products;

        } else if (Array.isArray(data.data)) {

            allProducts = data.data;

        } else {

            allProducts = [];
        }

        console.log(
            "Total Products:",
            allProducts.length
        );

        if (productsCountElement) {
            productsCountElement.textContent =
                allProducts.length;
        }

        if (allProducts.length === 0) {

            Object.values(storeContainers).forEach(id => {

                const container =
                    document.getElementById(id);

                if (container) {
                    container.innerHTML =
                        "<p>No products found.</p>";
                }
            });

            return;
        }

        createStoreSections();

        updateCartUI();

        updateAdminProjectStats();

    } catch (error) {

        console.error(
            "Load Products Error:",
            error
        );

        Object.values(storeContainers).forEach(id => {

            const container =
                document.getElementById(id);

            if (container) {

                container.innerHTML = `
                    <p>
                        ❌ Unable to load products.
                        <br><br>
                        ${escapeHTML(error.message)}
                    </p>
                `;
            }
        });

    } finally {

        if (loading) {
            loading.style.display = "none";
        }

        if (loadProductsButton) {
            loadProductsButton.disabled = false;
            loadProductsButton.textContent =
                "🔄 Load Products";
        }
    }
}

// =========================================================
// CREATE STORE SECTIONS
// =========================================================

function createStoreSections() {

    stores.forEach(storeName => {

        const container =
            document.getElementById(
                storeContainers[storeName]
            );

        if (!container) {
            return;
        }

        container.innerHTML = "";

        const storeProducts =
            allProducts.filter(product => {

                return getStoreName(product)
                    .toLowerCase()
                    .trim() ===
                    storeName
                        .toLowerCase()
                        .trim();
            });

        if (storeProducts.length === 0) {

            container.innerHTML = `
                <p>
                    No products available in
                    ${escapeHTML(storeName)}.
                </p>
            `;

            return;
        }

        storeProducts.forEach(product => {

            container.appendChild(
                createProductCard(product)
            );

        });
    });
}

// =========================================================
// CREATE PRODUCT CARD
// =========================================================

function createProductCard(product) {

    const card =
        document.createElement("div");

    card.className = "product-card";

    const productId =
        getProductId(product);

    const name =
        product.name ||
        product.product_name ||
        "Product";

    const brand =
        product.brand ||
        "Brand";

    const price =
        Number(product.price || 0);

    const rating =
        Number(
            product.rating ??
            product.average_rating ??
            0
        );

    const reviews =
        Number(
            product.reviews ??
            product.review_count ??
            0
        );

    const stock =
        product.stock ??
        "Available";

    const discount =
        product.discount ??
        "";

    const delivery =
        getDelivery(product);

    const image =
        getProductImage(product);

    const productUrl =
        product.product_url ||
        product.url ||
        "";

    card.innerHTML = `

        <img
            class="product-image"
            src="${escapeHTML(image)}"
            alt="${escapeHTML(name)}"
        >

        <div class="product-info">

            <h3>
                ${escapeHTML(name)}
            </h3>

            <p class="product-brand">
                ${escapeHTML(brand)}
            </p>

            <div class="product-price">
                ₹${price.toFixed(2)}
            </div>

            <div class="product-rating">
                ⭐ ${rating.toFixed(1)}
                (${reviews} reviews)
            </div>

            <div class="product-stock">
                📦 Stock:
                ${escapeHTML(String(stock))}
            </div>

            <p>
                🚚 Delivery:
                ${escapeHTML(delivery)}
            </p>

            ${
                discount
                    ? `
                        <p>
                            🔥 ${escapeHTML(String(discount))}% OFF
                        </p>
                    `
                    : ""
            }

            <div class="product-actions">

                <button
                    type="button"
                    class="add-cart-btn"
                >
                    🛒 Add to Cart
                </button>

                ${
                    productUrl
                        ? `
                            <button
                                type="button"
                                class="view-product-btn"
                            >
                                🔗 View
                            </button>
                        `
                        : ""
                }

            </div>

        </div>
    `;

    // Add to cart
    const addButton =
        card.querySelector(".add-cart-btn");

    if (addButton) {

        addButton.addEventListener(
            "click",
            function () {

                addToCart(productId);

            }
        );
    }

    // View product
    const viewButton =
        card.querySelector(".view-product-btn");

    if (viewButton) {

        viewButton.addEventListener(
            "click",
            function () {

                window.open(
                    productUrl,
                    "_blank"
                );

            }
        );
    }

    // Image error
    const imageElement =
        card.querySelector(".product-image");

    if (imageElement) {

        imageElement.addEventListener(
            "error",
            function () {

                this.src =
                    "https://via.placeholder.com/200x150?text=Product";

            }
        );
    }

    return card;
}

// =========================================================
// ADD TO CART
// =========================================================

function addToCart(productId) {

    const product =
        allProducts.find(
            item =>
                getProductId(item) ===
                String(productId)
        );

    if (!product) {

        alert("❌ Product not found.");

        return;
    }

    const id =
        getProductId(product);

    if (!id) {

        alert("❌ Product ID not found.");

        return;
    }

    const existing =
        cart.find(
            item =>
                String(item.id) ===
                String(id)
        );

    if (existing) {

        existing.quantity =
            Number(existing.quantity || 0) + 1;

    } else {

        cart.push({

            id: id,

            name:
                product.name ||
                product.product_name ||
                "Product",

            price:
                Number(product.price || 0),

            quantity: 1,

            store:
                getStoreName(product),

            image:
                getProductImage(product)
        });
    }

    saveCart();

    updateCartUI();

    alert("✅ Product added to cart!");
}

// =========================================================
// REMOVE FROM CART
// =========================================================

function removeFromCart(index) {

    if (!cart[index]) {
        return;
    }

    cart.splice(index, 1);

    saveCart();

    updateCartUI();
}

// =========================================================
// CHANGE QUANTITY
// =========================================================

function changeQuantity(index, change) {

    if (!cart[index]) {
        return;
    }

    cart[index].quantity =
        Number(cart[index].quantity || 1) +
        Number(change);

    if (cart[index].quantity <= 0) {

        cart.splice(index, 1);
    }

    saveCart();

    updateCartUI();
}

// =========================================================
// SAVE CART
// =========================================================

function saveCart() {

    localStorage.setItem(
        "cart",
        JSON.stringify(cart)
    );
}

// =========================================================
// CART TOTAL
// =========================================================

function getCartTotal() {

    return cart.reduce(
        (total, item) => {

            return (
                total +
                Number(item.price || 0) *
                Number(item.quantity || 0)
            );

        },
        0
    );
}

// =========================================================
// UPDATE CART UI
// =========================================================

function updateCartUI() {

    if (cartCountElement) {

        const count =
            cart.reduce(
                (total, item) =>
                    total +
                    Number(item.quantity || 0),
                0
            );

        cartCountElement.textContent =
            count;
    }

    if (cartTotalElement) {

        cartTotalElement.textContent =
            getCartTotal().toFixed(2);
    }

    if (!cartContainer) {
        return;
    }

    if (cart.length === 0) {

        cartContainer.innerHTML = `
            <p>
                Your cart is empty.
            </p>
        `;

        return;
    }

    let html = "";

    cart.forEach((item, index) => {

        const itemTotal =
            Number(item.price || 0) *
            Number(item.quantity || 0);

        html += `

            <div class="cart-item">

                <img
                    class="cart-item-image"
                    src="${escapeHTML(item.image)}"
                    alt="${escapeHTML(item.name)}"
                >

                <div class="cart-item-info">

                    <h3>
                        ${escapeHTML(item.name)}
                    </h3>

                    <p>
                        Store:
                        ${escapeHTML(item.store)}
                    </p>

                    <p>
                        Product ID:
                        ${escapeHTML(item.id)}
                    </p>

                    <p>
                        Price:
                        ₹${Number(item.price).toFixed(2)}
                    </p>

                    <p>
                        Item Total:
                        ₹${itemTotal.toFixed(2)}
                    </p>

                    <div class="quantity-controls">

                        <button
                            type="button"
                            onclick="changeQuantity(${index}, -1)"
                        >
                            −
                        </button>

                        <span>
                            ${Number(item.quantity)}
                        </span>

                        <button
                            type="button"
                            onclick="changeQuantity(${index}, 1)"
                        >
                            +
                        </button>

                    </div>

                </div>

                <button
                    type="button"
                    class="remove-cart-btn"
                    onclick="removeFromCart(${index})"
                >
                    Remove
                </button>

            </div>
        `;
    });

    cartContainer.innerHTML = html;

    if (cartSummary) {

        if (cartTotalElement) {
            cartTotalElement.textContent =
                getCartTotal().toFixed(2);
        }
    }
}

// =========================================================
// OPEN ORDER FORM
// =========================================================

function openOrderForm() {

    if (cart.length === 0) {

        alert("❌ Cart is empty.");

        return;
    }

    const oldSection =
        document.getElementById("order-section");

    if (oldSection) {
        oldSection.remove();
    }

    const section =
        document.createElement("div");

    section.id = "order-section";

    section.style.marginTop = "20px";

    section.innerHTML = `

        <div class="order-card">

            <h2>📦 Place Order</h2>

            <p>
                Enter your details to complete your order.
            </p>

            <input
                id="customer-name"
                type="text"
                placeholder="Enter your name"
            >

            <input
                id="customer-email"
                type="email"
                placeholder="Enter your email"
            >

            <button
                id="confirm-order-button"
                class="primary-btn"
                type="button"
            >
                ✅ Confirm Order
            </button>

            <button
                id="close-order-button"
                class="secondary-btn"
                type="button"
                style="margin-left:10px;"
            >
                Cancel
            </button>

        </div>
    `;

    const cartSection =
        document.getElementById("cart-section");

    if (cartSection) {

        cartSection.appendChild(section);

    } else {

        document.body.appendChild(section);
    }

    document
        .getElementById("confirm-order-button")
        .addEventListener(
            "click",
            placeCartOrder
        );

    document
        .getElementById("close-order-button")
        .addEventListener(
            "click",
            function () {

                section.remove();

            }
        );

    section.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}

// =========================================================
// PLACE CART ORDER
// =========================================================

async function placeCartOrder() {

    if (cart.length === 0) {

        alert("❌ Cart is empty.");

        return;
    }

    const nameInput =
        document.getElementById("customer-name");

    const emailInput =
        document.getElementById("customer-email");

    const name =
        nameInput
            ? nameInput.value.trim()
            : "";

    const email =
        emailInput
            ? emailInput.value.trim()
            : "";

    if (!name) {

        alert("Please enter customer name.");

        if (nameInput) {
            nameInput.focus();
        }

        return;
    }

    if (!email) {

        alert("Please enter email address.");

        if (emailInput) {
            emailInput.focus();
        }

        return;
    }

    const emailPattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {

        alert("Please enter a valid email address.");

        return;
    }

    // Backend currently supports one product per order.
    const item = cart[0];

    const productId =
        Number(item.id);

    const quantity =
        Number(item.quantity);

    if (!productId || productId <= 0) {

        alert("❌ Invalid Product ID.");

        return;
    }

    if (!quantity || quantity <= 0) {

        alert("❌ Invalid quantity.");

        return;
    }

    const confirmButton =
        document.getElementById(
            "confirm-order-button"
        );

    if (confirmButton) {

        confirmButton.disabled = true;
        confirmButton.textContent =
            "Placing Order... ⏳";
    }

    try {

        const response =
            await fetch(
                `${API_URL}/orders`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        customer_name:
                            name,

                        customer_email:
                            email,

                        product_id:
                            productId,

                        quantity:
                            quantity
                    })
                }
            );

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        console.log(
            "Order API response:",
            data
        );

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `Order failed: HTTP ${response.status}`
            );
        }

        const orderNumber =
            data.order_number ||
            data.order_id ||
            "Created";

        if (data.order_number) {

            localStorage.setItem(
                "lastOrderNumber",
                data.order_number
            );

            // Save local order information
            const orders =
                JSON.parse(
                    localStorage.getItem("orders") || "[]"
                );

            orders.push({

                order_number:
                    data.order_number,

                customer_name:
                    name,

                customer_email:
                    email,

                product:
                    item.name,

                quantity:
                    quantity,

                total_amount:
                    data.total_amount ??
                    item.price * quantity,

                status:
                    data.status ||
                    "Confirmed"
            });

            localStorage.setItem(
                "orders",
                JSON.stringify(orders)
            );
        }

        alert(
            `✅ Order placed successfully!\n\nOrder Number: ${orderNumber}`
        );

        cart = [];

        saveCart();

        updateCartUI();

        const orderSection =
            document.getElementById(
                "order-section"
            );

        if (orderSection) {
            orderSection.remove();
        }

        setOrderNumbers(
            data.order_number
        );

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    <h3>
                        ✅ Order placed successfully!
                    </h3>

                    <br>

                    <p>
                        <strong>
                            Order Number:
                        </strong>

                        ${escapeHTML(orderNumber)}
                    </p>

                    <p>
                        <strong>
                            Product:
                        </strong>

                        ${escapeHTML(
                            data.product ||
                            data.product_name ||
                            item.name
                        )}
                    </p>

                    <p>
                        <strong>
                            Quantity:
                        </strong>

                        ${quantity}
                    </p>

                    <p>
                        <strong>
                            Total:
                        </strong>

                        ₹${Number(
                            data.total_amount ??
                            item.price * quantity
                        ).toFixed(2)}
                    </p>

                    <p>
                        <strong>
                            Status:
                        </strong>

                        ${escapeHTML(
                            data.status ||
                            "Confirmed"
                        )}
                    </p>

                </div>
            `;
        }

        updateAdminProjectStats();

    } catch (error) {

        console.error(
            "Place Order Error:",
            error
        );

        alert(
            `❌ Unable to place order.\n\n${error.message}`
        );

        if (confirmButton) {

            confirmButton.disabled = false;

            confirmButton.textContent =
                "✅ Confirm Order";
        }
    }
}

// =========================================================
// SET ORDER NUMBERS
// =========================================================

function setOrderNumbers(orderNumber) {

    if (!orderNumber) {
        return;
    }

    if (trackOrderNumber) {
        trackOrderNumber.value =
            orderNumber;
    }

    if (cancelOrderNumber) {
        cancelOrderNumber.value =
            orderNumber;
    }

    if (refundOrderNumber) {
        refundOrderNumber.value =
            orderNumber;
    }
}

// =========================================================
// GET ORDER NUMBER
// =========================================================

function getOrderNumber(inputElement) {

    if (!inputElement) {
        return "";
    }

    return inputElement.value.trim();
}

// =========================================================
// TRACK ORDER
// =========================================================

async function trackOrder() {

    const orderNumber =
        getOrderNumber(
            trackOrderNumber
        );

    if (!orderNumber) {

        alert(
            "Please enter Order Number."
        );

        return;
    }

    if (orderResult) {

        orderResult.innerHTML =
            "<p>Loading order details... ⏳</p>";
    }

    try {

        const response =
            await fetch(
                `${API_URL}/orders/${encodeURIComponent(orderNumber)}`
            );

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `HTTP Error: ${response.status}`
            );
        }

        const order =
            data.order ||
            data;

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    <h3>
                        📦 Order Details
                    </h3>

                    <br>

                    <p>
                        <strong>
                            Order Number:
                        </strong>

                        ${escapeHTML(
                            order.order_number ||
                            orderNumber
                        )}
                    </p>

                    <p>
                        <strong>
                            Customer:
                        </strong>

                        ${escapeHTML(
                            order.customer_name ||
                            "N/A"
                        )}
                    </p>

                    <p>
                        <strong>
                            Email:
                        </strong>

                        ${escapeHTML(
                            order.customer_email ||
                            "N/A"
                        )}
                    </p>

                    <p>
                        <strong>
                            Product:
                        </strong>

                        ${escapeHTML(
                            order.product_name ||
                            "N/A"
                        )}
                    </p>

                    <p>
                        <strong>
                            Quantity:
                        </strong>

                        ${escapeHTML(
                            String(
                                order.quantity ?? 0
                            )
                        )}
                    </p>

                    <p>
                        <strong>
                            Total:
                        </strong>

                        ₹${Number(
                            order.total_amount || 0
                        ).toFixed(2)}
                    </p>

                    <p>
                        <strong>
                            Status:
                        </strong>

                        ${escapeHTML(
                            order.status ||
                            "Unknown"
                        )}
                    </p>

                    <p>
                        <strong>
                            Created:
                        </strong>

                        ${escapeHTML(
                            order.created_at ||
                            "N/A"
                        )}
                    </p>

                </div>
            `;
        }

    } catch (error) {

        console.error(
            "Track Order Error:",
            error
        );

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    ❌ Unable to track order.

                    <br><br>

                    ${escapeHTML(
                        error.message
                    )}

                </div>
            `;
        }
    }
}

// =========================================================
// CANCEL ORDER
// =========================================================

async function cancelOrder() {

    const orderNumber =
        getOrderNumber(
            cancelOrderNumber
        );

    if (!orderNumber) {

        alert(
            "Please enter Order Number."
        );

        return;
    }

    const confirmed =
        confirm(
            `Are you sure you want to cancel order ${orderNumber}?`
        );

    if (!confirmed) {
        return;
    }

    if (orderResult) {

        orderResult.innerHTML =
            "<p>Cancelling order... ⏳</p>";
    }

    try {

        const response =
            await fetch(
                `${API_URL}/orders/${encodeURIComponent(orderNumber)}/cancel`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `Cancel failed: HTTP ${response.status}`
            );
        }

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    ✅ Order cancelled successfully!

                    <br><br>

                    Order Number:

                    <strong>
                        ${escapeHTML(
                            data.order_number ||
                            orderNumber
                        )}
                    </strong>

                    <br><br>

                    Status:

                    ${escapeHTML(
                        data.status ||
                        "Cancelled"
                    )}

                </div>
            `;
        }

    } catch (error) {

        console.error(
            "Cancel Order Error:",
            error
        );

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    ❌ Unable to cancel order.

                    <br><br>

                    ${escapeHTML(
                        error.message
                    )}

                </div>
            `;
        }
    }
}

// =========================================================
// REFUND ORDER
// =========================================================

async function refundOrder() {

    const orderNumber =
        getOrderNumber(
            refundOrderNumber
        );

    if (!orderNumber) {

        alert(
            "Please enter Order Number."
        );

        return;
    }

    const confirmed =
        confirm(
            `Do you want to request a refund for order ${orderNumber}?`
        );

    if (!confirmed) {
        return;
    }

    if (orderResult) {

        orderResult.innerHTML =
            "<p>Processing refund request... ⏳</p>";
    }

    try {

        const response =
            await fetch(
                `${API_URL}/orders/${encodeURIComponent(orderNumber)}/refund`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `Refund failed: HTTP ${response.status}`
            );
        }

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    💰 Refund request successful!

                    <br><br>

                    Order Number:

                    <strong>
                        ${escapeHTML(
                            data.order_number ||
                            orderNumber
                        )}
                    </strong>

                    <br><br>

                    Status:

                    ${escapeHTML(
                        data.status ||
                        "Refunded"
                    )}

                    <br><br>

                    ${escapeHTML(
                        data.message ||
                        "Refund request has been submitted."
                    )}

                </div>
            `;
        }

    } catch (error) {

        console.error(
            "Refund Order Error:",
            error
        );

        if (orderResult) {

            orderResult.innerHTML = `

                <div>

                    ❌ Unable to process refund.

                    <br><br>

                    ${escapeHTML(
                        error.message
                    )}

                </div>
            `;
        }
    }
}

// =========================================================
// ADMIN - LOAD USERS
// =========================================================

async function loadAdminUsers() {

    try {

        const response =
            await fetch(
                `${API_URL}/users`
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to load users"
            );
        }

        const users =
            data.users || [];

        displayAdminUsers(users);

        updateAdminUserStats(users);

        updateAdminProjectStats();

    } catch (error) {

        console.error(
            "Admin users error:",
            error
        );

        const tbody =
            document.getElementById(
                "admin-users-body"
            );

        if (tbody) {

            tbody.innerHTML = `

                <tr>

                    <td
                        colspan="7"
                        class="empty-users"
                    >
                        ❌ Unable to load users.
                        <br>
                        ${escapeHTML(error.message)}
                    </td>

                </tr>
            `;
        }
    }
}

// =========================================================
// DISPLAY ADMIN USERS
// =========================================================

function displayAdminUsers(users) {

    const tbody =
        document.getElementById(
            "admin-users-body"
        );

    const count =
        document.getElementById(
            "admin-user-count"
        );

    if (!tbody) {
        return;
    }

    if (count) {

        count.textContent =
            `${users.length} User${users.length !== 1 ? "s" : ""}`;
    }

    if (users.length === 0) {

        tbody.innerHTML = `

            <tr>

                <td
                    colspan="7"
                    class="empty-users"
                >
                    No users found
                </td>

            </tr>
        `;

        return;
    }

    tbody.innerHTML =
        users.map(user => {

            const status =
                user.status || "Active";

            const statusClass =
                status === "Active"
                    ? "status-active"
                    : "status-inactive";

            const nextStatus =
                status === "Active"
                    ? "Inactive"
                    : "Active";

            return `

                <tr>

                    <td>
                        #${escapeHTML(String(user.id))}
                    </td>

                    <td>
                        <strong>
                            ${escapeHTML(
                                user.name ||
                                "Unknown"
                            )}
                        </strong>
                    </td>

                    <td>
                        ${escapeHTML(
                            user.email ||
                            "-"
                        )}
                    </td>

                    <td>
                        ${escapeHTML(
                            user.phone ||
                            "-"
                        )}
                    </td>

                    <td>

                        <span
                            class="${statusClass}"
                        >
                            ${escapeHTML(status)}
                        </span>

                    </td>

                    <td>
                        ${formatAdminDate(
                            user.created_at
                        )}
                    </td>

                    <td>

                        <button
                            class="action-btn view-btn"
                            onclick="viewAdminUser(${user.id})"
                        >
                            👁 View
                        </button>

                        <button
                            class="action-btn status-btn"
                            onclick="changeAdminUserStatus(${user.id}, '${nextStatus}')"
                        >
                            ${
                                nextStatus === "Active"
                                    ? "🟢 Activate"
                                    : "⏸ Deactivate"
                            }
                        </button>

                        <button
                            class="action-btn delete-btn"
                            onclick="deleteAdminUser(${user.id})"
                        >
                            🗑 Delete
                        </button>

                    </td>

                </tr>
            `;

        }).join("");
}

// =========================================================
// ADMIN USER STATS
// =========================================================

function updateAdminUserStats(users) {

    const totalUsers =
        document.getElementById(
            "admin-total-users"
        );

    const activeUsers =
        document.getElementById(
            "admin-active-users"
        );

    if (totalUsers) {

        totalUsers.textContent =
            users.length;
    }

    if (activeUsers) {

        activeUsers.textContent =
            users.filter(
                user =>
                    user.status === "Active"
            ).length;
    }
}

// =========================================================
// ADMIN ADD USER
// =========================================================

async function addAdminUser() {

    const nameInput =
        document.getElementById(
            "admin-user-name"
        );

    const emailInput =
        document.getElementById(
            "admin-user-email"
        );

    const phoneInput =
        document.getElementById(
            "admin-user-phone"
        );

    const name =
        nameInput
            ? nameInput.value.trim()
            : "";

    const email =
        emailInput
            ? emailInput.value.trim()
            : "";

    const phone =
        phoneInput
            ? phoneInput.value.trim()
            : "";

    if (!name || !email) {

        alert(
            "Please enter name and email."
        );

        return;
    }

    try {

        const response =
            await fetch(
                `${API_URL}/users`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        name: name,

                        email: email,

                        phone: phone
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            alert(
                data.error ||
                "Unable to add user"
            );

            return;
        }

        alert(
            "✅ User added successfully!"
        );

        if (nameInput) {
            nameInput.value = "";
        }

        if (emailInput) {
            emailInput.value = "";
        }

        if (phoneInput) {
            phoneInput.value = "";
        }

        await loadAdminUsers();

    } catch (error) {

        console.error(
            "Add user error:",
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}

// =========================================================
// ADMIN VIEW USER
// =========================================================

async function viewAdminUser(userId) {

    try {

        const response =
            await fetch(
                `${API_URL}/users/${userId}`
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            alert(
                data.error ||
                "User not found"
            );

            return;
        }

        const user =
            data.user;

        alert(

            "User Details\n\n" +

            "ID: " +
            user.id +

            "\nName: " +
            user.name +

            "\nEmail: " +
            user.email +

            "\nPhone: " +
            (user.phone || "-") +

            "\nStatus: " +
            user.status +

            "\nCreated: " +
            formatAdminDate(
                user.created_at
            )
        );

    } catch (error) {

        console.error(
            "View user error:",
            error
        );

        alert(
            "Unable to load user."
        );
    }
}

// =========================================================
// ADMIN CHANGE STATUS
// =========================================================

async function changeAdminUserStatus(
    userId,
    newStatus
) {

    try {

        const response =
            await fetch(
                `${API_URL}/users/${userId}/status`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        status:
                            newStatus
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            alert(
                data.error ||
                "Unable to update status"
            );

            return;
        }

        await loadAdminUsers();

    } catch (error) {

        console.error(
            "Status update error:",
            error
        );

        alert(
            "Unable to update user status."
        );
    }
}

// =========================================================
// ADMIN DELETE USER
// =========================================================

async function deleteAdminUser(userId) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this user?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API_URL}/users/${userId}`,
                {
                    method: "DELETE"
                }
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            alert(
                data.error ||
                "Unable to delete user"
            );

            return;
        }

        alert(
            "✅ User deleted successfully!"
        );

        await loadAdminUsers();

    } catch (error) {

        console.error(
            "Delete user error:",
            error
        );

        alert(
            "Unable to delete user."
        );
    }
}

// =========================================================
// ADMIN DATE
// =========================================================

function formatAdminDate(dateValue) {

    if (!dateValue) {
        return "-";
    }

    try {

        return new Date(dateValue)
            .toLocaleDateString("en-IN");

    } catch {

        return String(dateValue);
    }
}

// =========================================================
// ADMIN PROJECT STATS
// =========================================================

function updateAdminProjectStats() {

    const productsCount =
        document.getElementById(
            "admin-total-products"
        );

    if (productsCount) {

        productsCount.textContent =
            allProducts.length;
    }

    const totalOrders =
        document.getElementById(
            "admin-total-orders"
        );

    if (totalOrders) {

        const savedOrders =
            JSON.parse(
                localStorage.getItem(
                    "orders"
                ) || "[]"
            );

        totalOrders.textContent =
            savedOrders.length;
    }
}

// =========================================================
// CHECKOUT BUTTON
// =========================================================

if (checkoutButton) {

    checkoutButton.addEventListener(
        "click",
        openOrderForm
    );
}

// =========================================================
// SEND BUTTON
// =========================================================

if (sendButton) {

    sendButton.addEventListener(
        "click",
        sendMessage
    );
}

// =========================================================
// CHAT ENTER KEY
// =========================================================

if (messageInput) {

    messageInput.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                event.preventDefault();

                sendMessage();
            }
        }
    );
}

// =========================================================
// LOAD PRODUCTS BUTTON
// =========================================================

if (loadProductsButton) {

    loadProductsButton.addEventListener(
        "click",
        loadProducts
    );
}

// =========================================================
// TRACK BUTTON
// =========================================================

if (trackOrderButton) {

    trackOrderButton.addEventListener(
        "click",
        trackOrder
    );
}

// =========================================================
// CANCEL BUTTON
// =========================================================

if (cancelOrderButton) {

    cancelOrderButton.addEventListener(
        "click",
        cancelOrder
    );
}

// =========================================================
// REFUND BUTTON
// =========================================================

if (refundOrderButton) {

    refundOrderButton.addEventListener(
        "click",
        refundOrder
    );
}

// =========================================================
// START APPLICATION
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        updateCartUI();

        loadProducts();

        updateAdminProjectStats();

        const lastOrder =
            localStorage.getItem(
                "lastOrderNumber"
            );

        if (lastOrder) {

            setOrderNumbers(
                lastOrder
            );
        }

    }
);

console.log(
    "✅ TechStore AI Customer Support loaded successfully."
);