"""Logging configuration."""

import logging
from rich.logging import RichHandler
from rich.console import Console

logger = logging.getLogger("claims_agent")
logger.setLevel(logging.INFO)
logger.handlers.clear()

console_handler = RichHandler(
    rich_tracebacks=True,
    console=Console(stderr=True),
    show_time=True,
    show_path=False
)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)
