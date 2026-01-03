import json
import pytest
from pathlib import Path
from src.etl.pipeline import _load_manifest

def test_load_manifest_validation(tmp_path):
    # Case 1: Valid manifest
    valid_manifest = [
        {"file_path": "test.csv", "type": "test", "timestamp": "2023-01-01T00:00:00"}
    ]
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(valid_manifest), encoding='utf-8')

    loaded = _load_manifest(tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["file_path"] == "test.csv"

    # Case 2: Invalid structure (dict instead of list)
    invalid_manifest_dict = {"file_path": "test.csv"}
    manifest_file.write_text(json.dumps(invalid_manifest_dict), encoding='utf-8')

    # Current behavior: might return the dict (which behaves like a list of keys) or fail?
    # If it returns a dict, len() is number of keys.
    # If we want it to return [], we need to validate.
    loaded = _load_manifest(tmp_path)
    # Ideally, this should be empty list if validation fails
    print(f"\nLoaded dict manifest type: {type(loaded)}")

    # Case 3: List of invalid items (strings instead of dicts)
    invalid_manifest_list = ["invalid_item"]
    manifest_file.write_text(json.dumps(invalid_manifest_list), encoding='utf-8')

    loaded = _load_manifest(tmp_path)
    print(f"Loaded list of strings manifest: {loaded}")

    # Case 4: Missing keys
    incomplete_manifest = [{"file_path": "test.csv"}] # missing type, timestamp
    manifest_file.write_text(json.dumps(incomplete_manifest), encoding='utf-8')
    loaded = _load_manifest(tmp_path)
    print(f"Loaded incomplete manifest: {loaded}")

if __name__ == "__main__":
    test_load_manifest_validation(Path("/tmp"))
