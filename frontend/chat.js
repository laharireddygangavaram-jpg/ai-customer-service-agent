const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const chatBox = document.getElementById("chat-box");

function addMessage(message, type) {
    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message", type);
    messageDiv.textContent = message;

    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    // Show user message
    addMessage(message, "user");

    // Clear input
    messageInput.value = "";

    // Disable button while waiting
    sendButton.disabled = true;
    sendButton.textContent = "Sending...";

    try {
        const response = await fetch(
            "http://127.0.0.1:5000/api/chat",
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
        console.error("Error:", error);

        addMessage(
            "Unable to connect to the customer support server. Please make sure Flask is running.",
            "bot"
        );
    }

    // Enable button again
    sendButton.disabled = false;
    sendButton.textContent = "Send";

    messageInput.focus();
}


// Send when button is clicked
sendButton.addEventListener("click", sendMessage);


// Send when Enter is pressed
messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});