"""Regression checks for report denominators and retained classification evidence."""

import copy
import json
from pathlib import Path

import pytest

from opentrons_ai.research.build_paper import validate_evidence

pytest.importorskip("numpy")


def evidence():
    path = Path(__file__).resolve().parents[1] / "docs/research/data/evidence.json"
    return json.loads(path.read_text())


def test_reviewed_evidence_reconciles():
    validate_evidence(evidence())


def test_rejects_movement_duration_substituted_for_block_duration():
    data = copy.deepcopy(evidence())
    row = data["runs"][0]["rhythm"][-1]
    row["notes_per_s"] = 16 / sum(end - start for start, end in row["move_times_s"])
    with pytest.raises(ValueError, match="denominator"):
        validate_evidence(data)


def test_rejects_classification_count_without_matching_predictions():
    data = copy.deepcopy(evidence())
    data["runs"][0]["rhythm"][-1]["correct"] += 1
    with pytest.raises(ValueError, match="predictions"):
        validate_evidence(data)
