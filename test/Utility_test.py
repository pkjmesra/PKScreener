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
import datetime
import os
import platform
from unittest.mock import ANY, Mock, patch

import pandas as pd
import pytz

from pkscreener.classes.ColorText import colorText
from pkscreener.classes.Utility import tools


# Positive test case for clearScreen() function
def test_clearScreen():
    # Mocking the os.system() function
    with patch("os.system") as mock_os_system:
        tools.clearScreen()
        # Assert that os.system() is called with the correct argument
        if platform.system() == "Windows":
            mock_os_system.assert_called_once_with("cls")
        else:
            mock_os_system.assert_called_once_with("clear")

# Positive test case for showDevInfo() function
def test_showDevInfo():
    # Mocking the input() function
    with patch("builtins.input", return_value="Y") as mock_input:
        result = tools.showDevInfo()
        # Assert that input() is called with the correct argument
        mock_input.assert_called_once_with(
            colorText.BOLD + colorText.FAIL + "[+] Press <Enter> to continue!" + colorText.END
        )
        # Assert that the result is not None
        assert result is not None

# Positive test case for setLastScreenedResults() function
def test_setLastScreenedResults():
    # Mocking the pd.DataFrame.to_pickle() function
    mock_df = pd.DataFrame()
    with patch("pandas.DataFrame.to_pickle") as mock_to_pickle:
        with patch("pandas.DataFrame.sort_values") as mock_sort_values:
            tools.setLastScreenedResults(mock_df)
            mock_sort_values.assert_called_once()
            # Assert that pd.DataFrame.to_pickle() is called with the correct argument
            mock_to_pickle.assert_called_once_with("last_screened_results.pkl")

# Positive test case for getLastScreenedResults() function
def test_getLastScreenedResults():
    # Mocking the pd.read_pickle() function
    with patch("pandas.read_pickle") as mock_read_pickle:
        with patch("builtins.input"):
            tools.getLastScreenedResults()
            # Assert that pd.read_pickle() is called with the correct argument
            mock_read_pickle.assert_called_once_with("last_screened_results.pkl")

# Positive test case for formatRatio() function
def test_formatRatio():
    ratio = 2.0
    volumeRatio = 1.5
    result = tools.formatRatio(ratio, volumeRatio)
    # Assert that the result is formatted correctly
    assert result == "\033[1m\033[92m2.0x\033[0m"

# Positive test case for removeAllColorStyles() function
def test_removeAllColorStyles():
    styledText = "\033[94mHello World!\033[0m"
    result = tools.removeAllColorStyles(styledText)
    # Assert that the result is the original text without any color styles
    assert result == "Hello World!"

# Positive test case for getCellColor() function
def test_getCellColor():
    cellStyledValue = "\033[92mHello World!\033[0m"
    result = tools.getCellColor(cellStyledValue)
    # Assert that the result is the correct cell fill color and cleaned up styled value
    assert result == ("green", "Hello World!")

# Positive test case for tradingDate() function
def test_tradingDate():
    # Mocking the datetime.datetime.now() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_now:
        mock_now.return_value = datetime.datetime(2023, 1, 1)
        result = tools.tradingDate()
        # Assert that the result is the correct trading date
        assert result == datetime.date(2022, 12, 30)

# Positive test case for currentDateTime() function
def test_currentDateTime():
    curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%y_%H.%M.%S")
    result = tools.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
    # Assert that the result is the correct current date and time
    assert result == curr

# Positive test case for isTradingTime() function
def test_isTradingTime():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 3, 10, 30)
        result = tools.isTradingTime()
        # Assert that the result is True
        assert result is True

# Positive test case for isTradingWeekday() function
def test_isTradingWeekday():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 1, 10, 30)
        result = tools.isTradingWeekday()
        # Assert that the result is False
        assert result is False

# Positive test case for ispreMarketTime() function
def test_ispreMarketTime():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 3, 8, 30)
        result = tools.ispreMarketTime()
        # Assert that the result is True
        assert result is True

# Positive test case for ispostMarketTime() function
def test_ispostMarketTime():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 4, 16, 30)
        result = tools.ispostMarketTime()
        # Assert that the result is True
        assert result is True

# Positive test case for isClosingHour() function
def test_isClosingHour():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 4, 15, 30)
        result = tools.isClosingHour()
        # Assert that the result is True
        assert result is True

# Positive test case for secondsAfterCloseTime() function
def test_secondsAfterCloseTime():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 4, 15, 35)
        result = tools.secondsAfterCloseTime()
        # Assert that the result is the correct number of seconds
        assert result == 300

# Positive test case for secondsBeforeOpenTime() function
def test_secondsBeforeOpenTime():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 5, 9, 10)
        result = tools.secondsBeforeOpenTime()
        # Assert that the result is the correct number of seconds
        assert result == -300

# Positive test case for nextRunAtDateTime() function
def test_nextRunAtDateTime():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 3, 10, 30)
        result = tools.nextRunAtDateTime()
        # Assert that the result is the correct next run datetime
        assert result == datetime.datetime(2023, 1, 3, 10, 35)

# Positive test case for afterMarketStockDataExists() function
def test_afterMarketStockDataExists():
    # Mocking the tools.currentDateTime() function
    with patch("pkscreener.classes.Utility.tools.currentDateTime") as mock_currentDateTime:
        mock_currentDateTime.return_value = datetime.datetime(2023, 1, 2, 16, 30)
        curr = mock_currentDateTime.return_value
        weekday = curr.weekday()
        cache_date = curr
        if weekday == 5 or weekday == 6:  # for saturday and sunday
            cache_date = curr - datetime.timedelta(days=weekday - 4)
        cache_date = cache_date.strftime("%d%m%y")
        cache_file = "stock_data_" + str(cache_date) + ".pkl"
        result = tools.afterMarketStockDataExists()
        # Assert that the result is True and the cache file name is correct
        assert result == (False, cache_file)

# Positive test case for saveStockData() function
def test_saveStockData():
    stockDict = {"AAPL": 100, "GOOG": 200}
    configManager = Mock()
    loadCount = 2
    try:
        os.remove("stock_data_1.pkl")
    except Exception:
        pass
    with patch("pkscreener.classes.Utility.tools.afterMarketStockDataExists") as mock_data:
        mock_data.return_value = False, "stock_data_1.pkl"
        mock_pickle = Mock()
        with patch("pickle.dump", mock_pickle) as mock_dump:
            tools.saveStockData(stockDict, configManager, loadCount)
            # Assert that pickle.dump() is called with the correct arguments
            mock_dump.assert_called_once_with(stockDict.copy(),ANY)

# Positive test case for loadStockData() function
def test_loadStockData():
    # Mocking the pickle.load() function
    mock_pickle = Mock()
    pd.DataFrame().to_pickle("stock_data_2.pkl")
    with patch("pickle.load", mock_pickle) as mock_load:
        mock_load.return_value = []
        with patch("pkscreener.classes.Utility.tools.afterMarketStockDataExists") as mock_data:
            mock_data.return_value = True, "stock_data_2.pkl"
            stockDict = {}
            configManager = Mock()
            downloadOnly = False
            defaultAnswer = "Y"
            tools.loadStockData(stockDict, configManager, downloadOnly, defaultAnswer)
            # Assert that pickle.load() is called
            mock_load.assert_called_once()

# Positive test case for promptSaveResults() function
def test_promptSaveResults():
    # Mocking the pd.DataFrame.to_excel() function
    mock_df = pd.DataFrame()
    with patch("pandas.DataFrame.to_excel") as mock_to_excel:
        result = tools.promptSaveResults(mock_df,defaultAnswer="Y")
        # Assert that pd.DataFrame.to_excel() is called with the correct argument
        mock_to_excel.assert_called_once_with(ANY, engine="xlsxwriter")
        # Assert that the result is not None
        assert result is not None

# Positive test case for promptFileExists() function
def test_promptFileExists():
    # Mocking the input() function
    with patch("builtins.input", return_value="Y") as mock_input:
        result = tools.promptFileExists()
        # Assert input() is called correct argument
        mock_input.assert_called_once_with(
            colorText.BOLD + colorText.WARN + "[>] stock_data_*.pkl already exists. Do you want to replace this? [Y/N]: "
        )
        # Assert that the result is "Y"
        assert result == "Y"

# Positive test case for promptRSIValues() function
def test_promptRSIValues():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["30", "70"]) as mock_input:
        result = tools.promptRSIValues()
        # Assert that input() is called twice with the correct arguments
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + "[+] Enter Max RSI value: "
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (30, 70)

# Positive test case for promptCCIValues() function
def test_promptCCIValues():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["-100", "100"]) as mock_input:
        result = tools.promptCCIValues()
        # Assert that input() is called twice with the correct arguments
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + "[+] Enter Max CCI value: "
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (-100, 100)

# Positive test case for promptVolumeMultiplier() function
def test_promptVolumeMultiplier():
    # Mocking the input() function
    with patch("builtins.input", return_value="2") as mock_input:
        result = tools.promptVolumeMultiplier()
        # Assert that input() is called with the correct argument
        mock_input.assert_called_once_with(
            colorText.BOLD + colorText.WARN + "\n[+] Enter Min Volume ratio value (Default = 2): " + colorText.END
        )
        # Assert that the result is 2
        assert result == 2

# Positive test case for promptReversalScreening() function
def test_promptReversalScreening():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["4","50"]) as mock_input:
        result = tools.promptReversalScreening()
        # Assert that input() is called with the correct argument
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + "\n[+] Enter MA Length (E.g. 50 or 200): "
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (4, 50)

def test_promptReversalScreening_4x_Does_not_raise_value_error():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["4","x","\n"]) as mock_input:
        result = tools.promptReversalScreening()
        # Assert that input() is called with the correct argument
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] Invalid Option Selected. Press <Enter> to try again..."
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (None, None)
def test_promptReversalScreening_Input6():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["6","7"]) as mock_input:
        result = tools.promptReversalScreening()
        # Assert that input() is called with the correct argument
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + "\n[+] Enter NR timeframe [Integer Number] (E.g. 4, 7, etc.): "
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (6, 7)

def test_promptReversalScreening_Input1():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["1"]) as mock_input:
        result = tools.promptReversalScreening()
        # Assert that input() is called with the correct argument
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + """[+] Select Option:"""
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (1, None)

# Positive test case for promptChartPatterns() function
def test_promptChartPatterns():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["4"]) as mock_input:
        result = tools.promptChartPatterns()
        # Assert that input() is called with the correct arguments
        mock_input.assert_called_with(
            colorText.BOLD + colorText.WARN + "[+] Select Option:" + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (4, 0)

def test_promptChartPatterns_Input1():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["1","3"]) as mock_input:
        result = tools.promptChartPatterns()
        # Assert that input() is called with the correct arguments
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + "\n[+] How many candles (TimeFrame) to look back Inside Bar formation? : "
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (1, 3)

def test_promptChartPatterns_Input3():
    # Mocking the input() function
    with patch("builtins.input", side_effect=["3","2"]) as mock_input:
        result = tools.promptChartPatterns()
        # Assert that input() is called with the correct arguments
        mock_input.assert_called_with(
            colorText.BOLD
            + colorText.WARN
            + "\n[+] Enter Percentage within which all MA/EMAs should be (Ideal: 1-2%)? : "
            + colorText.END
        )
        # Assert that the result is the correct tuple
        assert result == (3, .02)
# Positive test case for getProgressbarStyle() function
def test_getProgressbarStyle():
    result = tools.getProgressbarStyle()
    # Assert that the result is the correct tuple
    if "Windows" in platform.platform():
        assert result == ("classic2", "dots_recur")
    else:
        assert result == ("smooth", "waves")

# Positive test case for getNiftyModel() function
def test_getNiftyModel():
    # Mocking the os.path.isfile() function
    with patch("os.path.isfile", return_value=True) as mock_isfile:
        # Mocking the keras.models.load_model() function
        mock_load_model = Mock()
        m1 = str(mock_load_model)
        f = open("nifty_model_v2.h5","wb")
        f.close()
        pd.DataFrame().to_pickle("nifty_model_v2.pkl")
        with patch("keras.models.load_model", return_value=mock_load_model) as mock_keras_load_model:
            # Mocking the joblib.load() function
            mock_joblib_load = Mock()
            m2 = str(mock_joblib_load)
            with patch("joblib.load", return_value=mock_joblib_load) as mock_joblib_load:
                result = tools.getNiftyModel(retrial=True)
                # Assert that os.path.isfile called twice with the correct argument
                mock_isfile.assert_called_with("nifty_model_v2.pkl")
                # Assert that keras.models.load_model() is called with the correct argument
                mock_keras_load_model.assert_called_with("nifty_model_v2.h5")
                # Assert that joblib.load() is called with the correct argument
                mock_joblib_load.assert_called_with("nifty_model_v2.pkl")
                # Assert that the result is the correct tuple
                assert (str(result[0]), str(result[1])) == (m1, m2)

# Positive test case for getSigmoidConfidence() function
def test_getSigmoidConfidence():
    x = 0.7
    result = tools.getSigmoidConfidence(x)
    # Assert that the result is the correct sigmoid confidence value
    assert result == 39.999

# Positive test case for alertSound() function
def test_alertSound():
    # Mocking the print() function
    with patch("builtins.print") as mock_print:
        tools.alertSound(1)
        # Assert that print() is called with the correct argument
        mock_print.assert_called_once_with("\a")