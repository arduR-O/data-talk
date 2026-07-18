import pytest
import contextvars
from agentic_orchestrator import DebugLogger, ThreadSafeDebugLogger, _debug_logger_var

def test_debug_logger_init():
    logger = DebugLogger(enabled=False)
    assert logger.enabled is False
    assert len(logger.logs) == 0

def test_debug_logger_logging():
    logger = DebugLogger(enabled=True)
    logger._log("INFO", "Test log message", {"some": "data"})
    assert len(logger.logs) == 1
    assert logger.logs[0]["level"] == "INFO"
    assert logger.logs[0]["message"] == "Test log message"
    assert logger.logs[0]["data"] == {"some": "data"}

def test_thread_safe_debug_logger():
    # Verify that the ThreadSafeDebugLogger creates and uses contextvar-based loggers
    proxy = ThreadSafeDebugLogger()
    
    # 1. Accessing current sets default
    logger1 = proxy.current
    assert isinstance(logger1, DebugLogger)
    
    # 2. Creating a new context session isolates logs
    token = _debug_logger_var.set(DebugLogger(enabled=True))
    logger2 = proxy.current
    assert logger2 is not logger1
    
    # Test delegate logs
    proxy._log("TOOL", "Proxy log")
    assert len(proxy.logs) == 1
    assert proxy.logs[0]["message"] == "Proxy log"
    assert len(logger1.logs) == 0  # Isolated
    
    # Reset context
    _debug_logger_var.reset(token)
    assert proxy.current is logger1
