"""Append-only JSONL trade / event journal."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def append_journal(
    path: str,
    record: Dict[str, Any],
    event_type: Optional[str] = None,
) -> None:
    """
    Append one JSON object as a line to path.
    Creates parent directories if needed.
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    payload = dict(record)
    if event_type and "event" not in payload:
        payload["event"] = event_type
    if "ts" not in payload:
        payload["ts"] = datetime.now(timezone.utc).isoformat()

    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, default=str) + "\n")
    logger.debug("Journaled event to %s: %s", path, payload.get("event", "record"))
