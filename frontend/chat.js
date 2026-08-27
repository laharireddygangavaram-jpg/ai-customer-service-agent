const API_URL = "http://127.0.0.1:5000/api";

const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const chatBox = document.getElementById("chat-box");

function addMessage(message, type) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message " + type;
    messageDiv.textContent = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) return;

    addMessage(message, "user");
    messageInput.value = "";

    sendButton.disabled = true;
    sendButton.textContent = "Sending...";

    try {
        const response = await fetch(API_URL + "/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        if (response.ok) {
            addMessage(data.response, "bot");
        } else {
            addMessage(
                data.error || "Something went wrong.",
                "bot"
            );
        }

    } catch (error) {
        console.error(error);

        addMessage(
            "Unable to connect to the customer support server.",
            "bot"
        );
    }

    sendButton.disabled = false;
    sendButton.textContent = "Send";
    messageInput.focus();
}

sendButton.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

const loadProductsButton =
    document.getElementById("load-products-button");

const productsContainer =
    document.getElementById("products-container");

if (loadProductsButton) {
    loadProductsButton.addEventListener(
        "click",
        loadProducts
    );
}

async function loadProducts() {

    productsContainer.innerHTML =
        "<p>Loading products...</p>";

    try {

        const response =
            await fetch(API_URL + "/products");

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to load products"
            );
        }

        productsContainer.innerHTML = "";

        const products =
            data.products || data;

        products.forEach(function(product) {

            const card =
                document.createElement("div");

            card.className = "product-card";

            card.innerHTML = `
                <h3>${product.name}</h3>
                <p>${product.description}</p>
                <p>Price: $${product.price}</p>
                <p>Stock: ${product.stock}</p>
                <button onclick="selectProduct(${product.id})">
                    Buy This Product
                </button>
            `;

            productsContainer.appendChild(card);
        });

    } catch (error) {

        console.error(error);

        productsContainer.innerHTML =
            "<p>Unable to load products.</p>";
    }
}

function selectProduct(productId) {

    document.getElementById("product-id").value =
        productId;

    document.getElementById("quantity").value = 1;

    document.getElementById("customer-name").focus();
}

const placeOrderButton =
    document.getElementById("place-order-button");

const orderResult =
    document.getElementById("order-result");

if (placeOrderButton) {
    placeOrderButton.addEventListener(
        "click",
        placeOrder
    );
}

async function placeOrder() {

    const customerName =
        document.getElementById("customer-name").value.trim();

    const customerEmail =
        document.getElementById("customer-email").value.trim();

    const productId =
        Number(
            document.getElementById("product-id").value
        );

    const quantity =
        Number(
            document.getElementById("quantity").value
        );

    if (
        !customerName ||
        !customerEmail ||
        !productId ||
        !quantity
    ) {

        orderResult.innerHTML =
            "<p>Please fill all order details.</p>";

        return;
    }

    placeOrderButton.disabled = true;

    try {

        const response =
            await fetch(API_URL + "/orders", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    customer_name: customerName,
                    customer_email: customerEmail,
                    product_id: productId,
                    quantity: quantity

                })
            });

        const data =
            await response.json();

        if (!response.ok) {

            orderResult.innerHTML =
                `<p>${data.error || "Order failed."}</p>`;

            return;
        }

        orderResult.innerHTML = `
            <div class="success">
                <h3>Order Placed Successfully!</h3>
                <p>Order ID: <strong>${data.order_number}</strong></p>
                <p>Product: ${data.product}</p>
                <p>Quantity: ${data.quantity}</p>
                <p>Total: $${data.total_amount}</p>
                <p>Status: ${data.status}</p>
            </div>
        `;

        document.getElementById("order-number").value =
            data.order_number;

        loadProducts();

    } catch (error) {

        console.error(error);

        orderResult.innerHTML =
            "<p>Unable to place order.</p>";
    }

    placeOrderButton.disabled = false;
}

const trackOrderButton =
    document.getElementById("track-order-button");

const trackingResult =
    document.getElementById("tracking-result");

if (trackOrderButton) {
    trackOrderButton.addEventListener(
        "click",
        trackOrder
    );
}

async function trackOrder() {

    const orderNumber =
        document.getElementById("order-number").value.trim();

    if (!orderNumber) {

        trackingResult.innerHTML =
            "<p>Please enter an order number.</p>";

        return;
    }

    trackingResult.innerHTML =
        "<p>Checking order...</p>";

    try {

        const response =
            await fetch(
                API_URL +
                "/orders/" +
                encodeURIComponent(orderNumber)
            );

        const data =
            await response.json();

        if (!response.ok) {

            trackingResult.innerHTML =
                `<p>${data.error || "Order not found."}</p>`;

            return;
        }

        const order = data.order;

        trackingResult.innerHTML = `
            <div class="tracking-card">
                <h3>Order Details</h3>
                <p>Order ID: <strong>${order.order_number}</strong></p>
                <p>Customer: ${order.customer_name}</p>
                <p>Email: ${order.customer_email}</p>
                <p>Product: ${order.product_name}</p>
                <p>Quantity: ${order.quantity}</p>
                <p>Total: $${order.total_amount}</p>
                <p>Status: <strong>${order.status}</strong></p>
                <p>Created: ${order.created_at}</p>
            </div>
        `;

    } catch (error) {

        console.error(error);

        trackingResult.innerHTML =
            "<p>Unable to connect to the server.</p>";
    }
}