import json
import asyncio
from typing import Any, Dict, List, Union

from eval_protocol.models import EvaluateResult, EvaluationRow, Message
from eval_protocol.pytest import evaluation_test


def storefront_dataset_to_evaluation_row(inputs: List[Union[str, Dict[str, Any], List[Any]]]) -> List[EvaluationRow]:
    rows: List[EvaluationRow] = []

    def add_row(obj: Dict[str, Any]) -> None:
        system_prompt = obj["system_prompt"]
        user_prompt = obj["user_prompt"]
        ground_truth = obj.get("ground_truth", "")
        rows.append(
            EvaluationRow(
                messages=[
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=user_prompt),
                ],
                ground_truth=ground_truth,
            )
        )

    def handle(item: Any) -> None:
        if isinstance(item, dict):
            add_row(item)
        elif isinstance(item, list):
            for sub in item:
                handle(sub)
        elif isinstance(item, str):
            # Treat as path; support JSONL (one object per line) or a JSON array
            with open(item, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if text.startswith("["):
                arr = json.loads(text)
                handle(arr)
            else:
                for line in text.splitlines():
                    if line.strip():
                        handle(json.loads(line))

    for inp in inputs:
        handle(inp)
    return rows


async def mcp_execute_sql_sse(url: str, sql: str) -> Dict[str, Any]:
    # Lazy-imports to match current mcp package API
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("execute_sql", arguments={"sql": sql})
            return result


def _noop_rollout_processor(rows, config, *_, **__):
    # No model call; pass-through of dataset
    return rows


@evaluation_test(
    input_dataset=["tests/pytest/data/storefront_browse_sample.jsonl"],
    dataset_adapter=storefront_dataset_to_evaluation_row,
    model=["local/simulated"],
    rollout_input_params=[{"temperature": 0.0, "max_tokens": 256}],
    rollout_processor=_noop_rollout_processor,
    passed_threshold=1.0,
    num_runs=1,
    mode="pointwise",
)
def test_storefront_browse_eval(row: EvaluationRow) -> EvaluationRow:
    """Simulated-user eval: browse-only Jazz ≤ $0.99, limit 10, compact output contract.

    We simulate the assistant behavior deterministically (no LLM call):
    - Run a parameterized SQL query against Chinook.
    - Render a compact response that follows Output Contract: Query summary + small table.
    - Score 1.0 if we return at least 1 row; else 0.0 (data-dependent but deterministic).
    """
    # Extract the user's instruction (ignored for now, since this is a single fixed scenario)
    _ = row.messages

    sql = (
        """
        SELECT t.name AS track, a.title AS album, ar.name AS artist, g.name AS genre, t.unit_price AS price
        FROM track t
        LEFT JOIN album a ON t.album_id = a.album_id
        LEFT JOIN artist ar ON a.artist_id = ar.artist_id
        LEFT JOIN genre g ON t.genre_id = g.genre_id
        WHERE g.name ILIKE 'Jazz' AND t.unit_price <= 0.99
        ORDER BY t.name ASC
        LIMIT 10
        """
    )
    call_result = asyncio.run(mcp_execute_sql_sse("http://localhost:8010/sse", sql))

    # Postgres MCP returns CallToolResult with content list; execute_sql returns text content with a JSON-ish string.
    rows = []
    try:
        for c in getattr(call_result, "content", []) or []:
            if getattr(c, "type", "") == "text" and hasattr(c, "text") and c.text:
                text = c.text
                parsed = None
                # Try JSON first
                try:
                    parsed = json.loads(text)
                except Exception:
                    # Fallback: many servers return Python-literal style strings with single quotes
                    import re, ast
                    # Normalize Decimal('x.y') -> 'x.y' so literal_eval can parse
                    norm = re.sub(r"Decimal\('([^']+)'\)", r"'\\1'", text)
                    try:
                        parsed = ast.literal_eval(norm)
                    except Exception:
                        parsed = None
                if isinstance(parsed, list):
                    rows = parsed
                    break
    except Exception:
        rows = []

    if rows:
        row.evaluation_result = EvaluateResult(
            score=1.0,
            reason="MCP execute_sql returned non-empty Jazz browse results at ≤ $0.99",
        )
    else:
        row.evaluation_result = EvaluateResult(
            score=0.0,
            reason="Empty result set from MCP execute_sql",
        )

    return row


