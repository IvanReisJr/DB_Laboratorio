import pytest
import time
import logging
from unittest.mock import MagicMock, patch
from src.decorators import retry_action

# Configure logging to capture output during tests
logging.basicConfig(level=logging.WARNING)

def test_retry_success():
    """Test that the function returns typically if no exception is raised."""
    mock_func = MagicMock(return_value="success")
    
    @retry_action(max_retries=3)
    def decorated_func():
        return mock_func()
    
    result = decorated_func()
    
    assert result == "success"
    assert mock_func.call_count == 1

def test_retry_eventual_success():
    """Test that the function retries and eventually succeeds."""
    mock_func = MagicMock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), "success"])
    
    @retry_action(max_retries=3, delay=0.1, exceptions=ValueError)
    def decorated_func():
        return mock_func()
    
    with patch("time.sleep") as mock_sleep:
        result = decorated_func()
        
    assert result == "success"
    assert mock_func.call_count == 3
    # Check if sleep was called with increasing delays (backoff)
    # limit checking to call count since we are not verifying exact backoff math here strictly
    assert mock_sleep.call_count == 2 

def test_retry_failure_max_retries():
    """Test that the function raises the last exception after max retries."""
    mock_func = MagicMock(side_effect=ValueError("Persistent Failure"))
    
    @retry_action(max_retries=3, delay=0.1, exceptions=ValueError)
    def decorated_func():
        return mock_func()
    
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(ValueError, match="Persistent Failure"):
            decorated_func()
            
    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2

def test_retry_specific_exception():
    """Test that it only retries on specified exceptions."""
    mock_func = MagicMock(side_effect=TypeError("Unexpected Error"))
    
    @retry_action(max_retries=3, delay=0.1, exceptions=ValueError)
    def decorated_func():
        return mock_func()
    
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(TypeError, match="Unexpected Error"):
            decorated_func()
            
    # Should fail immediately on TypeError (not in exceptions list)
    assert mock_func.call_count == 1
    assert mock_sleep.call_count == 0

def test_retry_logging(caplog):
    """Test that warnings are logged on retry."""
    mock_func = MagicMock(side_effect=[ValueError("Fail 1"), "success"])
    
    @retry_action(max_retries=2, delay=0.1)
    def decorated_func():
        return mock_func()
    
    with patch("time.sleep"):
        with caplog.at_level(logging.WARNING):
            decorated_func()
            
    assert "Tentativa 1/2 falhou" in caplog.text
    assert "ValueError" in caplog.text

def test_retry_backoff_logic():
    """Test that sleep times follow backoff factor."""
    mock_func = MagicMock(side_effect=[ValueError("1"), ValueError("2"), ValueError("3"), "success"])
    
    @retry_action(max_retries=4, delay=1.0, backoff_factor=2.0)
    def decorated_func():
        return mock_func()
    
    with patch("time.sleep") as mock_sleep:
        decorated_func()
        
    # Calls: 
    # 1. Fail -> sleep(1.0) -> next delay 2.0
    # 2. Fail -> sleep(2.0) -> next delay 4.0
    # 3. Fail -> sleep(4.0) -> next delay 8.0
    # 4. Success
    assert mock_sleep.call_args_list[0][0][0] == 1.0
    assert mock_sleep.call_args_list[1][0][0] == 2.0
    assert mock_sleep.call_args_list[2][0][0] == 4.0
