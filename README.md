# Stardog Knowledge Graph Intelligence Assistant

A Streamlit app for natural language queries over any Stardog knowledge graph. Supports both **LangChain** (via `langchain-stardog`) and **MCP (Model Context Protocol)** backends.

## Features

- LangChain backend: Uses `langchain-stardog` and Voicebox API
- Conversational UI with context and multi-turn support
- View generated SPARQL and raw results
- Example queries for your data

## Quick Start

### Prerequisites

- Python 3.9+
- Stardog Cloud API token
- A Stardog knowledge graph loaded (any domain)

### Installation

```bash
uv pip install -e .
cp .env.example .env
# Edit .env with your Stardog Cloud credentials
```

### Setup
Populate the required environment variables in the `.env` file or specify them on the UI:

```
SD_VOICEBOX_API_TOKEN=your-api-token
OPENAI_API_KEY=required-for-agent-tools-demo
SD_VOICEBOX_CLIENT_ID=optional-client-id
STARDOG_ENDPOINT=set-to-https://cloud.stardog.com/api-by-default
```

### Run the App

```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

## Usage

- Select backend in the sidebar (LangChain or MCP)
- Enter your API token and (optionally) client ID
- Click "Initialize App"
- Ask questions using the chat interface or example queries


## Project Structure

```
mcp-lc-demo/
├── app.py
├── backends/
│   ├── langchain_backend.py
│   └── mcp_backend.py
├── static/logo.jpeg
├── .env.example
└── README.md
```

## References

- [Stardog Cloud](https://cloud.stardog.com)
- [langchain-stardog](https://pypi.org/project/langchain-stardog/)
- [stardog-cloud-mcp](https://github.com/stardog-union/stardog-cloud-mcp)
- [LangChain Docs](https://python.langchain.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
