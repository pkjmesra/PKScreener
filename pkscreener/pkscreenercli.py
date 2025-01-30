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
# Pyinstaller compile Windows: pyinstaller --onefile --icon=screenshots\icon.ico pkscreener\pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive_progress
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=screenshots/icon.ico pkscreener/pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive_progress
import warnings
warnings.simplefilter("ignore", UserWarning,append=True)
import argparse
import builtins
import logging
import json
import traceback
import datetime
# Keep module imports prior to classes
import os
import csv
import re
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
import time

from PKDevTools.classes import log as log
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from pkscreener import Imports
from PKDevTools.classes.OutputControls import OutputControls
from pkscreener.classes.MarketMonitor import MarketMonitor
import pkscreener.classes.ConfigManager as ConfigManager

if __name__ == '__main__':
    multiprocessing.freeze_support()
    # fix to https://stackoverflow.com/q/62748654/9191338
    # Python incorrectly tracks shared memory even if it is not
    # created by the process. The following patch is a workaround.
    from unittest.mock import patch
    patch("multiprocessing.resource_tracker.register",lambda *args, **kwargs: None)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"

printenabled=False
originalStdOut=None
original__stdout=None
LoggedIn = False
cron_runs=0

def decorator(func):
    # @infer_global(new_func)
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
    global printenabled,originalStdOut, original__stdout
    printenabled = not disable
    if disable:
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
            if originalStdOut is not None and original__stdout is not None:
                sys.stdout.close()
                sys.__stdout__.close()
        except Exception as e:# pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        sys.stdout = originalStdOut if originalStdOut is not None else sys.stdout
        sys.__stdout__ = original__stdout if original__stdout is not None else sys.__stdout__

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
    "--barometer",
    action="store_true",
    help="Send global market barometer to telegram channel or a user",
    required=False,
)
argParser.add_argument(
    "--bot",
    action="store_true",
    help="Run only in telegram bot mode",
    required=False,
)
argParser.add_argument(
    "--botavailable",
    action="store_true",
    help="Enforce whether bot is going to be available or not.",
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
    "--fname",
    help="file name with results contents",
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
    help="Monitor for intraday scanners and their results.",
    nargs='?',
    const='X',
    type=str,
    required=False,
)
argParser.add_argument(
    "--maxdisplayresults",
    help="Maximum number of results to display.",
    required=False,
)
argParser.add_argument(
    "--maxprice",
    help="Maximum Price for the stock to be considered.",
    required=False,
)
argParser.add_argument(
    "--minprice",
    help="Minimum Price for the stock to be considered.",
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
    "--progressstatus",
    help="Pass default progress status that you'd like to get displayed when running the scans",
    required=False,
)
argParser.add_argument(
    "--runintradayanalysis",
    action="store_true",
    help="Run analysis for morning vs EoD LTP values",
    required=False,
)
argParser.add_argument(
    "--simulate",
    type=json.loads, # '{"isTrading":true,"currentDateTime":"2024-04-29 09:35:38"}'
    help="Simulate various conditions",
    required=False,
)
argParser.add_argument(
    "--singlethread",
    action="store_true",
    help="Run analysis for debugging purposes in a single process, single threaded environment",
    required=False,
)
argParser.add_argument(
    "--slicewindow",
    type=str,
    help="Time slice window value - a date or datetime string with timezone in international format",
    required=False,
)
argParser.add_argument(
    "--stocklist",
    type=str,
    help="Comma separated list of stocks passed from previous scan results",
    required=False,
)
argParser.add_argument(
    "--systemlaunched",
    action="store_true",
    help="Indicator to show that this is a system launched screener, using os.system",
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
    "--telegram",
    action="store_true",
    help="Run with an assumption that this instance is launched via telegram bot",
    required=False,
)
argParser.add_argument(
    "--triggertimestamp",
    help="Optionally, send the timestamp value when this was triggered",
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
argParser.add_argument(
    "--pipedtitle",
    help="Piped Titles",
    required=False,
)
argParser.add_argument(
    "--pipedmenus",
    help="Piped Menus",
    required=False,
)
argParser.add_argument(
    "--usertag",
    help="User defined tag value(s)",
    required=False,
)
argParser.add_argument(
    "--testalloptions",
    action="store_true",
    help="runs and tests all options",
    required=False,
)

def csv_split(s):
    return list(csv.reader([s], delimiter=' '))[0]

def re_split(s):
    def strip_quotes(s):
        if s and (s[0] == '"' or s[0] == "'") and s[0] == s[-1]:
            return s[1:-1]
        return s
    # pieces = [p for p in re.split("( |\\\".*?\\\"|'.*?')", s) if p.strip()]
    return [strip_quotes(p).replace('\\"', '"').replace("\\'", "'") for p in re.findall(r'(?:[^"\s]*"(?:\\.|[^"])*"[^"\s]*)+|(?:[^\'\s]*\'(?:\\.|[^\'])*\'[^\'\s]*)+|[^\s]+', s)]

def get_debug_args():
    global args
    try:
        if args is not None:
            # make sure that args are mutable
            args = list(args)
        return args
    except NameError as e: # pragma: no cover
        args = sys.argv[1:]
        if isinstance(args,list):
            if len(args) == 1:
                # re.findall(r'[^"\s]\S*|".+?"', line)
                # list(csv.reader([line], delimiter=" "))
                # pieces = [p for p in re.split("( |\\\".*?\\\"|'.*?')", test) if p.strip()]
                return re_split(args[0]) #args[0].split(" ")
            else:
                return args
        return None
    except TypeError as e: # pragma: no cover
        # NameSpace object is not iterable
        return args
    except Exception as e: # pragma: no cover
        return None
    # return ' --systemlaunched -a y -e -o "X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:" -u -1001785195297 --stocklist GLS,NESCO,SBICARD,DREAMFOLKS,JAGRAN,ACEINTEG,RAMASTEEL'.split(" ")

args = get_debug_args()
argsv = argParser.parse_known_args(args=args)
# argsv = argParser.parse_known_args()
args = argsv[0]
# args.slicewindow = "2024-09-06 10:55:12.481253+05:30"
results = None
resultStocks = None
plainResults = None
start_time = None
dbTimestamp = None
elapsed_time = None
configManager = ConfigManager.tools()


def exitGracefully():
    try:
        from PKDevTools.classes import Archiver
        from pkscreener.globals import resetConfigToDefault
        filePath = None
        try:
            filePath = os.path.join(Archiver.get_user_data_dir(), "monitor_outputs")
        except: # pragma: no cover
            pass
        if filePath is None:
            return
        index = 0
        while index < configManager.maxDashboardWidgetsPerRow*configManager.maxNumResultRowsInMonitor:
            try:
                os.remove(f"{filePath}_{index}.txt")
            except: # pragma: no cover
                pass
            index += 1

        argsv = argParser.parse_known_args()
        args = argsv[0]
        if args is not None and args.options is not None and not args.options.upper().startswith("T"):
            resetConfigToDefault(force=True)
            
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            if args is None or (args is not None and args.options is not None and "|" not in args.options):
                del os.environ['PKDevTools_Default_Log_Level']
        configManager.logsEnabled = False
        configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)
    except RuntimeError: # pragma: no cover
        OutputControls().printOutput(f"{colorText.WARN}If you're running from within docker, please run like this:{colorText.END}\n{colorText.FAIL}docker run -it pkjmesra/pkscreener:latest\n{colorText.END}")
        pass

def logFilePath():
    try:
        from PKDevTools.classes import Archiver

        filePath = os.path.join(Archiver.get_user_data_dir(), "pkscreener-logs.txt")
        f = open(filePath, "w")
        if f is not None:
            f.write("Logger file for pkscreener!")
            f.close()
    except Exception:# pragma: no cover
        filePath = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
    return filePath


def setupLogger(shouldLog=False, trace=False):
    if not shouldLog:
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            del os.environ['PKDevTools_Default_Log_Level']
        return
    log_file_path = logFilePath()

    if os.path.exists(log_file_path):
        try:
            os.remove(log_file_path)
        except Exception:# pragma: no cover
            pass
    OutputControls().printOutput(colorText.FAIL + "\n  [+] Logs will be written to:"+colorText.END)
    OutputControls().printOutput(colorText.GREEN + f"  [+] {log_file_path}"+colorText.END)
    OutputControls().printOutput(colorText.FAIL + "  [+] If you need to share, open this folder, copy and zip the log file to share.\n" + colorText.END)
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
        OutputControls().printOutput(
                colorText.FAIL
                + "  [+] TA-Lib is not installed. Looking for pandas_ta."
                + colorText.END
            )
        sleep(1)
        if Imports["pandas_ta"]:
            issueLink = "https://github.com/pkjmesra/PKScreener"
            issueLink = f"\x1b[97m\x1b]8;;{issueLink}\x1b\\{issueLink}\x1b]8;;\x1b\\\x1b[0m"
            taLink = "https://github.com/ta-lib/ta-lib-python"
            taLink = f"\x1b[97m\x1b]8;;{taLink}\x1b\\{taLink}\x1b]8;;\x1b\\\x1b[0m"
            OutputControls().printOutput(
                colorText.GREEN
                + f"  [+] Found and falling back on pandas_ta.\n  [+] For full coverage(candle patterns), you may wish to read the README file in PKScreener repo :  {issueLink}\n  [+] or follow instructions from\n  [+] {taLink}"
                + colorText.END
            )
            sleep(1)
        else:
            OutputControls().printOutput(
                colorText.FAIL
                + f"  [+] Neither ta-lib nor pandas_ta was located. You need at least one of them to continue! \n  [+] Please follow instructions from README file under PKScreener repo: {issueLink}"
                + colorText.END
            )
            OutputControls().takeUserInput("Press any key to try anyway...")
    
def runApplication():
    from pkscreener.globals import main, sendQuickScanResult,sendMessageToTelegramChannel, sendGlobalMarketBarometer, updateMenuChoiceHierarchy, isInterrupted, refreshStockData, closeWorkersAndExit, resetUserMenuChoiceOptions,menuChoiceHierarchy
    # From a previous call to main with args, it may have been mutated.
    # Let's stock to the original args passed by user
    try:
        savedPipedArgs = None
        savedPipedArgs = args.pipedmenus if args is not None and args.pipedmenus is not None else None
    except: # pragma: no cover
        pass
    global results, resultStocks, plainResults, dbTimestamp, elapsed_time, start_time,argParser
    from pkscreener.classes.MenuOptions import menus, PREDEFINED_SCAN_MENU_TEXTS, PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS,PREDEFINED_SCAN_MENU_VALUES
    args = get_debug_args()
    monitorOption = None
    if not isinstance(args,argparse.Namespace) and not hasattr(args, "side_effect"):
        argsv = argParser.parse_known_args(args=args)
        # argsv = argParser.parse_known_args()
        args = argsv[0]
    # During the previous run, we may have made several changes to the original args variable.
    # We need to re-load the original args
    if args is not None and not args.exit and not args.monitor:
        argsv = argParser.parse_known_args()
        args = argsv[0]
    # args.slicewindow = "2024-09-06 10:55:12.481253+05:30"
    if args.user is None:
        from PKDevTools.classes.Environment import PKEnvironment
        Channel_Id, _, _, _ = PKEnvironment().secrets
        if Channel_Id is not None and len(str(Channel_Id)) > 0:
            args.user = int(f"-{Channel_Id}")
    if args.triggertimestamp is None:
        args.triggertimestamp = int(PKDateUtilities.currentDateTimestamp())
    else:
        args.triggertimestamp = int(args.triggertimestamp)
    if args.systemlaunched and args.options is not None:
        args.systemlaunched = args.options
    
    # if sys.argv[0].endswith(".py"):
    #     args.monitor = 'X'
    #     args.answerdefault = 'Y'
    args.pipedmenus = savedPipedArgs
    if args.options is not None:
        args.options = args.options.replace("::",":").replace("\"","").replace("'","")
        if args.options.upper().startswith("C") or "C:" in args.options.upper():
            args.runintradayanalysis = True
        args,choices = updateProgressStatus(args)
        
    if args.runintradayanalysis:
        generateIntradayAnalysisReports(args)
    else:
        if args.testalloptions:
            allMenus,_ = menus.allMenus(index=0)
            for scanOption in allMenus:
                 args.options = f"{scanOption}:SBIN,"
                 _, _ = main(userArgs=args)
            sys.exit(0)

        if args.barometer:
            sendGlobalMarketBarometer(userArgs=args)
            sys.exit(0)
        else:
            monitorOption_org = ""
            # args.monitor = configManager.defaultMonitorOptions
            if args.monitor:
                args.monitor = args.monitor.replace("::",":").replace("\"","").replace("'","")
                configManager.getConfig(ConfigManager.parser)
                args.answerdefault = args.answerdefault or 'Y'
                MarketMonitor().hiddenColumns = configManager.alwaysHiddenDisplayColumns
                if MarketMonitor().monitorIndex == 0:
                    dbTimestamp = PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
                    elapsed_time = 0
                    if start_time is None:
                        start_time = time.time()
                    else:
                        elapsed_time = round(time.time() - start_time,2)
                        start_time = time.time()
                monitorOption_org = MarketMonitor().currentMonitorOption()
                monitorOption = monitorOption_org.replace("::",":").replace("\"","").replace("'","")
                monitorOption = checkIntradayComponent(args, monitorOption)
                if monitorOption.startswith("|"):
                    monitorOption = monitorOption[1:]
                    monitorOptions = monitorOption.split(":")
                    if monitorOptions[1] != "0":
                        monitorOptions[1] = "0"
                        monitorOption = ":".join(monitorOptions)
                    # We need to pipe the output from previous run into the next one
                    if monitorOption.startswith("{") and "}" in monitorOption:
                        srcIndex = monitorOption.split("}")[0].split("{")[-1]
                        monitorOption="".join(monitorOption.split("}")[1:])
                        try:
                            srcIndex = int(srcIndex)
                            # Let's get the previously saved result for the monitor
                            savedStocks = MarketMonitor().monitorResultStocks[str(srcIndex)]
                            innerPipes = monitorOption.split("|")
                            nextPipe = innerPipes[0]
                            nextMonitor = nextPipe.split(">")[0]
                            innerPipes[0] = f"{nextMonitor}:{savedStocks}"
                            monitorOption = ":>|".join(innerPipes)
                            monitorOption = monitorOption.replace("::",":").replace(":>:>",":>")
                            # monitorOption = f"{monitorOption}:{savedStocks}:"
                        except: # pragma: no cover
                            # Probably wrong (non-integer) index passed. Let's continue anyway
                            pass
                    elif resultStocks is not None:
                        resultStocks = ",".join(resultStocks)
                        monitorOption = f"{monitorOption}:{resultStocks}"
                args.options = monitorOption.replace("::",":")
                fullMonitorMode = MarketMonitor().monitorIndex == 1 and args.options is not None and plainResults is not None
                partMonitorMode = len(MarketMonitor().monitors) == 1 and args.options is not None and plainResults is not None
                if (fullMonitorMode or partMonitorMode):
                    # Load the stock data afresh for each cycle
                    refreshStockData(args.options)
            try:
                results = None
                plainResults = None
                resultStocks = None
                if args is not None and ((args.options is not None and "|" in args.options) or args.systemlaunched):
                    args.maxdisplayresults = 2000
                updateConfigDurations(args=args)
                updateConfig(args=args)
                results, plainResults = main(userArgs=args)
                if args.pipedmenus is not None:
                    while args.pipedmenus is not None:
                        args,_ = updateProgressStatus(args,monitorOptions=monitorOption)
                        results, plainResults = main(userArgs=args)
                    # sys.exit(0)
                if isInterrupted():
                    closeWorkersAndExit()
                    exitGracefully()
                    sys.exit(0)
                runPipedScans = True
                while runPipedScans:
                    runPipedScans = pipeResults(plainResults,args)
                    if runPipedScans:
                        args,_ = updateProgressStatus(args,monitorOptions=monitorOption)
                        results, plainResults = main(userArgs=args)
                    else:
                        if args is not None and args.pipedtitle is not None and "|" in args.pipedtitle:
                            OutputControls().printOutput(
                                    colorText.WARN
                                    + f"  [+] Pipe Results Found: {args.pipedtitle}. {'Reduce number of piped scans if no stocks could be found.' if '[0]' in args.pipedtitle else ''}"
                                    + colorText.END
                                )
                            if args.answerdefault is None:
                                OutputControls().takeUserInput("Press <Enter> to continue...")
            except SystemExit: # pragma: no cover
                closeWorkersAndExit()
                exitGracefully()
                sys.exit(0)
            except KeyboardInterrupt: # pragma: no cover
                closeWorkersAndExit()
                exitGracefully()
                sys.exit(0)
            except Exception as e: # pragma: no cover
                default_logger().debug(e, exc_info=True)
                if args.log:
                    traceback.print_exc()
                # Probably user cancelled an operation by choosing a cancel sub-menu somewhere
                pass
            if plainResults is not None and not plainResults.empty:
                try:
                    plainResults.set_index("Stock", inplace=True)
                except: # pragma: no cover
                    pass
                try:
                    results.set_index("Stock", inplace=True)
                except: # pragma: no cover
                    pass
                plainResults = plainResults[~plainResults.index.duplicated(keep='first')]
                results = results[~results.index.duplicated(keep='first')]
                resultStocks = plainResults.index
            if args.monitor is not None:
                MarketMonitor().saveMonitorResultStocks(plainResults)
                if results is not None and len(monitorOption_org) > 0:
                    chosenMenu = args.pipedtitle if args.pipedtitle is not None else updateMenuChoiceHierarchy()
                    MarketMonitor().refresh(screen_df=results,screenOptions=monitorOption_org, chosenMenu=chosenMenu[:120],dbTimestamp=f"{dbTimestamp} | CycleTime:{elapsed_time}s",telegram=args.telegram)
                    menuChoiceHierarchy = ""
                    args.pipedtitle = ""

def updateProgressStatus(args,monitorOptions=None):
    from pkscreener.classes.MenuOptions import PREDEFINED_SCAN_MENU_TEXTS,PREDEFINED_SCAN_MENU_VALUES
    try:
        choices = ""
        if args.systemlaunched or monitorOptions is not None:
            optionsToUse = args.options if monitorOptions is None else monitorOptions
            choices = f"--systemlaunched -a y -e -o '{optionsToUse.replace('C:','X:').replace('D:','')}'"
            from pkscreener.classes.MenuOptions import INDICES_MAP
            searchChoices = choices
            for indexKey in INDICES_MAP.keys():
                if indexKey.isnumeric():
                    searchChoices = searchChoices.replace(f"X:{indexKey}:","X:12:")
            indexNum = PREDEFINED_SCAN_MENU_VALUES.index(searchChoices)
            selectedIndexOption = choices.split(":")[1]
            choices = f"P_1_{str(indexNum +1)}_{str(selectedIndexOption)}" if ">|" in choices else choices
            args.progressstatus = f"  [+] {choices} => Running {choices}"
            args.usertag = PREDEFINED_SCAN_MENU_TEXTS[indexNum]
            args.maxdisplayresults = 2000 #if monitorOptions is None else 100
    except: # pragma: no cover
        choices = ""
        pass
    return args, choices

def generateIntradayAnalysisReports(args):
    from pkscreener.globals import main, isInterrupted, closeWorkersAndExit, resetUserMenuChoiceOptions
    from pkscreener.classes.MenuOptions import menus, PREDEFINED_SCAN_MENU_TEXTS, PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS,PREDEFINED_SCAN_MENU_VALUES
    from PKDevTools.classes import Archiver
    maxdisplayresults = configManager.maxdisplayresults
    configManager.maxdisplayresults = 2000
    configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    runOptions = []
    otherMenus = []
    if len(args.options.split(":")) >= 4:
        runOptions = [args.options]
    else:
        runOptions = PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS
            # otherMenus =  menus.allMenus(topLevel="C", index=12)
        if len(otherMenus) > 0:
            runOptions.extend(otherMenus)
    import pandas as pd
    optionalFinalOutcome_df = pd.DataFrame()
    import pkscreener.classes.Utility as Utility
    # Delete any existing data from the previous run.
    configManager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(),pattern="stock_data_*.pkl")
    analysis_index = 1
    for runOption in runOptions:
        try:
            runOptionName = f"--systemlaunched -a y -e -o '{runOption.replace('C:','X:').replace('D:','')}'"
            indexNum = PREDEFINED_SCAN_MENU_VALUES.index(runOptionName)
            runOptionName = f"{'  [+] P_1_'+str(indexNum +1) if '>|' in runOption else runOption}"
        except Exception as e: # pragma: no cover
            default_logger().debug(e,exc_info=True)
            runOptionName = f"  [+] {runOption.replace('D:','').replace(':D','').replace(':','_').replace('_D','').replace('C_','X_')}"
            pass
        args.progressstatus = f"{runOptionName} => Running Intraday Analysis: {analysis_index} of {len(runOptions)}..."
        analysisOptions = runOption.split("|")
        analysisOptions[-1] = analysisOptions[-1].replace("X:","C:")
        runOption = "|".join(analysisOptions)
        args.options = runOption
        try:
            results,plainResults = main(userArgs=args,optionalFinalOutcome_df=optionalFinalOutcome_df)
            if args.pipedmenus is not None:
                while args.pipedmenus is not None:
                    results, plainResults = main(userArgs=args)
            if isInterrupted():
                closeWorkersAndExit()
                exitGracefully()
                sys.exit(0)
            runPipedScans = True
            while runPipedScans:
                runPipedScans = pipeResults(plainResults,args)
                if runPipedScans:
                    results, plainResults = main(userArgs=args,optionalFinalOutcome_df=optionalFinalOutcome_df)
            if results is not None and len(results) >= len(optionalFinalOutcome_df) and not results.empty and len(results.columns) > 5:
                import numpy as np
                if "%Chng" in results.columns and "EoDDiff" in results.columns:
                    optionalFinalOutcome_df = results
            if optionalFinalOutcome_df is not None and "EoDDiff" not in optionalFinalOutcome_df.columns:
                # Somehow the file must have been corrupted. Let's re-download
                configManager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl")
                configManager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(), pattern="*intraday_stock_data_*.pkl")
            if isInterrupted():
                break
        except KeyboardInterrupt: # pragma: no cover
            closeWorkersAndExit()
            exitGracefully()
            sys.exit(0)
        except Exception as e: # pragma: no cover
            OutputControls().printOutput(e)
            if args.log:
                traceback.print_exc()
        resetUserMenuChoiceOptions()
        analysis_index += 1
            # saveSendFinalOutcomeDataframe(optionalFinalOutcome_df)

    configManager.maxdisplayresults = maxdisplayresults
    configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    saveSendFinalOutcomeDataframe(optionalFinalOutcome_df)

def saveSendFinalOutcomeDataframe(optionalFinalOutcome_df):
    import pandas as pd
    from pkscreener.classes import Utility
    from pkscreener.globals import sendQuickScanResult,showBacktestResults

    if optionalFinalOutcome_df is not None and not optionalFinalOutcome_df.empty:
        final_df = None
        try:
            optionalFinalOutcome_df.drop('FairValue', axis=1, inplace=True, errors="ignore")
            df_grouped = optionalFinalOutcome_df.groupby("Stock")
            for stock, df_group in df_grouped:
                if stock == "BASKET":
                    if final_df is None:
                        final_df = df_group[["Pattern","LTP","LTP@Alert","SqrOffLTP","SqrOffDiff","EoDDiff","DayHigh","DayHighDiff"]]
                    else:
                        final_df = pd.concat([final_df, df_group[["Pattern","LTP","LTP@Alert","SqrOffLTP","SqrOffDiff","EoDDiff","DayHigh","DayHighDiff"]]], axis=0)
        except: # pragma: no cover
            pass
        if final_df is not None and not final_df.empty:
            with pd.option_context('mode.chained_assignment', None):
                final_df = final_df[["Pattern","LTP@Alert","LTP","EoDDiff","SqrOffLTP","SqrOffDiff","DayHigh","DayHighDiff"]]
                final_df.rename(
                        columns={
                            "Pattern": "Scan Name",
                            "LTP@Alert": "Basket Value@Alert",
                            "LTP": "Basket Value@EOD",
                            "SqrOffLTP": "Basket Value@SqrOff",
                            "DayHigh": "Basket Value@DayHigh",
                            },
                            inplace=True,
                        )
                final_df.dropna(inplace=True)
                final_df.dropna(how= "all", axis=1, inplace=True)
            mark_down = colorText.miniTabulator().tabulate(
                                    final_df,
                                    headers="keys",
                                    tablefmt=colorText.No_Pad_GridFormat,
                                    showindex = False
                                ).encode("utf-8").decode(Utility.STD_ENCODING)
            showBacktestResults(final_df,optionalName="Intraday_Backtest_Result_Summary",choices="Summary")
            OutputControls().printOutput(mark_down)
            from PKDevTools.classes.Environment import PKEnvironment
            Channel_Id, _, _, _ = PKEnvironment().secrets
            if Channel_Id is not None and len(str(Channel_Id)) > 0:
                sendQuickScanResult(menuChoiceHierarchy="IntradayAnalysis",
                                        user=int(f"-{Channel_Id}"),
                                        tabulated_results=mark_down,
                                        markdown_results=mark_down,
                                        caption="Intraday Analysis Summary - Morning alert vs Market Close",
                                        pngName= f"PKS_IA_{PKDateUtilities.currentDateTime().strftime('%Y-%m-%d_%H:%M:%S')}",
                                        pngExtension= ".png",
                                        forceSend=True
                                        )

def checkIntradayComponent(args, monitorOption):
    lastComponent = monitorOption.split(":")[-1]
    if "i" not in lastComponent:
        possiblePositions = monitorOption.split(":i")
        if len(possiblePositions) > 1:
            lastComponent = f"i {possiblePositions[1]}"
                # previousCandleDuration = configManager.duration
    if "i" in lastComponent:
        # We need to switch to intraday scan
        monitorOption = monitorOption.replace(lastComponent,"")
        args.intraday = lastComponent.replace("i","").strip()
        configManager.toggleConfig(candleDuration=args.intraday, clearCache=False)
        # args.options = f"{monitorOption}:{args.options[len(lastComponent):]}"
    else:
        # We need to switch to daily scan
        args.intraday = None
        configManager.toggleConfig(candleDuration='1d', clearCache=False)
    return monitorOption

def updateConfigDurations(args):
    if args is None or args.options is None:
        return
    nextOnes = args.options.split(">")
    if len(nextOnes) > 1:
        monitorOption = nextOnes[0]
        if len(monitorOption) == 0:
            return
        lastComponent = ":".join(monitorOption.split(":")[-2:])
        if "i" in lastComponent and "," not in lastComponent and " " in lastComponent:
            if "i" in lastComponent.split(":")[-2]:
                lastComponent = lastComponent.split(":")[-2]
            else:
                lastComponent = lastComponent.split(":")[-1]
            # We need to switch to intraday scan
            args.intraday = lastComponent.replace("i","").strip()
            configManager.toggleConfig(candleDuration=args.intraday, clearCache=False)
        else:
            # We need to switch to daily scan
            args.intraday = None
            configManager.toggleConfig(candleDuration='1d', clearCache=False)

def pipeResults(prevOutput,args):
    if args is None or args.options is None:
        return False
    hasFoundStocks = False
    nextOnes = args.options.split(">")
    if len(nextOnes) > 1:
        monitorOption = nextOnes[1]
        if len(monitorOption) == 0:
            return False
        lastComponent = ":".join(monitorOption.split(":")[-2:])
        if "i" in lastComponent and "," not in lastComponent and " " in lastComponent:
            if "i" in lastComponent.split(":")[-2]:
                lastComponent = lastComponent.split(":")[-2]
            else:
                lastComponent = lastComponent.split(":")[-1]
            # We need to switch to intraday scan
            monitorOption = monitorOption.replace(lastComponent,"")
            args.intraday = lastComponent.replace("i","").strip()
            configManager.toggleConfig(candleDuration=args.intraday, clearCache=False)
        else:
            # We need to switch to daily scan
            args.intraday = None
            configManager.toggleConfig(candleDuration='1d', clearCache=False)
        if monitorOption.startswith("|"):
            monitorOption = monitorOption.replace("|","")
            monitorOptions = monitorOption.split(":")
            if monitorOptions[0].upper() in ["X","C"] and monitorOptions[1] != "0":
                monitorOptions[1] = "0"
                monitorOption = ":".join(monitorOptions)
            if "B" in monitorOptions[0].upper() and monitorOptions[1] != "30":
                monitorOption = ":".join(monitorOptions).upper().replace(f"{monitorOptions[0].upper()}:{monitorOptions[1]}",f"{monitorOptions[0].upper()}:30:{monitorOptions[1]}")
            # We need to pipe the output from previous run into the next one
            if prevOutput is not None and not prevOutput.empty:
                try:
                    prevOutput.set_index("Stock", inplace=True)
                except: # pragma: no cover
                    pass
                prevOutput_results = prevOutput[~prevOutput.index.duplicated(keep='first')]
                prevOutput_results = prevOutput_results.index
                hasFoundStocks = len(prevOutput_results) > 0
                prevOutput_results = ",".join(prevOutput_results)
                monitorOption = monitorOption.replace(":D:",":")
                monitorOption = f"{monitorOption}:{prevOutput_results}"
        args.options = monitorOption.replace("::",":")
        args.options = args.options + ":D:>" + ":D:>".join(nextOnes[2:])
        args.options = args.options.replace("::",":")
        return True and hasFoundStocks
    return False

def removeOldInstances():
    import glob
    pattern = "pkscreenercli*"
    thisInstance = sys.argv[0]
    for f in glob.glob(pattern, root_dir=os.getcwd(), recursive=True):
        fileToDelete = f if (os.sep in f and f.startswith(thisInstance[:10])) else os.path.join(os.getcwd(),f)
        if not fileToDelete.endswith(thisInstance):
            try:
                os.remove(fileToDelete)
            except: # pragma: no cover
                pass

def updateConfig(args):
    if args is None:
        return
    configManager.getConfig(ConfigManager.parser)
    if args.intraday:
        configManager.toggleConfig(candleDuration=args.intraday, clearCache=False)
        if configManager.candlePeriodFrequency not in ["d","mo"] or configManager.candleDurationFrequency not in ["m"]:
            configManager.period = "1d"
            configManager.duration = args.intraday
            configManager.setConfig(ConfigManager.parser,default=True, showFileCreatedText=False)
    elif configManager.candlePeriodFrequency not in ["y","max","mo"] or configManager.candleDurationFrequency not in ["d","wk","mo","h"]:
        if args.answerdefault is not None or args.systemlaunched:
            configManager.period = "1y"
            configManager.duration = "1d"
            configManager.setConfig(ConfigManager.parser,default=True, showFileCreatedText=False)

def pkscreenercli():
    global originalStdOut, args
    if sys.platform.startswith("darwin"):
        try:
            multiprocessing.set_start_method("fork")
        except RuntimeError as e:# pragma: no cover
            if "RUNNER" not in os.environ.keys() and ('PKDevTools_Default_Log_Level' in os.environ.keys() and os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
                OutputControls().printOutput(
                    "  [+] RuntimeError with 'multiprocessing'.\n  [+] Please contact the Developer, if this does not work!"
                )
                OutputControls().printOutput(e)
                traceback.print_exc()
            pass
    try:
        removeOldInstances()
        OutputControls(enableMultipleLineOutput=(args is None or args.monitor is None or args.runintradayanalysis),enableUserInput=(args is None or args.answerdefault is None)).printOutput("",end="\r")
        configManager.getConfig(ConfigManager.parser)
        userAcceptance = configManager.tosAccepted
        if not configManager.tosAccepted:
            if (args is not None and args.answerdefault is not None and str(args.answerdefault).lower() == "n"):
                OutputControls().printOutput(f"{colorText.FAIL}You seem to have passed disagreement to the Disclaimer and Terms Of Service of PKScreener by passing in {colorText.END}{colorText.WARN}--answerdefault N or -a N{colorText.END}. Exiting now!")
                sleep(5)
                sys.exit(0)
            allArgs = args.__dict__
            disclaimerLink = '\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b\\https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b]8;;\x1b\\\x1b[0m'
            tosLink = '\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/tos.txt\x1b\\https://pkjmesra.github.io/PKScreener/tos.txt\x1b]8;;\x1b\\\x1b[0m'
            for argKey in allArgs.keys():
                arg = allArgs[argKey]
                if arg is not None and arg:
                    userAcceptance = True
                    OutputControls().printOutput(f"{colorText.GREEN}By using this Software and passing a value for [{argKey}={arg}], you agree to\n[+] having read through the Disclaimer{colorText.END} ({disclaimerLink})\n[+]{colorText.GREEN} and accept Terms Of Service {colorText.END}({tosLink}){colorText.GREEN} of PKScreener. {colorText.END}\n[+] {colorText.WARN}If that is not the case, you MUST immediately terminate PKScreener by pressing Ctrl+C now!{colorText.END}")
                    sleep(2)
                    break
        if not userAcceptance and ((args is not None and args.answerdefault is not None and str(args.answerdefault).lower() != "y") or (args is not None and args.answerdefault is None)):
            userAcceptance = OutputControls().takeUserInput(f"{colorText.WARN}By using this Software, you agree to\n[+] having read through the Disclaimer {colorText.END}({disclaimerLink}){colorText.WARN}\n[+] and accept Terms Of Service {colorText.END}({tosLink}){colorText.WARN} of PKScreener ? {colorText.END}(Y/N){colorText.GREEN} [Default: {colorText.END}{colorText.FAIL}N{colorText.END}{colorText.GREEN}] :{colorText.END}",defaultInput="N",enableUserInput=True) or "N"
            if str(userAcceptance).lower() != "y":
                OutputControls().printOutput(f"\n{colorText.WARN}You seem to have\n    [+] passed disagreement to the Disclaimer and \n    [+] not accepted Terms Of Service of PKScreener.\n{colorText.END}{colorText.FAIL}[+] You MUST read and agree to the disclaimer and MUST accept the Terms of Service to use PKScreener.{colorText.END}\n\n{colorText.WARN}Exiting now!{colorText.END}")
                sleep(5)
                sys.exit(0)
        try:
            from pkscreener.classes import VERSION
            # Reset logging. If the user indeed passed the --log flag, it will be enabled later anyways
            del os.environ['PKDevTools_Default_Log_Level']
        except: # pragma: no cover
            pass
        configManager.logsEnabled = False
        configManager.tosAccepted = True
        configManager.appVersion = VERSION
        configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)
        import atexit
        atexit.register(exitGracefully)
        # Set the trigger timestamp
        if args.triggertimestamp is None:
            args.triggertimestamp = int(PKDateUtilities.currentDateTimestamp())
        else:
            args.triggertimestamp = int(args.triggertimestamp)
        # configManager.restartRequestsCache()
        # args.monitor = configManager.defaultMonitorOptions
        if args.monitor is not None:
            from pkscreener.classes.MenuOptions import NA_NON_MARKET_HOURS
            configuredMonitorOptions = configManager.defaultMonitorOptions.split("~") if len(configManager.myMonitorOptions) < 1 else configManager.myMonitorOptions.split("~")
            for monitorOption in NA_NON_MARKET_HOURS:
                if monitorOption in configuredMonitorOptions and not PKDateUtilities.isTradingTime():
                    # These can't be run in non-market hours
                    configuredMonitorOptions.remove(monitorOption)
            MarketMonitor(monitors=args.monitor.split("~") if len(args.monitor) > 5 else configuredMonitorOptions,
                        maxNumResultsPerRow=configManager.maxDashboardWidgetsPerRow,
                        maxNumColsInEachResult=6,
                        maxNumRowsInEachResult=10,
                        maxNumResultRowsInMonitor=configManager.maxNumResultRowsInMonitor,
                        pinnedIntervalWaitSeconds=configManager.pinnedMonitorSleepIntervalSeconds,
                        alertOptions=configManager.soundAlertForMonitorOptions.split("~"))

        if args.log or configManager.logsEnabled:
            setupLogger(shouldLog=True, trace=args.testbuild)
            if not args.prodbuild and args.answerdefault is None:
                try:
                    OutputControls().takeUserInput("Press <Enter> to continue...")
                except EOFError: # pragma: no cover
                    OutputControls().printOutput(f"{colorText.WARN}If you're running from within docker, please run like this:{colorText.END}\n{colorText.FAIL}docker run -it pkjmesra/pkscreener:latest\n{colorText.END}")
                    pass
        else:
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                del os.environ['PKDevTools_Default_Log_Level']
                # os.environ["PKDevTools_Default_Log_Level"] = str(log.logging.NOTSET)
        if args.simulate:
            os.environ["simulation"] = json.dumps(args.simulate)
        elif "simulation" in os.environ.keys():
            del os.environ['simulation']
        # Import other dependency here because if we import them at the top
        # multiprocessing behaves in unpredictable ways
        import pkscreener.classes.Utility as Utility

        configManager.default_logger = default_logger()
        if originalStdOut is None:
            # Clear only if this is the first time it's being called from some
            # loop within workflowtriggers.
            Utility.tools.clearScreen(userArgs=args, clearAlways=True)
        warnAboutDependencies()
        if args.prodbuild:
            if args.options and len(args.options.split(":")) > 0:
                indexOption = 0
                doNotDisableGlobalPrint = False
                while indexOption <= 15: # Max integer menu index in level1_X_MenuDict in MenuOptions.py
                    # Menu option 30 is for ATR trailing stops which uses vectorbt
                    # which in turn uses numba which requires print function to be inferred globally
                    # If we try to override print with new_func, it expects this new_func
                    # to be globally available. So to avoid these changes, let's just skip
                    # prodmode for menu option 30
                    doNotDisableGlobalPrint = f":{indexOption}:30:" in args.options
                    if doNotDisableGlobalPrint:
                        break
                    indexOption += 1
                if not doNotDisableGlobalPrint:
                    disableSysOut()
            else:
                disableSysOut()

        if not configManager.checkConfigFile():
            configManager.setConfig(
                ConfigManager.parser, default=True, showFileCreatedText=False
            )
        from pkscreener.classes.PKUserRegistration import PKUserRegistration, ValidationResult
        if args.systemlaunched and not PKUserRegistration.validateToken()[0]:
            result = PKUserRegistration.login()
            if result != ValidationResult.Success:
                OutputControls().printOutput(f"\n[+] {colorText.FAIL}You MUST be a premium/paid user to use this feature!{colorText.END}\n")
                input("Press any key to exit...")
                sys.exit(0)

        if args.systemlaunched and args.options is not None:
            args.systemlaunched = args.options
            
        if args.telegram:
            # Launched by bot for intraday monitor?
            if (PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]) or ("PKDevTools_Default_Log_Level" in os.environ.keys()):
                from PKDevTools.classes import Archiver
                filePath = os.path.join(Archiver.get_user_data_dir(), "monitor_outputs_1.txt")
                if os.path.exists(filePath):
                    default_logger().info("monitor_outputs_1.txt already exists! This means an instance may already be running. Exiting now...")
                    # Since the file exists, it means, there is another instance running
                    return
            else:
                # It should have been launched only during the trading hours
                default_logger().info("--telegram option must be launched ONLY during NSE trading hours. Exiting now...")
                return
        # Check and see if we're running only the telegram bot
        if args.bot:
            from pkscreener import pkscreenerbot
            pkscreenerbot.runpkscreenerbot(availability=args.botavailable)
            return
        updateConfig(args)
        if args.options is not None:
            if str(args.options) == "0":
                # Must be from unit tests to be able to break out of loops via eventing
                args.options = None
            args.options = args.options.replace("::",":")
        
        if args.maxprice:
            configManager.maxLTP = args.maxprice
            configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        if args.minprice:
            configManager.minLTP = args.minprice
            configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        global LoggedIn
        if not LoggedIn and not args.telegram and not args.bot and not args.systemlaunched and not args.testbuild:
            from pkscreener.classes.PKUserRegistration import PKUserRegistration
            if not PKUserRegistration.login():
                sys.exit(0)
            LoggedIn = True
        if args.testbuild and not args.prodbuild:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] Started in TestBuild mode!"
                + colorText.END
            )
            runApplication()
            from pkscreener.globals import closeWorkersAndExit
            closeWorkersAndExit()
            exitGracefully()
            sys.exit(0)
        elif args.download:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] Download ONLY mode! Stocks will not be screened!"
                + colorText.END
            )
            configManager.restartRequestsCache()
            # if args.intraday is None:
            #     configManager.toggleConfig(candleDuration="1d", clearCache=False)
            runApplication()
            from pkscreener.globals import closeWorkersAndExit
            closeWorkersAndExit()
            exitGracefully()
            sys.exit(0)
        else:
            runApplicationForScreening()
    except KeyboardInterrupt: # pragma: no cover
        from pkscreener.globals import closeWorkersAndExit
        closeWorkersAndExit()
        exitGracefully()
        sys.exit(0)
    except Exception as e: # pragma: no cover
        if "RUNNER" not in os.environ.keys() and ('PKDevTools_Default_Log_Level' in os.environ.keys() and os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
                OutputControls().printOutput(
                    "  [+] RuntimeError with 'multiprocessing'.\n  [+] Please contact the Developer, if this does not work!"
                )
                OutputControls().printOutput(e)
                traceback.print_exc()
        pass

def runLoopOnScheduleOrStdApplication(hasCronInterval):
    if hasCronInterval:
        scheduleNextRun()
    else:
        runApplication()

def runApplicationForScreening():
    from pkscreener.globals import closeWorkersAndExit
    try:
        hasCronInterval = args.croninterval is not None and str(args.croninterval).isnumeric()
        shouldBreak = (args.exit and not hasCronInterval)or args.user is not None or args.testbuild
        runLoopOnScheduleOrStdApplication(hasCronInterval)
        while True:
            if shouldBreak:
                break
            runLoopOnScheduleOrStdApplication(hasCronInterval)
        if args.v:
            disableSysOut(disable=False)
            return
        closeWorkersAndExit()
        exitGracefully()
        sys.exit(0)
    except SystemExit: # pragma: no cover
        closeWorkersAndExit()
        exitGracefully()
        sys.exit(0)
    except (RuntimeError, Exception) as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        if args.prodbuild:
            disableSysOut(disable=False)
        OutputControls().printOutput(
            f"{e}\n  [+] An error occurred! Please run with '-l' option to collect the logs.\n  [+] For example, 'pkscreener -l' and then contact the developer!"
        )
        if "RUNNER" in os.environ.keys() or ('PKDevTools_Default_Log_Level' in os.environ.keys() and os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
            traceback.print_exc()
        if args.v:
            disableSysOut(disable=False)
            return
        closeWorkersAndExit()
        exitGracefully()
        sys.exit(0)


def scheduleNextRun():
    sleepUntilNextExecution = not PKDateUtilities.isTradingTime()
    while sleepUntilNextExecution:
        OutputControls().printOutput(
            colorText.FAIL
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
    global cron_runs
    if cron_runs > 0:
        OutputControls().printOutput(
            colorText.GREEN + f'=> Going to fetch again in {int(args.croninterval)} sec. at {(PKDateUtilities.currentDateTime() + datetime.timedelta(seconds=120)).strftime("%Y-%m-%d %H:%M:%S")} IST...' + colorText.END,
            end="\r",
            flush=True,
        )
        sleep(int(args.croninterval) if not args.testbuild else 3)
    runApplication()
    cron_runs += 1

if __name__ == "__main__":
    try:
        pkscreenercli()
    except KeyboardInterrupt: # pragma: no cover
        from pkscreener.globals import closeWorkersAndExit
        closeWorkersAndExit()
        exitGracefully()
        sys.exit(0)
