# LangChain Integration Demo with Stardog Voicebox

A Streamlit app for natural language queries over any Stardog knowledge graph using Voicebox. 

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

- Enter your API token and (optionally) client ID
- Click "Initialize App"
- Select the query mode and ask questions using the chat interface or example queries

## Project Structure

```
mcp-lc-demo/
├── app.py
├── pyproject.toml
├── README.md
├── backends/
│   ├── __init__.py
│   ├── langchain_backend.py
│   ├── langchain_tools.py
│   ├── mcp_backend.py
├── static/
│   └── logo.jpeg
```

## References

- [Stardog Cloud](https://cloud.stardog.com)
- [langchain-stardog](https://pypi.org/project/langchain-stardog/)
- [stardog-cloud-mcp](https://github.com/stardog-union/stardog-cloud-mcp)
- [LangChain Docs](https://python.langchain.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
