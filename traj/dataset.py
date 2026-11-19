"""Load the eval task set (and corpus/orders paths) from data/."""

import json
from pathlib import Path


def load_tasks(data_dir):
    with open(Path(data_dir) / "tasks.json") as f:
        return json.load(f)


def load_config(path):
    with open(path) as f:
        return json.load(f)
