"""Shared helpers for AI providers that need to parse JSON out of chatty output."""
from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of a possibly chatty response."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"could not parse JSON from model output: {text[:200]!r}")