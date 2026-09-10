
// =========================================================
// TECHSTORE AI CUSTOMER SUPPORT - FRONTEND
// =========================================================

let allProducts = [];
let cart = JSON.parse(localStorage.getItem("cart")) || [];

const API_URL = "http://127.0.0.1:5000/api";

// =========================================================
// DOM ELEMENTS
// =========================================================

const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

const loadProductsButton =
    document.getElementById("load-products-button");

const cartContainer =
    document.getElementById("cart-container");

const cartSummary =
    document.getElementById("cart-summary");

const orderResult =
    document.getElementById("order-result");

const trackOrderNumber =
    document.getElementById("track-order-number");

const cancelOrderNumber =
    document.getElementById("cancel-order-number");

const refundOrderNumber =
    document.getElementById("refund-order-number");

const trackOrderButton =
    document.getElementById("track-order-button");

const cancelOrderButton =
    document.getElementById("cancel-order-button");

const refundOrderButton =
    document.getElementById("refund-order-button");

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
// GET PRODUCT ID
// =========================================================

function getProductId(product) {

    return String(
        product.id ??
        product.product_id ??
        ""
    );
}

// =========================================================
// GET STORE NAME
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

    const storeMap = {
        5: "Amazon",
        6: "Flipkart",
        7: "Meesho",
        8: "Myntra"
    };

    return storeMap[storeId] || "Other Store";
}

// =========================================================
// GET PRODUCT IMAGE
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
// GET DELIVERY
// =========================================================

function getDelivery(product) {

    const delivery =
        product.delivery ??
        product.delivery_time;

    // If backend gives 2 or 3, use it
    if (
        delivery !== undefined &&
        delivery !== null &&
        delivery !== "" &&
        Number(delivery) > 0
    ) {

        if (
            typeof delivery === "number" ||
            !isNaN(Number(delivery))
        ) {
            return `${Number(delivery)} days`;
        }

        return String(delivery);
    }

    // Default delivery
    return Math.random() < 0.5
        ? "2 days"
        : "3 days";
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

    messageDiv.className =
        `message ${type}`;

    messageDiv.textContent =
        message;

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

    addMessage(
        message,
        "user"
    );

    messageInput.value = "";

    if (sendButton) {
        sendButton.disabled = true;
    }

    const thinkingMessage =
        addMessage(
            "Thinking... 🤖",
            "bot"
        );

    try {

        const response =
            await fetch(
                `${API_URL}/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
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

        addMessage(
            reply,
            "bot"
        );

        // =================================================
        // PRODUCT QUESTION DETECTION
        // =================================================

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
            "buy"

        ];

        const isProductQuestion =
            productKeywords.some(
                keyword =>
                    lowerMessage.includes(keyword)
            );

        // If user asks about a product,
        // make sure products are loaded.
        // No recommendation section is created.
        if (isProductQuestion) {

            if (allProducts.length === 0) {
                await loadProducts();
            }
        }

    } catch (error) {

        console.error(
            "Chat Error:",
            error
        );

        if (thinkingMessage) {
            thinkingMessage.remove();
        }

        addMessage(
            "❌ Unable to connect to AI server. Please make sure the backend is running on port 5000.",
            "bot"
        );

    } finally {

        if (sendButton) {
            sendButton.disabled = false;
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

    Object.values(storeContainers)
        .forEach(id => {

            const container =
                document.getElementById(id);

            if (container) {

                container.innerHTML =
                    "<p>Loading products... ⏳</p>";
            }
        });

    if (loadProductsButton) {

        loadProductsButton.disabled = true;

        loadProductsButton.textContent =
            "Loading...";
    }

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
                `Products API Error: ${response.status}`
            );
        }

        if (Array.isArray(data)) {

            allProducts = data;

        } else if (
            Array.isArray(data.products)
        ) {

            allProducts = data.products;

        } else if (
            Array.isArray(data.data)
        ) {

            allProducts = data.data;

        } else {

            allProducts = [];
        }

        console.log(
            "Total Products:",
            allProducts.length
        );

        if (allProducts.length === 0) {

            Object.values(storeContainers)
                .forEach(id => {

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

    } catch (error) {

        console.error(
            "Load Products Error:",
            error
        );

        Object.values(storeContainers)
            .forEach(id => {

                const container =
                    document.getElementById(id);

                if (container) {

                    container.innerHTML = `
                        <div class="error-message">
                            ❌ Unable to load products.
                            <br><br>
                            Please make sure the backend is running.
                        </div>
                    `;
                }
            });

    } finally {

        if (loadProductsButton) {

            loadProductsButton.disabled = false;

            loadProductsButton.textContent =
                "Load Products";
        }
    }
}

// =========================================================
// CREATE STORE SECTIONS
// =========================================================

function createStoreSections() {

    stores.forEach(
        storeName => {

            const container =
                document.getElementById(
                    storeContainers[storeName]
                );

            if (!container) {
                return;
            }

            container.innerHTML = "";

            const storeProducts =
                allProducts.filter(
                    product =>
                        getStoreName(product)
                            .toLowerCase()
                            .trim() ===
                        storeName.toLowerCase()
                );

            if (storeProducts.length === 0) {

                container.innerHTML = `
                    <p class="no-products">
                        No products available in
                        ${escapeHTML(storeName)}.
                    </p>
                `;

                return;
            }

            storeProducts.forEach(
                product => {

                    container.appendChild(
                        createProductCard(product)
                    );

                }
            );
        }
    );
}

// =========================================================
// CREATE PRODUCT CARD
// =========================================================

function createProductCard(product) {

    const card =
        document.createElement("div");

    card.className =
        "product-card";

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

        <div class="product-image-box">

            <img
                class="product-image"
                src="${escapeHTML(image)}"
                alt="${escapeHTML(name)}"
            >

        </div>

        <div class="product-info">

            <h4>
                ${escapeHTML(name)}
            </h4>

            <p class="brand">
                ${escapeHTML(brand)}
            </p>

            <div class="rating">

                ⭐ ${rating.toFixed(1)}

                <span>
                    (${reviews} reviews)
                </span>

            </div>

            <div class="price">
                ₹${price.toFixed(2)}
            </div>

            ${
                discount
                    ? `
                        <div class="discount">
                            ${escapeHTML(
                                String(discount)
                            )}% OFF
                        </div>
                    `
                    : ""
            }

            <p class="stock">

                📦 Stock:

                ${escapeHTML(
                    String(stock)
                )}

            </p>

            <p class="delivery">

                🚚 Delivery:

                ${escapeHTML(
                    String(delivery)
                )}

            </p>

            <div class="product-buttons">

                <button
                    class="cart-button"
                    type="button"
                >
                    🛒 Add to Cart
                </button>

                ${
                    productUrl
                        ? `
                            <button
                                class="view-button"
                                type="button"
                            >
                                🔗 View Product
                            </button>
                        `
                        : ""
                }

            </div>

        </div>
    `;

    // =====================================================
    // ADD TO CART
    // =====================================================

    const addButton =
        card.querySelector(".cart-button");

    if (addButton) {

        addButton.addEventListener(
            "click",
            function () {

                addToCart(productId);

            }
        );
    }

    // =====================================================
    // VIEW PRODUCT
    // =====================================================

    const viewButton =
        card.querySelector(".view-button");

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

    // =====================================================
    // IMAGE ERROR
    // =====================================================

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

        alert(
            "❌ Product not found."
        );

        return;
    }

    const id =
        getProductId(product);

    if (!id) {

        alert(
            "❌ Product ID not found."
        );

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
                Number(
                    product.price || 0
                ),

            quantity: 1,

            store:
                getStoreName(product),

            image:
                getProductImage(product)
        });
    }

    saveCart();

    updateCartUI();

    alert(
        "✅ Product added to cart!"
    );
}

// =========================================================
// REMOVE FROM CART
// =========================================================

function removeFromCart(index) {

    if (!cart[index]) {
        return;
    }

    cart.splice(
        index,
        1
    );

    saveCart();

    updateCartUI();
}

// =========================================================
// CHANGE QUANTITY
// =========================================================

function changeQuantity(
    index,
    change
) {

    if (!cart[index]) {
        return;
    }

    cart[index].quantity =
        Number(
            cart[index].quantity || 1
        ) +
        Number(change);

    if (
        cart[index].quantity <= 0
    ) {

        cart.splice(
            index,
            1
        );
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

    if (!cartContainer) {
        return;
    }

    if (cart.length === 0) {

        cartContainer.innerHTML = `
            <p class="cart-empty">
                Your cart is empty.
            </p>
        `;

        if (cartSummary) {
            cartSummary.innerHTML = "";
        }

        return;
    }

    let html = `
        <div class="cart-items">
    `;

    cart.forEach(
        (item, index) => {

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

                    <div class="cart-item-details">

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
                                class="quantity-minus"
                                data-index="${index}"
                            >
                                −
                            </button>

                            <span class="quantity-value">
                                ${Number(item.quantity)}
                            </span>

                            <button
                                type="button"
                                class="quantity-plus"
                                data-index="${index}"
                            >
                                +
                            </button>

                        </div>

                    </div>

                    <button
                        type="button"
                        class="remove-cart-button"
                        data-index="${index}"
                    >
                        Remove
                    </button>

                </div>
            `;
        }
    );

    html += `
        </div>
    `;

    cartContainer.innerHTML =
        html;

    if (cartSummary) {

        cartSummary.innerHTML = `

            <h3>
                Total:
                ₹${getCartTotal().toFixed(2)}
            </h3>

            <button
                type="button"
                id="place-cart-order-button"
            >
                📦 Place Order
            </button>
        `;
    }

    // =====================================================
    // MINUS
    // =====================================================

    cartContainer
        .querySelectorAll(".quantity-minus")
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    function () {

                        changeQuantity(
                            Number(
                                this.dataset.index
                            ),
                            -1
                        );

                    }
                );
            }
        );

    // =====================================================
    // PLUS
    // =====================================================

    cartContainer
        .querySelectorAll(".quantity-plus")
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    function () {

                        changeQuantity(
                            Number(
                                this.dataset.index
                            ),
                            1
                        );

                    }
                );
            }
        );

    // =====================================================
    // REMOVE
    // =====================================================

    cartContainer
        .querySelectorAll(".remove-cart-button")
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    function () {

                        removeFromCart(
                            Number(
                                this.dataset.index
                            )
                        );

                    }
                );
            }
        );

    // =====================================================
    // PLACE ORDER BUTTON
    // =====================================================

    const placeButton =
        document.getElementById(
            "place-cart-order-button"
        );

    if (placeButton) {

        placeButton.addEventListener(
            "click",
            openOrderForm
        );
    }
}

// =========================================================
// OPEN ORDER FORM
// =========================================================

function openOrderForm() {

    if (cart.length === 0) {

        alert(
            "❌ Cart is empty."
        );

        return;
    }

    let section =
        document.getElementById(
            "order-section"
        );

    if (!section) {

        section =
            document.createElement(
                "section"
            );

        section.id =
            "order-section";

        section.className =
            "card";

        const mainContainer =
            document.querySelector(
                ".main-container"
            );

        if (mainContainer) {

            mainContainer.appendChild(
                section
            );
        }
    }

    section.innerHTML = `

        <h2>
            📦 Place Order
        </h2>

        <p>
            Enter your details to place the order.
        </p>

        <div class="order-form">

            <input
                id="customer-name"
                type="text"
                placeholder="Customer Name"
            >

            <input
                id="customer-email"
                type="email"
                placeholder="Email"
            >

            <button
                id="confirm-order-button"
                type="button"
            >
                Confirm Order
            </button>

        </div>
    `;

    const confirmButton =
        document.getElementById(
            "confirm-order-button"
        );

    if (confirmButton) {

        confirmButton.addEventListener(
            "click",
            placeCartOrder
        );
    }

    section.scrollIntoView({
        behavior: "smooth"
    });
}

// =========================================================
// PLACE CART ORDER
// =========================================================

async function placeCartOrder() {

    if (cart.length === 0) {

        alert(
            "❌ Cart is empty."
        );

        return;
    }

    const nameInput =
        document.getElementById(
            "customer-name"
        );

    const emailInput =
        document.getElementById(
            "customer-email"
        );

    const name =
        nameInput
            ? nameInput.value.trim()
            : "";

    const email =
        emailInput
            ? emailInput.value.trim()
            : "";

    if (!name || !email) {

        alert(
            "Please enter customer name and email."
        );

        return;
    }

    // =====================================================
    // BACKEND SUPPORTS ONE PRODUCT PER ORDER
    // =====================================================

    const item = cart[0];

    const productId =
        Number(item.id);

    const quantity =
        Number(item.quantity);

    if (!productId || productId <= 0) {

        alert(
            "❌ Invalid Product ID."
        );

        console.error(
            "Invalid product ID:",
            item.id
        );

        return;
    }

    if (!quantity || quantity <= 0) {

        alert(
            "❌ Invalid quantity."
        );

        return;
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

        alert(
            `✅ Order placed successfully!\n\nOrder Number: ${orderNumber}`
        );

        if (data.order_number) {

            localStorage.setItem(
                "lastOrderNumber",
                data.order_number
            );
        }

        // =================================================
        // CLEAR CART
        // =================================================

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

                <div class="success-message">

                    ✅ Order placed successfully!

                    <br><br>

                    Order Number:

                    <strong>
                        ${escapeHTML(
                            orderNumber
                        )}
                    </strong>

                    <br><br>

                    Product:

                    ${escapeHTML(
                        data.product ||
                        item.name
                    )}

                    <br><br>

                    Quantity:

                    ${escapeHTML(
                        String(
                            data.quantity ||
                            quantity
                        )
                    )}

                    <br><br>

                    Total:

                    ₹${Number(
                        data.total_amount ||
                        item.price * quantity
                    ).toFixed(2)}

                    <br><br>

                    Status:

                    ${escapeHTML(
                        data.status ||
                        "Confirmed"
                    )}

                </div>
            `;
        }

    } catch (error) {

        console.error(
            "Place Order Error:",
            error
        );

        alert(
            `❌ Unable to place order.\n\n${error.message}`
        );
    }
}

// =========================================================
// SET ORDER NUMBERS
// =========================================================

function setOrderNumbers(
    orderNumber
) {

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

function getOrderNumber(
    inputElement
) {

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

                <div class="order-result">

                    <h3>
                        📦 Order Details
                    </h3>

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

                <div class="error-message">

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

                <div class="success-message">

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

                <div class="error-message">

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

                <div class="success-message">

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

                <div class="error-message">

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
// EVENT LISTENERS
// =========================================================

if (sendButton) {

    sendButton.addEventListener(
        "click",
        sendMessage
    );
}

if (messageInput) {

    messageInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                event.preventDefault();

                sendMessage();
            }
        }
    );
}

if (loadProductsButton) {

    loadProductsButton.addEventListener(
        "click",
        loadProducts
    );
}

if (trackOrderButton) {

    trackOrderButton.addEventListener(
        "click",
        trackOrder
    );
}

if (cancelOrderButton) {

    cancelOrderButton.addEventListener(
        "click",
        cancelOrder
    );
}

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
    function () {

        updateCartUI();

        loadProducts();

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
    "TechStore AI Customer Support loaded successfully."
);

