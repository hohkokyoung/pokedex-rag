"""Helpers for reading the raw PokéAPI CSV dataset."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterator
from pathlib import Path

from app.core.config import REPO_ROOT

CSV_DIR = REPO_ROOT / "data" / "raw" / "pokeapi" / "csv"

ENGLISH_LANGUAGE_ID = 9


def read_csv(name: str) -> Iterator[dict[str, str]]:
    """Yield rows of ``<name>.csv`` as dicts. Raises if the file is missing."""
    path = CSV_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing CSV {path}. Download the PokéAPI dataset into data/raw/pokeapi/csv first."
        )
    with path.open(newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


_WHITESPACE = re.compile(r"\s+")


def clean_flavor_text(text: str) -> str:
    """Normalise PokéAPI flavour text: strip form-feeds/newlines, collapse spaces."""
    # A soft hyphen marks a word broken across lines ("con\xad\nvert"): rejoin it.
    text = re.sub("\xad\\s*", "", text)
    text = text.replace("\x0c", " ").replace("\n", " ").replace("\r", " ")
    return _WHITESPACE.sub(" ", text).strip()


def csv_dir_exists() -> bool:
    return CSV_DIR.exists() and (CSV_DIR / "pokemon.csv").exists()


def dataset_path() -> Path:
    return CSV_DIR
