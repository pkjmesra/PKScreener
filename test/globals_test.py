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

import platform
from unittest.mock import patch

import pytest

from pkscreener.globals import *

# Positive test cases

def test_initExecution_positive():
    menuOption = "X"
    selectedMenu = initExecution(menuOption)
    assert selectedMenu.menuKey == menuOption

def test_initPostLevel0Execution_positive():
    menuOption = "X"
    tickerOption = "1"
    executeOption = "0"
    t, e = initPostLevel0Execution(menuOption, tickerOption, executeOption)
    assert str(t) == tickerOption
    assert str(e) == executeOption

def test_initPostLevel1Execution_positive():
    tickerOption = "1"
    executeOption = "0"
    t, e = initPostLevel1Execution(tickerOption, executeOption)
    assert str(t) == tickerOption
    assert str(e) == executeOption

def test_getTestBuildChoices_positive():
    tickerOption = "1"
    executeOption = "0"
    menuOption, selectedTickerOption, selectedExecuteOption, selectedChoice = getTestBuildChoices(tickerOption, executeOption)
    assert menuOption == "X"
    assert str(selectedTickerOption) == tickerOption
    assert str(selectedExecuteOption) == executeOption
    assert selectedChoice == {"0": "X", "1": tickerOption, "2": executeOption}

def test_getDownloadChoices_positive():
    menuOption, selectedTickerOption, selectedExecuteOption, selectedChoice = getDownloadChoices(defaultAnswer='Y')
    assert menuOption == "X"
    assert str(selectedTickerOption) == "12"
    assert str(selectedExecuteOption) == "2"
    assert selectedChoice == {"0": "X", "1": "12", "2": "2"}

def test_handleSecondaryMenuChoices_positive():
    menuOption = "H"
    with patch("pkscreener.classes.Utility.tools.showDevInfo") as mock_showDevInfo:
        handleSecondaryMenuChoices(menuOption,defaultAnswer='Y')
        mock_showDevInfo.assert_called_once_with(defaultAnswer='Y')

def test_getTopLevelMenuChoices_positive():
    startupoptions = "X:1:0"
    testBuild = False
    downloadOnly = False
    options, menuOption, tickerOption, executeOption = getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly)
    assert options == ["X", "1", "0"]
    assert menuOption == "X"
    assert tickerOption == "1"
    assert executeOption == "0"

def test_handleScannerExecuteOption4_positive():
    executeOption = 4
    options = ["X", "1", "0", "30"]
    daysForLowestVolume = handleScannerExecuteOption4(executeOption, options)
    assert daysForLowestVolume == 30

def test_populateQueues_positive():
    items = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
    tasks_queue = multiprocessing.JoinableQueue()
    populateQueues(items, tasks_queue)
    if "Darwin" in platform.system():
        # On Mac, using qsize raises error
        # assert not tasks_queue.empty()
        pass
    else:
        # Raises NotImplementedError on Mac OSX because of broken sem_getvalue()
        assert tasks_queue.qsize() == len(items) + multiprocessing.cpu_count()

# Negative test cases

def test_initExecution_exit_positive():
    menuOption = "Z"
    with pytest.raises(SystemExit):
        with patch("builtins.input"):
            initExecution(menuOption)

def test_initPostLevel0Execution_negative():
    menuOption = "X"
    tickerOption = "15"
    executeOption = "0"
    with patch("builtins.print") as mock_print:
        initPostLevel0Execution(menuOption, tickerOption, executeOption)
        mock_print.assert_called_with(colorText.BOLD
            + colorText.FAIL
            + "\n[+] Please enter a valid numeric option & Try Again!"
            + colorText.END)

def test_initPostLevel1Execution_negative():
    tickerOption = "1"
    executeOption = "45"
    with patch("builtins.print") as mock_print:
        initPostLevel1Execution(tickerOption, executeOption)
        mock_print.assert_called_with(colorText.BOLD
        + colorText.FAIL
        + "\n[+] Please enter a valid numeric option & Try Again!"
        + colorText.END)

def test_getTestBuildChoices_negative():
    tickerOption = "A"
    executeOption = "0"
    r1, r2, r3, r4 = getTestBuildChoices(tickerOption, executeOption)
    assert r1 == 'X'
    assert r2 == 1
    assert r3 == 0
    assert r4 == {"0": "X", "1": "1", "2": "0"}

def test_getDownloadChoices_negative():
    with patch('builtins.input', return_value='N'):
        menuOption, selectedTickerOption, selectedExecuteOption, selectedChoice = getDownloadChoices()
        assert menuOption == "X"
        assert selectedTickerOption == 12
        assert selectedExecuteOption == 2
        assert selectedChoice == {"0": "X", "1": "12", "2": "2"}

def test_getTopLevelMenuChoices_negative():
    startupoptions = "X:1:0"
    testBuild = False
    downloadOnly = False
    options, menuOption, tickerOption, executeOption = getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly)
    assert options == ["X", "1", "0"]
    assert menuOption == "X"
    assert tickerOption == "1"
    assert executeOption == "0"

def test_handleScannerExecuteOption4_negative():
    executeOption = 4
    options = ["X", "1", "0", "A"]
    with patch("builtins.print") as mock_print:
        with patch("builtins.input"):
            handleScannerExecuteOption4(executeOption, options)
            mock_print.assert_called_with(colorText.BOLD
                + colorText.FAIL
                + "[+] Error: Non-numeric value entered! Please try again!"
                + colorText.END)

def test_getTopLevelMenuChoices_edge():
    startupoptions = ""
    testBuild = False
    downloadOnly = False
    options, menuOption, tickerOption, executeOption = getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly)
    assert options == ['']
    assert menuOption == ""
    assert tickerOption is None
    assert executeOption is None
