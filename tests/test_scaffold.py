import os
from pathlib import Path
from dotenv import load_dotenv

def test_env_has_sec_key():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    assert os.environ.get("SEC_OPENDATA_API_KEY"), "SEC_OPENDATA_API_KEY missing from .env"

def test_directory_layout_exists():
    root = Path(__file__).resolve().parent.parent
    for p in ["data/raw", "data/processed", "notebooks", "benchmarks/monte_carlo"]:
        assert (root / p).is_dir(), f"missing directory: {p}"
