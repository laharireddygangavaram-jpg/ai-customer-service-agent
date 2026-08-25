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

        # Ollama local evaluation
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

You have access to the following customer service tools:

1. lookup_order
   Use this when a customer asks about an order status.

2. process_refund
   Use this when a customer requests a refund.

3. check_inventory
   Use this when a customer asks whether a product is available.

4. escalate_to_human
   Use this for urgent, payment, account, or complex issues.

5. get_product_catalog
   Use this when the customer asks about available products.

IMPORTANT:
- Never invent order information.
- Never invent inventory information.
- Use the appropriate tool whenever possible.
- Be polite and professional.
- Clearly explain the result to the customer.

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
            print("\n" + "=" * 60)
            print(f"❌ OLLAMA ERROR: {type(e).__name__}")
            print(f"❌ MESSAGE: {str(e)}")
            print("=" * 60 + "\n")

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
        """
        Detect the required customer service tool
        from the customer's message.
        """

        text = message.lower()

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

            if (
                "order" in text
                or "status" in text
                or "delivery" in text
                or "track" in text
                or "where" in text
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

        if (
            "refund" in text
            or "money back" in text
            or "return" in text
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

        if any(word in text for word in inventory_words):

            products = [
                "headphones",
                "wireless headphones",
                "smart watch",
                "smartwatch",
                "laptop",
                "phone case",
            ]

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
        ]

        if any(word in text for word in catalog_words):
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

        if any(word in text for word in urgent_words):
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
        """Execute a registered customer service tool."""

        try:
            logger.info(
                f"Executing tool: {tool_name} "
                f"with args: {arguments}"
            )

            tool_function = (
                self.tool_registry.get_function(tool_name)
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
                f"{customer_id}: {user_message[:100]}..."
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

            print("\n" + "=" * 60)
            print(
                f"❌ ACTUAL ERROR: {type(e).__name__}"
            )
            print(
                f"❌ MESSAGE: {str(e)}"
            )
            print("=" * 60 + "\n")

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
        # Detect required tool
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

        tool_call = self._detect_tool_call(
            user_message
        )

        # -----------------------------------------------------
        # Execute tool
        # -----------------------------------------------------

        tool_result = None

        if tool_call:

            tool_name = tool_call["name"]
            arguments = tool_call["arguments"]

            tool_result = self._execute_tool(
                tool_name,
                arguments,
            )

            # Add tool result to conversation
            self.conversation_history.append(
                {
                    "role": "system",
                    "content": (
                        f"Tool '{tool_name}' returned:\n"
                        f"{tool_result}\n\n"
                        "Use this information to answer "
                        "the customer's request. "
                        "Do not mention internal tool names."
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