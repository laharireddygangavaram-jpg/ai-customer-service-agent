from customer_service_agent import CustomerServiceAgent

# Create one agent instance
agent = CustomerServiceAgent()


def get_customer_support_response(user_message):
    """
    Send customer message to the actual AI Customer Service Agent.
    The agent uses Ollama Gemma3 and available tools.
    """

    try:
        response = agent.chat(user_message)
        return response

    except Exception as e:
        print(f"Error in AI agent: {e}")

        return (
            "Sorry, I am unable to process your request right now."
        )