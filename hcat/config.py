import json
import os
from pathlib import Path

DATA_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data"

CONFIG_PATH = DATA_DIR / "config.json"


DEFAULT_CONFIG = {
    "default_scan_months": 3,
    "max_workers": 3,
    "sleep_between_videos": 0.5,
    "sleep_between_channels": 2.0,
    "ytdlp_timeout": 60,
    "holodex_api_key": "",
}


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
