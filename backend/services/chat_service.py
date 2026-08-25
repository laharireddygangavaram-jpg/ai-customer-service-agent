def get_customer_support_response(user_message):

    user_message = user_message.lower()

    if "hello" in user_message or "hi" in user_message:
        return "Hello! Welcome to our customer support. How can I help you?"

    elif "order" in user_message:
        return "Sure! Please provide your order ID so I can help you."

    elif "refund" in user_message:
        return "I can help you with your refund request. Please provide your order ID."

    elif "thank" in user_message:
        return "You're welcome! Is there anything else I can help you with?"

    else:
        return "I'm sorry, I couldn't understand your request. Please provide more details."