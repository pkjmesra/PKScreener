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
import pytest
import os
from configparser import ConfigParser
from unittest.mock import patch
from pkscreener.classes.ConfigManager import tools
from PKDevTools.classes.log import default_logger
from PKDevTools.classes import Archiver

@pytest.fixture
def config_parser():
    parser = ConfigParser()
    return parser

def test_deleteFileWithPattern(config_parser):
    tool = tools()
    with patch('glob.glob') as mock_glob, patch('os.remove') as mock_os:
        mock_glob.return_value = ['file1.pkl', 'file2.pkl']
        path = Archiver.get_user_data_dir().replace(f"results{os.sep}Data","actions-data-download")
        tool.deleteFileWithPattern(pattern='*.pkl', excludeFile="*.txt")
        mock_os.assert_called_with(f'{path}{os.sep}file2.pkl')
        assert mock_os.call_count >= 2
        tool.deleteFileWithPattern(pattern='*.pkl', excludeFile=None)
        mock_os.assert_called_with(f'{path}{os.sep}file2.pkl')

# def test_setConfig_default(config_parser):
#     tool = tools()
#     tool.setConfig(config_parser, default=True, showFileCreatedText=False)
#     tool.default_logger = default_logger()
#     assert tool.default_logger is not None
#     assert config_parser.get('config', 'period') in ['1y','1d']
#     assert config_parser.get('config', 'daysToLookback') in ['22','50']
#     assert config_parser.get('config', 'duration') in ['1d','1m','1h']
#     assert float(config_parser.get('filters', 'minPrice')) >= 5
#     assert '50000' in config_parser.get('filters', 'maxPrice')
#     assert config_parser.get('filters', 'volumeRatio') == '2.5'
#     assert config_parser.get('filters', 'consolidationPercentage') in ['10','10.0']
#     assert config_parser.get('config', 'shuffle') == 'y'
#     assert config_parser.get('config', 'cacheStockData') == 'y'
#     assert config_parser.get('config', 'onlyStageTwoStocks') == 'y'
#     assert config_parser.get('config', 'useEMA') == 'n'
#     assert config_parser.get('config', 'showunknowntrends') == 'y'
#     assert config_parser.get('config', 'logsEnabled') == 'n'
#     assert float(config_parser.get('config', 'generalTimeout')) >= 2
#     assert float(config_parser.get('config', 'longTimeout')) >= 4
#     assert config_parser.get('config', 'maxNetworkRetryCount') == '10'
#     assert config_parser.get('config', 'backtestPeriod') == '120'
#     assert config_parser.get('filters', 'minimumVolume') == '10000'
#     with patch('builtins.input') as mock_input:
#         tool.setConfig(config_parser, default=True, showFileCreatedText=True)
#         mock_input.assert_called_once()

def test_setConfig_non_default(config_parser):
    tool = tools()
    with patch('builtins.input') as mock_input, patch('builtins.open') as mock_open:
        mock_input.side_effect = ['450', '30', '1', '20', '50000', '2.5', '10', 'n', 'n', 'n', 'n', 'n','n', '2', '4', '10', '30', '10000','1','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n','\n']
        tool.setConfig(config_parser, default=False, showFileCreatedText=False)
        mock_open.assert_called_with('pkscreener.ini', 'w')

# def test_getConfig(config_parser):
#     tool = tools()
#     try:
#         config_parser.remove_section("config")
#     except Exception as e:  # pragma: no cover
#         pass
#     config_parser.add_section("config")
#     config_parser.set('config', 'period', '1y')
#     config_parser.set('config', 'daysToLookback', '22')
#     config_parser.set('config', 'duration', '1d')
#     config_parser.set('config', 'minPrice', '20.0')
#     config_parser.set('config', 'maxPrice', '50000')
#     config_parser.set('config', 'volumeRatio', '2.5')
#     config_parser.set('config', 'consolidationPercentage', '10')
#     config_parser.set('config', 'shuffle', 'y')
#     config_parser.set('config', 'cacheStockData', 'y')
#     config_parser.set('config', 'onlyStageTwoStocks', 'y')
#     config_parser.set('config', 'useEMA', 'n')
#     config_parser.set('config', 'showunknowntrends', 'y')
#     config_parser.set('config', 'logsEnabled', 'n')
#     config_parser.set('config', 'generalTimeout', '2')
#     config_parser.set('config', 'longTimeout', '4')
#     config_parser.set('config', 'maxNetworkRetryCount', '10')
#     config_parser.set('config', 'backtestPeriod', '120')
#     config_parser.set('config', 'minimumVolume', '10000')
#     config_parser.set('config', 'backtestPeriodFactor', '1')
#     tool.getConfig(config_parser)
#     assert tool.period in ['1y','1d']
#     assert tool.daysToLookback >= 22
#     assert tool.duration in ['1d','1m','1h']
#     assert tool.minLTP >= 5.0
#     assert tool.maxLTP == 50000
#     assert tool.volumeRatio == 2.5
#     assert tool.consolidationPercentage == 10
#     assert tool.shuffleEnabled == True
#     assert tool.cacheEnabled == True
#     assert tool.stageTwo == True
#     assert tool.useEMA == False
#     assert tool.showunknowntrends == True
#     assert tool.logsEnabled == False
#     assert tool.generalTimeout == 2
#     assert tool.longTimeout == 4
#     assert tool.maxNetworkRetryCount == 10
#     assert tool.backtestPeriod == 120
#     assert tool.minVolume == 10000
#     assert tool.backtestPeriodFactor == 1
#     with patch('configparser.ConfigParser.read', return_value = ""):
#         with patch('pkscreener.classes.ConfigManager.tools.setConfig') as mock_setconfig:
#             tool.getConfig(config_parser)
#             mock_setconfig.assert_called_once()

def test_toggleConfig_swing(config_parser):
    tool = tools()
    tool.period = '1d'
    tool.duration = '1h'
    tool.cacheEnabled = True
    tool.toggleConfig('1d', clearCache=False)
    assert tool.period == '1y'
    assert tool.duration == '1d'
    assert tool.daysToLookback == 22
    assert tool.cacheEnabled == True
    tool.toggleConfig(None, clearCache=False)
    assert tool.duration == '1d'


def test_isIntradayConfig(config_parser):
    tool = tools()
    tool.duration = '1m'
    assert tool.isIntradayConfig() == True
    tool.duration = '1h'
    assert tool.isIntradayConfig() == True
    tool.duration = '1d'
    assert tool.isIntradayConfig() == False

def test_showConfigFile(config_parser):
    tool = tools()
    with patch('builtins.input') as mock_input, patch('builtins.open') as mock_open:
        mock_input.side_effect = ['\n']
        mock_open.return_value.read.return_value = 'config data'
        assert tool.showConfigFile(defaultAnswer='Y') == '  [+] PKScreener User Configuration:\nconfig data'
        mock_input.assert_not_called()
        from PKDevTools.classes.OutputControls import OutputControls
        prevValue = OutputControls().enableUserInput
        OutputControls().enableUserInput = True
        assert tool.showConfigFile(defaultAnswer=None) == '  [+] PKScreener User Configuration:\nconfig data'
        OutputControls().enableUserInput = prevValue
        mock_input.assert_called()

def test_checkConfigFile(config_parser):
    tool = tools()
    with patch('builtins.open') as mock_open:
        mock_open.return_value.close.return_value = None
        assert tool.checkConfigFile() == True

def test_toggleConfig_intraday(config_parser):
    tool = tools()
    tool.period = '1y'
    tool.duration = '1d'
    tool.cacheEnabled = True
    tool.toggleConfig('1h', clearCache=True)
    assert tool.period == '4mo'
    assert tool.duration == '1h'
    assert tool.daysToLookback <= 50
    assert tool.cacheEnabled == True

    tool.toggleConfig('35d', clearCache=True)
    assert tool.duration == '35d'
    assert tool.period == '1y'
    tool.toggleConfig('35m', clearCache=True)
    assert tool.duration == '35m'
    assert tool.period == '1d'

def test_CandleDurationInt(config_parser):
    tool = tools()
    tool.duration = '1d'
    assert tool.candleDurationInt == 1
    tool.duration = '320m'
    assert tool.candleDurationInt == 320
    tool.duration = '2y'
    assert tool.candleDurationInt == 2
    tool.duration = '50w'
    assert tool.candleDurationInt == 50
    tool.duration = 'max'
    assert tool.candleDurationInt == "max"

def test_CandlePeriodInt(config_parser):
    tool = tools()
    tool.period = '1d'
    assert tool.candlePeriodInt == 1
    tool.period = '320m'
    assert tool.candlePeriodInt == 320
    tool.period = '2y'
    assert tool.candlePeriodInt == 2
    tool.period = '50w'
    assert tool.candlePeriodInt == 50
    tool.period = 'max'
    assert tool.candlePeriodInt == "max"