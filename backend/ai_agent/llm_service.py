import requests


class LLMService:

    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "gemma3"

    def generate_response(self, user_message):

        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": user_message,
                "stream": False
            }
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]