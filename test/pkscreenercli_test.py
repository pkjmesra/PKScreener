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
import logging
from unittest.mock import patch

import pytest

from pkscreener import pkscreenercli
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger
from pkscreenr.globals import shutdown

# Mocking necessary functions or dependencies
@pytest.fixture(autouse=True)
def mock_dependencies():
    pkscreenercli.args.exit = True
    pkscreenercli.args.answerdefault = 'Y'
    with patch('pkscreener.globals.main'):
        with patch('pkscreener.classes.Utility.tools.clearScreen'):
            yield

def patched_caller(*args, **kwargs):
    if kwargs is not None:
        userArgs = kwargs["userArgs"]
        maxCount = userArgs.options
        pkscreenercli.args.options = str(int(maxCount) - 1)
        if int(pkscreenercli.args.options) == 0:
            pkscreenercli.args.exit = True
    else:
        pkscreenercli.args.exit = True

# Positive test case - Test if pkscreenercli function runs in download-only mode
def test_pkscreenercli_download_only_mode():
    with patch('pkscreener.globals.main') as mock_main:
        with pytest.raises(SystemExit):
            pkscreenercli.args.download = True
            pkscreenercli.pkscreenercli()
            mock_main.assert_called_once_with(downloadOnly=True, startupoptions=None, defaultConsoleAnswer="Y", user=None)

# Positive test case - Test if pkscreenercli function runs with cron interval
def test_pkscreenercli_with_cron_interval():
    pkscreenercli.args.croninterval = "3"
    with patch('pkscreener.globals.main', new=patched_caller) as mock_main:
        with patch('pkscreener.classes.Utility.tools.isTradingTime') as mock_is_trading_time:
            mock_is_trading_time.return_value = True
            pkscreenercli.args.exit = False
            pkscreenercli.args.options="2"
            with pytest.raises(SystemExit):
                pkscreenercli.pkscreenercli()
                assert mock_main.call_count == 2

# Positive test case - Test if pkscreenercli function runs without cron interval
def test_pkscreenercli_with_cron_interval_preopen():
    pkscreenercli.args.croninterval = "3"
    with patch('pkscreener.globals.main', new=patched_caller) as mock_main:
        with patch('pkscreener.classes.Utility.tools.isTradingTime') as mock_is_trading_time:
            mock_is_trading_time.return_value = False
            with patch('pkscreener.classes.Utility.tools.secondsBeforeOpenTime') as mock_secondsBeforeOpenTime:
                mock_secondsBeforeOpenTime.return_value = -3601
                pkscreenercli.args.exit = False
                pkscreenercli.args.options="1"
                with pytest.raises(SystemExit):
                    pkscreenercli.pkscreenercli()
                    assert mock_main.call_count == 1

# Positive test case - Test if pkscreenercli function runs without any errors
def test_pkscreenercli_exits():
    with patch('pkscreener.globals.main') as mock_main:
        with pytest.raises(SystemExit):
            pkscreenercli.pkscreenercli()
            mock_main.assert_called_once()

# Positive test case - Test if setupLogger function is called when logging is enabled
def test_setupLogger_logging_enabled():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_setup_logger:
        with patch('pkscreener.classes.Utility.tools.isTradingTime') as mock_is_trading_time:
            with pytest.raises(SystemExit):
                pkscreenercli.args.log = True
                mock_is_trading_time.return_value = False
                pkscreenercli.pkscreenercli()
                mock_setup_logger.assert_called_once()
                assert default_logger().level == logging.DEBUG

# Negative test case - Test if setupLogger function is not called when logging is disabled
def test_setupLogger_logging_disabled():
    with patch('pkscreener.classes.log.setup_custom_logger') as mock_setup_logger:
        with patch('pkscreener.classes.Utility.tools.isTradingTime') as mock_is_trading_time:
            mock_is_trading_time.return_value = False
            mock_setup_logger.assert_not_called()
            assert default_logger().level == logging.NOTSET

# Positive test case - Test if pkscreenercli function runs in test-build mode
def test_pkscreenercli_test_build_mode():
    with patch('builtins.print') as mock_print:
        pkscreenercli.args.testbuild = True
        pkscreenercli.pkscreenercli()
        mock_print.assert_called_with(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Started in TestBuild mode!"
            + colorText.END
        )

def test_pkscreenercli_prodbuild_mode():
    with patch('pkscreener.pkscreenercli.disableSysOut') as mock_disableSysOut:
        pkscreenercli.args.prodbuild = True
        with pytest.raises(SystemExit):
            pkscreenercli.pkscreenercli()
            mock_disableSysOut.assert_called_once()
    try:
        import signal
        signal.signal(signal.SIGBREAK, shutdown)
        signal.signal(signal.SIGTERM,shutdown)
    except Exception:
        pass
