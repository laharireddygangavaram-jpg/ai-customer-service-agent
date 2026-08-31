from flask import Blueprint, request, jsonify
from database.database import get_connection
from database.models import get_all_products, create_order, get_order, cancel_order
import uuid
store_bp = Blueprint("store", __name__)


@store_bp.route("/products", methods=["GET"])
def products():
    products = get_all_products()

    return jsonify({
        "products": [dict(product) for product in products]
    })


@store_bp.route("/orders", methods=["POST"])
def place_order():
    data = request.get_json()

    required_fields = [
        "customer_name",
        "customer_email",
        "product_id",
        "quantity"
    ]

    if not data or any(field not in data for field in required_fields):
        return jsonify({
            "error": "customer_name, customer_email, product_id and quantity are required"
        }), 400

    customer_name = data["customer_name"]
    customer_email = data["customer_email"]
    product_id = data["product_id"]
    quantity = data["quantity"]

    if quantity <= 0:
        return jsonify({
            "error": "Quantity must be greater than 0"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        connection.close()
        return jsonify({
            "error": "Product not found"
        }), 404

    if product["stock"] < quantity:
        connection.close()
        return jsonify({
            "error": "Insufficient stock"
        }), 400

    total_amount = product["price"] * quantity
    order_number = "ORD-" + str(uuid.uuid4())[:8].upper()

    cursor.execute(
        """
        UPDATE products
        SET stock = stock - ?
        WHERE id = ?
        """,
        (quantity, product_id)
    )

    connection.commit()
    connection.close()

    create_order(
        order_number,
        customer_name,
        customer_email,
        product_id,
        quantity,
        total_amount
    )

    return jsonify({
        "message": "Order placed successfully",
        "order_number": order_number,
        "product": product["name"],
        "quantity": quantity,
        "total_amount": total_amount,
        "status": "Confirmed"
    }), 201


@store_bp.route("/orders/<order_number>", methods=["GET"])
def track_order(order_number):
    order = get_order(order_number)

    if not order:
        return jsonify({
            "error": "Order not found"
        }), 404

    return jsonify({
        "order": dict(order)
    })
@store_bp.route("/orders/<order_number>/cancel", methods=["PUT"])
def cancel_order_route(order_number):

    try:
        cancelled = cancel_order(order_number)

        if not cancelled:
            return jsonify({
                "message": "Order cannot be cancelled or order not found"
            }), 400

        return jsonify({
            "message": "Order cancelled successfully",
            "order_number": order_number,
            "status": "Cancelled"
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Unable to cancel order",
            "message": str(e)
        }), 500