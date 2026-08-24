from database.models import add_customer, save_chat, get_chat_history

# Add customer
customer_id = add_customer(
    "Lahari",
    "lahari@example.com"
)

print("Customer ID:", customer_id)

# Save chat
save_chat(
    customer_id,
    "Hello",
    "Hello! How can I help you?"
)

# Get chat history
history = get_chat_history(customer_id)

print("\nChat History:")

for chat in history:
    print(dict(chat))