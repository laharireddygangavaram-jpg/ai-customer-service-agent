async function placeOrder() {

    const customerName =
        document.getElementById("customer-name").value.trim();

    const customerEmail =
        document.getElementById("customer-email").value.trim();

    const productId =
        Number(document.getElementById("product-id").value);

    const quantity =
        Number(document.getElementById("quantity").value);

    if (!customerName || !customerEmail || !productId || !quantity) {
        orderResult.innerHTML =
            "<p>Please fill all order details.</p>";
        return;
    }

    placeOrderButton.disabled = true;
    placeOrderButton.textContent = "Placing Order...";

    try {

        const response = await fetch(API_URL + "/orders", {
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

        const text = await response.text();

        let data;

        try {
            data = JSON.parse(text);
        } catch {
            throw new Error(
                "Server returned invalid response: " + text
            );
        }

        if (!response.ok) {
            throw new Error(
                data.error || data.message || "Order failed"
            );
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

        console.error("PLACE ORDER ERROR:", error);

        orderResult.innerHTML =
            `<p>Unable to place order: ${error.message}</p>`;

    } finally {

        placeOrderButton.disabled = false;
        placeOrderButton.textContent = "Place Order";
    }
}