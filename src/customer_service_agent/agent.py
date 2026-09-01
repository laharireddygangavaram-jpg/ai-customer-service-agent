
"""
Advanced AI Customer Service Agent
TechStore - Ollama + Gemma3

Features:
- Normal AI chat
- Product catalog
- Product recommendation
- Budget filtering
- Product comparison
- Same product across different stores
- Inventory checking
- Place order
- Order tracking
- Cancel order
- Refund
- Human escalation
- Conversation history
"""

import json
import re
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests
from loguru import logger

from .tools import create_tool_registry


class CustomerServiceAgent:
    """
    TechStore AI Customer Service Agent.

    Uses Ollama locally instead of OpenAI API.
    """

    def __init__(
        self,
        config=None,
        model: str = "gemma3:latest"
    ):
        self.config = config
        self.model = model

        # --------------------------------------------------
        # OLLAMA
        # --------------------------------------------------

        self.ollama_url = "http://127.0.0.1:11434/api/chat"

        # --------------------------------------------------
        # TOOLS
        # --------------------------------------------------

        self.tool_registry = create_tool_registry()

        # --------------------------------------------------
        # CONVERSATION
        # --------------------------------------------------

        self.conversation_history: List[Dict[str, Any]] = []

        # --------------------------------------------------
        # METADATA
        # --------------------------------------------------

        self.total_interactions = 0
        self.total_tool_calls = 0
        self.customer_id = None
        self.last_interaction = None

        # --------------------------------------------------
        # SYSTEM PROMPT
        # --------------------------------------------------

        self.system_prompt = self._create_system_prompt()

        logger.info(
            f"CustomerServiceAgent initialized with Ollama model: {self.model}"
        )

    # ======================================================
    # SYSTEM PROMPT
    # ======================================================

    def _create_system_prompt(self) -> str:

        return """
You are TechStore AI Customer Support Agent.

You are a helpful, polite and intelligent shopping assistant.

IMPORTANT RULES:

1. PRODUCT SEARCH

When the customer asks for a product category,
show only products belonging to that category.

Examples:

- laptops -> laptops only
- phones -> phones only
- tablets -> tablets only
- monitors -> monitors only
- smart TVs -> smart TVs only
- shoes -> shoes only
- headphones -> headphones only

Never include unrelated products.

2. BUDGET

If customer provides a budget such as:

- laptop under 40000
- phone below 20000
- products within 30000

only show products within that budget.

3. RECOMMENDATION

If customer says:

- recommend
- recommand
- recommendation
- suggest
- best product
- which one should I buy
- what should I buy

provide a recommendation when enough information is available.

4. COMPARISON

If customer says:

compare Boat Rockerz 450

compare the same product across different stores.

Show:

- Store
- Product
- Price
- Rating
- Stock
- Delivery

If customer provides two different products,
compare the two products.

5. ORDERS

For placing an order collect:

- Product name
- Quantity
- Customer name
- Customer email

Use the place_order tool.

Never invent order numbers.

6. ORDER TRACKING

If customer provides an order number,
use lookup_order.

7. CANCEL ORDER

Use cancel_order.

8. REFUND

Use process_refund.

9. INVENTORY

Use check_inventory.

10. HUMAN SUPPORT

Escalate difficult customer issues to human support.

11. IMPORTANT

Never invent:

- product prices
- stock
- store names
- order numbers

Use tools for real product and order information.

Keep responses simple and customer-friendly.
"""

    # ======================================================
    # CATEGORY EXTRACTION
    # ======================================================

    def _extract_category(
        self,
        message: str
    ) -> Optional[str]:

        text = message.lower().strip()

        # Common typing mistakes
        replacements = {
            "lapyop": "laptop",
            "lapop": "laptop",
            "laptp": "laptop",
            "laptpo": "laptop",
            "lappop": "laptop",
            "moniter": "monitor",
            "monitr": "monitor",
            "moniter": "monitor",
            "hedphone": "headphone",
            "headphne": "headphone"
        }

        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)

        # Laptop
        if any(word in text for word in [
            "laptop",
            "laptops",
            "notebook",
            "notebooks"
        ]):
            return "laptop"

        # Phone
        if any(word in text for word in [
            "phone",
            "phones",
            "mobile",
            "mobiles",
            "smartphone",
            "smartphones"
        ]):
            return "phone"

        # Tablet
        if any(word in text for word in [
            "tablet",
            "tablets"
        ]):
            return "tablet"

        # Monitor
        if any(word in text for word in [
            "monitor",
            "monitors"
        ]):
            return "monitor"

        # Smart TV
        if any(word in text for word in [
            "smart tv",
            "smart tvs",
            "smart television",
            "smart televisions"
        ]):
            return "smart_tv"

        # Shoes
        if any(word in text for word in [
            "shoe",
            "shoes",
            "footwear",
            "sneaker",
            "sneakers"
        ]):
            return "shoe"

        # Headphones
        if any(word in text for word in [
            "headphone",
            "headphones",
            "earphone",
            "earphones",
            "earbud",
            "earbuds"
        ]):
            return "headphone"

        return None

    # ======================================================
    # BUDGET EXTRACTION
    # ======================================================

    def _extract_budget(
        self,
        message: str
    ) -> Optional[float]:

        text = message.lower()

        patterns = [

            # under 40000
            r"\bunder\s*[₹rs.]?\s*([\d,]+)",

            # below 40000
            r"\bbelow\s*[₹rs.]?\s*([\d,]+)",

            # less than 40000
            r"\bless\s+than\s*[₹rs.]?\s*([\d,]+)",

            # within 40000
            r"\bwithin\s*[₹rs.]?\s*([\d,]+)",

            # budget 40000
            r"\bbudget\s*[=:]?\s*[₹rs.]?\s*([\d,]+)",

            # budget of 40000
            r"\bbudget\s+of\s*[₹rs.]?\s*([\d,]+)",

            # upto 40000
            r"\bup\s*to\s*[₹rs.]?\s*([\d,]+)",

            # up to 40000
            r"\bupto\s*[₹rs.]?\s*([\d,]+)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                try:

                    return float(
                        match.group(1).replace(",", "")
                    )

                except ValueError:
                    pass

        return None

    # ======================================================
    # QUANTITY EXTRACTION
    # ======================================================

    def _extract_quantity(
        self,
        message: str
    ) -> int:

        patterns = [

            r"\bquantity\s*[:=]?\s*(\d+)",

            r"\bqty\s*[:=]?\s*(\d+)",

            r"\b(\d+)\s*(?:items?|pieces?|units?)\b",

            r"\bbuy\s+(\d+)\b",

            r"\border\s+(\d+)\b"
        ]

        text = message.lower()

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                try:

                    quantity = int(
                        match.group(1)
                    )

                    if quantity > 0:
                        return quantity

                except ValueError:
                    pass

        return 1

    # ======================================================
    # ORDER NUMBER
    # ======================================================

    def _extract_order_number(
        self,
        message: str
    ) -> Optional[str]:

        patterns = [

            r"\bORD[-_ ]?\d+\b",

            r"\bORDER[-_ ]?\d+\b",

            r"\b[A-Z]{2,5}\d{3,}\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                message,
                re.IGNORECASE
            )

            if match:

                return match.group(0)

        return None

    # ======================================================
    # PRODUCT NAME
    # ======================================================

    def _extract_product_name(
        self,
        message: str
    ) -> str:

        text = message.strip()

        patterns = [

            r"(?:place|put|make)\s+(?:an?\s+)?order\s+(?:for|of)\s+(.+)",

            r"(?:buy|purchase)\s+(.+)",

            r"(?:order)\s+(.+)",

            r"(?:inventory|stock|availability)"
            r"\s+(?:of|for)\s+(.+)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                product = match.group(1).strip()

                product = re.sub(
                    r"\b(quantity|qty)"
                    r"\s*[:=]?\s*\d+\b",
                    "",
                    product,
                    flags=re.IGNORECASE
                )

                return product.strip(" .,")

        return text

    # ======================================================
    # COMPARE PRODUCT EXTRACTION
    # ======================================================

    def _extract_compare_products(
        self,
        message: str
    ) -> List[str]:

        text = message.strip()

        text = re.sub(
            r"^\s*compare\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"^\s*comparison\s*(?:of|between)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        separators = [

            r"\s+\band\b\s+",

            r"\s+\bvs\b\.?\s+",

            r"\s+\bversus\b\s+",

            r"\s*\|\s*"
        ]

        for separator in separators:

            parts = re.split(
                separator,
                text,
                maxsplit=1,
                flags=re.IGNORECASE
            )

            if len(parts) == 2:

                result = [
                    parts[0].strip(" .,"),
                    parts[1].strip(" .,")
                ]

                return [
                    item
                    for item in result
                    if item
                ]

        if text:

            return [
                text.strip(" .,")
            ]

        return []

    # ======================================================
    # TOOL DETECTION
    # ======================================================

    def _detect_tool_call(
        self,
        message: str
    ) -> Optional[Dict[str, Any]]:

        text = message.lower().strip()

        # ----------------------------------------------
        # Fix common spelling mistakes
        # ----------------------------------------------

        normalized_text = text

        replacements = {
            "lapyop": "laptop",
            "lapop": "laptop",
            "laptp": "laptop",
            "moniter": "monitor",
            "monitr": "monitor",
            "recommand": "recommend"
        }

        for wrong, correct in replacements.items():

            normalized_text = normalized_text.replace(
                wrong,
                correct
            )

        # ----------------------------------------------
        # COMPARISON
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "compare",

            "comparison",

            "compare price",

            "price comparison"
        ]):

            return {
                "name": "compare_products",

                "args": {
                    "message": message
                }
            }

        # ----------------------------------------------
        # RECOMMENDATION
        # ----------------------------------------------

        recommendation_words = [

            "recommend",

            "recommendation",

            "suggest",

            "suggestion",

            "best product",

            "which one should i buy",

            "what should i buy",

            "best laptop",

            "best phone",

            "best tablet",

            "best headphone",

            "best headphones"
        ]

        if any(
            word in normalized_text
            for word in recommendation_words
        ):

            category = self._extract_category(
                normalized_text
            )

            return {
                "name": "recommend_product",

                "args": {
                    "query": category or message
                }
            }

        # ----------------------------------------------
        # PLACE ORDER
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "place order",

            "place an order",

            "put order",

            "buy this",

            "purchase this",

            "i want to order",

            "i want to buy",

            "order this"
        ]):

            product_name = self._extract_product_name(
                message
            )

            return {
                "name": "place_order",

                "args": {
                    "message": message,

                    "product_name": product_name,

                    "quantity": self._extract_quantity(
                        message
                    )
                }
            }

        # ----------------------------------------------
        # CANCEL ORDER
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "cancel order",

            "cancel my order",

            "cancel the order"
        ]):

            order_number = self._extract_order_number(
                message
            )

            return {
                "name": "cancel_order",

                "args": {
                    "order_number": order_number or "",

                    "message": message
                }
            }

        # ----------------------------------------------
        # REFUND
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "refund",

            "money back",

            "return my money"
        ]):

            order_number = self._extract_order_number(
                message
            )

            return {
                "name": "process_refund",

                "args": {
                    "order_number": order_number or "",

                    "reason": message
                }
            }

        # ----------------------------------------------
        # ORDER TRACKING
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "track order",

            "track my order",

            "order status",

            "where is my order",

            "delivery status"
        ]):

            order_number = self._extract_order_number(
                message
            )

            return {
                "name": "lookup_order",

                "args": {
                    "order_number": order_number or ""
                }
            }

        # ----------------------------------------------
        # INVENTORY
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "inventory",

            "stock",

            "available",

            "availability",

            "is it available",

            "is this available"
        ]):

            product_name = self._extract_product_name(
                message
            )

            return {
                "name": "check_inventory",

                "args": {
                    "product_name": product_name
                }
            }

        # ----------------------------------------------
        # PRODUCT CATALOG
        # ----------------------------------------------

        category = self._extract_category(
            normalized_text
        )

        if category:

            return {
                "name": "get_product_catalog",

                "args": {
                    "query": category
                }
            }

        # ----------------------------------------------
        # HUMAN SUPPORT
        # ----------------------------------------------

        if any(word in normalized_text for word in [

            "human",

            "agent",

            "customer care",

            "customer support",

            "talk to someone",

            "speak to someone",

            "representative"
        ]):

            return {
                "name": "escalate_to_human",

                "args": {
                    "reason": message
                }
            }

        return None

    # ======================================================
    # EXECUTE TOOL
    # ======================================================

    def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Any:

        try:

            tool = self.tool_registry.get_tool(
                tool_name
            )

            if tool is None:

                return {
                    "success": False,

                    "message":
                        f"Tool '{tool_name}' not found."
                }

            clean_args = {
                key: value
                for key, value in args.items()
                if value is not None
            }

            logger.info(
                f"Executing tool: "
                f"{tool_name} | Args: {clean_args}"
            )

            result = tool(
                **clean_args
            )

            self.total_tool_calls += 1

            return result

        except TypeError as e:

            logger.error(
                f"Tool argument error: "
                f"{tool_name} - {e}"
            )

            return {
                "success": False,

                "message":
                    f"Tool execution error: {str(e)}"
            }

        except Exception as e:

            logger.error(
                f"Tool execution failed: "
                f"{tool_name} - {e}"
            )

            return {
                "success": False,

                "message": str(e)
            }

    # ======================================================
    # COMPARE PRODUCTS
    # ======================================================

    def _compare_products(
        self,
        message: str
    ) -> Any:

        tool = self.tool_registry.get_tool(
            "compare_products"
        )

        if tool is None:

            return {
                "success": False,

                "message":
                    "Compare tool not found."
            }

        try:

            return tool(
                message=message
            )

        except Exception as e:

            logger.error(
                f"Comparison failed: {e}"
            )

            return {
                "success": False,

                "message":
                    f"Comparison failed: {str(e)}"
            }

    # ======================================================
    # GET PRODUCTS
    # ======================================================

    def _get_products(
        self,
        category: str
    ) -> Any:

        return self.execute_tool(
            "get_product_catalog",

            {
                "query": category
            }
        )

    # ======================================================
    # RECOMMEND PRODUCT
    # ======================================================

    def _recommend_product(
        self,
        query: str
    ) -> Any:

        tool = self.tool_registry.get_tool(
            "recommend_product"
        )

        # If recommendation tool exists
        if tool is not None:

            try:

                return tool(
                    query=query
                )

            except TypeError:

                try:

                    return tool(
                        message=query
                    )

                except Exception as e:

                    return {
                        "success": False,

                        "message": str(e)
                    }

            except Exception as e:

                return {
                    "success": False,

                    "message": str(e)
                }

        # ----------------------------------------------
        # FALLBACK RECOMMENDATION
        # ----------------------------------------------

        category = self._extract_category(
            query
        )

        # If category is not provided
        if not category:

            return {
                "success": False,

                "message": (
                    "Please tell me the product "
                    "category and your budget."
                )
            }

        result = self._get_products(
            category
        )

        if not isinstance(result, dict):

            return result

        products = result.get(
            "products",
            []
        )

        if not products:

            return {
                "success": False,

                "message":
                    "No products found for recommendation."
            }

        # Budget filter
        budget = self._extract_budget(
            query
        )

        if budget is not None:

            products = [

                product

                for product in products

                if float(
                    product.get("price", 0)
                ) <= budget
            ]

        if not products:

            return {
                "success": False,

                "message": (
                    f"No {category} products found "
                    f"within your budget."
                )
            }

        # Highest rating first
        # Cheapest product used as tie breaker

        sorted_products = sorted(

            products,

            key=lambda item: (

                float(
                    item.get("rating", 0)
                ),

                -float(
                    item.get("price", 999999999)
                )
            ),

            reverse=True
        )

        recommendation = sorted_products[0]

        return {
            "success": True,

            "recommendation":
                recommendation,

            "products":
                products
        }

    # ======================================================
    # STORE NAME
    # ======================================================

    def _get_store_name(
        self,
        product: Dict[str, Any]
    ) -> str:

        store = product.get(
            "store_name"
        )

        if store:
            return str(store)

        store_id = product.get(
            "store_id"
        )

        store_map = {

            5: "Amazon",

            6: "Flipkart",

            7: "Meesho",

            8: "Myntra"
        }

        return store_map.get(
            store_id,
            "TechStore"
        )

    # ======================================================
    # FORMAT PRODUCT
    # ======================================================

    def _format_product(
        self,
        product: Dict[str, Any]
    ) -> str:

        name = product.get(
            "name",
            "Unknown Product"
        )

        price = product.get(
            "price",
            "N/A"
        )

        rating = product.get(
            "rating",
            "N/A"
        )

        stock = product.get(
            "stock",
            "N/A"
        )

        store = self._get_store_name(
            product
        )

        delivery = product.get(
            "delivery_days"
        )

        result = (

            f"• {name}\n"

            f"  💰 ₹{price}\n"

            f"  ⭐ {rating}/5\n"

            f"  📦 Stock: {stock}\n"

            f"  🛒 Store: {store}"
        )

        if delivery is not None:

            result += (

                f"\n  🚚 Delivery: "
                f"{delivery} days"
            )

        return result

    # ======================================================
    # FORMAT CATALOG
    # ======================================================

    def _format_catalog_response(
        self,
        result: Any
    ) -> str:

        if not isinstance(result, dict):

            return str(result)

        if not result.get(
            "success",
            True
        ):

            return result.get(
                "message",
                "Unable to load products."
            )

        products = result.get(
            "products",
            []
        )

        if not products:

            return result.get(
                "message",
                "No products found."
            )

        lines = [
            "🛍️ Products Found:"
        ]

        for product in products:

            lines.append(
                self._format_product(
                    product
                )
            )

        return "\n".join(
            lines
        )

    # ======================================================
    # FORMAT COMPARISON
    # ======================================================

    def _format_comparison_response(
        self,
        result: Any
    ) -> str:

        if not isinstance(result, dict):

            return str(result)

        if not result.get(
            "success",
            True
        ):

            return result.get(
                "message",
                "Unable to compare products."
            )

        comparison_type = result.get(
            "comparison_type"
        )

        products = result.get(
            "products",
            []
        )

        # ----------------------------------------------
        # SAME PRODUCT ACROSS STORES
        # ----------------------------------------------

        if comparison_type == (
            "same_product_across_stores"
        ):

            lines = [

                "🔍 Product Comparison",

                "",

                "Same product across different stores:"
            ]

            for product in products:

                name = product.get(
                    "name",
                    "Unknown"
                )

                store = product.get(
                    "store_name",
                    self._get_store_name(
                        product
                    )
                )

                price = product.get(
                    "price",
                    "N/A"
                )

                rating = product.get(
                    "rating",
                    "N/A"
                )

                reviews = product.get(
                    "review_count",
                    0
                )

                stock = product.get(
                    "stock",
                    "N/A"
                )

                delivery = product.get(
                    "delivery_days",
                    0
                )

                lines.append(

                    "\n"

                    f"🛒 {store}\n"

                    f"   Product: {name}\n"

                    f"   💰 Price: ₹{price}\n"

                    f"   ⭐ Rating: {rating}/5\n"

                    f"   💬 Reviews: {reviews}\n"

                    f"   📦 Stock: {stock}\n"

                    f"   🚚 Delivery: "
                    f"{delivery} days"
                )

            cheapest = result.get(
                "cheapest"
            )

            highest_rated = result.get(
                "highest_rated"
            )

            recommended = result.get(
                "recommended"
            )

            lines.append("")

            if cheapest:

                lines.append(
                    f"💰 Cheapest: {cheapest}"
                )

            if highest_rated:

                lines.append(
                    f"⭐ Highest Rated: "
                    f"{highest_rated}"
                )

            if recommended:

                lines.append(
                    f"🏆 Recommended: "
                    f"{recommended}"
                )

            return "\n".join(
                lines
            )

        # ----------------------------------------------
        # TWO DIFFERENT PRODUCTS
        # ----------------------------------------------

        lines = [

            "🔍 Product Comparison",

            ""
        ]

        for product in products:

            lines.append(
                self._format_product(
                    product
                )
            )

            lines.append("")

        cheapest = result.get(
            "cheapest"
        )

        highest_rated = result.get(
            "highest_rated"
        )

        recommended = result.get(
            "recommended"
        )

        if cheapest:

            lines.append(
                f"💰 Cheapest: {cheapest}"
            )

        if highest_rated:

            lines.append(
                f"⭐ Highest Rated: "
                f"{highest_rated}"
            )

        if recommended:

            lines.append(
                f"🏆 Recommended: "
                f"{recommended}"
            )

        return "\n".join(
            lines
        )

    # ======================================================
    # FORMAT RECOMMENDATION
    # ======================================================

    def _format_recommendation_response(
        self,
        result: Any
    ) -> str:

        if not isinstance(result, dict):

            return str(result)

        if not result.get(
            "success",
            True
        ):

            return result.get(
                "message",
                "Unable to recommend a product."
            )

        product = result.get(
            "recommendation"
        )

        if not product:

            product = result.get(
                "recommended_product"
            )

        if isinstance(
            product,
            dict
        ):

            lines = [

                "🏆 Recommended Product",

                "",

                self._format_product(
                    product
                )
            ]

            description = product.get(
                "description"
            )

            if description:

                lines.extend([

                    "",

                    f"📝 {description}"
                ])

            return "\n".join(
                lines
            )

        recommended = result.get(
            "recommended"
        )

        if recommended:

            return (

                "🏆 Recommended Product:\n"

                f"{recommended}"
            )

        return str(result)

    # ======================================================
    # FORMAT TOOL RESPONSE
    # ======================================================

    def _format_tool_response(
        self,
        tool_name: str,
        result: Any
    ) -> str:

        # Catalog
        if tool_name == (
            "get_product_catalog"
        ):

            return self._format_catalog_response(
                result
            )

        # Comparison
        if tool_name == (
            "compare_products"
        ):

            return self._format_comparison_response(
                result
            )

        # Recommendation
        if tool_name == (
            "recommend_product"
        ):

            return self._format_recommendation_response(
                result
            )

        # Non-dict
        if not isinstance(
            result,
            dict
        ):

            return str(result)

        # Message
        if "message" in result:

            # Some successful tools contain
            # both success and message.
            # We still prefer useful message.

            return str(
                result["message"]
            )

        # Error
        if "error" in result:

            return str(
                result["error"]
            )

        # Successful tool responses
        if result.get(
            "success"
        ) is True:

            # ------------------------------------------
            # PLACE ORDER
            # ------------------------------------------

            if tool_name == (
                "place_order"
            ):

                order_number = result.get(

                    "order_number",

                    result.get(
                        "order_id",
                        "N/A"
                    )
                )

                product = result.get(

                    "product",

                    result.get(
                        "product_name",
                        "N/A"
                    )
                )

                quantity = result.get(
                    "quantity",
                    1
                )

                total = result.get(

                    "total_amount",

                    result.get(
                        "total",
                        "N/A"
                    )
                )

                status = result.get(
                    "status",
                    "Confirmed"
                )

                return (

                    "✅ Order Placed Successfully!\n\n"

                    f"🧾 Order Number: "
                    f"{order_number}\n"

                    f"📦 Product: "
                    f"{product}\n"

                    f"🔢 Quantity: "
                    f"{quantity}\n"

                    f"💰 Total: ₹"
                    f"{total}\n"

                    f"📌 Status: "
                    f"{status}"
                )

            # ------------------------------------------
            # LOOKUP ORDER
            # ------------------------------------------

            if tool_name == (
                "lookup_order"
            ):

                order = result.get(
                    "order",
                    result
                )

                if isinstance(
                    order,
                    dict
                ):

                    return (

                        "📦 Order Details\n\n"

                        f"🧾 Order Number: {order.get('order_number', 'N/A')}\n"
                        f"📦 Product: {order.get('product_name', 'N/A')}\n"
                        f"🔢 Quantity: {order.get('quantity', 'N/A')}\n"
                        f"💰 Total: ₹{order.get('total_amount', 'N/A')}\n"
                        f"📌 Status: {order.get('status', 'N/A')}"
                    )

            # ------------------------------------------
            # CANCEL
            # ------------------------------------------

            if tool_name == (
                "cancel_order"
            ):

                return (
                    "✅ Order cancellation "
                    "request processed.\n\n"
                    f"{result}"
                )

            # ------------------------------------------
            # REFUND
            # ------------------------------------------

            if tool_name == (
                "process_refund"
            ):

                return (
                    "💰 Refund request processed.\n\n"
                    f"{result}"
                )

            # ------------------------------------------
            # INVENTORY
            # ------------------------------------------

            if tool_name == (
                "check_inventory"
            ):

                return (
                    "📦 Inventory Information\n\n"
                    f"{result}"
                )

            # ------------------------------------------
            # HUMAN ESCALATION
            # ------------------------------------------

            if tool_name == (
                "escalate_to_human"
            ):

                return (
                    "👨‍💼 Your request has been "
                    "escalated to a human support agent."
                )

        return json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )

    # ======================================================
    # OLLAMA
    # ======================================================

    def _ask_ollama(
        self,
        user_message: str
    ) -> str:

        messages = [

            {
                "role": "system",

                "content":
                    self.system_prompt
            }
        ]

        for item in self.conversation_history[-10:]:

            if item.get(
                "role"
            ) in [

                "user",

                "assistant"
            ]:

                messages.append({

                    "role":
                        item["role"],

                    "content":
                        item["content"]
                })

        messages.append({

            "role":
                "user",

            "content":
                user_message
        })

        payload = {

            "model":
                self.model,

            "messages":
                messages,

            "stream":
                False
        }

        try:

            response = requests.post(

                self.ollama_url,

                json=payload,

                timeout=180
            )

            response.raise_for_status()

            data = response.json()

            message = data.get(
                "message",
                {}
            )

            content = message.get(
                "content",
                ""
            )

            if content:

                return content.strip()

            return (
                "I am sorry, I could not generate "
                "a response right now."
            )

        except requests.exceptions.ConnectionError:

            return (

                "❌ Ollama is not running.\n\n"

                "Please start Ollama using:\n"

                "ollama run gemma3"
            )

        except requests.exceptions.Timeout:

            return (

                "⏳ Ollama took too long to respond. "

                "Please try again."
            )

        except Exception as e:

            logger.error(
                f"Ollama error: {e}"
            )

            return (
                "Sorry, I am unable to process "
                "your request right now."
            )

    # ======================================================
    # PROCESS MESSAGE
    # ======================================================

    def process_message(
        self,
        user_message: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:

        start_time = time.time()

        message = (
            user_message or ""
        ).strip()

        if not message:

            return {

                "success": False,

                "response":
                    "Please enter a message."
            }

        if customer_id:

            self.customer_id = customer_id

        self.total_interactions += 1

        self.last_interaction = (
            datetime.now().isoformat()
        )

        self.conversation_history.append({

            "role":
                "user",

            "content":
                message
        })

        # ----------------------------------------------
        # DETECT TOOL
        # ----------------------------------------------

        tool_call = self._detect_tool_call(
            message
        )

        tool_result = None

        tool_name = None

        tool_args = None

        # ----------------------------------------------
        # TOOL EXECUTION
        # ----------------------------------------------

        if tool_call:

            tool_name = tool_call[
                "name"
            ]

            tool_args = tool_call.get(
                "args",
                {}
            )

            logger.info(
                f"Detected tool: "
                f"{tool_name}"
            )

            # ------------------------------------------
            # COMPARE
            # ------------------------------------------

            if tool_name == (
                "compare_products"
            ):

                tool_result = (
                    self._compare_products(
                        message
                    )
                )

            # ------------------------------------------
            # RECOMMEND
            # ------------------------------------------

            elif tool_name == (
                "recommend_product"
            ):

                tool_result = (
                    self._recommend_product(
                        tool_args.get(
                            "query",
                            message
                        )
                    )
                )

            # ------------------------------------------
            # OTHER TOOLS
            # ------------------------------------------

            else:

                tool_result = (
                    self.execute_tool(
                        tool_name,
                        tool_args
                    )
                )

            # ------------------------------------------
            # BUDGET FILTER
            # ------------------------------------------

            if (
                tool_name ==
                "get_product_catalog"
            ):

                budget = (
                    self._extract_budget(
                        message
                    )
                )

                if (
                    budget is not None
                    and isinstance(
                        tool_result,
                        dict
                    )
                ):

                    products = (
                        tool_result.get(
                            "products",
                            []
                        )
                    )

                    filtered_products = [

                        product

                        for product in products

                        if float(
                            product.get(
                                "price",
                                0
                            )
                        ) <= budget
                    ]

                    tool_result[
                        "products"
                    ] = filtered_products

                    tool_result[
                        "budget"
                    ] = budget

                    if not filtered_products:

                        tool_result[
                            "message"
                        ] = (

                            f"No products found "
                            f"under ₹{budget:.0f}."
                        )

            # ------------------------------------------
            # FORMAT
            # ------------------------------------------

            formatted_response = (
                self._format_tool_response(
                    tool_name,
                    tool_result
                )
            )

            self.conversation_history.append({

                "role":
                    "assistant",

                "content":
                    formatted_response
            })

            elapsed = round(

                time.time()
                - start_time,

                3
            )

            return {

                "success":
                    True,

                "response":
                    formatted_response,

                "tool":
                    tool_name,

                "tool_args":
                    tool_args,

                "tool_result":
                    tool_result,

                "response_time":
                    elapsed
            }

        # ----------------------------------------------
        # NORMAL AI CHAT
        # ----------------------------------------------

        response = self._ask_ollama(
            message
        )

        self.conversation_history.append({

            "role":
                "assistant",

            "content":
                response
        })

        elapsed = round(

            time.time()
            - start_time,

            3
        )

        return {

            "success":
                True,

            "response":
                response,

            "tool":
                None,

            "tool_result":
                None,

            "response_time":
                elapsed
        }

    # ======================================================
    # CHAT
    # ======================================================

    def chat(
        self,
        user_message: str,
        customer_id: Optional[str] = None
    ) -> str:

        result = self.process_message(

            user_message,

            customer_id
        )

        return result.get(

            "response",

            "Sorry, I could not process "
            "your request."
        )

    # ======================================================
    # RUN
    # ======================================================

    def run(
        self,
        user_message: str,
        customer_id: Optional[str] = None
    ) -> str:

        return self.chat(

            user_message,

            customer_id
        )

    # ======================================================
    # CONVERSATION SUMMARY
    # ======================================================

    def get_conversation_summary(
        self
    ) -> str:

        if not self.conversation_history:

            return (
                "No conversation available."
            )

        user_messages = [

            item["content"]

            for item in self.conversation_history

            if item.get(
                "role"
            ) == "user"
        ]

        if not user_messages:

            return (
                "No customer messages yet."
            )

        return (

            "Conversation summary:\n"

            + "\n".join(

                f"- {msg}"

                for msg in user_messages[-5:]
            )
        )

    # ======================================================
    # CONVERSATION HISTORY
    # ======================================================

    def get_conversation_history(
        self,
        formatted: bool = True
    ) -> List[Dict[str, Any]]:

        if not formatted:

            return (
                self.conversation_history.copy()
            )

        return [

            item

            for item in self.conversation_history

            if item.get(
                "role"
            ) in [
                "user",
                "assistant"
            ]
        ]

    # ======================================================
    # RESET
    # ======================================================

    def reset_conversation(
        self,
        keep_system_prompt: bool = True
    ) -> None:

        self.conversation_history = []

        logger.info(
            "Conversation reset."
        )

    # ======================================================
    # AGENT INFO
    # ======================================================

    def get_agent_info(
        self
    ) -> Dict[str, Any]:

        try:

            available_tools = list(

                self.tool_registry.tools.keys()
            )

        except Exception:

            available_tools = []

        return {

            "agent":
                "CustomerServiceAgent",

            "status":
                "Ready",

            "model":
                self.model,

            "llm":
                "Ollama",

            "ollama_url":
                self.ollama_url,

            "total_interactions":
                self.total_interactions,

            "total_tool_calls":
                self.total_tool_calls,

            "customer_id":
                self.customer_id,

            "available_tools":
                available_tools
        }

    # ======================================================
    # PERFORMANCE
    # ======================================================

    def get_performance_report(
        self,
        last_n_interactions: int = 50
    ) -> str:

        return (

            "🔧 AGENT PERFORMANCE\n\n"

            f"Model: {self.model}\n"

            f"Total interactions: "
            f"{self.total_interactions}\n"

            f"Total tool calls: "
            f"{self.total_tool_calls}\n"
        )

    # ======================================================
    # SAVE CONVERSATION
    # ======================================================

    def save_conversation(
        self,
        filepath: str
    ) -> None:

        data = {

            "conversation_history":
                self.conversation_history,

            "customer_id":
                self.customer_id,

            "total_interactions":
                self.total_interactions,

            "total_tool_calls":
                self.total_tool_calls,

            "saved_at":
                datetime.now().isoformat()
        }

        with open(

            filepath,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                data,

                file,

                indent=2,

                ensure_ascii=False
            )

        logger.info(
            f"Conversation saved: "
            f"{filepath}"
        )

    # ======================================================
    # LOAD CONVERSATION
    # ======================================================

    def load_conversation(
        self,
        filepath: str
    ) -> None:

        with open(

            filepath,

            "r",

            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        self.conversation_history = (
            data.get(
                "conversation_history",
                []
            )
        )

        self.customer_id = (
            data.get(
                "customer_id"
            )
        )

        self.total_interactions = (
            data.get(
                "total_interactions",
                0
            )
        )

        self.total_tool_calls = (
            data.get(
                "total_tool_calls",
                0
            )
        )

        logger.info(
            f"Conversation loaded: "
            f"{filepath}"
        )

    # ======================================================
    # DEMO MODE
    # ======================================================

    @property
    def is_demo_mode(
        self
    ) -> bool:

        return False


# ==========================================================
# MAIN TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "TECHSTORE AI CUSTOMER SERVICE AGENT"
    )

    print("=" * 60)

    agent = CustomerServiceAgent()

    print(
        "\nAgent Information:"
    )

    print(

        json.dumps(

            agent.get_agent_info(),

            indent=2,

            ensure_ascii=False
        )
    )

    print(
        "\nTesting laptop search..."
    )

    result = agent.process_message(
        "show me laptops"
    )

    print(
        "\nResponse:"
    )

    print(
        result.get(
            "response",
            ""
        )
    )

    print(
        "\nTesting budget search..."
    )

    result = agent.process_message(
        "laptop under 40000"
    )

    print(
        "\nResponse:"
    )

    print(
        result.get(
            "response",
            ""
        )
    )

    print(
        "\nTesting comparison..."
    )

    result = agent.process_message(
        "compare Boat Rockerz 450"
    )

    print(
        "\nResponse:"
    )

    print(
        result.get(
            "response",
            ""
        )
    )

