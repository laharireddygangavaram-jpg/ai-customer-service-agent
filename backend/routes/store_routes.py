from flask import Blueprint, request, jsonify
from database.database import get_connection

from database.models import (
    get_all_products,
    create_order,
    get_order,
    cancel_order,
    refund_order
)

import uuid

store_bp = Blueprint("store", __name__)


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@store_bp.route("/products", methods=["GET"])
def products():

    products = get_all_products()

    return jsonify({
        "products": [dict(product) for product in products]
    })


# =========================================================
# PLACE ORDER
# =========================================================

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

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):

        return jsonify({
            "error": "Quantity must be a number"
        }), 400

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


# =========================================================
# TRACK ORDER
# =========================================================

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


# =========================================================
# CANCEL ORDER
# =========================================================

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


# =========================================================
# REFUND ORDER
# =========================================================

@store_bp.route("/orders/<order_number>/refund", methods=["POST"])
def refund_order_route(order_number):

    try:

        # Check whether order exists
        order = get_order(order_number)

        if not order:

            return jsonify({
                "error": "Order not found"
            }), 404

        # Request refund
        refunded = refund_order(order_number)

        if not refunded:

            return jsonify({
                "message": "Order cannot be refunded",
                "order_number": order_number
            }), 400

        return jsonify({
            "message": "Refund processed successfully",
            "order_number": order_number,
            "status": "Refunded"
        }), 200

    except Exception as e:

        return jsonify({
            "error": "Unable to process refund",
            "message": str(e)
        }), 500


# =========================================================
# PRODUCT COMPARISON
# =========================================================

@store_bp.route("/compare", methods=["GET"])
def compare_products():

    product_query = request.args.get("product", "").strip()

    connection = get_connection()
    cursor = connection.cursor()

    # If no product specified, return all marketplace products
    if not product_query:

        cursor.execute("""
            SELECT
                products.id,
                products.name,
                products.description,
                products.brand,
                products.price,
                products.stock,
                products.rating,
                products.reviews,
                products.image_url,
                stores.name AS store_name
            FROM products
            JOIN stores
                ON products.store_id = stores.id
            WHERE products.store_id IN (5, 6, 7, 8)
            ORDER BY products.price ASC
        """)

    else:

        search = f"%{product_query}%"

        cursor.execute("""
            SELECT
                products.id,
                products.name,
                products.description,
                products.brand,
                products.price,
                products.stock,
                products.rating,
                products.reviews,
                products.image_url,
                stores.name AS store_name
            FROM products
            JOIN stores
                ON products.store_id = stores.id
            WHERE products.store_id IN (5, 6, 7, 8)
            AND (
                products.name LIKE ?
                OR products.brand LIKE ?
                OR products.description LIKE ?
            )
            ORDER BY products.price ASC
        """, (
            search,
            search,
            search
        ))

    products = cursor.fetchall()

    connection.close()

    return jsonify({
        "success": True,
        "query": product_query,
        "count": len(products),
        "products": [dict(product) for product in products]
    })