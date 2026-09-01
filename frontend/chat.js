
const API_URL = "http://127.0.0.1:5000";

// =====================================
// DOM ELEMENTS
// =====================================

const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");

const loadProductsButton =
    document.getElementById("load-products-button");

const amazonProducts =
    document.getElementById("amazon-products");

const flipkartProducts =
    document.getElementById("flipkart-products");

const meeshoProducts =
    document.getElementById("meesho-products");

const myntraProducts =
    document.getElementById("myntra-products");


// =====================================
// ESCAPE HTML
// =====================================

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// =====================================
// CHAT MESSAGE
// =====================================

function addMessage(message, type) {

    const div = document.createElement("div");

    div.classList.add("message");

    if (type === "user") {
        div.classList.add("user");
    } else {
        div.classList.add("bot");
    }

    div.textContent = message;

    chatBox.appendChild(div);

    chatBox.scrollTop = chatBox.scrollHeight;
}


// =====================================
// FORMAT PRICE
// =====================================

function formatPrice(price) {

    if (
        price === null ||
        price === undefined ||
        price === ""
    ) {
        return "Price unavailable";
    }

    const number = Number(price);

    if (Number.isNaN(number)) {
        return `₹${price}`;
    }

    return `₹${number.toLocaleString("en-IN")}`;
}


// =====================================
// GET STORE NAME
// =====================================

function getStoreName(product) {

    return (
        product.store_name ||
        product.store ||
        product.platform ||
        product.marketplace ||
        product.source ||
        ""
    )
    .toString()
    .trim()
    .toLowerCase();
}


// =====================================
// GET STORE CATEGORY
// =====================================

function getStoreCategory(product) {

    const store = getStoreName(product);

    if (store.includes("amazon")) {
        return "amazon";
    }

    if (store.includes("flipkart")) {
        return "flipkart";
    }

    if (store.includes("meesho")) {
        return "meesho";
    }

    if (store.includes("myntra")) {
        return "myntra";
    }

    return "other";
}


// =====================================
// CREATE PRODUCT CARD
// =====================================

function createProductCard(product) {

    const name =
        product.name ||
        product.product_name ||
        product.title ||
        "Unknown Product";

    const description =
        product.description ||
        "No description available.";

    const price =
        product.price ??
        product.selling_price ??
        product.current_price ??
        product.cost ??
        0;

    const rating =
        product.rating ??
        product.stars ??
        "";

    const reviews =
        product.reviews ??
        product.review_count ??
        product.total_reviews ??
        "";

    const stock =
        product.stock ??
        "";

    const image =
        product.image_url ||
        product.image ||
        product.thumbnail ||
        "";

    const productUrl =
        product.product_url ||
        product.url ||
        product.link ||
        "";


    const card = document.createElement("div");

    card.className = "product-card";


    // IMAGE

    let imageHTML = "";

    if (image) {

        imageHTML = `
            <img
                src="${escapeHTML(image)}"
                alt="${escapeHTML(name)}"
                class="product-image"
                onerror="this.style.display='none';"
            >
        `;

    } else {

        imageHTML = `
            <div class="product-image-placeholder">
                🛍️
            </div>
        `;

    }


    // RATING

    let ratingHTML = "";

    if (rating !== "") {

        ratingHTML = `
            <div class="product-rating">
                ⭐ ${escapeHTML(rating)}
                ${
                    reviews !== ""
                        ? ` (${escapeHTML(reviews)} reviews)`
                        : ""
                }
            </div>
        `;

    }


    // STOCK

    let stockHTML = "";

    if (stock !== "") {

        stockHTML = `
            <div class="product-stock">
                Stock: ${escapeHTML(stock)}
            </div>
        `;

    }


    // BUTTON

    let buttonHTML = "";

    if (productUrl) {

        buttonHTML = `
            <a
                href="${escapeHTML(productUrl)}"
                target="_blank"
                rel="noopener noreferrer"
                class="product-button"
            >
                View Product
            </a>
        `;

    }


    card.innerHTML = `

        ${imageHTML}

        <div class="product-content">

            <h3 class="product-name">
                ${escapeHTML(name)}
            </h3>

            <p class="product-description">
                ${escapeHTML(description)}
            </p>

            <div class="product-price">
                ${formatPrice(price)}
            </div>

            ${ratingHTML}

            ${stockHTML}

            ${buttonHTML}

        </div>
    `;


    return card;
}


// =====================================
// SHOW EMPTY MESSAGE
// =====================================

function showEmptyMessage(container, message) {

    if (!container) {
        return;
    }

    container.innerHTML = `
        <p class="no-products">
            ${escapeHTML(message)}
        </p>
    `;
}


// =====================================
// CLEAR PRODUCTS
// =====================================

function clearProducts() {

    amazonProducts.innerHTML = "";
    flipkartProducts.innerHTML = "";
    meeshoProducts.innerHTML = "";
    myntraProducts.innerHTML = "";
}


// =====================================
// RENDER PRODUCTS
// =====================================

function renderProducts(products) {

    clearProducts();


    if (!products || products.length === 0) {

        showEmptyMessage(
            amazonProducts,
            "No Amazon products available."
        );

        showEmptyMessage(
            flipkartProducts,
            "No Flipkart products available."
        );

        showEmptyMessage(
            meeshoProducts,
            "No Meesho products available."
        );

        showEmptyMessage(
            myntraProducts,
            "No Myntra products available."
        );

        return;
    }


    let amazonCount = 0;
    let flipkartCount = 0;
    let meeshoCount = 0;
    let myntraCount = 0;


    products.forEach(product => {

        const category =
            getStoreCategory(product);

        const card =
            createProductCard(product);


        if (category === "amazon") {

            amazonProducts.appendChild(card);

            amazonCount++;

        }


        else if (category === "flipkart") {

            flipkartProducts.appendChild(card);

            flipkartCount++;

        }


        else if (category === "meesho") {

            meeshoProducts.appendChild(card);

            meeshoCount++;

        }


        else if (category === "myntra") {

            myntraProducts.appendChild(card);

            myntraCount++;

        }


        // Unknown stores
        else {

            console.log(
                "Unknown store:",
                product
            );

        }

    });


    // Empty sections

    if (amazonCount === 0) {

        showEmptyMessage(
            amazonProducts,
            "No Amazon products available."
        );

    }


    if (flipkartCount === 0) {

        showEmptyMessage(
            flipkartProducts,
            "No Flipkart products available."
        );

    }


    if (meeshoCount === 0) {

        showEmptyMessage(
            meeshoProducts,
            "No Meesho products available."
        );

    }


    if (myntraCount === 0) {

        showEmptyMessage(
            myntraProducts,
            "No Myntra products available."
        );

    }


    console.log("Amazon:", amazonCount);
    console.log("Flipkart:", flipkartCount);
    console.log("Meesho:", meeshoCount);
    console.log("Myntra:", myntraCount);

}


// =====================================
// LOAD PRODUCTS
// =====================================

async function loadProducts() {

    console.log("Loading products...");


    try {

        loadProductsButton.disabled = true;

        loadProductsButton.textContent =
            "Loading...";


        const response = await fetch(
            `${API_URL}/api/products`
        );


        console.log(
            "API Status:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                `HTTP Error ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "PRODUCT API RESPONSE:",
            data
        );


        let products = [];


        if (Array.isArray(data)) {

            products = data;

        }

        else if (
            data &&
            Array.isArray(data.products)
        ) {

            products = data.products;

        }


        console.log(
            "Total Products:",
            products.length
        );


        renderProducts(products);


    }

    catch (error) {

        console.error(
            "LOAD PRODUCTS ERROR:",
            error
        );


        clearProducts();


        showEmptyMessage(
            amazonProducts,
            "Unable to load Amazon products."
        );

        showEmptyMessage(
            flipkartProducts,
            "Unable to load Flipkart products."
        );

        showEmptyMessage(
            meeshoProducts,
            "Unable to load Meesho products."
        );

        showEmptyMessage(
            myntraProducts,
            "Unable to load Myntra products."
        );


        alert(
            "Unable to load products. Check the backend."
        );

    }


    finally {

        loadProductsButton.disabled = false;

        loadProductsButton.textContent =
            "Load Products";

    }

}


// =====================================
// SEND CHAT MESSAGE
// =====================================

async function sendMessage() {

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


    sendButton.disabled = true;


    try {

        const response = await fetch(
            `${API_URL}/api/chat`,
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


        if (!response.ok) {

            throw new Error(
                `HTTP Error ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "CHAT RESPONSE:",
            data
        );


        const reply =
            data.response ||
            data.reply ||
            data.message ||
            "Sorry, I could not process your request.";


        addMessage(
            reply,
            "bot"
        );

    }


    catch (error) {

        console.error(
            "CHAT ERROR:",
            error
        );


        addMessage(
            "Sorry, I am unable to process your request right now.",
            "bot"
        );

    }


    finally {

        sendButton.disabled = false;

        messageInput.focus();

    }

}


// =====================================
// EVENT LISTENERS
// =====================================

sendButton.addEventListener(
    "click",
    sendMessage
);


loadProductsButton.addEventListener(
    "click",
    loadProducts
);


messageInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter"
        ) {

            event.preventDefault();

            sendMessage();

        }

    }
);


// =====================================
// FRONTEND LOADED
// =====================================

console.log(
    "TechStore AI Customer Support loaded successfully."
);

