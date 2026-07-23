from flask import Blueprint, request, jsonify
from services.chat_service import get_customer_support_response

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({
            "error": "Message is required"
        }), 400

    user_message = data["message"]

    response = get_customer_support_response(user_message)

    return jsonify({
        "user_message": user_message,
        "response": response
    })