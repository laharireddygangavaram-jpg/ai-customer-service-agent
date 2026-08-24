import os
from openai import OpenAI
from .prompts import create_prompt


class LLMService:

    def _init_(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(api_key=api_key)

    def generate_response(self, user_message):

        prompt = create_prompt(user_message)

        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        return response.output_text