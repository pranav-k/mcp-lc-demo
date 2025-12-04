"""
A Streamlit demo app showcasing Stardog LangChain/MCP integration.
"""

import streamlit as st
import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from backends.langchain_backend import LangChainBackend
from backends.mcp_backend import MCPBackend

load_dotenv()

st.set_page_config(
    page_title="LangChain/MCP Demo",
    page_icon="/resources/logo.png",
    layout="wide"
)

# Example queries for the sidebar
EXAMPLE_QUERIES = [
    "Who are the top 5 deal owners by total deal value?",
    "Which products are most frequently ordered?",
    "Show me all active deals",
    "Which people influence deals but aren't the deal owners?",
    "What products were purchased by companies with high-value deals?",
    "Show me the reporting chain for deal owners",
    "Which brands are associated with our highest-value orders?",
    "Find companies that have multiple deals from different source partners",
    "What is the average order value by product category?",
    "Who are the key decision makers in our top accounts?"
]

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "backend_type" not in st.session_state:
        st.session_state.backend_type = "langchain"
    if "backend" not in st.session_state:
        st.session_state.backend = None
    if "show_sparql" not in st.session_state:
        st.session_state.show_sparql = True
    if "show_results" not in st.session_state:
        st.session_state.show_results = False
    if "query_mode" not in st.session_state:
        st.session_state.query_mode = "simple"  # simple, agent, or chain
    if "show_tool_calls" not in st.session_state:
        st.session_state.show_tool_calls = True

def run_async(coro):
    """
    Helper function to run async coroutines in Streamlit.
    Handles event loop lifecycle properly.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)

def get_backend(backend_type: str, config: Dict[str, str]):
    """Initialize and return the appropriate backend"""
    try:
        if backend_type == "langchain":
            return LangChainBackend(config)
        elif backend_type == "mcp":
            return MCPBackend(config)
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
    except Exception as e:
        st.error(f"Failed to initialize {backend_type} backend: {str(e)}")
        return None

def render_sidebar():
    """Render the sidebar with configuration and examples"""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Backend selection
        backend_type = st.radio(
            "Select Backend",
            options=["langchain", "mcp"],
            index=0 if st.session_state.backend_type == "langchain" else 1,
            format_func=lambda x: "🦜 LangChain (langchain-stardog)" if x == "langchain" else "🔧 MCP Tools",
            help="Choose between LangChain integration or MCP tools"
        )

        if backend_type != st.session_state.backend_type:
            st.session_state.backend_type = backend_type
            st.session_state.backend = None  # Reset backend on change

        st.divider()

        # Configuration inputs
        st.subheader("Stardog Cloud Credentials")

        api_token = st.text_input(
            "API Token",
            value=os.getenv("SD_VOICEBOX_API_TOKEN", ""),
            type="password",
            help="Your Stardog Cloud API token from cloud.stardog.com"
        )

        client_id = st.text_input(
            "Client ID (Optional)",
            value=os.getenv("SD_VOICEBOX_CLIENT_ID", ""),
            help="Optional client ID for usage tracking"
        )

        if backend_type == "mcp":
            endpoint = st.text_input(
                "MCP Endpoint",
                value=os.getenv("MCP_ENDPOINT", "http://localhost:7001/mcp"),
                help="MCP server endpoint URL"
            )
        else:
            endpoint = st.text_input(
                "Stardog Endpoint",
                value=os.getenv("STARDOG_ENDPOINT", "https://cloud.stardog.com/api"),
                help="Stardog Cloud API endpoint"
            )

        config = {
            "api_token": api_token,
            "client_id": client_id,
            "endpoint": endpoint
        }

        # Initialize app button
        if st.button("Initialize App", use_container_width=True):
            with st.spinner(f"Initializing {backend_type} backend..."):
                backend = get_backend(backend_type, config)
                if backend:
                    st.session_state.backend = backend
                    st.success(f"{backend_type.title()} backend initialized!")
                    st.rerun()

        # Show backend status
        if st.session_state.backend:
            st.success(f"✅ {st.session_state.backend_type.title()} backend active")

        st.divider()

        # Demo Mode Selection (only for LangChain backend)
        if st.session_state.backend_type == "langchain" and st.session_state.backend:
            st.subheader("🎯 Demo Mode")

            query_mode = st.selectbox(
                "Select Query Mode",
                options=["simple", "agent", "chain"],
                index=["simple", "agent", "chain"].index(st.session_state.query_mode),
                format_func=lambda x: {
                    "simple": "Simple - Direct Voicebox Query",
                    "agent": "Agent - Multi-Tool Orchestration",
                    "chain": "Chain - Translation Pipeline"
                }[x],
                help="Choose how to process queries"
            )

            if query_mode != st.session_state.query_mode:
                st.session_state.query_mode = query_mode

            # Show description based on mode
            if query_mode == "simple":
                st.caption("Direct queries to Voicebox. Best for standard Q&A.")
            elif query_mode == "agent":
                st.caption("Agent decides which tools to use (Voicebox + Calculator + Shipping).")
                st.info("💡 Try: 'What's the shipping cost for order X to San Francisco?'")
            elif query_mode == "chain":
                st.caption("Auto-translate queries and responses.")
                st.info("💡 Try asking in Spanish: '¿Cuáles son los mejores productos?'")

            st.divider()

        # Options
        st.subheader("Display Options")

        st.session_state.show_sparql = st.checkbox(
            "Show Generated SPARQL",
            value=st.session_state.show_sparql,
            help="Display the generated SPARQL query with results"
        )

        st.session_state.show_results = st.checkbox(
            "Show Raw Results",
            value=st.session_state.show_results,
            help="Display raw JSON results from the query"
        )

        if st.session_state.query_mode in ["agent", "chain"]:
            st.session_state.show_tool_calls = st.checkbox(
                "Show Tool Calls / Chain Steps",
                value=st.session_state.show_tool_calls,
                help="Display intermediate tool calls or chain execution steps"
            )

        # st.divider()
        #
        # # Example queries
        # st.subheader("💡 Example Questions")
        # st.caption("Click to use:")

        # for i, query in enumerate(EXAMPLE_QUERIES):
        #     if st.button(query, key=f"example_{i}", use_container_width=True):
        #         st.session_state.example_query = query
        #         st.rerun()

        # Clear conversation button
        if st.session_state.backend and st.session_state.messages:
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset Context", use_container_width=True, help="Clear conversation context"):
                    st.session_state.backend.reset_conversation()
                    st.success("Context reset!")
            with col2:
                if st.button("🗑️ Clear Chat", use_container_width=True, help="Clear all messages"):
                    st.session_state.messages = []
                    st.session_state.backend.reset_conversation()
                    st.rerun()

def render_message(role: str, content: Dict[str, Any]):
    """Render a chat message with optional SPARQL query"""
    with st.chat_message(role):
        if role == "assistant":
            # Display the answer
            answer = content.get("answer", content.get("text", ""))
            st.markdown(answer)

            # Display SPARQL query if available and enabled
            if st.session_state.show_sparql and content.get("sparql"):
                with st.expander("🔍 Generated SPARQL Query"):
                    st.code(content["sparql"], language="sparql")

            # Display raw results if available and enabled
            if st.session_state.show_results and content.get("results"):
                with st.expander("📊 Raw Results"):
                    st.json(content["results"])

            # Show conversation ID if available
            if content.get("conversation_id"):
                st.caption(f"Conversation ID: {content['conversation_id'][:8]}...")
        else:
            st.markdown(content)

def main():
    """Main application logic"""
    initialize_session_state()

    # Header
    st.title("Stardog MCP/LangChain Demo")
    st.caption(f"Powered by Stardog Cloud + {st.session_state.backend_type.title()}")

    # Render sidebar
    render_sidebar()

    # Check if backend is initialized
    if st.session_state.backend is None:
        st.info("👈 Please configure and initialize a backend in the sidebar to get started.")

        # Show intro content
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🚀 Getting Started")
            st.markdown("""
            1. **Get your API credentials** from [cloud.stardog.com](https://cloud.stardog.com)
            2. **Configure your backend** in the sidebar (LangChain or MCP)
            3. **Click Initialize** to connect to your Stardog Cloud instance
            4. **Start asking questions** about against your configured KG!
            """)

        with col2:
            st.subheader("🔧 Backend Options")

            st.markdown("**🦜 LangChain Backend**")
            st.caption("""
            Uses the `langchain-stardog` package with Voicebox API.
            Best for: Production applications, agent workflows.
            """)

            st.markdown("**🔧 MCP Backend**")
            st.caption("""
            Uses Model Context Protocol tools directly.
            Best for: IDE integrations, development tools.
            """)

        return

    # Display chat messages
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

    # Handle example query selection
    if "example_query" in st.session_state:
        user_input = st.session_state.example_query
        del st.session_state.example_query
    else:
        user_input = None

    # Chat input
    if prompt := (user_input or st.chat_input("Ask about your customer data...")):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Call appropriate method based on query mode
                    if st.session_state.query_mode == "agent" and hasattr(st.session_state.backend, 'query_with_agent'):
                        response = run_async(st.session_state.backend.query_with_agent(prompt))
                    elif st.session_state.query_mode == "chain" and hasattr(st.session_state.backend, 'query_with_chain'):
                        response = run_async(st.session_state.backend.query_with_chain(prompt))
                    else:
                        # Default: simple query
                        response = run_async(st.session_state.backend.query(prompt))

                    # Display answer
                    st.markdown(response.get("answer", "No answer generated."))

                    # Display tool calls for agent mode
                    if st.session_state.show_tool_calls and response.get("tool_calls"):
                        with st.expander(f"🔧 Tool Calls ({response.get('agent_steps', 0)} steps)"):
                            for i, call in enumerate(response["tool_calls"], 1):
                                st.markdown(f"**Step {i}: {call['tool']}**")
                                st.code(f"Input: {call['input']}", language="json")
                                st.caption(f"Output: {call['output']}")
                                st.divider()

                    # Display chain steps for chain mode
                    if st.session_state.show_tool_calls and response.get("chain_steps"):
                        with st.expander(f"⛓️ Chain Steps ({len(response['chain_steps'])} steps)"):
                            for i, step in enumerate(response["chain_steps"], 1):
                                st.markdown(f"**Step {i}: {step['step']}**")
                                st.caption(f"Result: {step['result']}")
                                st.divider()

                    # Display SPARQL if available and enabled
                    if st.session_state.show_sparql and response.get("sparql"):
                        with st.expander("🔍 Generated SPARQL Query"):
                            st.code(response["sparql"], language="sparql")

                    # Display raw results if available and enabled
                    if st.session_state.show_results and response.get("results"):
                        with st.expander("📊 Raw Results"):
                            st.json(response["results"])

                    # Show conversation ID
                    if response.get("conversation_id"):
                        st.caption(f"Conversation ID: {response['conversation_id'][:8]}...")

                    # Save to message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": {"text": error_msg}
                    })

if __name__ == "__main__":
    main()
