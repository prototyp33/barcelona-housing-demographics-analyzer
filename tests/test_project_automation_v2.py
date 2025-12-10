import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".github" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import project_automation_v2 as pav2  # noqa: E402


def test_project_cache_is_singleton() -> None:
    """
    Verifica que ProjectCache devuelva siempre la misma instancia.
    """
    cache_a = pav2.ProjectCache()
    cache_b = pav2.ProjectCache()
    assert cache_a is cache_b


def test_get_item_id_for_issue_optimized_parses_response() -> None:
    """
    Verifica que el lookup directo retorne el item_id desde la respuesta GraphQL.
    """
    mock_gh = MagicMock()
    response: Dict[str, Any] = {
        "node": {
            "items": {
                "nodes": [
                    {
                        "id": "item123",
                        "content": {"number": 42},
                    }
                ]
            }
        }
    }
    mock_gh.execute_query.return_value = response

    item_id = pav2.get_item_id_for_issue_optimized(
        gh=mock_gh,
        project_id="proj1",
        issue_number=42,
        owner="owner",
        repo="repo",
    )

    assert item_id == "item123"
    mock_gh.execute_query.assert_called_once()
    call_args, call_kwargs = mock_gh.execute_query.call_args
    variables: Dict[str, Any] = {}
    if call_kwargs and "variables" in call_kwargs:
        variables = call_kwargs["variables"]
    elif len(call_args) >= 2 and isinstance(call_args[1], dict):
        variables = call_args[1]
    assert variables["queryString"] == "repo:owner/repo number:42 is:issue"


def test_update_fields_batch_builds_single_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifica que la mutación batch incluya múltiples aliases en una sola llamada.
    """
    mock_gh = MagicMock()
    captured_mutations = {}

    def fake_execute_query(mutation: str, variables: Dict[str, Any] | None = None) -> Dict[str, Any]:
        captured_mutations["mutation"] = mutation
        return {"data": {}}

    mock_gh.execute_query.side_effect = fake_execute_query

    updates = [
        pav2.FieldUpdate(
            alias="field0",
            field_id="fid0",
            value_payload='singleSelectOptionId: "opt0"',
        ),
        pav2.FieldUpdate(
            alias="field1",
            field_id="fid1",
            value_payload='text: "hello"',
        ),
    ]

    pav2.update_fields_batch(
        gh=mock_gh,
        project_id="proj1",
        item_id="item1",
        updates=updates,
    )

    assert "mutation" in captured_mutations
    mutation = captured_mutations["mutation"]
    assert "field0:" in mutation
    assert "field1:" in mutation
    assert mutation.count("updateProjectV2ItemFieldValue") == 2

