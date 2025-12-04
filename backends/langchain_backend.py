"""
LangChain + langchain-stardog backend implementation
"""

import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_stardog import VoiceboxAskRunnable, VoiceboxClient


load_dotenv()
logging.basicConfig(level=logging.INFO)


class LangChainBackend:
    """Backend using langchain-stardog package with Voicebox"""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize LangChain backend

        Args:
            config: Configuration dictionary containing:
                - api_token: Stardog Cloud API token
                - client_id: Optional client ID
                - endpoint: Stardog Cloud endpoint (default: https://cloud.stardog.com/api)
        """
        logging.info("Initializing LangChainBackend with config")
        self.api_token = config.get("api_token") or os.getenv("SD_VOICEBOX_API_TOKEN", "")
        self.client_id = config.get("client_id") or os.getenv("SD_VOICEBOX_CLIENT_ID", "")
        self.endpoint = config.get("endpoint") or os.getenv("STARDOG_ENDPOINT", "https://cloud.stardog.com/api")

        if not self.api_token:
            raise ValueError("API token is required for LangChain backend")
        else:
            logging.info("API token found")

        # Initialize Voicebox client
        self.client = VoiceboxClient(
            api_token=self.api_token,
            client_id=self.client_id if self.client_id else None,
            endpoint=self.endpoint
        )

        # Initialize the Ask runnable
        self.ask_runnable = VoiceboxAskRunnable(client=self.client)

        # Track conversation ID for multi-turn conversations
        self.conversation_id = None

    async def query(self, question: str) -> Dict[str, Any]:
        """
        Query Voicebox with a natural language question (async)

        Args:
            question: Natural language question

        Returns:
            Dictionary containing:
                - answer: The natural language answer
                - sparql: The generated SPARQL query
                - results: Raw query results
        """
        try:
            # Prepare input
            input_data = {"question": question}
            if self.conversation_id:
                input_data["conversation_id"] = self.conversation_id

            # logging.info(f"LangChainBackend endpoint: {self.endpoint}")
            # logging.info(f"LangChainBackend api_token: {self.api_token}")

            # Execute query using async endpoint
            result = await self.ask_runnable.ainvoke(input_data)
            # logging.info(f"LangChainBackend api_token2: {self.api_token}")

            # Update conversation ID for context
            if "conversation_id" in result:
                self.conversation_id = result["conversation_id"]

            # logging.info(f"LangChainBackend results: {result["answer"]}")
            # Format response
            response = {
                "answer": result.get("answer", "No answer generated."),
                "conversation_id": result.get("conversation_id", "")
            }

            return response

        except Exception as e:
            raise Exception(f"LangChain backend query failed: {str(e)}")

    def reset_conversation(self):
        """Reset the conversation context"""
        self.conversation_id = None

    # ========================================================================
    # Advanced Features: Agent with Multiple Tools
    # ========================================================================

    async def query_with_agent(
        self,
        question: str,
        tools_to_use: list = None,
        llm_model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Query using an agent that can use multiple tools including Voicebox.

        Uses standard LangChain create_tool_calling_agent pattern.
        Demonstrates how Voicebox integrates seamlessly with LangChain ecosystem.

        Args:
            question: Natural language question
            tools_to_use: List of tool names to include. Options:
                         - "voicebox": Query knowledge graph
                         - "calculator": Mathematical calculations
                         - "distance": Calculate distances
                         - "shipping": Calculate shipping costs
            llm_model: OpenAI model (default: gpt-4o-mini)

        Returns:
            Dictionary with answer, tool_calls, and agent_steps
        """
        from langchain.agents import create_agent
        from langchain_stardog import VoiceboxAskTool
        from .langchain_tools import (
            calculator,
            calculate_distance,
            calculate_shipping_cost,
        )

        try:
            logging.info("Querying LangChain with agent")
            # Prepare Voicebox tool - just like any other LangChain tool!
            voicebox_tool = VoiceboxAskTool(client=self.client)

            # Map tool names to actual tools
            tool_map = {
                "voicebox": voicebox_tool,
                "calculator": calculator,
                "distance": calculate_distance,
                "shipping": calculate_shipping_cost,
            }

            # Select tools
            if tools_to_use is None:
                tools_to_use = ["voicebox", "calculator", "distance", "shipping"]

            tools = [tool_map[name] for name in tools_to_use if name in tool_map]

            # System prompt for the agent
            system_prompt = """You are a helpful assistant with access to multiple tools:

- voicebox_ask: Query the knowledge graph for customer data, orders, products, etc.
- calculator: Perform mathematical calculations
- calculate_distance: Calculate distance between two locations
- calculate_shipping_cost: Calculate shipping costs based on distance and order value

Use the appropriate tools to answer questions accurately and concisely.

IMPORTANT: Do not use LaTeX, math notation (like $ or $$), or special formatting in your responses. Use plain text for all numbers and calculations."""

            # Create agent using modern create_agent API (super simple!)
            agent = create_agent(
                f"openai:{llm_model}",
                tools,
                system_prompt=system_prompt
            )

            # Execute agent (returns state with messages)
            result = await agent.ainvoke({"messages": [("user", question)]})

            # Extract messages from result
            messages = result.get("messages", [])

            # Get the final AI response (last message)
            answer = ""
            tool_calls_list = []

            # Creating response for Streamlit
            for msg in messages:
                # Check if it's an AI message
                if hasattr(msg, 'content') and hasattr(msg, 'type'):
                    if msg.type == "ai":
                        answer = msg.content
                    # Track tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_calls_list.append({
                                "tool": tc.get("name", "unknown"),
                                "input": tc.get("args", {}),
                                "output": ""  # Tool output comes in separate messages
                            })
                    # Track tool results
                    elif msg.type == "tool":
                        if tool_calls_list:
                            tool_calls_list[-1]["output"] = str(msg.content)[:200]

            logging.info(f"AGENT answer: {answer}")
            # Format response
            response = {
                "answer": answer or "No answer generated.",
                "tool_calls": tool_calls_list,
                "agent_steps": len(tool_calls_list),
                "mode": "agent"
            }

            return response

        except Exception as e:
            raise Exception(f"Agent query failed: {str(e)}")

    # ========================================================================
    # Advanced Features: Chain Composition (Translation Example)
    # ========================================================================

    async def query_with_chain(
        self,
        question: str,
        chain_type: str = "translation"
    ) -> Dict[str, Any]:
        """
        Query using LangChain's pipe operator (|) for chain composition.

        Demonstrates idiomatic LangChain: detect → translate → query → translate back
        All composed with the | operator!

        Args:
            question: Natural language question (can be in any language)
            chain_type: Type of chain to use:
                       - "translation": Detect language, translate, query, translate back

        Returns:
            Dictionary with answer and chain steps
        """
        from langchain_core.runnables import RunnableLambda
        from .langchain_tools import detect_language, translate_text

        try:
            if chain_type == "translation":
                chain_steps = []

                # Step 1: Detect language and create context dict
                def detect_and_prepare(q: str) -> dict:
                    lang = detect_language.invoke({"text": q})
                    chain_steps.append({"step": "detect_language", "result": lang})
                    return {"question": q, "detected_lang": lang, "original_question": q}

                # Step 2: Translate to English if needed
                def translate_to_english(data: dict) -> dict:
                    if data["detected_lang"] != "English":
                        translated = translate_text.invoke({
                            "text": data["question"],
                            "source_lang": data["detected_lang"],
                            "target_lang": "English"
                        })
                        chain_steps.append({"step": "translate_to_english", "result": translated})
                        data["question"] = translated
                    return data

                # Step 3: Query Voicebox
                async def query_voicebox(data: dict) -> dict:
                    input_data = {"question": data["question"]}
                    if self.conversation_id:
                        input_data["conversation_id"] = self.conversation_id

                    result = await self.ask_runnable.ainvoke(input_data)
                    answer = result.get("answer", "")
                    chain_steps.append({"step": "voicebox_query", "result": answer[:200]})

                    # Update conversation ID
                    if "conversation_id" in result:
                        self.conversation_id = result["conversation_id"]

                    data["answer"] = answer
                    return data

                # Step 4: Translate back to original language if needed
                def translate_back(data: dict) -> dict:
                    if data["detected_lang"] != "English":
                        translated = translate_text.invoke({
                            "text": data["answer"],
                            "source_lang": "English",
                            "target_lang": data["detected_lang"]
                        })
                        chain_steps.append({"step": "translate_to_source", "result": translated})
                        data["answer"] = translated
                    return data

                # Compose the entire chain with pipe operator!
                translation_chain = (
                    RunnableLambda(detect_and_prepare)
                    | RunnableLambda(translate_to_english)
                    | RunnableLambda(query_voicebox)
                    | RunnableLambda(translate_back)
                )

                # Execute the composed chain
                result = await translation_chain.ainvoke(question)

                # Format response
                response = {
                    "answer": result["answer"],
                    "original_question": result["original_question"],
                    "detected_language": result["detected_lang"],
                    "chain_steps": chain_steps,
                    "mode": "chain"
                }

                return response

            else:
                raise ValueError(f"Unknown chain type: {chain_type}")

        except Exception as e:
            raise Exception(f"Chain query failed: {str(e)}")