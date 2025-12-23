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
import math
import os
import sys

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"

import platform
import time

import joblib
import numpy as np
import pytz
from halo import Halo
from genericpath import isfile
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.ColorText import colorText
from pkscreener import Imports

import warnings
from time import sleep

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from PKDevTools.classes import Archiver

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher
from pkscreener.classes.MarketStatus import MarketStatus
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.Utils import random_user_agent

from pkscreener.classes.ArtTexts import getArtText
from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus

import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = None

configManager = ConfigManager.tools()
configManager.getConfig(ConfigManager.parser)
nseFetcher = nseStockDataFetcher()
fetcher = Fetcher.screenerStockDataFetcher()

artText = f"{getArtText()}\n"

STD_ENCODING=sys.stdout.encoding if sys.stdout is not None else 'utf-8'

def marketStatus():
    return ""
    # task = PKTask("Nifty 50 Market Status",MarketStatus().getMarketStatus)
    lngStatus = MarketStatus().marketStatus
    nseStatus = ""
    next_bell = ""
    try:
        nseStatus = NSEMarketStatus({},None).status
        next_bell = NSEMarketStatus({},None).getNextBell()
    except: # pragma: no cover
        pass
    # scheduleTasks(tasksList=[task])
    if lngStatus == "":
        lngStatus = MarketStatus().getMarketStatus(exchangeSymbol="^IXIC" if configManager.defaultIndex == 15 else "^NSEI")
    if "close" in lngStatus and nseStatus == "open":
        lngStatus = lngStatus.replace("Closed","open")
    if len(next_bell) > 0 and next_bell not in lngStatus:
        lngStatus = f"{lngStatus} | Next Bell: {colorText.WARN}{next_bell.replace('T',' ').split('+')[0]}{colorText.END}"
    return (lngStatus +"\n") if lngStatus is not None else "\n"

art = colorText.GREEN + f"{getArtText()}\n" + colorText.END + f"{marketStatus()}"

lastScreened = os.path.join(
    Archiver.get_user_data_dir(), "last_screened_results.pkl"
)

# Class for managing misc and utility methods

class tools:

    def formatRatio(ratio, volumeRatio):
        if ratio >= volumeRatio and ratio != np.nan and (not math.isinf(ratio)):
            return colorText.GREEN + str(ratio) + "x" + colorText.END
        return colorText.FAIL + (f"{ratio}x" if pd.notna(ratio) else "") + colorText.END
    
    def stockDecoratedName(stockName,exchangeName):
        decoratedName = f"{colorText.WHITE}\x1B]8;;https://in.tradingview.com/chart?symbol={'NSE' if exchangeName=='INDIA' else 'NASDAQ'}%3A{stockName}\x1B\\{stockName}\x1B]8;;\x1B\\{colorText.END}"
        return decoratedName

    def set_github_output(name, value):
        if "GITHUB_OUTPUT" in os.environ.keys():
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                print(f"{name}={value}", file=fh)

    def loadLargeDeals():
        shouldFetch = False
        dealsFile = os.path.join(Archiver.get_user_data_dir(),"large_deals.json")
        dealsFileSize = os.stat(dealsFile).st_size if os.path.exists(dealsFile) else 0
        if dealsFileSize > 0:
            modifiedDateTime = Archiver.get_last_modified_datetime(dealsFile)
            curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            shouldFetch = modifiedDateTime.date() < curr.date()
        else:
            shouldFetch = True
        if shouldFetch:
            from PKNSETools.Benny.NSE import NSE
            import json
            try:
                nseFetcher = NSE(Archiver.get_user_data_dir())
                jsonDict = nseFetcher.largeDeals()
                if jsonDict and len(jsonDict) > 0:
                    with open(dealsFile,"w") as f:
                        f.write(json.dumps(jsonDict))
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                default_logger().debug(e,exc_info=True)
                pass

    @Halo(text='', spinner='dots')
    def tryFetchFromServer(cache_file,repoOwner="pkjmesra",repoName="PKScreener",directory="results/Data",hideOutput=False,branchName="refs/heads/actions-data-download"):
        if not hideOutput:
            OutputControls().printOutput(
                        colorText.FAIL
                        + "[+] Loading data from server. Market Stock Data is not cached, or forced to redownload .."
                        + colorText.END
                    )
            OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Downloading {colorText.END}{colorText.FAIL}{'Intraday' if configManager.isIntradayConfig() else 'Daily'}{colorText.END}{colorText.GREEN} cache from server ({'Primary' if repoOwner=='pkjmesra' else 'Secondary'}) for faster processing, Please Wait.."
                    + colorText.END
                )
        cache_url = (
                f"https://raw.githubusercontent.com/{repoOwner}/{repoName}/{branchName}/{directory}/"
                + cache_file  # .split(os.sep)[-1]
            )
        headers = {
                    'authority': 'raw.githubusercontent.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'dnt': '1',
                    'sec-ch-ua-mobile': '?0',
                    # 'sec-ch-ua-platform': '"macOS"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',                  
                    'origin': 'https://github.com',
                    'referer': f'https://github.com/{repoOwner}/{repoName}/blob/{branchName}/{directory}/{cache_file}',
                    'user-agent': f'{random_user_agent()}' 
                    #'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
            }
        resp = fetcher.fetchURL(cache_url, headers=headers, stream=True)
        filesize = 0
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            filesize = int(contentLength) if contentLength is not None else 0
            # File size should be more than at least 10 MB
        if (resp is None or (resp is not None and resp.status_code != 200) or filesize <= 10*1024*1024) and (repoOwner=="pkjmesra" and directory=="actions-data-download"):
            return tools.tryFetchFromServer(cache_file,repoOwner=repoName)
        return resp

    def getProgressbarStyle():
        bar = "smooth"
        spinner = "waves"
        if "Windows" in platform.platform():
            bar = "classic2"
            spinner = "dots_recur"
        return bar, spinner

    @Halo(text='', spinner='dots')
    def getNiftyModel(retrial=False):
        if "Windows" in platform.system() and not 'pytest' in sys.modules:
            try:
                sys.stdin.reconfigure(encoding='utf-8')
                sys.stdout.reconfigure(encoding='utf-8')
            except: # pragma: no cover
                pass
        files = [
            os.path.join(Archiver.get_user_data_dir(), "nifty_model_v2.h5"),
            os.path.join(Archiver.get_user_data_dir(), "nifty_model_v2.pkl"),
        ]
        model = None
        pkl = None
        urls = [
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/ml/nifty_model_v2.h5",
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/ml/nifty_model_v2.pkl",
        ]
        if os.path.isfile(files[0]) and os.path.isfile(files[1]):
            file_age = (time.time() - os.path.getmtime(files[0])) / 604800
            if file_age > 1:
                download = True
                os.remove(files[0])
                os.remove(files[1])
            else:
                download = False
        else:
            download = True
        if download:
            for file_url in urls:
                resp = fetcher.fetchURL(file_url, stream=True)
                if resp is not None and resp.status_code == 200:
                    OutputControls().printOutput(
                        colorText.GREEN
                        + "  [+] Downloading AI model (v2) for Nifty predictions, Please Wait.."
                        + colorText.END
                    )
                    try:
                        chunksize = 1024 * 1024 * 1
                        filesize = int(
                            int(resp.headers.get("content-length")) / chunksize
                        )
                        filesize = 1 if not filesize else filesize
                        bar, spinner = tools.getProgressbarStyle()
                        f = open(
                            os.path.join(
                                Archiver.get_user_data_dir(), file_url.split("/")[-1]
                            ),
                            "wb"
                        )
                        dl = 0
                        # with alive_bar(
                        #     filesize, bar=bar, spinner=spinner, manual=True
                        # ) as progressbar:
                        for data in resp.iter_content(chunk_size=chunksize):
                            dl += 1
                            f.write(data)
                                # progressbar(dl / filesize)
                                # if dl >= filesize:
                                #     progressbar(1.0)
                        f.close()
                    except KeyboardInterrupt: # pragma: no cover
                        raise KeyboardInterrupt
                    except Exception as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        OutputControls().printOutput("[!] Download Error - " + str(e))
            time.sleep(3)
        try:
            if os.path.isfile(files[0]) and os.path.isfile(files[1]):
                pkl = joblib.load(files[1])
                if Imports["keras"]:
                    try:
                        import keras
                    except: # pragma: no cover
                        OutputControls().printOutput("This installation might not work well, especially for NIFTY prediction. Please install 'keras' library on your machine!")
                        OutputControls().printOutput(
                                colorText.FAIL
                                + "  [+] 'Keras' library is not installed. You may wish to follow instructions from\n  [+] https://github.com/pkjmesra/PKScreener/"
                                + colorText.END
                            )
                        pass
                model = keras.models.load_model(files[0]) if Imports["keras"] else None
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            os.remove(files[0])
            os.remove(files[1])
            if not retrial:
                tools.getNiftyModel(retrial=True)
        if model is None:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] 'Keras' library is not installed. Prediction failed! You may wish to follow instructions from\n  [+] https://github.com/pkjmesra/PKScreener/"
                + colorText.END
            )
        return model, pkl

    def getSigmoidConfidence(x):
        out_min, out_max = 0, 100
        if x > 0.5:
            in_min = 0.50001
            in_max = 1
        else:
            in_min = 0
            in_max = 0.5
        return round(
            ((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min), 3
        )

    def alertSound(beeps=3, delay=0.2):
        for i in range(beeps):
            OutputControls().printOutput("\a")
            sleep(delay)
    
    def getMaxColumnWidths(df):
        columnWidths = [None]
        addnlColumnWidths = [40 if (x in ["Trend(22Prds)"] or "-Pd" in x) else (20 if (x in ["Pattern"]) else ((25 if (x in ["MA-Signal"]) else (10 if "ScanOption" in x else None)))) for x in df.columns]
        columnWidths.extend(addnlColumnWidths)
        columnWidths = columnWidths[:-1]
        return columnWidths
