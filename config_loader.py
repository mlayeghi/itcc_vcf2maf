#!/usr/bin/env python3

import json
import os

from pathlib import Path



def load_config(path: str = "config.json") -> dict:
    global CONFIG
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open() as f:
        CONFIG = json.load(f)

    return CONFIG