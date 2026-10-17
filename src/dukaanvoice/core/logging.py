from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root application logger with structured, readable output."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
