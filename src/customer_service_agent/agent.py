"""
Main customer service agent implementation.
Uses Ollama locally instead of OpenAI API.
"""

import json
import time
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import OpenAI
from loguru import logger

from .config import AgentConfig
from .models import ConversationMetadata
from .tools import create_tool_registry
from .utils import (
    format_conversation_history,
    calculate_response_time,
    sanitize_user_input,
    ConversationLogger,
)


class CustomerServiceAgent:
    """Customer service agent using local Ollama Gemma3 model."""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        model: Optional[str] = None,
    ):
        self.config = config or AgentConfig.from_env()
        self.model = model or "gemma3:latest"

        self.client = None
        self.client_available = False

        self._initialize_ollama_client()

        self.tool_registry = create_tool_registry()

        self.evaluator = None

        self.conversation_logger = ConversationLogger(
            self.config.log_file
        )

        self.system_prompt = self._create_system_prompt()

        self.conversation_history: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        self.metadata = ConversationMetadata()

        logger.info(
            f"CustomerServiceAgent initialized with "
            f"Ollama model: {self.model}"
        )

    # =========================================================
    # OLLAMA CLIENT
    # =========================================================

    def _initialize_ollama_client(self) -> None:
        """Initialize Ollama using OpenAI-compatible API."""

        try:
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
            )

            self.client.models.list()

            self.client_available = True

            logger.info(
                "Ollama client initialized successfully"
            )

        except Exception as e:
            logger.error(
                f"Ollama initialization failed: {str(e)}"
            )

            self.client_available = False
            self.client = None

    # =========================================================
    # SYSTEM PROMPT
    # =========================================================

    def _create_system_prompt(self) -> str:
        """Create system prompt."""

        return """
You are an intelligent customer service agent for TechStore.

You have access to customer service tools.

Rules:
- Be polite and professional.
- Never invent order information.
- Never invent inventory information.
- Never invent product information.
- Use the provided tool result when available.
- Do not output tool_code.
- Do not output Python code.
- Do not describe internal tools.
- Give the customer a natural answer.

You are running locally using Gemma3 through Ollama.
"""

    # =========================================================
    # OLLAMA API
    # =========================================================

    def _call_ollama(self, **kwargs) -> Any:
        """Call local Ollama model."""

        if self.client is None or not self.client_available:
            raise RuntimeError(
                "Ollama is not available. "
                "Make sure Ollama is running."
            )

        try:
            return self.client.chat.completions.create(
                **kwargs
            )

        except Exception as e:
            logger.error(
                f"Ollama API error: {type(e).__name__}: {str(e)}"
            )
            raise

    # =========================================================
    # SENTIMENT
    # =========================================================

    def _analyze_sentiment(
        self,
        message: str,
    ) -> Dict[str, Any]:
        """Simple local sentiment analysis."""

        message_lower = message.lower()

        negative_words = [
            "angry",
            "broken",
            "refund",
            "bad",
            "terrible",
            "worst",
            "urgent",
            "problem",
            "issue",
            "hate",
            "not working",
            "charged twice",
        ]

        positive_words = [
            "thank",
            "thanks",
            "good",
            "great",
            "excellent",
            "happy",
            "awesome",
        ]

        negative_count = sum(
            word in message_lower
            for word in negative_words
        )

        positive_count = sum(
            word in message_lower
            for word in positive_words
        )

        if negative_count > positive_count:
            sentiment = "negative"
            score = -0.5

        elif positive_count > negative_count:
            sentiment = "positive"
            score = 0.5

        else:
            sentiment = "neutral"
            score = 0.0

        self.metadata.sentiment_scores.append(score)

        return {
            "sentiment": sentiment,
            "score": score,
        }

    # =========================================================
    # TOOL DETECTION
    # =========================================================

    def _detect_tool_call(
        self,
        message: str,
    ) -> Optional[Dict[str, Any]]:
        """Detect required customer service tool."""

        text = message.lower().strip()

        # -----------------------------------------------------
        # ORDER LOOKUP
        # -----------------------------------------------------

        order_match = re.search(
            r"\bORD[-\s]?\d{5}\b",
            message,
            re.IGNORECASE,
        )

        if order_match:

            order_number = (
                order_match.group(0)
                .upper()
                .replace(" ", "-")
            )

            if any(
                word in text
                for word in [
                    "order",
                    "status",
                    "delivery",
                    "track",
                    "where",
                ]
            ):
                return {
                    "name": "lookup_order",
                    "arguments": {
                        "order_number": order_number
                    },
                }

        # -----------------------------------------------------
        # REFUND
        # -----------------------------------------------------

        if any(
            word in text
            for word in [
                "refund",
                "money back",
                "return",
            ]
        ):

            if order_match:

                order_number = (
                    order_match.group(0)
                    .upper()
                    .replace(" ", "-")
                )

                return {
                    "name": "process_refund",
                    "arguments": {
                        "order_number": order_number,
                        "reason": message,
                    },
                }

        # -----------------------------------------------------
        # INVENTORY
        # -----------------------------------------------------

        inventory_words = [
            "in stock",
            "available",
            "availability",
            "stock",
            "do you have",
        ]

        products = [
            "wireless headphones",
            "headphones",
            "smart watch",
            "smartwatch",
            "laptop",
            "phone case",
            "camera",
            "earbuds",
            "speakers",
            "keyboard",
            "mouse",
        ]

        if any(word in text for word in inventory_words):

            for product in products:

                if product in text:

                    return {
                        "name": "check_inventory",
                        "arguments": {
                            "product_name": product
                        },
                    }

        # -----------------------------------------------------
        # PRODUCT CATALOG
        # -----------------------------------------------------

        catalog_words = [
            "products",
            "catalog",
            "what do you sell",
            "what products",
            "show products",
            "show me",
            "show",
            "looking for",
            "looking at",
            "browse",
            "see",
        ]

        product_categories = [
            "wireless headphones",
            "headphones",
            "smart watch",
            "smartwatch",
            "laptop",
            "phone case",
            "camera",
            "earbuds",
            "speakers",
            "keyboard",
            "mouse",
        ]

        # "show me headphones"
        if (
            any(word in text for word in catalog_words)
            and any(
                product in text
                for product in product_categories
            )
        ):
            return {
                "name": "get_product_catalog",
                "arguments": {},
            }

        # Direct product request
        if any(
            product in text
            for product in product_categories
        ):
            return {
                "name": "get_product_catalog",
                "arguments": {},
            }

        # -----------------------------------------------------
        # HUMAN ESCALATION
        # -----------------------------------------------------

        urgent_words = [
            "charged twice",
            "payment issue",
            "account problem",
            "speak to human",
            "human agent",
            "manager",
            "urgent",
        ]

        if any(
            word in text
            for word in urgent_words
        ):

            priority = "high"

            if "urgent" in text:
                priority = "urgent"

            return {
                "name": "escalate_to_human",
                "arguments": {
                    "issue_description": message,
                    "priority": priority,
                },
            }

        return None

    # =========================================================
    # EXECUTE TOOL
    # =========================================================

    def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        """Execute registered customer service tool."""

        try:

            logger.info(
                f"Executing tool: {tool_name} "
                f"with args: {arguments}"
            )

            tool_function = (
                self.tool_registry.get_function(
                    tool_name
                )
            )

            result = tool_function(**arguments)

            self.metadata.total_tool_calls += 1

            if not isinstance(result, str):
                result = json.dumps(result)

            logger.info(
                f"Tool executed successfully: {tool_name}"
            )

            return result

        except Exception as e:

            logger.error(
                f"Tool execution failed: "
                f"{tool_name}: {str(e)}"
            )

            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                }
            )

    # =========================================================
    # PRODUCT CATALOG FORMATTER
    # =========================================================

    def _format_product_catalog(
        self,
        tool_result: str,
    ) -> str:
        """Format product catalog result for customer."""

        try:

            catalog = json.loads(tool_result)

            products = catalog.get(
                "products",
                [],
            )

            if not products:
                return (
                    "Sorry, I couldn't find any "
                    "products right now."
                )

            lines = [
                "Here are the available products:"
            ]

            for product in products:

                name = product.get(
                    "name",
                    "Unknown product",
                )

                price = product.get(
                    "price",
                    0,
                )

                rating = product.get(
                    "rating",
                    0,
                )

                stock = product.get(
                    "stock",
                    0,
                )

                store = product.get(
                    "store_name",
                    "N/A",
                )

                lines.append(
                    f"• {name} | "
                    f"Price: ₹{price:.0f} | "
                    f"Rating: {rating}/5 | "
                    f"Stock: {stock} | "
                    f"Store: {store}"
                )

            return "\n".join(lines)

        except Exception as e:

            logger.error(
                f"Product catalog formatting failed: "
                f"{str(e)}"
            )

            return (
                "I found the products, but I couldn't "
                "format the catalog correctly."
            )

    # =========================================================
    # CLEAN AI RESPONSE
    # =========================================================

    def _clean_response(
        self,
        response: str,
    ) -> str:
        """Remove unwanted tool-code output."""

        if not response:
            return (
                "I apologize, but I couldn't generate "
                "a response."
            )

        # Remove tool code blocks
        response = re.sub(
            r"```tool_code.*?```",
            "",
            response,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove tool_code text
        response = re.sub(
            r"tool_code\s*.*",
            "",
            response,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove common fake tool-call format
        response = re.sub(
            r"get_product_catalog\s*\(.*",
            "",
            response,
            flags=re.DOTALL | re.IGNORECASE,
        )

        response = response.strip()

        if not response:
            return (
                "I apologize, but I couldn't generate "
                "a response."
            )

        return response

    # =========================================================
    # CHAT
    # =========================================================

    def chat(
        self,
        user_message: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """Process customer message."""

        start_time = time.time()

        try:

            logger.info(
                f"Processing message from customer "
                f"{customer_id}: "
                f"{user_message[:100]}..."
            )

            if customer_id:
                self.metadata.customer_id = customer_id

            sanitized_message = sanitize_user_input(
                user_message
            )

            self._analyze_sentiment(
                sanitized_message
            )

            self.conversation_history.append(
                {
                    "role": "user",
                    "content": sanitized_message,
                }
            )

            response = self._get_agent_response()

            self.metadata.total_interactions += 1

            self.metadata.last_interaction = (
                datetime.now().isoformat()
            )

            response_time = calculate_response_time(
                start_time
            )

            self.conversation_logger.log_interaction(
                user_input=sanitized_message,
                agent_response=response,
                customer_id=customer_id,
            )

            logger.info(
                f"Message processed successfully "
                f"in {response_time:.2f}s"
            )

            return response

        except Exception as e:

            logger.exception(
                "Error while processing customer message"
            )

            return (
                "I apologize, but I encountered an error "
                "processing your request. "
                "Please make sure Ollama is running "
                "and Gemma3 is available."
            )

    # =========================================================
    # AGENT RESPONSE
    # =========================================================

    def _get_agent_response(self) -> str:
        """
        Generate response using Ollama and execute
        customer service tools when required.
        """

        # -----------------------------------------------------
        # Get latest user message
        # -----------------------------------------------------

        user_message = ""

        for message in reversed(
            self.conversation_history
        ):

            if message.get("role") == "user":

                user_message = message.get(
                    "content",
                    "",
                )

                break

        # -----------------------------------------------------
        # Detect tool
        # -----------------------------------------------------

        tool_call = self._detect_tool_call(
            user_message
        )

        tool_name = None
        tool_result = None

        # -----------------------------------------------------
        # Execute tool
        # -----------------------------------------------------

        if tool_call:

            tool_name = tool_call["name"]

            arguments = tool_call["arguments"]

            tool_result = self._execute_tool(
                tool_name,
                arguments,
            )

            logger.info(
                f"Tool executed: {tool_name}"
            )

        # -----------------------------------------------------
        # DIRECT PRODUCT CATALOG
        # -----------------------------------------------------

        if tool_name == "get_product_catalog":

            final_response = (
                self._format_product_catalog(
                    tool_result
                )
            )

            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": final_response,
                }
            )

            return final_response

        # -----------------------------------------------------
        # OTHER TOOL RESULTS
        # -----------------------------------------------------

        if tool_result:

            self.conversation_history.append(
                {
                    "role": "system",
                    "content": (
                        "A customer service tool was executed.\n\n"
                        f"Tool result:\n{tool_result}\n\n"
                        "Answer the customer using the tool result.\n"
                        "Do not mention internal tool names.\n"
                        "Do not generate tool calls.\n"
                        "Do not output tool_code.\n"
                        "Answer naturally and professionally."
                    ),
                }
            )

        # -----------------------------------------------------
        # Prepare conversation
        # -----------------------------------------------------

        formatted_history = (
            format_conversation_history(
                self.conversation_history,
                self.config.max_conversation_history,
            )
        )

        # -----------------------------------------------------
        # Ask Gemma3
        # -----------------------------------------------------

        response = self._call_ollama(
            model=self.model,
            messages=formatted_history,
            temperature=self.config.default_temperature,
        )

        response_message = (
            response.choices[0].message
        )

        final_response = (
            response_message.content
            or "I apologize, but I couldn't generate "
               "a response."
        )

        # -----------------------------------------------------
        # Clean response
        # -----------------------------------------------------

        final_response = self._clean_response(
            final_response
        )

        # -----------------------------------------------------
        # Save response
        # -----------------------------------------------------

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": final_response,
            }
        )

        return final_response

    # =========================================================
    # AGENT INFORMATION
    # =========================================================

    def get_agent_info(
        self,
    ) -> Dict[str, Any]:
        """Return agent information."""

        return {
            "agent": "CustomerServiceAgent",
            "status": (
                "Ready"
                if self.client_available
                else "Ollama Offline"
            ),
            "model": self.model,
            "backend": "Ollama",
            "local": True,
            "available_tools": [
                tool.get("function", {}).get(
                    "name",
                    "unknown",
                )
                for tool in self.tool_registry.get_all_schemas()
            ],
            "total_interactions": (
                self.metadata.total_interactions
            ),
            "total_tool_calls": (
                self.metadata.total_tool_calls
            ),
        }

    # =========================================================
    # CONVERSATION SUMMARY
    # =========================================================

    def get_conversation_summary(
        self,
    ) -> Dict[str, Any]:
        """Return conversation summary."""

        return {
            "customer_id": (
                self.metadata.customer_id
            ),
            "total_interactions": (
                self.metadata.total_interactions
            ),
            "total_tool_calls": (
                self.metadata.total_tool_calls
            ),
            "messages": len(
                self.conversation_history
            ),
            "last_interaction": (
                self.metadata.last_interaction
            ),
        }

    # =========================================================
    # PERFORMANCE REPORT
    # =========================================================

    def get_performance_report(
        self,
    ) -> Dict[str, Any]:
        """Return local performance information."""

        return {
            "model": self.model,
            "backend": "Ollama",
            "total_interactions": (
                self.metadata.total_interactions
            ),
            "total_tool_calls": (
                self.metadata.total_tool_calls
            ),
            "sentiment_samples": len(
                self.metadata.sentiment_scores
            ),
            "status": (
                "Ready"
                if self.client_available
                else "Ollama Offline"
            ),
        }