"""Logging configuration.

Call ``configure_logging`` once at startup. Policy (see docs/security.md):
never log secrets, tokens, connection strings, or full financial/personal
details. Log *references* (TXN-84721, CASE-1001) and outcomes, not payloads.
"""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger once; safe to call repeatedly."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    root.setLevel(level.upper())
