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
import unittest
import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
from pkscreener.classes.ConsoleMenuUtility import PKConsoleTools
from PKDevTools.classes.ColorText import colorText

class TestPKConsoleTools(unittest.TestCase):

    @patch('os.system')
    @patch('platform.platform',return_value="Windows")
    @pytest.mark.skip(reason="API has changed")
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_clear_screen(self, mock_print, mock_platform, mock_system):
        PKConsoleTools.clearScreen(clearAlways=True)
        mock_system.assert_called()
        mock_print.assert_called()

    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.Utils.random_user_agent', return_value="Mozilla/5.0")
    @patch('pkscreener.classes.ConsoleUtility.PKConsoleTools.fetcher.fetchURL')
    @patch('platform.platform',return_value="Windows")
    def test_show_dev_info(self, mock_platform, mock_fetch, mock_user_agent, mock_print):
        mock_fetch.return_value = MagicMock(status_code=200, text='<text xmlns="http://www.w3.org/2000/svg" x="905" y="140" transform="scale(.1)" textLength="270">599k</text>')
        result = PKConsoleTools.showDevInfo()
        self.assertIn("599k", result)
        mock_print.assert_called()

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.isdir', return_value=True)
    @patch('pandas.DataFrame.to_pickle')
    def test_set_last_screened_results_success(self, mock_pickle, mock_isdir, mock_open):
        df = pd.DataFrame({'Stock': ['AAPL', 'GOOGL']})
        PKConsoleTools.setLastScreenedResults(df, df_save=df, choices="test")
        mock_pickle.assert_called()
        mock_open.assert_called()

    @patch('builtins.open', new_callable=mock_open, read_data="AAPL,GOOGL")
    @patch('pandas.read_pickle', return_value=pd.DataFrame({'Stock': ['AAPL', 'GOOGL']}))
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('platform.platform',return_value="Windows")
    def test_get_last_screened_results_success(self, mock_platform, mock_print, mock_read_pickle, mock_open):
        PKConsoleTools.getLastScreenedResults()
        mock_read_pickle.assert_called()
        mock_print.assert_called()

    def test_formatted_backtest_output_success(self):
        result = PKConsoleTools.formattedBacktestOutput(85)
        self.assertIn(colorText.GREEN, result)
        
        result = PKConsoleTools.formattedBacktestOutput(65)
        self.assertIn(colorText.WARN, result)

        result = PKConsoleTools.formattedBacktestOutput(45)
        self.assertIn(colorText.FAIL, result)

    def test_get_formatted_backtest_summary(self):
        result = PKConsoleTools.getFormattedBacktestSummary("85%", columnName="Overall")
        self.assertIn(colorText.GREEN, result)

        result = PKConsoleTools.getFormattedBacktestSummary("-15%", pnlStats=True, columnName="Overall")
        self.assertIn(colorText.FAIL, result)
