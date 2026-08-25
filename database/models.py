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