"""Runtime configuration loading for DynaX model implementations."""

from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "config.json"


def load_dynax_config() -> dict[str, object]:
    """Load the per-run config, falling back to the repository default."""
    config_path = Path(os.environ.get("DYNAX_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)
