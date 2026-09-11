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

        # Process refund
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
# PRODUCT COMPARISON - GET
# =========================================================

@store_bp.route("/compare", methods=["GET"])
def compare_products_get():

    product_query = request.args.get("product", "").strip()

    return perform_product_comparison(product_query)


# =========================================================
# PRODUCT COMPARISON - POST
# =========================================================

@store_bp.route("/products/compare", methods=["POST"])
def compare_products_post():

    data = request.get_json(silent=True) or {}

    product_query = (
        data.get("product_name")
        or data.get("product")
        or data.get("query")
        or ""
    ).strip()

    if not product_query:

        return jsonify({
            "success": False,
            "error": "Product name is required",
            "products": []
        }), 400

    return perform_product_comparison(product_query)


# =========================================================
# PERFORM PRODUCT COMPARISON
# =========================================================

def perform_product_comparison(product_query):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Search products from Amazon, Flipkart, Meesho, Myntra
        search = f"%{product_query}%"

        cursor.execute(
            """
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
            WHERE
                (
                    LOWER(stores.name) LIKE '%amazon%'
                    OR LOWER(stores.name) LIKE '%flipkart%'
                    OR LOWER(stores.name) LIKE '%meesho%'
                    OR LOWER(stores.name) LIKE '%myntra%'
                )
                AND (
                    products.name LIKE ?
                    OR products.brand LIKE ?
                    OR products.description LIKE ?
                )
            ORDER BY products.price ASC
            """,
            (
                search,
                search,
                search
            )
        )

        products = cursor.fetchall()

        result = []

        for product in products:

            product_data = dict(product)

            # Frontend-friendly store field
            product_data["store"] = product_data.get(
                "store_name",
                "Unknown"
            )

            # Frontend-friendly image field
            product_data["image"] = product_data.get(
                "image_url",
                ""
            )

            result.append(product_data)

        return jsonify({
            "success": True,
            "query": product_query,
            "count": len(result),
            "products": result
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Unable to compare products",
            "message": str(e),
            "products": []
        }), 500

    finally:

        connection.close()
        # =========================================================
# ADMIN - USERS MANAGEMENT
# =========================================================

def create_users_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# =========================================================
# GET ALL USERS - ADMIN
# =========================================================

@store_bp.route("/users", methods=["GET"])
def get_users():

    try:

        create_users_table()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                phone,
                status,
                created_at
            FROM users
            ORDER BY id DESC
        """)

        users = cursor.fetchall()

        connection.close()

        return jsonify({
            "success": True,
            "count": len(users),
            "users": [dict(user) for user in users]
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Unable to get users",
            "message": str(e)
        }), 500


# =========================================================
# GET SINGLE USER - ADMIN
# =========================================================

@store_bp.route("/users/<int:user_id>", methods=["GET"])
def get_single_user(user_id):

    try:

        create_users_table()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                phone,
                status,
                created_at
            FROM users
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()

        connection.close()

        if not user:

            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "user": dict(user)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Unable to get user",
            "message": str(e)
        }), 500


# =========================================================
# ADD USER - ADMIN
# =========================================================

@store_bp.route("/users", methods=["POST"])
def add_user():

    try:

        data = request.get_json(silent=True) or {}

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()

        if not name or not email:

            return jsonify({
                "success": False,
                "error": "Name and email are required"
            }), 400

        create_users_table()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = ?
        """, (email,))

        existing_user = cursor.fetchone()

        if existing_user:

            connection.close()

            return jsonify({
                "success": False,
                "error": "User with this email already exists"
            }), 409

        cursor.execute("""
            INSERT INTO users
            (name, email, phone, status)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            "Active"
        ))

        connection.commit()

        user_id = cursor.lastrowid

        connection.close()

        return jsonify({
            "success": True,
            "message": "User added successfully",
            "user_id": user_id
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Unable to add user",
            "message": str(e)
        }), 500


# =========================================================
# DELETE USER - ADMIN
# =========================================================

@store_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):

    try:

        create_users_table()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM users
            WHERE id = ?
        """, (user_id,))

        deleted = cursor.rowcount

        connection.commit()
        connection.close()

        if deleted == 0:

            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "User deleted successfully"
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Unable to delete user",
            "message": str(e)
        }), 500


# =========================================================
# UPDATE USER STATUS - ADMIN
# =========================================================

@store_bp.route("/users/<int:user_id>/status", methods=["PUT"])
def update_user_status(user_id):

    try:

        data = request.get_json(silent=True) or {}

        status = data.get("status", "").strip()

        if status not in ["Active", "Inactive"]:

            return jsonify({
                "success": False,
                "error": "Status must be Active or Inactive"
            }), 400

        create_users_table()

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET status = ?
            WHERE id = ?
        """, (
            status,
            user_id
        ))

        updated = cursor.rowcount

        connection.commit()
        connection.close()

        if updated == 0:

            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "User status updated",
            "status": status
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Unable to update user status",
            "message": str(e)
        }), 500