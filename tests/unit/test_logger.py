import pytest
from unittest.mock import patch, MagicMock, call
import logging

from src.core.logger import setup_logger


class TestLogger:
    """Tests for the logger module"""
    
    @patch('src.core.logger.logging')
    def test_setup_logger(self, mock_logging):
        """Test setup_logger function"""
        # Mock the logging module
        mock_file_handler = MagicMock()
        mock_stream_handler = MagicMock()
        mock_logger = MagicMock()
        
        mock_logging.FileHandler.return_value = mock_file_handler
        mock_logging.StreamHandler.return_value = mock_stream_handler
        mock_logging.getLogger.return_value = mock_logger
        
        # Call the function
        result = setup_logger()
        
        # Verify that basicConfig was called with the correct parameters
        mock_logging.basicConfig.assert_called_once()
        args, kwargs = mock_logging.basicConfig.call_args
        
        # Check the arguments
        assert kwargs['level'] == logging.INFO
        assert kwargs['format'] == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert len(kwargs['handlers']) == 2
        
        # Verify that FileHandler was called with the correct parameters
        mock_logging.FileHandler.assert_called_once_with('medication_bot.log')
        
        # Verify that StreamHandler was called
        mock_logging.StreamHandler.assert_called_once()
        
        # Verify that getLogger was called with the correct parameters
        mock_logging.getLogger.assert_called_once()
        
        # Verify that the function returns the logger
        assert result == mock_logger
    
    @patch('src.core.logger.logging.basicConfig')
    @patch('src.core.logger.logging.FileHandler')
    @patch('src.core.logger.logging.StreamHandler')
    @patch('src.core.logger.logging.getLogger')
    def test_logger_integration(self, mock_get_logger, mock_stream_handler, mock_file_handler, mock_basic_config):
        """Test logger integration"""
        # Import the logger directly
        from src.core.logger import logger
        
        # Verify that the logger is properly initialized
        assert logger == mock_get_logger.return_value
