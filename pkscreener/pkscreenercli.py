#!/usr/bin/python3
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
# Pyinstaller compile Windows: pyinstaller --onefile --icon=screenshots\icon.ico pkscreener\pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=screenshots/icon.ico pkscreener/pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress
import warnings
warnings.simplefilter("ignore", UserWarning,append=True)
import argparse
import builtins
import logging
import traceback

# Keep module imports prior to classes
import os
import sys
import tempfile
os.environ["PYTHONWARNINGS"]="ignore::UserWarning"
import multiprocessing

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    logging.getLogger("tensorflow").setLevel(logging.ERROR)
except Exception:# pragma: no cover
    pass

from time import sleep

from PKDevTools.classes import log as log
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from pkscreener import Imports
import pkscreener.classes.ConfigManager as ConfigManager

multiprocessing.freeze_support()
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"
# from pkscreener.classes.IntradayMonitor import intradayMonitorInstance

printenabled=False
originalStdOut=None
original__stdout=None
def decorator(func):
    def new_func(*args, **kwargs):
        if printenabled:
            try:
                func(*args,**kwargs)
            except Exception as e:# pragma: no cover
                default_logger().debug(e, exc_info=True)
                pass

    return new_func


# print = decorator(print) # current file
def disableSysOut(input=True, disable=True):
    global printenabled
    printenabled = not disable
    if disable:
        global originalStdOut, original__stdout
        if originalStdOut is None:
            builtins.print = decorator(builtins.print)  # all files
            if input:
                builtins.input = decorator(builtins.input)  # all files
            originalStdOut = sys.stdout
            original__stdout = sys.__stdout__
        sys.stdout = open(os.devnull, "w")
        sys.__stdout__ = open(os.devnull, "w")
    else:
        try:
            sys.stdout.close()
            sys.__stdout__.close()
        except Exception as e:# pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        sys.stdout = originalStdOut
        sys.__stdout__ = original__stdout

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument(
    "-a",
    "--answerdefault",
    help="Pass default answer to questions/choices in the application. Example Y, N",
    required=False,
)
argParser.add_argument(
    "--backtestdaysago",
    help="Run scanner for -b days ago from today.",
    required=False,
)
argParser.add_argument(
    "-c",
    "--croninterval",
    help="Pass interval in seconds to wait before the program is run again with same parameters",
    required=False,
)
argParser.add_argument(
    "-d",
    "--download",
    action="store_true",
    help="Only download Stock data in .pkl file (No analysis will be run)",
    required=False,
)
argParser.add_argument(
    "-e",
    "--exit",
    action="store_true",
    help="Exit right after executing just once",
    required=False,
)
argParser.add_argument(
    "--forceBacktestsForZeroResultDays",
    help="Force run the backtests even for those days when we already have zero results saved in the repo",
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument(
    "-i",
    "--intraday",
    help="Use Intraday configurations and use the candlestick duration that is passed. Acceptable values 1m, 5m, 10m, 15m, 1h etc.",
    required=False,
)
argParser.add_argument(
    "-m",
    "--monitor",
    action="store_true",
    help="Monitor for intraday scanners and their results.",
    required=False,
)
argParser.add_argument(
    "--maxdisplayresults",
    help="Maximum number of results to display.",
    required=False,
)
argParser.add_argument(
    "-o",
    "--options",
    help="Pass selected options in the <MainMenu>:<SubMenu>:<SubMenu>:etc. format. For example: ./pkscreenercli.py -a Y -o X:12:10 -e will run the screener with answer Y as default choice to questions and scan with menu choices: Scanners > Nifty (All Stocks) > Closing at least 2%% up since last 3 day",
    required=False,
)
argParser.add_argument(
    "-p",
    "--prodbuild",
    action="store_true",
    help="Run in production-build mode",
    required=False,
)
argParser.add_argument(
    "-t",
    "--testbuild",
    action="store_true",
    help="Run in test-build mode",
    required=False,
)
argParser.add_argument(
    "-u",
    "--user",
    help="Telegram user ID to whom the results must be sent.",
    required=False,
)
argParser.add_argument(
    "-l",
    "--log",
    action="store_true",
    help="Run with full logging enabled",
    required=False,
)
argParser.add_argument("-v", action="store_true")  # Dummy Arg for pytest -v
argsv = argParser.parse_known_args()
args = argsv[0]

configManager = ConfigManager.tools()


def logFilePath():
    try:
        from PKDevTools.classes import Archiver

        filePath = os.path.join(Archiver.get_user_outputs_dir(), "pkscreener-logs.txt")
        f = open(filePath, "w")
        f.write("Logger file for pkscreener!")
        f.close()
    except Exception:# pragma: no cover
        filePath = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
    return filePath


def setupLogger(shouldLog=False, trace=False):
    if not shouldLog:
        del os.environ['PKDevTools_Default_Log_Level']
        return
    log_file_path = logFilePath()

    if os.path.exists(log_file_path):
        try:
            os.remove(log_file_path)
        except Exception:# pragma: no cover
            pass
    print(colorText.FAIL + "\n[+] Logs will be written to:"+colorText.END)
    print(colorText.GREEN + f"[+] {log_file_path}"+colorText.END)
    print(colorText.FAIL + "[+] If you need to share, open this folder, copy and zip the log file to share.\n" + colorText.END)
    # logger = multiprocessing.log_to_stderr(log.logging.DEBUG)
    log.setup_custom_logger(
        "pkscreener",
        log.logging.DEBUG,
        trace=trace,
        log_file_path=log_file_path,
        filter=None,
    )
    os.environ["PKDevTools_Default_Log_Level"] = str(log.logging.DEBUG)

def warnAboutDependencies():
    if not Imports["talib"]:
        print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] TA-Lib is not installed. Looking for pandas_ta."
                + colorText.END
            )
        sleep(1)
        if Imports["pandas_ta"]:
            print(
                colorText.BOLD
                + colorText.GREEN
                + "[+] Found and falling back on pandas_ta.\n[+] For full coverage(candle patterns), you may wish to read the README file in PKScreener repo : https://github.com/pkjmesra/PKScreener \n[+] or follow instructions from\n[+] https://github.com/ta-lib/ta-lib-python"
                + colorText.END
            )
            sleep(1)
        else:
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Neither ta-lib nor pandas_ta was located. You need at least one of them to continue! \n[+] Please follow instructions from README file under PKScreener repo: https://github.com/pkjmesra/PKScreener"
                + colorText.END
            )
            input("Press any key to try anyway...")

def runApplication():
    from pkscreener.globals import main
    # From a previous call to main with args, it may have been mutated.
    # Let's stock to the original args passed by user
    argsv = argParser.parse_known_args()
    args = argsv[0]

    main(userArgs=args)


def pkscreenercli():
    global originalStdOut
    if sys.platform.startswith("darwin"):
        try:
            multiprocessing.set_start_method("fork")
        except RuntimeError as e:# pragma: no cover
            if "RUNNER" not in os.environ.keys() and ('PKDevTools_Default_Log_Level' in os.environ.keys() and os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
                print(
                    "[+] RuntimeError with 'multiprocessing'.\n[+] Please contact the Developer, if this does not work!"
                )
                print(e)
                traceback.print_exc()
            pass
    configManager.getConfig(ConfigManager.parser)
    # configManager.restartRequestsCache()

    if args.log or configManager.logsEnabled:
        setupLogger(shouldLog=True, trace=args.testbuild)
        if not args.prodbuild and args.answerdefault is None:
            input("Press <Enter> to continue...")
    else:
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            del os.environ['PKDevTools_Default_Log_Level']
            # os.environ["PKDevTools_Default_Log_Level"] = str(log.logging.NOTSET)
    # Import other dependency here because if we import them at the top
    # multiprocessing behaves in unpredictable ways
    import pkscreener.classes.Utility as Utility

    configManager.default_logger = default_logger()
    if originalStdOut is None:
        # Clear only if this is the first time it's being called from some
        # loop within workflowtriggers.
        Utility.tools.clearScreen(userArgs=args)
    warnAboutDependencies()
    if args.prodbuild:
        disableSysOut()

    if not configManager.checkConfigFile():
        configManager.setConfig(
            ConfigManager.parser, default=True, showFileCreatedText=False
        )
    if args.monitor:
        Utility.tools.clearScreen()
        print("Not Implemented Yet!")
        # intradayMonitorInstance.monitor()
        sys.exit(0)
    if args.intraday:
        configManager.toggleConfig(candleDuration=args.intraday, clearCache=False)
    else:
        configManager.toggleConfig(candleDuration='1d', clearCache=False)
    if args.options is not None and str(args.options) == "0":
        # Must be from unit tests to be able to break out of loops via eventing
        args.options = None

    if args.testbuild and not args.prodbuild:
        print(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Started in TestBuild mode!"
            + colorText.END
        )
        runApplication()
    elif args.download:
        print(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Download ONLY mode! Stocks will not be screened!"
            + colorText.END
        )
        if args.intraday is None:
            configManager.toggleConfig(candleDuration="1d", clearCache=False)
        runApplication()
        sys.exit(0)
    else:
        runApplicationForScreening()

def runLoopOnScheduleOrStdApplication(hasCronInterval):
    if hasCronInterval:
        scheduleNextRun()
    else:
        runApplication()

def runApplicationForScreening():
    try:
        shouldBreak = args.exit or args.user is not None or args.testbuild
        hasCronInterval = args.croninterval is not None and str(args.croninterval).isnumeric()
        runLoopOnScheduleOrStdApplication(hasCronInterval)
        while True:
            if shouldBreak:
                break
            runLoopOnScheduleOrStdApplication(hasCronInterval)
        if args.v:
            disableSysOut(disable=False)
            return
        sys.exit(0)
    except (RuntimeError, Exception) as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        if args.prodbuild:
            disableSysOut(disable=False)
        print(
            f"{e}\n[+] An error occurred! Please run with '-l' option to collect the logs.\n[+] For example, 'pkscreener -l' and then contact the developer!"
        )
        if "RUNNER" in os.environ.keys() or ('PKDevTools_Default_Log_Level' in os.environ.keys() and os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
            traceback.print_exc()
        if args.v:
            disableSysOut(disable=False)
            return
        sys.exit(0)


def scheduleNextRun():
    sleepUntilNextExecution = not PKDateUtilities.isTradingTime()
    while sleepUntilNextExecution:
        print(
            colorText.BOLD
            + colorText.FAIL
            + (
                "SecondsAfterClosingTime[%d] SecondsBeforeMarketOpen [%d]. Next run at [%s]"
                % (
                    int(PKDateUtilities.secondsAfterCloseTime()),
                    int(PKDateUtilities.secondsBeforeOpenTime()),
                    str(
                        PKDateUtilities.nextRunAtDateTime(
                            bufferSeconds=3600,
                            cronWaitSeconds=int(args.croninterval),
                        )
                    ),
                )
            )
            + colorText.END
        )
        if (PKDateUtilities.secondsAfterCloseTime() >= 3600) and (
            PKDateUtilities.secondsAfterCloseTime() <= (3600 + 1.5 * int(args.croninterval))
        ):
            sleepUntilNextExecution = False
        if (PKDateUtilities.secondsBeforeOpenTime() <= -3600) and (
            PKDateUtilities.secondsBeforeOpenTime() >= (-3600 - 1.5 * int(args.croninterval))
        ):
            sleepUntilNextExecution = False
        sleep(int(args.croninterval))
    print(
        colorText.BOLD + colorText.GREEN + "=> Going to fetch again!" + colorText.END,
        end="\r",
        flush=True,
    )
    sleep(3)
    runApplication()


if __name__ == "__main__":
    pkscreenercli()
