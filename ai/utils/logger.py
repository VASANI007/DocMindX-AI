"""
    DocMindX AI - Clinical Audit and Structured Logging Engine
"""
import os
import logging
import sys

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "history", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

def setup_logger(name: str = "DocMindXAI", log_file: str = "DocMindX.log") -> logging.Logger:
    """Configures structured stream and file logging."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console Handler
        c_handler = logging.StreamHandler(sys.stdout)
        c_format = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)
        
        # File Handler
        try:
            file_path = os.path.join(LOGS_DIR, log_file)
            f_handler = logging.FileHandler(file_path, encoding="utf-8")
            f_format = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}')
            f_handler.setFormatter(f_format)
            logger.addHandler(f_handler)
        except Exception:
            pass
            
    return logger

logger = setup_logger()
