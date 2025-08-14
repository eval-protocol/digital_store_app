## Digital Store App (Eval Protocol + MCP)

Build and test a database-aware storefront assistant using Eval Protocol and a Postgres MCP server. This repo follows a test-driven agent development workflow.

For background and a walkthrough, see the blog post: [Test-Driven Agent Development with Eval Protocol](https://fireworks.ai/blog/test-driven-agent-development).

### Requirements
- Python 3.10+
- Docker (for Postgres + MCP server)
- uv (recommended) or pip

### Setup
1) Create and activate a virtual environment
```bash
uv venv .venv
source .venv/bin/activate
```

2) Install in editable mode
```bash
uv pip install -e .
```

3) (Optional) Start Postgres + MCP server
```bash
# Starts Postgres (Chinook) and the Postgres MCP server
docker compose up -d
```

### Running tests
- Fast local tests (no external model calls):
```bash
pytest -q
```

- Full MCP/agent integration tests (require Docker up and a model key):
```bash
export RUN_MCP_EVAL=1
export FIREWORKS_API_KEY=your_fireworks_api_key
pytest -q
```

- Run a single test with a summary line printed:
```bash
EP_PRINT_SUMMARY=1 pytest tests/pytest/test_storefront_agent_eval.py::test_storefront_agent_browse -q
```

- Emit a JSON summary artifact for CI:
```bash
EP_SUMMARY_JSON=artifacts/ pytest -q
# writes JSON files under ./artifacts/
```

### Useful environment variables
- RUN_MCP_EVAL=1: enable MCP/agent integration test suite
- FIREWORKS_API_KEY: API key for Fireworks models used in agent tests
- EP_PRINT_SUMMARY=1: print a concise summary line to stdout
- EP_SUMMARY_JSON=<path or dir>: write machine-readable summary JSON(s)
- EP_MAX_DATASET_ROWS=<N|none>: clamp dataset/messages length per run

### Services
- docker-compose.yml defines:
  - db: Postgres 16 with Chinook schema/data
  - mcp: Postgres MCP server exposing tools (e.g., execute_sql) on port 8010

### Project structure
- tests/pytest/: evaluation tests (batch and pointwise)
- prompts/: system prompt(s)
- external/: third-party assets (Chinook database SQL, MCP server repo)
- scripts/: helper scripts (MCP proxy, etc.)

### Troubleshooting
- Editable install errors about "Multiple top-level packages" were resolved by explicitly disabling package discovery in pyproject.toml.
- If MCP tests fail to connect, ensure `docker compose ps` shows both db and mcp healthy.
- The agent tests hit real models—credentials and network access are required.
