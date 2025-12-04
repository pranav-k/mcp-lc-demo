"""
MCP (Model Context Protocol) backend implementation
"""

from typing import Dict, Any
import httpx
import json
import os


class MCPBackend:
    """Backend using MCP tools to interact with Stardog Cloud"""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize MCP backend

        Args:
            config: Configuration dictionary containing:
                - api_token: Stardog Cloud API token
                - client_id: Optional client ID
                - endpoint: MCP server endpoint (default: http://localhost:7001/mcp)
        """
        self.api_token = config.get("api_token") or os.getenv("SD_VOICEBOX_API_TOKEN", "")
        self.client_id = config.get("client_id") or os.getenv("SD_VOICEBOX_CLIENT_ID", "")
        self.endpoint = config.get("endpoint") or os.getenv("MCP_ENDPOINT", "http://localhost:7001/mcp")

        if not self.api_token:
            raise ValueError("API token is required for MCP backend")

        # Setup HTTP client with headers
        self.headers = {
            "x-sdc-api-key": self.api_token,
            "Content-Type": "application/json"
        }

        if self.client_id:
            self.headers["x-sdc-client-id"] = self.client_id

        # Track conversation ID for multi-turn conversations
        self.conversation_id = None

    def query(self, question: str) -> Dict[str, Any]:
        """
        Query Voicebox via MCP with a natural language question

        Args:
            question: Natural language question

        Returns:
            Dictionary containing:
                - answer: The natural language answer
                - sparql: The generated SPARQL query
                - results: Raw query results
        """
        try:
            # Prepare MCP tool call
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "voicebox_ask",
                    "arguments": {
                        "question": question
                    }
                }
            }

            # Add conversation ID if we have one
            if self.conversation_id:
                payload["params"]["arguments"]["conversation_id"] = self.conversation_id

            # Make HTTP request
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()

            # Parse response
            result = response.json()

            if "error" in result:
                raise Exception(f"MCP error: {result['error']}")

            # Extract result data
            result_data = result.get("result", {})

            # Handle different response formats
            if isinstance(result_data, dict) and "content" in result_data:
                # MCP tool response format
                content = result_data["content"]
                if isinstance(content, list) and len(content) > 0:
                    content_item = content[0]
                    if "text" in content_item:
                        # Parse the text content as JSON
                        data = json.loads(content_item["text"])
                    else:
                        data = content_item
                else:
                    data = content
            else:
                data = result_data

            # Update conversation ID
            if "conversation_id" in data:
                self.conversation_id = data["conversation_id"]

            # Format response
            response = {
                "answer": data.get("answer", "No answer generated."),
                "sparql": data.get("sparql_query", ""),
                "results": data.get("results", []),
                "conversation_id": data.get("conversation_id", "")
            }

            return response

        except httpx.HTTPError as e:
            raise Exception(f"MCP backend HTTP error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"MCP backend JSON parse error: {str(e)}")
        except Exception as e:
            raise Exception(f"MCP backend query failed: {str(e)}")

    def reset_conversation(self):
        """Reset the conversation context"""
        self.conversation_id = None

    def get_settings(self) -> Dict[str, Any]:
        """Get Voicebox settings via MCP"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "voicebox_settings",
                    "arguments": {}
                }
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise Exception(f"MCP error: {result['error']}")

            return result.get("result", {})

        except Exception as e:
            raise Exception(f"Failed to get settings: {str(e)}")