from database.database import get_connection


def add_customer(name, email):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO customers (name, email)
        VALUES (?, ?)
        """,
        (name, email)
    )

    connection.commit()
    customer_id = cursor.lastrowid
    connection.close()

    return customer_id


def save_chat(customer_id, user_message, ai_response):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chat_history
        (customer_id, user_message, ai_response)
        VALUES (?, ?, ?)
        """,
        (customer_id, user_message, ai_response)
    )

    connection.commit()
    connection.close()


def get_chat_history(customer_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_message, ai_response, created_at
        FROM chat_history
        WHERE customer_id = ?
        ORDER BY created_at
        """,
        (customer_id,)
    )

    history = cursor.fetchall()
    connection.close()

    return history


def add_product(name, description, price, stock):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, description, price, stock)
        VALUES (?, ?, ?, ?)
        """,
        (name, description, price, stock)
    )

    connection.commit()
    product_id = cursor.lastrowid
    connection.close()

    return product_id
def get_all_products():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            products.id,
            products.name,
            products.description,
            products.price,
            products.stock,
            products.store_id,
            products.image_url,
            stores.name AS store_name,
            stores.image_url AS store_image
        FROM products
        LEFT JOIN stores
            ON products.store_id = stores.id
        ORDER BY products.store_id, products.id
        """
    )

    products = cursor.fetchall()
    connection.close()

    return products

def create_order(
    order_number,
    customer_name,
    customer_email,
    product_id,
    quantity,
    total_amount
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO orders
        (
            order_number,
            customer_name,
            customer_email,
            product_id,
            quantity,
            total_amount
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            order_number,
            customer_name,
            customer_email,
            product_id,
            quantity,
            total_amount
        )
    )

    connection.commit()
    order_id = cursor.lastrowid
    connection.close()

    return order_id


def get_order(order_number):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            orders.*,
            products.name AS product_name,
            products.description AS product_description
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.order_number = ?
        """,
        (order_number,)
    )

    order = cursor.fetchone()
    connection.close()

    return order


def cancel_order(order_number):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = 'Cancelled'
        WHERE order_number = ?
        AND status NOT IN ('Cancelled', 'Delivered')
        """,
        (order_number,)
    )

    connection.commit()

    cancelled = cursor.rowcount > 0

    connection.close()

    return cancelled