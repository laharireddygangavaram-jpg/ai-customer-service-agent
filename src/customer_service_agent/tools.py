
"""
Customer Service Agent - Tools
Database tools for products, orders, inventory, refunds and support.
"""

import os
import re
import sqlite3
import uuid
from datetime import datetime


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "customer_support.db"
)


# ============================================================
# TOOL REGISTRY
# ============================================================

class ToolRegistry:

    def __init__(self):
        self.tools = {}
        self.schemas = {}

    def register(
        self,
        name,
        function,
        description="",
        parameters=None
    ):

        self.tools[name] = function

        self.schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters or {
                    "type": "object",
                    "properties": {}
                }
            }
        }

    def get_tool(self, name):
        return self.tools.get(name)

    def get_all_schemas(self):
        return list(self.schemas.values())


# ============================================================
# CUSTOMER SERVICE TOOLS
# ============================================================

class CustomerServiceTools:

    def __init__(self):
        pass


    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    def get_connection(self):

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        connection.row_factory = sqlite3.Row

        return connection


    # ========================================================
    # LOOKUP ORDER
    # ========================================================

    def lookup_order(
        self,
        order_number=None
    ):

        if not order_number:

            return {
                "success": False,
                "message": "Please provide an order number."
            }

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    o.id,
                    o.order_number,
                    o.customer_name,
                    o.customer_email,
                    o.product_id,
                    o.quantity,
                    o.total_amount,
                    o.status,
                    o.created_at,
                    p.name AS product_name,
                    p.brand AS brand
                FROM orders o
                LEFT JOIN products p
                    ON o.product_id = p.id
                WHERE UPPER(o.order_number) = UPPER(?)
                LIMIT 1
                """,
                (
                    order_number.strip(),
                )
            )

            row = cursor.fetchone()

            if row is None:

                return {
                    "success": False,
                    "message": (
                        f"Order '{order_number}' "
                        "was not found."
                    )
                }

            return {
                "success": True,
                "order_number": row["order_number"],
                "customer_name": row["customer_name"],
                "customer_email": row["customer_email"],
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "brand": row["brand"],
                "quantity": row["quantity"],
                "total_amount": row["total_amount"],
                "status": row["status"],
                "created_at": row["created_at"]
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }

        finally:

            if connection:
                connection.close()


    # ========================================================
    # CANCEL ORDER
    # ========================================================

    def cancel_order(
        self,
        order_number=None
    ):

        if not order_number:

            return {
                "success": False,
                "message": "Please provide an order number."
            }

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    order_number,
                    product_id,
                    quantity,
                    status
                FROM orders
                WHERE UPPER(order_number) = UPPER(?)
                LIMIT 1
                """,
                (
                    order_number.strip(),
                )
            )

            row = cursor.fetchone()

            if row is None:

                return {
                    "success": False,
                    "message": (
                        f"Order '{order_number}' "
                        "was not found."
                    )
                }

            status = str(
                row["status"] or ""
            ).lower()

            if status in [
                "cancelled",
                "canceled"
            ]:

                return {
                    "success": False,
                    "message": "This order is already cancelled."
                }

            if status in [
                "delivered",
                "refunded"
            ]:

                return {
                    "success": False,
                    "message": (
                        f"Order cannot be cancelled "
                        f"because its status is "
                        f"'{row['status']}'."
                    )
                }

            cursor.execute(
                """
                UPDATE orders
                SET status = 'Cancelled'
                WHERE UPPER(order_number) = UPPER(?)
                """,
                (
                    order_number.strip(),
                )
            )

            cursor.execute(
                """
                UPDATE products
                SET stock = stock + ?
                WHERE id = ?
                """,
                (
                    row["quantity"],
                    row["product_id"]
                )
            )

            connection.commit()

            return {
                "success": True,
                "order_number": row["order_number"],
                "status": "Cancelled"
            }

        except Exception as e:

            if connection:
                connection.rollback()

            return {
                "success": False,
                "message": str(e)
            }

        finally:

            if connection:
                connection.close()


    # ========================================================
    # PROCESS REFUND
    # ========================================================

    def process_refund(
        self,
        order_number=None
    ):

        if not order_number:

            return {
                "success": False,
                "message": "Please provide an order number."
            }

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    order_number,
                    total_amount,
                    status
                FROM orders
                WHERE UPPER(order_number) = UPPER(?)
                LIMIT 1
                """,
                (
                    order_number.strip(),
                )
            )

            row = cursor.fetchone()

            if row is None:

                return {
                    "success": False,
                    "message": (
                        f"Order '{order_number}' "
                        "was not found."
                    )
                }

            status = str(
                row["status"] or ""
            ).lower()

            if status == "refunded":

                return {
                    "success": False,
                    "message": "This order is already refunded."
                }

            if status not in [
                "cancelled",
                "canceled"
            ]:

                return {
                    "success": False,
                    "message": (
                        "Refund can be processed "
                        "only for a cancelled order."
                    )
                }

            cursor.execute(
                """
                UPDATE orders
                SET status = 'Refunded'
                WHERE UPPER(order_number) = UPPER(?)
                """,
                (
                    order_number.strip(),
                )
            )

            connection.commit()

            return {
                "success": True,
                "order_number": row["order_number"],
                "refund_amount": row["total_amount"],
                "status": "Refunded"
            }

        except Exception as e:

            if connection:
                connection.rollback()

            return {
                "success": False,
                "message": str(e)
            }

        finally:

            if connection:
                connection.close()


    # ========================================================
    # NORMALIZE PRODUCT TEXT
    # ========================================================

    def _normalize_product_text(
        self,
        text
    ):

        text = str(text or "").lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    # ========================================================
    # CATEGORY ALIASES
    # ========================================================

    def _get_category_aliases(self):

        return {

            "monitor": [
                "monitor",
                "monitors"
            ],

            "smart_tv": [
                "smart tv",
                "smart tvs",
                "smart television",
                "smart televisions"
            ],

            "shoe": [
                "shoe",
                "shoes",
                "footwear",
                "sneaker",
                "sneakers"
            ],

            "phone": [
                "phone",
                "phones",
                "mobile",
                "mobiles",
                "smartphone",
                "smartphones"
            ],

            "laptop": [
                "laptop",
                "laptops",
                "notebook",
                "notebooks"
            ],

            "tablet": [
                "tablet",
                "tablets"
            ],

            "headphone": [
                "headphone",
                "headphones",
                "earphone",
                "earphones",
                "earbud",
                "earbuds"
            ]
        }


    # ========================================================
    # FIND CATEGORY
    # ========================================================

    def _find_category(
        self,
        query
    ):

        normalized = self._normalize_product_text(
            query
        )

        aliases = self._get_category_aliases()

        for category, words in aliases.items():

            for word in words:

                normalized_word = (
                    self._normalize_product_text(
                        word
                    )
                )

                if re.search(
                    r"\b"
                    + re.escape(normalized_word)
                    + r"\b",
                    normalized
                ):

                    return category

        return None


    # ========================================================
    # PRODUCT MATCH
    # ========================================================

    def _product_matches(
        self,
        product,
        query
    ):

        query_normalized = (
            self._normalize_product_text(
                query
            )
        )

        if not query_normalized:
            return True

        product_name = (
            self._normalize_product_text(
                product["name"]
            )
        )

        brand = (
            self._normalize_product_text(
                product["brand"] or ""
            )
        )

        description = (
            self._normalize_product_text(
                product["description"] or ""
            )
        )

        category = self._find_category(
            query
        )

        # ----------------------------------------------------
        # CATEGORY MATCH
        # ----------------------------------------------------

        if category:

            aliases = self._get_category_aliases()

            category_words = aliases.get(
                category,
                []
            )

            for word in category_words:

                normalized_word = (
                    self._normalize_product_text(
                        word
                    )
                )

                pattern = (
                    r"\b"
                    + re.escape(normalized_word)
                    + r"\b"
                )

                if (
                    re.search(
                        pattern,
                        product_name
                    )
                    or
                    re.search(
                        pattern,
                        description
                    )
                ):

                    return True

        # ----------------------------------------------------
        # EXACT NAME
        # ----------------------------------------------------

        if query_normalized == product_name:
            return True

        # ----------------------------------------------------
        # QUERY INSIDE PRODUCT NAME
        # ----------------------------------------------------

        if query_normalized in product_name:
            return True

        # ----------------------------------------------------
        # EXACT BRAND
        # ----------------------------------------------------

        if query_normalized == brand:
            return True

        # ----------------------------------------------------
        # WORD MATCH
        # ----------------------------------------------------

        query_words = [
            word
            for word in query_normalized.split()
            if len(word) > 2
        ]

        if not query_words:
            return False

        searchable_text = (
            product_name
            + " "
            + brand
            + " "
            + description
        )

        for word in query_words:

            if not re.search(
                r"\b"
                + re.escape(word)
                + r"\b",
                searchable_text
            ):

                return False

        return True


    # ========================================================
    # PLACE ORDER
    # ========================================================

    def place_order(
        self,
        product_name,
        quantity=1,
        customer_name="Guest Customer",
        customer_email="guest@example.com"
    ):

        if not product_name:

            return {
                "success": False,
                "message": "Please provide a product name."
            }

        try:

            quantity = int(quantity)

        except Exception:

            quantity = 1

        if quantity <= 0:

            return {
                "success": False,
                "message": (
                    "Quantity must be greater than zero."
                )
            }

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    brand,
                    price,
                    stock,
                    description
                FROM products
                """
            )

            rows = cursor.fetchall()

            selected_product = None

            normalized_query = (
                self._normalize_product_text(
                    product_name
                )
            )

            # EXACT MATCH
            for row in rows:

                normalized_name = (
                    self._normalize_product_text(
                        row["name"]
                    )
                )

                if normalized_name == normalized_query:

                    selected_product = row
                    break

            # PARTIAL/CATEGORY MATCH
            if selected_product is None:

                for row in rows:

                    if self._product_matches(
                        row,
                        product_name
                    ):

                        selected_product = row
                        break

            if selected_product is None:

                return {
                    "success": False,
                    "message": (
                        f"No product found for "
                        f"'{product_name}'."
                    )
                }

            product_id = selected_product["id"]

            real_product_name = (
                selected_product["name"]
            )

            brand = selected_product["brand"]

            unit_price = float(
                selected_product["price"]
            )

            previous_stock = int(
                selected_product["stock"]
            )

            if previous_stock < quantity:

                return {
                    "success": False,
                    "message": (
                        f"Only {previous_stock} "
                        f"unit(s) available for "
                        f"'{real_product_name}'."
                    )
                }

            total_amount = (
                unit_price * quantity
            )

            remaining_stock = (
                previous_stock - quantity
            )

            order_number = (
                "ORD-"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
                + "-"
                + uuid.uuid4().hex[:4].upper()
            )

            cursor.execute(
                """
                UPDATE products
                SET stock = ?
                WHERE id = ?
                """,
                (
                    remaining_stock,
                    product_id
                )
            )

            cursor.execute(
                """
                INSERT INTO orders (
                    order_number,
                    customer_name,
                    customer_email,
                    product_id,
                    quantity,
                    total_amount,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_number,
                    customer_name,
                    customer_email,
                    product_id,
                    quantity,
                    total_amount,
                    "Confirmed"
                )
            )

            connection.commit()

            return {
                "success": True,
                "order_number": order_number,
                "product_id": product_id,
                "product_name": real_product_name,
                "brand": brand,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "previous_stock": previous_stock,
                "remaining_stock": remaining_stock,
                "status": "Confirmed",
                "customer_name": customer_name,
                "customer_email": customer_email
            }

        except Exception as e:

            if connection:
                connection.rollback()

            return {
                "success": False,
                "message": str(e)
            }

        finally:

            if connection:
                connection.close()


    # ========================================================
    # CHECK INVENTORY
    # ========================================================

    def check_inventory(
        self,
        product_name
    ):

        if not product_name:

            return {
                "success": False,
                "message": "Please provide a product name."
            }

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    brand,
                    price,
                    stock,
                    description
                FROM products
                """
            )

            rows = cursor.fetchall()

            selected_product = None

            normalized_query = (
                self._normalize_product_text(
                    product_name
                )
            )

            for row in rows:

                normalized_name = (
                    self._normalize_product_text(
                        row["name"]
                    )
                )

                if normalized_name == normalized_query:

                    selected_product = row
                    break

            if selected_product is None:

                for row in rows:

                    if self._product_matches(
                        row,
                        product_name
                    ):

                        selected_product = row
                        break

            if selected_product is None:

                return {
                    "success": False,
                    "message": (
                        f"No product found for "
                        f"'{product_name}'."
                    )
                }

            return {
                "success": True,
                "product_id": selected_product["id"],
                "product_name": selected_product["name"],
                "brand": selected_product["brand"],
                "price": selected_product["price"],
                "stock": selected_product["stock"]
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }

        finally:

            if connection:
                connection.close()


    # ========================================================
    # PRODUCT CATALOG
    # ========================================================

    def get_product_catalog(
        self,
        query=""
    ):

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    price,
                    stock,
                    store_id,
                    image_url,
                    brand,
                    rating,
                    review_count,
                    delivery_days,
                    discount,
                    product_url
                FROM products
                ORDER BY id
                """
            )

            rows = cursor.fetchall()

            products = []

            for row in rows:

                if self._product_matches(
                    row,
                    query
                ):

                    products.append(
                        {
                            "id": row["id"],
                            "name": row["name"],
                            "description": row["description"],
                            "price": row["price"],
                            "stock": row["stock"],
                            "store_id": row["store_id"],
                            "image_url": row["image_url"],
                            "brand": row["brand"],
                            "rating": row["rating"],
                            "review_count": row["review_count"],
                            "delivery_days": row["delivery_days"],
                            "discount": row["discount"],
                            "product_url": row["product_url"]
                        }
                    )

            return {
                "success": True,
                "query": query,
                "count": len(products),
                "products": products
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e),
                "products": []
            }

        finally:

            if connection:
                connection.close()


    # ========================================================
    # STORE NAME
    # ========================================================

    def _get_store_name(
        self,
        store_id
    ):

        store_names = {
            5: "Amazon",
            6: "Flipkart",
            7: "Meesho",
            8: "Myntra"
        }

        try:
            store_id = int(store_id)
        except Exception:
            pass

        return store_names.get(
            store_id,
            "Online Store"
        )


    # ========================================================
    # GET PRODUCTS FOR COMPARISON
    # ========================================================

    def _get_comparison_products(
        self,
        product_name
    ):

        connection = None

        try:

            connection = self.get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    price,
                    stock,
                    store_id,
                    image_url,
                    brand,
                    rating,
                    review_count,
                    delivery_days,
                    discount,
                    product_url
                FROM products
                ORDER BY
                    price ASC,
                    rating DESC
                """
            )

            rows = cursor.fetchall()

            matches = []

            normalized_query = (
                self._normalize_product_text(
                    product_name
                )
            )

            # ------------------------------------------------
            # FIRST: EXACT / VERY CLOSE NAME MATCH
            # ------------------------------------------------

            for row in rows:

                normalized_name = (
                    self._normalize_product_text(
                        row["name"]
                    )
                )

                # Remove store suffix such as:
                # - Flipkart
                # - Meesho

                clean_name = re.sub(
                    r"\s*-\s*(amazon|flipkart|meesho|myntra)\s*$",
                    "",
                    normalized_name
                ).strip()

                if (
                    normalized_name == normalized_query
                    or clean_name == normalized_query
                    or normalized_query in clean_name
                ):

                    matches.append(row)


            # ------------------------------------------------
            # SECOND: PRODUCT MATCH
            # ------------------------------------------------

            if not matches:

                for row in rows:

                    if self._product_matches(
                        row,
                        product_name
                    ):

                        matches.append(row)


            # ------------------------------------------------
            # REMOVE DUPLICATES
            # ------------------------------------------------

            unique_products = []

            seen = set()

            for row in matches:

                key = (
                    row["id"],
                    row["store_id"]
                )

                if key in seen:
                    continue

                seen.add(key)

                unique_products.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "price": row["price"],
                        "stock": row["stock"],
                        "store_id": row["store_id"],
                        "store_name": self._get_store_name(
                            row["store_id"]
                        ),
                        "image_url": row["image_url"],
                        "brand": row["brand"],
                        "rating": row["rating"],
                        "review_count": row["review_count"],
                        "delivery_days": row["delivery_days"],
                        "discount": row["discount"],
                        "product_url": row["product_url"]
                    }
                )

            return unique_products

        except Exception:

            return []

        finally:

            if connection:
                connection.close()


    # ========================================================
    # COMPARE PRODUCTS
    #
    # Supports:
    #
    # 1. compare Boat Rockerz 450
    #
    #    -> Same product across stores
    #
    # 2. compare HP 15 Laptop and Dell Inspiron 15
    #
    #    -> Two different products
    # ========================================================

    def compare_products(
        self,
        message=None,
        product_name=None,
        product_name_1=None,
        product_name_2=None
    ):

        # ----------------------------------------------------
        # GET ORIGINAL QUERY
        # ----------------------------------------------------

        query = (
            message
            or product_name
            or ""
        ).strip()

        # ----------------------------------------------------
        # REMOVE COMPARE WORDS
        # ----------------------------------------------------

        query = re.sub(
            r"^\s*(please\s+)?compare\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        query = re.sub(
            r"^\s*(please\s+)?compare\s+products?\s+",
            "",
            query,
            flags=re.IGNORECASE
        )

        query = query.strip()


        # ----------------------------------------------------
        # TWO PRODUCT NAMES
        # ----------------------------------------------------

        first_product = (
            product_name_1
            or ""
        ).strip()

        second_product = (
            product_name_2
            or ""
        ).strip()


        # ----------------------------------------------------
        # DETECT "AND"
        # ----------------------------------------------------

        if not first_product or not second_product:

            match = re.match(
                r"^(.+?)\s+(?:and|vs|versus|with)\s+(.+)$",
                query,
                flags=re.IGNORECASE
            )

            if match:

                first_product = (
                    match.group(1).strip()
                )

                second_product = (
                    match.group(2).strip()
                )


        # ----------------------------------------------------
        # TWO DIFFERENT PRODUCTS
        # ----------------------------------------------------

        if first_product and second_product:

            first_matches = (
                self._get_comparison_products(
                    first_product
                )
            )

            second_matches = (
                self._get_comparison_products(
                    second_product
                )
            )

            products = (
                first_matches
                + second_matches
            )

            if not products:

                return {
                    "success": False,
                    "message": (
                        "No matching products found "
                        "for comparison."
                    ),
                    "products": []
                }

            return {
                "success": True,
                "comparison_type": "two_products",
                "product_1": first_product,
                "product_2": second_product,
                "count": len(products),
                "products": products
            }


        # ----------------------------------------------------
        # ONE PRODUCT
        # ----------------------------------------------------

        if not query:

            return {
                "success": False,
                "message": (
                    "Please provide a product name "
                    "to compare."
                ),
                "products": []
            }


        products = (
            self._get_comparison_products(
                query
            )
        )


        if not products:

            return {
                "success": False,
                "message": (
                    f"No products found for "
                    f"'{query}'."
                ),
                "products": []
            }


        # ----------------------------------------------------
        # FIND CHEAPEST PRODUCT
        # ----------------------------------------------------

        cheapest = min(
            products,
            key=lambda product: float(
                product.get("price") or 0
            )
        )


        # ----------------------------------------------------
        # FIND HIGHEST RATING
        # ----------------------------------------------------

        highest_rated = max(
            products,
            key=lambda product: float(
                product.get("rating") or 0
            )
        )


        return {
            "success": True,
            "comparison_type": "same_product_across_stores",
            "query": query,
            "count": len(products),
            "products": products,
            "cheapest": cheapest.get("name"),
            "highest_rated": highest_rated.get("name"),
            "recommended": cheapest.get("name")
        }


    # ========================================================
    # ESCALATE TO HUMAN
    # ========================================================

    def escalate_to_human(
        self,
        reason=""
    ):

        ticket_id = (
            "TKT-"
            + uuid.uuid4().hex[:8].upper()
        )

        return {
            "success": True,
            "ticket_id": ticket_id,
            "reason": reason,
            "message": (
                "Your request has been "
                "escalated to human support."
            )
        }


# ============================================================
# CREATE TOOL REGISTRY
# ============================================================

def create_tool_registry():

    tools = CustomerServiceTools()

    registry = ToolRegistry()


    # ========================================================
    # LOOKUP ORDER
    # ========================================================

    registry.register(
        name="lookup_order",
        function=tools.lookup_order,
        description=(
            "Look up an order using its order number."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": (
                        "Customer order number."
                    )
                }
            },
            "required": [
                "order_number"
            ]
        }
    )


    # ========================================================
    # CANCEL ORDER
    # ========================================================

    registry.register(
        name="cancel_order",
        function=tools.cancel_order,
        description=(
            "Cancel an existing customer order."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": (
                        "Customer order number."
                    )
                }
            },
            "required": [
                "order_number"
            ]
        }
    )


    # ========================================================
    # REFUND
    # ========================================================

    registry.register(
        name="process_refund",
        function=tools.process_refund,
        description=(
            "Process a refund for a cancelled order."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": (
                        "Customer order number."
                    )
                }
            },
            "required": [
                "order_number"
            ]
        }
    )


    # ========================================================
    # CHECK INVENTORY
    # ========================================================

    registry.register(
        name="check_inventory",
        function=tools.check_inventory,
        description=(
            "Check product stock availability."
        ),
        parameters={
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": (
                        "Product name."
                    )
                }
            },
            "required": [
                "product_name"
            ]
        }
    )


    # ========================================================
    # PLACE ORDER
    # ========================================================

    registry.register(
        name="place_order",
        function=tools.place_order,
        description=(
            "Place a customer order for a product."
        ),
        parameters={
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": (
                        "Product to order."
                    )
                },
                "quantity": {
                    "type": "integer",
                    "description": (
                        "Number of units to order."
                    ),
                    "minimum": 1
                }
            },
            "required": [
                "product_name",
                "quantity"
            ]
        }
    )


    # ========================================================
    # COMPARE PRODUCTS
    # ========================================================

    registry.register(
        name="compare_products",
        function=tools.compare_products,
        description=(
            "Compare products. If the customer gives one "
            "product name, find the same or matching product "
            "across different stores such as Amazon, Flipkart, "
            "Meesho and Myntra. Return price, rating, reviews, "
            "stock, delivery, image and product URL. If the "
            "customer gives two product names, compare both "
            "products."
        ),
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": (
                        "Complete customer comparison request, "
                        "for example 'compare Boat Rockerz 450' "
                        "or 'compare HP 15 Laptop and Dell Inspiron 15'."
                    )
                },
                "product_name": {
                    "type": "string",
                    "description": (
                        "Single product name to compare "
                        "across stores."
                    )
                },
                "product_name_1": {
                    "type": "string",
                    "description": (
                        "First product name."
                    )
                },
                "product_name_2": {
                    "type": "string",
                    "description": (
                        "Second product name."
                    )
                }
            },
            "required": []
        }
    )


    # ========================================================
    # ESCALATE TO HUMAN
    # ========================================================

    registry.register(
        name="escalate_to_human",
        function=tools.escalate_to_human,
        description=(
            "Escalate a customer request "
            "to human support."
        ),
        parameters={
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": (
                        "Reason for escalation."
                    )
                }
            },
            "required": [
                "reason"
            ]
        }
    )


    # ========================================================
    # PRODUCT CATALOG
    # ========================================================

    registry.register(
        name="get_product_catalog",
        function=tools.get_product_catalog,
        description=(
            "Search and return products "
            "from the product catalog."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Product name, brand, "
                        "or category to search."
                    )
                }
            },
            "required": []
        }
    )


    return registry


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("Database path:")
    print(DATABASE_PATH)

    print()

    print("Database exists:")
    print(os.path.exists(DATABASE_PATH))

    print()

    registry = create_tool_registry()

    print("Registered tools:")

    print(
        [
            item["function"]["name"]
            for item in registry.get_all_schemas()
        ]
    )

    print()

    print("get_tool available:")

    print(
        hasattr(
            registry,
            "get_tool"
        )
    )

    print()

    # --------------------------------------------------------
    # TEST ONE-PRODUCT COMPARISON
    # --------------------------------------------------------

    print("Testing compare_products:")

    test_result = (
        registry
        .get_tool("compare_products")(
            message="compare Boat Rockerz 450"
        )
    )

    print(test_result)
