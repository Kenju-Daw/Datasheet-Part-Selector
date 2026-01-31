"""
Logging configuration for Datasheet Part Selector backend

Logs to both console and file for easier debugging.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Log file path
log_file = logs_dir / f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create named loggers
def get_logger(name: str) -> logging.Logger:
    """Get a named logger"""
    return logging.getLogger(name)

# Suppress noisy libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

print(f"📝 Logging to: {log_file}")
