"""
Logger module for backward compatibility.
Exports a standard Python logger.
"""
import logging

# Get or create logger
logger = logging.getLogger("ai_manus")

# Set default level if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

__all__ = ['logger']
