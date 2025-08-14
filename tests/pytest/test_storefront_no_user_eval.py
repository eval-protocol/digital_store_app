import os
import json
import pytest
from typing import Any, Dict, List, Union

from eval_protocol.models import EvaluateResult, EvaluationRow, Message
from eval_protocol.pytest import evaluation_test, default_single_turn_rollout_processor


def single_prompt_adapter(inputs: List[Union[str, Dict[str, Any], List[Any]]]) -> List[EvaluationRow]:
	out: List[EvaluationRow] = []

	def add_row(obj: Dict[str, Any]) -> None:
		system_prompt = obj.get("system_prompt")
		system_prompt_path = obj.get("system_prompt_path")
		if system_prompt is None and system_prompt_path:
			with open(system_prompt_path, "r", encoding="utf-8") as f:
				system_prompt = f.read()
		out.append(
			EvaluationRow(
				messages=[
					Message(role="system", content=system_prompt),
					Message(role="user", content=obj["user_prompt"]),
				],
			)
		)

	def handle(item: Any) -> None:
		if isinstance(item, dict):
			add_row(item)
		elif isinstance(item, list):
			for sub in item:
				handle(sub)
		elif isinstance(item, str):
			with open(item, "r", encoding="utf-8") as f:
				text = f.read().strip()
			if text.startswith("["):
				import json as _json
				arr = _json.loads(text)
				handle(arr)
			else:
				for line in text.splitlines():
					if line.strip():
						import json as _json
						handle(_json.loads(line))

	for inp in inputs:
		handle(inp)
	return out


@evaluation_test(
	input_dataset=["tests/pytest/data/storefront_basic_prompt.jsonl"],
	dataset_adapter=single_prompt_adapter,
	completion_params=[{"model": "fireworks_ai/accounts/fireworks/models/gpt-oss-120b#pyroworks/wzflb9s1", "temperature": 0.0}],
	rollout_processor=default_single_turn_rollout_processor,
	mcp_config_path="mcp.json",
	passed_threshold=None,
	num_runs=1,
	mode="pointwise",
)
def test_storefront_basic_prompt(row: EvaluationRow) -> EvaluationRow:
	"""No simulated user; just ensure the assistant adheres to Output Contract scaffolding."""
	print("show row.messages", row.messages)
	assistant = next((m for m in row.messages if m.role == "assistant"), None)
	content = (assistant.content or "") if assistant else ""
	score = 1.0 if ("Query summary" in content) else 0.0
	row.evaluation_result = EvaluateResult(score=score, reason=("Includes Query summary" if score == 1.0 else "Missing Query summary"))
	return row


