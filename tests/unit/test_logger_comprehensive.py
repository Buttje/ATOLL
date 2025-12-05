"""Comprehensive tests for logger module."""

import pytest
import logging
from unittest.mock import patch, Mock
from atoll.utils.logger import get_logger, setup_logging


class TestLoggerComprehensive:
    """Comprehensive tests for logger."""
    
    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
    
    def test_get_logger_same_name_returns_same_instance(self):
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2
    
    @patch('logging.basicConfig')
    def test_setup_logging_default_level(self, mock_basic_config):
        """Test setup_logging with default level."""
        setup_logging()
        mock_basic_config.assert_called_once()
    
    @patch('logging.basicConfig')
    def test_setup_logging_custom_level(self, mock_basic_config):
        """Test setup_logging with custom level."""
        setup_logging(level="DEBUG")
        mock_basic_config.assert_called_once()
    
    @patch('logging.basicConfig')
    def test_setup_logging_with_file(self, mock_basic_config, tmp_path):
        """Test setup_logging with log file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)
        mock_basic_config.assert_called_once()
        assert log_file.parent.exists()
    
    @patch('logging.basicConfig')
    def test_setup_logging_custom_format(self, mock_basic_config):
        """Test setup_logging with custom format."""
        custom_format = "%(levelname)s - %(message)s"
        setup_logging(format_string=custom_format)
        mock_basic_config.assert_called_once()
        mock_basic_config.assert_called_once()