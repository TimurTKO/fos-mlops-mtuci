from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "release_manager.py"
spec = importlib.util.spec_from_file_location("release_manager", MODULE_PATH)
release_manager = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(release_manager)


def test_env_round_trip(tmp_path: Path):
    path = tmp_path / ".env"
    expected = {
        "API_IMAGE": "course-api",
        "API_TAG": "candidate",
        "API_PORT": "8000",
        "EXPECTED_SERVICE_VERSION": "1.1.0",
        "RELEASE_CHANNEL": "candidate",
        "SIMULATE_STARTUP_FAILURE": "0",
    }
    release_manager.write_env(path, expected)
    assert release_manager.read_env(path) == expected


def test_read_env_ignores_comments_and_blank_lines(tmp_path: Path):
    path = tmp_path / ".env"
    path.write_text("# comment\n\nAPI_TAG=stable\nAPI_PORT=8000\n", encoding="utf-8")
    assert release_manager.read_env(path) == {"API_TAG": "stable", "API_PORT": "8000"}
