"""
A Streamlit demo app showcasing Stardog LangChain integration.
"""

import asyncio
import os
from typing import Dict, Any

import streamlit as st
from dotenv import load_dotenv

from backends.langchain_backend import LangChainBackend
from backends.mcp_backend import MCPBackend

load_dotenv()

st.set_page_config(
    page_title="LangChain/MCP Demo",
    layout="wide"
)

# Example queries for the sidebar
EXAMPLE_QUERIES_SIMPLE = [
    "Show 5 popular products and their cost",
    "Who created a rewards account in January 2022?",
    "Which products are most frequently ordered?",
    "What is the average order value by product category?",
]
EXAMPLE_QUERIES_AGENT = [
    "Whats the shipping cost of Ladle from Chicago to Detroit?",
    "Whats the shipping cost of a Dishwasher from Los Angeles to San Diego?",
]
EXAMPLE_QUERIES_CHAIN = [
    "Mostrar 5 productos populares y su costo, según las ventas",
    "Lista de 5 productos populares",
    "¿Cuál es el mejor producto por monto total de ventas?",
    "¿Cuáles son los mejores productos?",
]

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        "messages": [],
        "backend_type": "langchain",
        "backend": None,
        "show_sparql": True,
        "show_results": False,
        "query_mode": "simple",  # simple, agent, or chain
        "show_tool_calls": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def run_async(coro):
    """
    Helper function to run async coroutines in Streamlit.
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
            "Selected Backend",
            options=["langchain"],  # Only LangChain is selectable
            index=0,  # LangChain preselected
            format_func=lambda x: "🦜 LangChain (langchain-stardog)" if x == "langchain" else x,
        )
        # MCP backend option is commented out for now
        # options=["langchain", "mcp"],
        # format_func=lambda x: "🦜 LangChain (langchain-stardog)" if x == "langchain" else "🔧 MCP Tools",
        # To re-enable MCP, uncomment above lines and adjust index as needed

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
            st.subheader(" Demo Mode")

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
                st.rerun()

            # Show description based on mode
            if query_mode == "simple":
                st.caption("Direct queries to Voicebox. Best for standard Q&A.")
            elif query_mode == "agent":
                st.caption("Agent decides which tools to use (Voicebox + Dist Calculator + Shipping Rate Calculator).")
                st.info("💡 Try: 'What's the shipping cost for {item} from Chicago to Detroit?'")
            elif query_mode == "chain":
                st.caption("Auto-translate queries and responses.")
                st.info("💡 Try asking in Spanish: '¿Cuáles son los mejores productos?'")

            st.divider()

        # Options
        st.subheader("Display Options")

        # Only show SPARQL checkbox in simple mode
        if st.session_state.query_mode == "simple":
            st.session_state.show_sparql = st.checkbox(
                "Show Generated SPARQL",
                value=st.session_state.show_sparql,
                help="Display the generated SPARQL query with results"
            )
        else:
            st.session_state.show_sparql = False

        # Only show tool calls/chain steps checkbox in agent/chain mode
        if st.session_state.query_mode in ["agent", "chain"]:
            # Default to True if not set or if mode just changed
            if "last_tool_calls_mode" not in st.session_state or st.session_state.last_tool_calls_mode != st.session_state.query_mode:
                st.session_state.show_tool_calls = True
                st.session_state.last_tool_calls_mode = st.session_state.query_mode
            st.session_state.show_tool_calls = st.checkbox(
                "Show Tool Calls / Chain Steps",
                value=st.session_state.show_tool_calls,
                help="Display intermediate tool calls or chain execution steps"
            )
        else:
            st.session_state.show_tool_calls = False


        # Clear conversation button
        if st.session_state.backend:
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

        # Only show example queries if backend is initialized
        if st.session_state.backend:
            st.divider()
            st.subheader("💡 Example Questions")
            st.caption("Click to use:")
            if st.session_state.query_mode == "simple":
                queries = EXAMPLE_QUERIES_SIMPLE
            elif st.session_state.query_mode == "agent":
                queries = EXAMPLE_QUERIES_AGENT
            else:
                queries = EXAMPLE_QUERIES_CHAIN
            for i, query in enumerate(queries):
                if st.button(query, key=f"example_{i}", use_container_width=True):
                    st.session_state.example_query = query
                    st.rerun()

def render_assistant_response(response):
    """Render the assistant's response, including answer, tool calls, chain steps, SPARQL, results, and conversation ID."""
    safe_answer = response.get("answer", response.get("text", "No answer generated.")).replace("$", "\\$")
    st.write(safe_answer)

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
                st.markdown(f"**Step {i}: {step['step']}")
                st.caption(f"Result: {step['result']}")
                st.divider()

    # Display SPARQL query if available and enabled
    if st.session_state.show_sparql and response.get("sparql"):
        with st.expander("🔍 Generated SPARQL Query"):
            st.code(response["sparql"], language="sparql")

    # Display raw results if available and enabled
    if st.session_state.show_results and response.get("results"):
        with st.expander("📊 Raw Results"):
            st.json(response["results"])

    # Show conversation ID if available
    if response.get("conversation_id"):
        st.caption(f"Conversation ID: {response['conversation_id'][:30]}...")

def render_message(role: str, content: Dict[str, Any]):
    """Render a chat message with optional SPARQL query, tool calls, or chain steps"""
    with st.chat_message(role):
        if role == "assistant":
            render_assistant_response(content)
        else:
            st.markdown(content)

def main():
    """Main application logic"""
    initialize_session_state()

    # Header with logo and title (Streamlit columns, robust)
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("static/logo.jpeg", width=108)
    with col_title:
        st.title("Stardog LangChain Demo")
    # st.caption(f"Powered by Stardog Cloud + {st.session_state.backend_type.title()}")

    # Render sidebar
    render_sidebar()

    # Check if backend is initialized
    if st.session_state.backend is None:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("👈 Please verify the configuration and initialize the app to get started.")

        # Show intro content
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("🚀 Getting Started")
            st.markdown("""
            1. **Get your API credentials** from [cloud.stardog.com](https://cloud.stardog.com)
            2. **Configure your backend** in the sidebar (LangChain or MCP)
            3. **Click Initialize** to connect to your Stardog Cloud instance
            4. **Start asking questions** about against your configured KG!
            """)

        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("🦜 LangChain Backend")
            st.markdown("""
            Uses the `langchain-stardog` package with Voicebox API.
            For installation: `pip install langchain-stardog`
            Use for: Production applications, agent workflows.
            """)
        #
        #     st.markdown("**MCP Backend**")
        #     st.caption("""
        #     Uses Model Context Protocol tools directly.
        #     Best for: IDE integrations, development tools.
        #     """)

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
    if prompt := (user_input or st.chat_input("Ask your question here...")):
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

                    render_assistant_response(response)

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
