"""Unit tests for utility modules."""

import pytest
import asyncio
import json
from unittest.mock import patch, Mock
from atoll.utils.async_helpers import timeout_wrapper, retry_async
from atoll.utils.validators import validate_config, validate_tool_response
from atoll.utils.logger import get_logger, setup_logging


class TestAsyncHelpers:
    """Test async utility functions."""
    
    @pytest.mark.asyncio
    async def test_timeout_wrapper_success(self):
        """Test timeout wrapper with successful execution."""
        async def quick_task():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await timeout_wrapper(quick_task(), timeout_seconds=1.0)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_wrapper_timeout(self):
        """Test timeout wrapper with timeout."""
        async def slow_task():
            await asyncio.sleep(2.0)
            return "never returned"
        
        result = await timeout_wrapper(slow_task(), timeout_seconds=0.1)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test retry with successful execution."""
        call_count = 0
        
        async def flaky_task():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "success"
        
        result = await retry_async(flaky_task, max_retries=3, delay=0.01)
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_async_all_failures(self):
        """Test retry when all attempts fail."""
        async def failing_task():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await retry_async(failing_task, max_retries=2, delay=0.01)


class TestValidators:
    """Test validation utilities."""
    
    def test_validate_config_valid(self):
        """Test validating a valid config."""
        config = {"name": "test", "value": 123}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            }
        }
        
        assert validate_config(config, schema) is True
    
    def test_validate_config_invalid(self):
        """Test validating an invalid config."""
        config = {"name": 123}  # name should be string
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        assert validate_config(config, schema) is False
    
    def test_validate_tool_response_valid(self):
        """Test validating a valid tool response."""
        assert validate_tool_response({"result": "success"}) is True
        assert validate_tool_response("string response") is True
        assert validate_tool_response([1, 2, 3]) is True
    
    def test_validate_tool_response_invalid(self):
        """Test validating invalid tool responses."""
        assert validate_tool_response(None) is False
        
        # Create a non-serializable object
        class NonSerializable:
            def __init__(self):
                self.func = lambda x: x
        
        assert validate_tool_response(NonSerializable()) is False


class TestLogger:
    """Test logging utilities."""
    
    def test_get_logger(self):
        """Test getting a logger."""
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"
    
    def test_setup_logging(self):
        """Test setting up logging."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(level="DEBUG")
            mock_config.assert_called_once()
            
            # Check that DEBUG level was set
            call_args = mock_config.call_args
            assert call_args[1]['level'] == 10  # DEBUG level