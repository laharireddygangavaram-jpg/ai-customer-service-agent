class ResponseHandler:

    @staticmethod
    def success(response):
        return {
            "success": True,
            "response": response
        }

    @staticmethod
    def error(message):
        return {
            "success": False,
            "response": message
        }

    @staticmethod
    def handle(response):
        if response:
            return ResponseHandler.success(response)

        return ResponseHandler.error(
            "Sorry, I was unable to process your request."
        )