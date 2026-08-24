from flask import Blueprint, request, jsonify
from ai_agent.agent import CustomerSupportAgent

chat_bp = Blueprint("chat", __name__)

agent = CustomerSupportAgent()


@chat_bp.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({
            "error": "Message is required"
        }), 400

    user_message = data["message"]

    response = agent.process_message(user_message)

    return jsonify({
        "user_message": user_message,
        "response": response
    })