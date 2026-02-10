"""
Stats Solver - Intelligent statistics method recommendation system.
"""

__version__ = "0.1.0"

import logging
import sys
from pathlib import Path


# Configure root logger
def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup application logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("stats_solver.log", encoding="utf-8"),
        ],
    )

    logger = logging.getLogger("stats_solver")
    logger.setLevel(log_level)

    return logger


# Initialize logger
logger = setup_logging()
