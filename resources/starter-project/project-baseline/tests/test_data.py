from pathlib import Path

import pytest

from mlops_course.data import load_contract, load_dataset

CONTRACT = Path("configs/data_contract.json")


def test_reference_dataset_matches_contract():
    contract = load_contract(CONTRACT)
    frame = load_dataset("data/train.csv", contract)
    assert len(frame) >= contract["minimum_rows"]


def test_bad_schema_is_rejected():
    contract = load_contract(CONTRACT)
    with pytest.raises((ValueError, TypeError)):
        load_dataset("data/incident_bad_schema.csv", contract)
