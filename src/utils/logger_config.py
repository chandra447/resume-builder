import os
import sys
from typing import Optional

from loguru import logger


def setup_logger(module_name: str, logs_dir: Optional[str] = None):  # type: ignore[no-untyped-def]
    """
    Configure Loguru logger with specific settings
    Args:
        module_name: usually passed as __name__ from the calling module
        logs_dir: directory for log files. Defaults to 'logs' in current directory
    Returns:
        logger: Configured logger instance bound to the module name
    """
    # Use provided logs_dir or default to 'logs' in current directory
    logs_dir = logs_dir or os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    configured_logger = logger.bind(name=module_name)

    # remove the default handler
    configured_logger.remove()

    # add console handler
    configured_logger.add(
        sys.stdout,
        format="""Service:SharePointSync | <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>
{exception}""",
        level="DEBUG",
        enqueue=True,
        diagnose=True,  # Show variables in the stack trace
        backtrace=True,  # Show full traceback
    )

    return configured_logger
