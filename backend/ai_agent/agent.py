import traceback

from .llm_service import LLMService
from .response_handler import ResponseHandler


class CustomerSupportAgent:

    def __init__(self):
        self.llm_service = LLMService()

    def process_message(self, user_message):

        if not user_message:
            return ResponseHandler.error(
                "Please enter a message."
            )

        try:
            response = self.llm_service.generate_response(
                user_message
            )

            return ResponseHandler.handle(response)

        except Exception as e:
            print("AI Agent Error:", e)
            traceback.print_exc()

            return ResponseHandler.error(
                "Sorry, I am unable to process your request right now."
            )