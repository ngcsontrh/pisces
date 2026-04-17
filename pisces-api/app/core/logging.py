"""Logging configuration for the translation pipeline.

Call ``setup_logging()`` once at process startup (in ``main.py``) to configure
a consistent log format across all modules.  All modules should use::

    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a human-readable format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
