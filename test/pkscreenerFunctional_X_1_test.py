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
# pytest --cov --cov-report=html:coverage_re

import os
import shutil
import sys
import warnings
import datetime
from datetime import timezone, timedelta
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pytest
from unittest.mock import ANY, MagicMock, patch

try:
    shutil.copyfile("pkscreener/.env.dev", ".env.dev")
    sys.path.append(os.path.abspath("pkscreener"))
except Exception:# pragma: no cover
    print("This test must be run from the root of the project!")
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from requests_cache import CachedSession

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.globals as globals
from pkscreener.classes import VERSION, Changelog, AssetsManager
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.globals import main
from pkscreener.pkscreenercli import argParser, disableSysOut
from RequestsMocker import RequestsMocker as PRM
from sharedmock import SharedMock
from PKDevTools.classes import Telegram

session = CachedSession(
    cache_name=f"{Archiver.get_user_data_dir().split(os.sep)[-1]}{os.sep}PKDevTools_cache",
    db_path=os.path.join(Archiver.get_user_data_dir(), "PKDevTools_cache.sqlite"),
    cache_control=True,
)
last_release = 0
configManager = ConfigManager.tools()
fetcher = Fetcher.screenerStockDataFetcher(configManager)
configManager.default_logger = default_logger()
disableSysOut(input=False)

this_version_components = VERSION.split(".")
this_major_minor = ".".join([this_version_components[0], this_version_components[1]])
this_version = float(this_major_minor)

last_release = 0

# Mocking necessary functions or dependencies
@pytest.fixture(autouse=True)
def mock_dependencies():
    sm_yf = SharedMock()
    sm_yf.return_value=PRM().patched_yf()
    patch("multiprocessing.resource_tracker.register",lambda *args, **kwargs: None)
    with patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen"):
        with patch("yfinance.download",new=PRM().patched_yf):
            with patch("pkscreener.classes.Fetcher.yf.download",new=PRM().patched_yf):
                with patch("PKDevTools.classes.Fetcher.fetcher.fetchURL",new=PRM().patched_fetchURL):
                    with patch("pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchURL",new=PRM().patched_fetchURL):
                        with patch("PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.fetchURL",new=PRM().patched_fetchURL):
                            with patch("PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.fetchNiftyCodes",return_value = ['SBIN']):
                                with patch("PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.fetchStockCodes",return_value = ['SBIN']):
                                    with patch("pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockData",sm_yf):
                                        with patch("PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.capitalMarketStatus",return_value = ("NIFTY 50 | Closed | 29-Jan-2024 15:30 | 21737.6 | ↑385 (1.8%)","NIFTY 50 | Closed | 29-Jan-2024 15:30 | 21737.6 | ↑385 (1.8%)",PKDateUtilities.currentDateTime().strftime("%Y-%m-%d"))):
                                            with patch("requests.get",new=PRM().patched_get):
                                                # with patch("requests.Session.get",new=PRM().patched_get):
                                                #     with patch("requests.sessions.Session.get",new=PRM().patched_get):
                                                with patch("requests_cache.CachedSession.get",new=PRM().patched_get):
                                                    with patch("requests_cache.CachedSession.post",new=PRM().patched_post):
                                                        with patch("requests.post",new=PRM().patched_post):
                                                            with patch("pandas.read_html",new=PRM().patched_readhtml):
                                                                with patch("PKNSETools.morningstartools.PKMorningstarDataFetcher.morningstarDataFetcher.fetchMorningstarFundFavouriteStocks",return_value=None):
                                                                    with patch("PKNSETools.morningstartools.PKMorningstarDataFetcher.morningstarDataFetcher.fetchMorningstarTopDividendsYieldStocks",return_value=None):
                                                                        with patch('yfinance.download', sm_yf):
                                                                            yield
    

def cleanup():
    # configManager.deleteFileWithPattern(pattern='*.pkl')
    configManager.deleteFileWithPattern(pattern="*.png")
    configManager.deleteFileWithPattern(pattern="*.xlsx")
    configManager.deleteFileWithPattern(pattern="*.html")
    configManager.deleteFileWithPattern(pattern="*.txt")
    # del os.environ['RUNNER']
    os.environ['RUNNER'] = "RUNNER"
    Telegram.TOKEN = "Token"

def getOrSetLastRelease():
    r = fetcher.fetchURL(
        "https://api.github.com/repos/pkjmesra/PKScreener/releases/latest", stream=True
    )
    try:
        tag = r.json()["tag_name"]
        version_components = tag.split(".")
        major_minor = ".".join([version_components[0], version_components[1]])
        last_release = float(major_minor)
    except Exception:# pragma: no cover
        if r.json()["message"] == "Not Found":
            last_release = 0

def messageSentToTelegramQueue(msgText=None):
    relevantMessageFound = False
    for message in globals.test_messages_queue:
        if msgText in message:
            relevantMessageFound = True
            break
    return relevantMessageFound

def test_if_changelog_version_changed():
    global last_release
    getOrSetLastRelease()
    v = Changelog.changelog().split("]")[1].split("[")[-1]
    v = str(v).replace("v", "")
    v_components = v.split(".")
    v_major_minor = ".".join([v_components[0], v_components[1]])
    v = float(v_major_minor)
    assert v >= float(last_release)
    assert f"v{str(last_release)}" in Changelog.changelog()
    assert f"v{str(VERSION)}" in Changelog.changelog()


def test_if_release_version_incremented():
    getOrSetLastRelease()
    assert this_version >= last_release


def test_configManager():
    configManager.getConfig(ConfigManager.parser)
    assert configManager.duration is not None
    assert configManager.period is not None
    assert configManager.consolidationPercentage is not None


# def test_option_B_10_0_1(mocker, capsys):
#     cleanup()
#     mocker.patch(
#         "builtins.input", side_effect=["B", "10", "0", "1", "SBIN,IRFC", "Y", "\n"]
#     )
#     args = argParser.parse_known_args(
#         args=["-e", "-t", "-p", "-a", "Y", "-o", "B:10:0:1:SBIN,IRFC"]
#     )[0]
#     fileGroup1 = ["PKScreener_B_0_1_OneLine_Summary.html","PKScreener_B_0_1_i_OneLine_Summary.html"]
#     fileGroup2 = ["PKScreener_B_0_1_Summary_StockSorted.html","PKScreener_B_0_1_i_Summary_StockSorted.html"]
#     fileGroup3 = ["PKScreener_B_0_1_backtest_result_StockSorted.html","PKScreener_B_0_1_i_backtest_result_StockSorted.html"]
#     fileGroups = [fileGroup1,fileGroup2,fileGroup3]
#     for fileGroup in fileGroups:
#         file1 = os.path.join(Archiver.get_user_outputs_dir().replace("results","Backtest-Reports"),fileGroup[0])
#         file2 = os.path.join(Archiver.get_user_outputs_dir().replace("results","Backtest-Reports"),fileGroup[1])
#         try:
#             os.remove(file1)
#         except:
#             pass
#         try:
#             os.remove(file2)
#         except:
#             pass
#     main(userArgs=args)
#     out, err = capsys.readouterr()
#     assert err == ""
#     assert globals.screenCounter.value >= 0
#     if globals.screenResults is not None and not globals.screenResults.empty:
#         for fileGroup in fileGroups:
#             file1 = os.path.join(Archiver.get_user_outputs_dir().replace("results","Backtest-Reports"),fileGroup[0])
#             file2 = os.path.join(Archiver.get_user_outputs_dir().replace("results","Backtest-Reports"),fileGroup[1])
#             fileSize = os.stat(file1).st_size if os.path.exists(file1) else (os.stat(file2).st_size if os.path.exists(file2) else 0)
#             assert (os.path.isfile(file1) or os.path.isfile(file2))
#             assert fileSize > 0
#             modified = datetime.datetime.fromtimestamp(os.stat(file1).st_mtime, tz=timezone.utc) if os.path.exists(file1) else (datetime.datetime.fromtimestamp(os.stat(file1).st_mtime, tz=timezone.utc) if os.path.exists(file2) else None)
#             assert modified is not None
#             diff = PKDateUtilities.currentDateTime() - modified
#             assert diff <= timedelta(minutes=5)

def test_option_D(mocker, capsys):
    cleanup()
    mocker.patch("builtins.input", side_effect=["Y"])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-o", "X:12:2", "-d"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    _ , cache_file = AssetsManager.PKAssetsManager.afterMarketStockDataExists(False,False)
    file1 = os.path.join(Archiver.get_user_data_dir().replace(f"results{os.sep}Data","actions-data-download"),cache_file)
    file2 = os.path.join(Archiver.get_user_data_dir().replace(f"results{os.sep}Data","actions-data-download"),f"intraday_{cache_file}")
    assert (os.path.isfile(file1) or os.path.isfile(file2))


def test_option_E(mocker, capsys):
    mocker.patch(
        "builtins.input",
        side_effect=[
            "E",
            str(configManager.period),
            str(configManager.daysToLookback),
            str(configManager.duration),
            str(configManager.minLTP),
            str(configManager.maxLTP),
            str(configManager.volumeRatio),
            str(configManager.consolidationPercentage),
            "y",
            "y",
            "y",
            "n",
            "n",
            str(configManager.generalTimeout),
            str(configManager.longTimeout),
            str(configManager.maxNetworkRetryCount),
            str(configManager.backtestPeriod),
            "\n",
        ],
    )
    args = argParser.parse_known_args(args=["-e", "-t", "-p", "-a", "Y"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == 0 or err == ""


def test_option_Y(mocker, capsys):
    cleanup()
    mocker.patch("builtins.input", side_effect=["Y", "\n"])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-u","00000","-o", "Y"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    assert messageSentToTelegramQueue("PKScreener User Configuration") == True

def test_option_H(mocker, capsys):
    cleanup()
    mocker.patch("builtins.input", side_effect=["H", "\n"])
    args = argParser.parse_known_args(args=["-e", "-a", "N", "-t", "-p","-u","00000","-o", "H"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    assert messageSentToTelegramQueue("[ChangeLog]") == True

def test_nifty_prediction(mocker, capsys):
    cleanup()
    from PKDevTools.classes.OutputControls import OutputControls
    prevValue = OutputControls().enableUserInput
    OutputControls().enableUserInput = True
    mocker.patch("builtins.input", side_effect=["X", "N"])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-t", "-p", "-l"])[0]
    main(userArgs=args)
    OutputControls().enableUserInput = prevValue
    out, err = capsys.readouterr()
    assert err == ""
    assert len(globals.test_messages_queue) > 0
    assert messageSentToTelegramQueue("Nifty AI prediction") == True



def test_option_T(mocker, capsys):
    originalPeriod = globals.configManager.period
    mocker.patch("builtins.input", side_effect=["T","L","2","\n"])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-t", "-p"])[0]
    # with pytest.raises(SystemExit):
    main(userArgs=args)
    globals.configManager.getConfig(ConfigManager.parser)
    assert globals.configManager != originalPeriod
    out, err = capsys.readouterr()
    assert err == ""
    
    # Get to the changed state
    mocker.patch("builtins.input", side_effect=["T","S","2","\n"])
    # with pytest.raises(SystemExit):
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    assert globals.configManager.period != originalPeriod


def test_option_U(mocker, capsys):
    cleanup()
    import platform
    mocker.patch("builtins.input", side_effect=["U", "Z", "Y", "\n"])
    mocker.patch.object(platform, "system", return_value="Windows")
    args = argParser.parse_known_args(args=["-e", "-a", "N", "-t", "-p", "-o", "U"])[0]
    main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""
    assert OTAUpdater.checkForUpdate.url is not None


def test_option_X_0(mocker):
    cleanup()
    mocker.patch(
        "builtins.input", side_effect=["X", "0", "0", globals.TEST_STKCODE, "y"]
    )
    args = argParser.parse_known_args(
        args=["-e", "-a", "Y","-u","00000", "-o", "X:0:0:" + globals.TEST_STKCODE]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0
    assert globals.screenResultsCounter.value >= 0
    assert globals.screenCounter.value >= 0
    assert messageSentToTelegramQueue("Scanners") == True
    
def test_option_X_0_input(mocker):
    cleanup()
    mocker.patch(
        "builtins.input", side_effect=["X", "0", "0", globals.TEST_STKCODE, "y"]
    )
    args = argParser.parse_known_args(args=["-e", "-a", "Y","-u","00000"])[0]
    Telegram.TOKEN = "Token"
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0
    assert globals.screenResultsCounter.value >= 0
    assert globals.screenCounter.value >= 0

def test_option_X_1_0(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "0", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y","-u","00000", "-o", "X:1:0"]
    )[0]
    Telegram.TOKEN = "Token"
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0
    assert globals.screenResultsCounter.value >= 0
    assert globals.screenCounter.value >= 0


def test_option_X_1_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_2(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "2", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:2"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "3", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:3"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_4(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "4", "5", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:4:5"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_5(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "5", "10", "90", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:5:10:90"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_2(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "2", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:2"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "3", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:3"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_4(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "4", "50", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:4:50"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_5(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "5", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:5"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_6_6(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "6", "4", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:6:4"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_6_7_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "7", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:7:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_6_7_2(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "7", "2", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:7:2"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_6_7_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "6", "7", "3", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:6:7:3"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_7_1_7(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "1", "7", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:7:1:7"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_7_2_7(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "2", "7", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:7:2:7"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_7_3_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "3", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:7:3:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_7_4(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "4", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:7:4"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_7_5(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "7", "5", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:7:5"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_8(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "8", "-100", "150", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:8:-100:150"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_9_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "9", "3", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:9:3"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_10(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "10", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:10"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_11(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "11", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:11"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_12(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "12", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:12"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_13(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "13", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:13"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_1_14(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "14", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:14"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_19(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "19", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:19"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0

def test_option_X_1_20(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "1", "20", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:1:20"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0
