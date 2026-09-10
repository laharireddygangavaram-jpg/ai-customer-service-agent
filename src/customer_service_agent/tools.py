import json
import uuid
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, Optional


# =========================================================
# DATABASE PATH
# =========================================================

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


# =========================================================
# TOOL REGISTRY
# =========================================================

class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name: str, function, schema: Dict[str, Any]):
        self.tools[name] = {
            "function": function,
            "schema": schema
        }

    def get_function(self, name: str):

        if name not in self.tools:
            raise ValueError(
                f"Tool '{name}' is not registered"
            )

        return self.tools[name]["function"]

    def get_all_schemas(self):

        return [
            {
                "type": "function",
                "function": tool["schema"]
            }
            for tool in self.tools.values()
        ]


# =========================================================
# CUSTOMER SERVICE TOOLS
# =========================================================

class CustomerServiceTools:

    def get_connection(self):

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        connection.row_factory = sqlite3.Row

        return connection


    # =====================================================
    # LOOKUP ORDER
    # =====================================================

    def lookup_order(self, order_number: str) -> str:

        try:

            connection = self.get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM orders
                WHERE order_number = ?
                """,
                (order_number,)
            )

            order = cursor.fetchone()

            connection.close()

            if not order:

                return json.dumps({
                    "success": False,
                    "message": "Order not found"
                })

            return json.dumps({
                "success": True,
                "order": dict(order)
            })

        except Exception as e:

            return json.dumps({
                "success": False,
                "error": str(e)
            })


    # =====================================================
    # REFUND
    # =====================================================

    def process_refund(
        self,
        order_number: str,
        reason: str,
        amount: float
    ) -> str:

        refund_id = (
            "REF-"
            + str(uuid.uuid4())[:8].upper()
        )

        return json.dumps({
            "success": True,
            "refund_id": refund_id,
            "order_number": order_number,
            "reason": reason,
            "amount": amount,
            "status": "Refund initiated",
            "message": "Your refund request has been successfully initiated."
        })


    # =====================================================
    # CHECK INVENTORY
    # =====================================================

    def check_inventory(
        self,
        product_name: str
    ) -> str:

        try:

            connection = self.get_connection()
            cursor = connection.cursor()

            search = f"%{product_name.lower()}%"

            cursor.execute(
                """
                SELECT
                    products.id,
                    products.name,
                    products.brand,
                    products.price,
                    products.stock,
                    products.rating,
                    products.reviews,
                    stores.name AS store_name
                FROM products
                LEFT JOIN stores
                    ON products.store_id = stores.id
                WHERE
                    LOWER(products.name) LIKE ?
                    OR LOWER(products.brand) LIKE ?
                    OR LOWER(products.description) LIKE ?
                ORDER BY products.price ASC
                """,
                (
                    search,
                    search,
                    search
                )
            )

            rows = cursor.fetchall()

            connection.close()

            if not rows:

                return json.dumps({
                    "success": False,
                    "search": product_name,
                    "count": 0,
                    "products": [],
                    "message": (
                        f"No product found for '{product_name}'"
                    )
                })

            products = [
                dict(row)
                for row in rows
            ]

            return json.dumps({
                "success": True,
                "product_name": product_name,
                "count": len(products),
                "products": products
            })

        except Exception as e:

            return json.dumps({
                "success": False,
                "error": str(e)
            })


    # =====================================================
    # HUMAN ESCALATION
    # =====================================================

    def escalate_to_human(
        self,
        issue_description: str,
        priority: str
    ) -> str:

        ticket_id = (
            "TICKET-"
            + str(uuid.uuid4())[:8].upper()
        )

        response_time = (
            "30 minutes"
            if priority in ["high", "urgent"]
            else "2 hours"
        )

        return json.dumps({
            "success": True,
            "ticket_id": ticket_id,
            "issue": issue_description,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "estimated_response_time": response_time,
            "message": (
                "Your issue has been escalated "
                "to our support team."
            )
        })


    # =====================================================
    # PRODUCT CATALOG
    # =====================================================

    def get_product_catalog(
        self,
        product_name: str = "",
        max_price: Optional[float] = None
    ) -> str:

        connection = None

        try:

            connection = self.get_connection()
            cursor = connection.cursor()

            query = """
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
                LEFT JOIN stores
                    ON products.store_id = stores.id
                WHERE 1 = 1
            """

            params = []

            # PRODUCT SEARCH

            if product_name and product_name.strip():

                search = product_name.strip().lower()

                query += """
                    AND (
                        LOWER(products.name) LIKE ?
                        OR LOWER(products.brand) LIKE ?
                        OR LOWER(products.description) LIKE ?
                    )
                """

                keyword = f"%{search}%"

                params.extend([
                    keyword,
                    keyword,
                    keyword
                ])

            # PRICE FILTER

            if max_price is not None:

                max_price = float(max_price)

                query += """
                    AND products.price <= ?
                """

                params.append(max_price)

            # SORT

            query += """
                ORDER BY
                    CASE
                        WHEN products.stock > 0 THEN 0
                        ELSE 1
                    END,
                    COALESCE(products.rating, 0) DESC,
                    COALESCE(products.reviews, 0) DESC,
                    products.price ASC
            """

            cursor.execute(
                query,
                params
            )

            rows = cursor.fetchall()

            products = [
                dict(row)
                for row in rows
            ]

            # NO PRODUCTS

            if not products:

                message = "No products found"

                if product_name:
                    message += f" for '{product_name}'"

                if max_price is not None:
                    message += f" under ₹{max_price:g}"

                return json.dumps({
                    "success": False,
                    "search": product_name,
                    "max_price": max_price,
                    "count": 0,
                    "products": [],
                    "message": message
                })

            # AVAILABLE PRODUCTS

            available_products = [
                product
                for product in products
                if (product.get("stock") or 0) > 0
            ]

            # BEST PRODUCT

            if available_products:

                best_product = max(
                    available_products,
                    key=lambda product: (
                        product.get("rating") or 0,
                        product.get("reviews") or 0,
                        -(product.get("price") or 999999)
                    )
                )

            else:

                best_product = max(
                    products,
                    key=lambda product: (
                        product.get("rating") or 0,
                        product.get("reviews") or 0
                    )
                )

            # CHEAPEST

            cheapest_product = min(
                products,
                key=lambda product: (
                    product.get("price")
                    if product.get("price") is not None
                    else 999999
                )
            )

            # HIGHEST RATED

            highest_rated = max(
                products,
                key=lambda product: (
                    product.get("rating") or 0,
                    product.get("reviews") or 0
                )
            )

            # STORE SUMMARY

            store_summary = {}

            for product in products:

                store = (
                    product.get("store_name")
                    or "Unknown"
                )

                if store not in store_summary:
                    store_summary[store] = []

                store_summary[store].append(product)

            # FINAL RESPONSE

            return json.dumps({
                "success": True,
                "search": product_name,
                "max_price": max_price,
                "count": len(products),
                "products": products,
                "best_option": best_product,
                "cheapest_option": cheapest_product,
                "highest_rated_option": highest_rated,
                "store_summary": store_summary,
                "available_stores": list(
                    store_summary.keys()
                ),
                "message": (
                    f"Found {len(products)} "
                    f"matching products."
                )
            })

        except Exception as e:

            return json.dumps({
                "success": False,
                "error": str(e)
            })

        finally:

            if connection:
                connection.close()


# =========================================================
# CREATE TOOL REGISTRY
# =========================================================

def create_tool_registry():

    tools = CustomerServiceTools()

    registry = ToolRegistry()

    # LOOKUP ORDER

    registry.register(
        "lookup_order",
        tools.lookup_order,
        {
            "name": "lookup_order",
            "description": "Look up order details using order number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string"
                    }
                },
                "required": ["order_number"]
            }
        }
    )

    # REFUND

    registry.register(
        "process_refund",
        tools.process_refund,
        {
            "name": "process_refund",
            "description": "Process a refund request for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string"
                    },
                    "reason": {
                        "type": "string"
                    },
                    "amount": {
                        "type": "number"
                    }
                },
                "required": [
                    "order_number",
                    "reason",
                    "amount"
                ]
            }
        }
    )

    # INVENTORY

    registry.register(
        "check_inventory",
        tools.check_inventory,
        {
            "name": "check_inventory",
            "description": "Check product availability and stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string"
                    }
                },
                "required": ["product_name"]
            }
        }
    )

    # ESCALATION

    registry.register(
        "escalate_to_human",
        tools.escalate_to_human,
        {
            "name": "escalate_to_human",
            "description": "Escalate customer issue to human support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_description": {
                        "type": "string"
                    },
                    "priority": {
                        "type": "string",
                        "enum": [
                            "low",
                            "medium",
                            "high",
                            "urgent"
                        ]
                    }
                },
                "required": [
                    "issue_description",
                    "priority"
                ]
            }
        }
    )

    # PRODUCT SEARCH

    registry.register(
        "get_product_catalog",
        tools.get_product_catalog,
        {
            "name": "get_product_catalog",
            "description": (
                "Search products across all stores. "
                "Use for product recommendations, "
                "budget searches and comparisons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": (
                            "Product such as camera, "
                            "laptop, phone or headphones."
                        )
                    },
                    "max_price": {
                        "type": "number",
                        "description": (
                            "Maximum budget."
                        )
                    }
                },
                "required": [
                    "product_name"
                ]
            }
        }
    )

    return registry