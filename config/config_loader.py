from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "model_config.yaml"

def load_model_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
