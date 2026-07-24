import os
import sys
from loguru import logger

def setup_logging():
    # Ensure logs output directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Standard Error Console Output
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG",
        enqueue=True
    )
    
    # Persistent Rotational File Output
    logger.add(
        "logs/cardioguard_backend.log",
        rotation="10 MB",
        retention="30 days",
        format=log_format,
        level="INFO",
        enqueue=True
    )

# Run logging initialization immediately
setup_logging()
