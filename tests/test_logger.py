"""Tests for src/logger.py — structured logging, formatters, OperationLogger."""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.logger import (
    StructuredFormatter,
    HumanReadableFormatter,
    OperationLogger,
    get_logger,
    setup_logging,
)


# ---------------------------------------------------------------------------
# StructuredFormatter
# ---------------------------------------------------------------------------
class TestStructuredFormatter:
    def test_basic_fields(self):
        fmt = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=1,
            msg="hello world", args=(), exc_info=None,
        )
        result = json.loads(fmt.format(record))
        assert result["level"] == "INFO"
        assert result["logger"] == "test"
        assert result["message"] == "hello world"
        assert result["line"] == 1
        assert "timestamp" in result

    def test_extra_fields(self):
        fmt = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=1,
            msg="op done", args=(), exc_info=None,
        )
        record.user_id = "alice"
        record.action = "add_record"
        record.resource_type = "accounting"
        record.resource_id = 42
        record.duration_ms = 123.45
        record.error = "some error"
        result = json.loads(fmt.format(record))
        assert result["user_id"] == "alice"
        assert result["action"] == "add_record"
        assert result["resource_type"] == "accounting"
        assert result["resource_id"] == 42
        assert result["duration_ms"] == 123.45
        assert result["error"] == "some error"

    def test_exception_info(self):
        fmt = StructuredFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=1,
            msg="failed", args=(), exc_info=exc_info,
        )
        result = json.loads(fmt.format(record))
        assert "exception" in result
        assert "ValueError" in result["exception"]
        assert "boom" in result["exception"]


# ---------------------------------------------------------------------------
# HumanReadableFormatter
# ---------------------------------------------------------------------------
class TestHumanReadableFormatter:
    def test_basic_format(self):
        fmt = HumanReadableFormatter()
        record = logging.LogRecord(
            name="mylogger", level=logging.WARNING, pathname="", lineno=5,
            msg="watch out", args=(), exc_info=None,
        )
        result = fmt.format(record)
        assert "WARNING" in result
        assert "mylogger" in result
        assert "watch out" in result

    def test_extra_fields(self):
        fmt = HumanReadableFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=1,
            msg="done", args=(), exc_info=None,
        )
        record.user_id = "bob"
        record.action = "delete"
        record.resource_type = "todo"
        record.resource_id = 7
        record.duration_ms = 50.0
        result = fmt.format(record)
        assert "user=bob" in result
        assert "action=delete" in result
        assert "type=todo" in result
        assert "id=7" in result
        assert "duration=50.0ms" in result

    def test_exception_info(self):
        fmt = HumanReadableFormatter()
        try:
            raise RuntimeError("oops")
        except RuntimeError:
            import sys
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=1,
            msg="crash", args=(), exc_info=exc_info,
        )
        result = fmt.format(record)
        assert "RuntimeError" in result
        assert "oops" in result


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------
class TestSetupLogging:
    def test_structured_formatter(self):
        setup_logging(level="DEBUG", structured=True)
        root = logging.getLogger()
        handler = root.handlers[-1]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_human_readable_formatter(self):
        setup_logging(level="INFO", structured=False)
        root = logging.getLogger()
        handler = root.handlers[-1]
        assert isinstance(handler.formatter, HumanReadableFormatter)

    def test_file_handler_created(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        setup_logging(log_file=log_file)
        root = logging.getLogger()
        assert len(root.handlers) >= 2
        file_handler = root.handlers[-1]
        assert isinstance(file_handler, logging.FileHandler)
        assert file_handler.baseFilename.endswith("test.log")

    def test_file_handler_structured_format(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        setup_logging(log_file=log_file)
        root = logging.getLogger()
        file_handler = root.handlers[-1]
        assert isinstance(file_handler.formatter, StructuredFormatter)


# ---------------------------------------------------------------------------
# OperationLogger
# ---------------------------------------------------------------------------
class TestOperationLogger:
    def test_normal_flow(self):
        logger = get_logger("test.oplogger")
        with OperationLogger(logger, "test_op", user_id="u1",
                             resource_type="todo", resource_id=5) as op:
            op.resource_id = 5
        # No exception = success

    def test_exception_flow(self):
        logger = get_logger("test.oplogger.exception")
        with pytest.raises(ValueError, match="boom"):
            with OperationLogger(logger, "failing_op", user_id="u1") as op:
                raise ValueError("boom")

    def test_build_extra_with_all_fields(self):
        logger = get_logger("test.build_extra")
        op = OperationLogger(logger, "op", user_id="alice",
                             resource_type="accounting", resource_id=99)
        extra = op._build_extra()
        assert extra == {
            "user_id": "alice",
            "resource_type": "accounting",
            "resource_id": 99,
        }

    def test_build_extra_no_fields(self):
        logger = get_logger("test.build_extra_empty")
        op = OperationLogger(logger, "op")
        extra = op._build_extra()
        assert extra == {}

    def test_build_extra_partial_fields(self):
        logger = get_logger("test.build_extra_partial")
        op = OperationLogger(logger, "op", user_id="bob")
        extra = op._build_extra()
        assert extra == {"user_id": "bob"}
        assert "resource_type" not in extra
        assert "resource_id" not in extra


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------
class TestGetLogger:
    def test_returns_named_logger(self):
        logger = get_logger("my.module")
        assert logger.name == "my.module"
        assert isinstance(logger, logging.Logger)
