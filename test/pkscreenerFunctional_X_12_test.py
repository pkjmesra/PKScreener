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
import io
import json
import shutil
import sys
import warnings
import datetime
from datetime import timezone, timedelta
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import pytest
import yfinance
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
from pkscreener.classes import VERSION, Changelog
from pkscreener.classes.MenuOptions import MenuRenderStyle, menus, MAX_SUPPORTED_MENU_OPTION
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.globals import main
from pkscreener.pkscreenercli import argParser, disableSysOut
from RequestsMocker import RequestsMocker as PRM
from sharedmock import SharedMock
from pkscreener.classes import Utility
from PKDevTools.classes import Telegram
from pkscreener import pkscreenercli

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
    with patch("pkscreener.classes.Utility.tools.clearScreen"):
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
    global last_release
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

def test_option_X_Z(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["X", "Z", ""])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-o", "X:Z"])[0]
    with pytest.raises(SystemExit):
        main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_option_X_12_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_21_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "21", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:21:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_21_2(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "21", "2", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:21:2"]
    )[0]
    main(userArgs=args)
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_21_3(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "21", "3", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:21:3"]
    )[0]
    main(userArgs=args)
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_22(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "22", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:22"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_23(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "23", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:23"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_24(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "24", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:24"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_25(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "12", "25", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:12:25"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert globals.screenResultsCounter.value >= 0


def test_option_X_12_Z(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["X", "12", "Z", ""])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-o", "X:12:Z"])[0]
    with pytest.raises(SystemExit):
        main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_option_X_14_1(mocker):
    cleanup()
    mocker.patch("builtins.input", side_effect=["X", "14", "1", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:14:1"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_X_W(mocker):
    cleanup()
    sample = {"Stock Code": ["SBIN", "INFY", "TATAMOTORS", "ITC"]}
    sample_data = pd.DataFrame(sample, columns=["Stock Code"])
    sample_data.to_excel(
        os.path.join(os.getcwd(), "watchlist.xlsx"), index=False, header=True
    )
    mocker.patch("builtins.input", side_effect=["X", "W", "y"])
    args = argParser.parse_known_args(
        args=["-e", "-t", "-p", "-a", "Y", "-o", "X:W:0"]
    )[0]
    main(userArgs=args)
    assert globals.screenResults is not None
    assert len(globals.screenResults) >= 0


def test_option_Z(mocker, capsys):
    mocker.patch("builtins.input", side_effect=["Z", ""])
    args = argParser.parse_known_args(args=["-e", "-a", "Y", "-o", "Z"])[0]
    with pytest.raises(SystemExit):
        main(userArgs=args)
    out, err = capsys.readouterr()
    assert err == ""


def test_ota_updater():
    cleanup()
    OTAUpdater.checkForUpdate(VERSION, skipDownload=True)
    if OTAUpdater.checkForUpdate.url is not None:
        assert (
            "exe" in OTAUpdater.checkForUpdate.url
            or "bin" in OTAUpdater.checkForUpdate.url
            or "run" in OTAUpdater.checkForUpdate.url
        )


def test_release_readme_urls():
    global last_release
    getOrSetLastRelease()
    f = open("pkscreener/release.md", "r")
    contents = f.read()
    f.close()
    failUrl = [
        f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreenercli_x64.bin",
        f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreenercli.exe",
    ]
    passUrl = [
        f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreenercli_x64.bin",
        f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreenercli.exe",
    ]
    if this_version > float(last_release):
        for url in failUrl:
            assert url not in contents
    # for url in passUrl:
    #     assert url in contents


def listedMenusFromRendering(selectedMenu=None, skipList=[]):
    m = menus()
    return m, m.renderForMenu(
        selectedMenu=selectedMenu,
        skip=skipList,
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )


# def test_option_X_12_all(mocker, capsys):
#     cleanup()
#     m, _ = listedMenusFromRendering()
#     x = m.find("X")
#     m, _ = listedMenusFromRendering(x)
#     x = m.find("12")
#     skipList = ["0", "Z", "M", "12" ,"21", "22"]
#     NA_Counter = 19
#     Last_Counter = MAX_SUPPORTED_MENU_OPTION
#     menuCounter = NA_Counter
#     while menuCounter <= Last_Counter:
#         skipList.extend([str(menuCounter)])
#         menuCounter += 1
#     m, cmds = listedMenusFromRendering(x, skipList=skipList)
#     argsList = []
#     for cmd in cmds:
#         startupOption = "X:12"
#         key = cmd.menuKey.upper()
#         startupOption = f"{startupOption}:{key}"
#         if str(key) in ["6", "7"]:
#             x = m.find(key)
#             _, cmds1 = listedMenusFromRendering(x, skipList=skipList)
#             for cmd1 in cmds1:
#                 startupOption = "X:12"
#                 startupOption = f"{startupOption}:{key}"
#                 key1 = cmd1.menuKey.upper()
#                 startupOption = f"{startupOption}:{key1}:D:D"
#                 args = argParser.parse_known_args(
#                     args=["-e", "-p", "-t", "-a", "Y", "-o", startupOption]
#                 )[0]
#                 argsList.extend([args])
#         else:
#             startupOption = f"{startupOption}:D:D"
#             args = argParser.parse_known_args(
#                 args=["-e", "-p", "-t", "-a", "Y", "-u","0000","-o", startupOption]
#             )[0]
#             argsList.extend([args])
#     for arg in argsList:
#         main(userArgs=arg)
#         # with pytest.raises(SystemExit):
#         #     pkscreenercli.args = arg
#         #     pkscreenercli.pkscreenercli()
#         out, err = capsys.readouterr()
#         # print(f"ElapsedTimeFor:{arg.options}:{globals.elapsed_time}")
#         assert err == ""
#         assert globals.screenCounter.value >= 1
#         if len(globals.test_messages_queue) > 0:
#             assert messageSentToTelegramQueue("Scanners") == True