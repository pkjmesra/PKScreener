"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import os
import logging
import tempfile
from unittest.mock import patch
from pkscreener.pkscreenercli import setupLogger

# Positive test case - should log when shouldLog is True
def test_setupLogger_positive_shouldLogTrue():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=True)
        assert mock_logger.called

# Negative test case - should not log when shouldLog is False
def test_setupLogger_negative_shouldLogFalse():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=False)
        assert not mock_logger.called

# Positive test case - should log to specified log file path
def test_setupLogger_positive_logFilePath():
    log_file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=True)
        assert mock_logger.call_args[1]['log_file_path'] == log_file_path

# Positive test case - should log with trace when testbuild is True
def test_setupLogger_positive_traceTrue():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=True, trace=True)
        assert mock_logger.call_args[1]['trace'] is True

# Negative test case - should not log with trace when testbuild is False
def test_setupLogger_negative_traceFalse():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=True, trace=False)
        assert mock_logger.call_args[1]['trace'] is False

# Positive test case - should remove existing log file if it exists
def test_setupLogger_positive_removeLogFile():
    log_file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
    with patch('pkscreener.classes.log.setup_custom_logger'):
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value
            with patch('os.remove') as mock_remove:
                setupLogger(shouldLog=True)
                assert mock_remove.called_with(log_file_path)

# Negative test case - should not remove log file if it does not exist
def test_setupLogger_negative_doNotRemoveLogFile():
    with patch('pkscreener.classes.log.setup_custom_logger'):
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('os.remove') as mock_remove:
                setupLogger(shouldLog=True)
                assert not mock_remove.called

# Positive test case - should print log file path
def test_setupLogger_positive_printLogFilePath(capsys):
    log_file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
    with patch('pkscreener.classes.log.setup_custom_logger'):
        setupLogger(shouldLog=True)
        captured = capsys.readouterr()
        assert log_file_path in captured.out

# Negative test case - should not print log file path when shouldLog is False
def test_setupLogger_negative_doNotPrintLogFilePath(capsys):
    with patch('pkscreener.classes.log.setup_custom_logger'):
        setupLogger(shouldLog=False)
        captured = capsys.readouterr()
        assert captured.out == ""

# Positive test case - should set log level to DEBUG
def test_setupLogger_positive_logLevel():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=True)
        assert mock_logger.call_args[0][1] == logging.DEBUG

# Positive test case - should set filter to None
def test_setupLogger_positive_filter():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_logger:
        setupLogger(shouldLog=True)
        assert mock_logger.call_args[1]['filter'] is None
