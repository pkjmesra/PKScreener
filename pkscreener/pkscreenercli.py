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
# Pyinstaller compile Windows: pyinstaller --onefile --icon=pkscreener\icon.ico pkscreener\pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=pkscreener/icon.ico pkscreener/pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress

import argparse
import builtins
import multiprocessing
# Keep module imports prior to classes
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def decorator(func):
    def new_func(*args, **kwargs):
        return
        # if printenabled:
        #     func("print:",*args,**kwargs)
        #     func("input:",*args,**kwargs)

    return new_func


# print = decorator(print) # current file
def disableSysOut(input=True):
    builtins.print = decorator(builtins.print)  # all files
    if input:
        builtins.input = decorator(builtins.input)  # all files
    sys.stdout = open(os.devnull, "w")
    sys.__stdout__ = open(os.devnull, "w")


from time import sleep

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes import log as log
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger

multiprocessing.freeze_support()

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument(
    "-a",
    "--answerdefault",
    help="Pass default answer to questions/choices in the application. Example Y, N",
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
args = argParser.parse_known_args()
args = args[0]

configManager = ConfigManager.tools()


def setupLogger(shouldLog=False, trace=False):
    if not shouldLog:
        return
    log_file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
    if os.path.exists(log_file_path):
        try:
            os.remove(log_file_path)
        except Exception:
            pass
    print(
        colorText.BOLD
        + colorText.GREEN
        + "[+] Logs will be written to:"
        + colorText.END
    )
    print(colorText.BOLD + colorText.FAIL + f"[+] {log_file_path}" + colorText.END)
    print(
        colorText.BOLD
        + colorText.GREEN
        + "[+] If you need to share, open this folder, copy and zip the log file to share."
        + colorText.END
    )
    # logger = multiprocessing.log_to_stderr(log.logging.DEBUG)
    log.setup_custom_logger(
        "pkscreener",
        log.logging.DEBUG,
        trace=trace,
        log_file_path=log_file_path,
        filter=None,
    )


def pkscreenercli():
    if sys.platform.startswith("darwin"):
        multiprocessing.set_start_method("fork")
    configManager.getConfig(ConfigManager.parser)

    if args.log or configManager.logsEnabled:
        setupLogger(shouldLog=True, trace=args.testbuild)
        if not args.prodbuild and args.answerdefault is None:
            input("Press any key to continue...")
    import pkscreener.classes.Utility as Utility
    from pkscreener.globals import main

    configManager.default_logger = default_logger()
    Utility.tools.clearScreen()

    if args.prodbuild:
        disableSysOut()

    if not configManager.checkConfigFile():
        configManager.setConfig(
            ConfigManager.parser, default=True, showFileCreatedText=False
        )
    if args.options is not None and str(args.options) == "0":
        # Must be from tests
        args.options = None
        
    if args.testbuild and not args.prodbuild:
        print(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Started in TestBuild mode!"
            + colorText.END
        )
        main(
            testBuild=True,
            startupoptions=args.options,
            defaultConsoleAnswer=args.answerdefault,
            user=args.user,
        )
    elif args.download:
        print(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Download ONLY mode! Stocks will not be screened!"
            + colorText.END
        )
        main(
            downloadOnly=True,
            startupoptions=args.options,
            defaultConsoleAnswer=args.answerdefault,
            user=args.user,
        )
        sys.exit(0)
    else:
        try:
            startupOptions = args.options
            defaultAnswer = args.answerdefault
            cronInterval = args.croninterval
            while True:
                startupOptions = args.options
                if cronInterval is not None and str(cronInterval).isnumeric():
                    sleepUntilNextExecution = not Utility.tools.isTradingTime()
                    while sleepUntilNextExecution:
                        print(
                            colorText.BOLD
                            + colorText.FAIL
                            + (
                                "SecondsAfterClosingTime[%d] SecondsBeforeMarketOpen [%d]. Next run at [%s]"
                                % (
                                    int(Utility.tools.secondsAfterCloseTime()),
                                    int(Utility.tools.secondsBeforeOpenTime()),
                                    str(
                                        Utility.tools.nextRunAtDateTime(
                                            bufferSeconds=3600,
                                            cronWaitSeconds=int(args.croninterval),
                                        )
                                    ),
                                )
                            )
                            + colorText.END
                        )
                        if (Utility.tools.secondsAfterCloseTime() >= 3600) and (
                            Utility.tools.secondsAfterCloseTime()
                            <= (3600 + 1.5 * int(args.croninterval))
                        ):
                            sleepUntilNextExecution = False
                        if (Utility.tools.secondsBeforeOpenTime() <= -3600) and (
                            Utility.tools.secondsBeforeOpenTime()
                            >= (-3600 - 1.5 * int(args.croninterval))
                        ):
                            sleepUntilNextExecution = False
                        sleep(int(cronInterval))
                    print(
                        colorText.BOLD
                        + colorText.GREEN
                        + "=> Going to fetch again!"
                        + colorText.END,
                        end="\r",
                        flush=True,
                    )
                    sleep(3)
                    main(
                        startupoptions=startupOptions,
                        defaultConsoleAnswer=defaultAnswer,
                        testing=(args.testbuild and args.prodbuild),
                        user=args.user,
                    )
                else:
                    main(
                        startupoptions=startupOptions,
                        defaultConsoleAnswer=defaultAnswer,
                        testing=(args.testbuild and args.prodbuild),
                        user=args.user,
                    )
                    if args.user is not None or args.exit:
                        sys.exit(0)
                    startupOptions = None
                    defaultAnswer = None
                    cronInterval = None
                if args.exit:
                    break
            sys.exit(0)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            sys.exit(0)
            # if isDevVersion == OTAUpdater.developmentVersion:
            #     raise(e)
            # input(colorText.BOLD + colorText.FAIL +
            #     "[+] Press any key to Exit!" + colorText.END)
            # sys.exit(0)


if __name__ == "__main__":
    pkscreenercli()
