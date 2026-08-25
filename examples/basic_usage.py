import os
import sys

# Add src folder to Python path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
)

from dotenv import load_dotenv
from customer_service_agent import CustomerServiceAgent


load_dotenv()


def main():
    print("=" * 60)
    print("🤖 AI CUSTOMER SERVICE AGENT")
    print("=" * 60)

    # Create agent
    agent = CustomerServiceAgent()

    # Agent information
    info = agent.get_agent_info()

    print(f"Agent: {info['agent']}")
    print(f"Status: {info['status']}")
    print(f"Model: {info['model']}")
    print(f"Backend: {info['backend']}")
    print(f"Local: {info['local']}")
    print(f"Available Tools: {info['available_tools']}")
    print("=" * 60)

    print("\nType 'exit' to stop.")
    print("Type your customer question below.\n")

    # Interactive chat loop
    while True:
        try:
            user_message = input(">>> ")

            if user_message.lower().strip() in ["exit", "quit", "bye"]:
                print("\n👋 Goodbye!")
                break

            if not user_message.strip():
                continue

            response = agent.chat(user_message)

            print("\n🤖 Agent:", response)
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()