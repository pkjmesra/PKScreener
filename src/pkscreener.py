#!/usr/bin/python3

# Pyinstaller compile Windows: pyinstaller --onefile --icon=src\icon.ico src\pkscreener.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=src/icon.ico src/pkscreener.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress

# Keep module imports prior to classes
import os
import sys
import multiprocessing
import argparse
import builtins
import tempfile

def decorator(func):
    def new_func(*args,**kwargs):
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
    sys.stdout = open(os.devnull, 'w')
    sys.__stdout__ = open(os.devnull, 'w')

import classes.ConfigManager as ConfigManager
import classes.Utility as Utility
import classes.log as log
from classes.ColorText import colorText
from globals import main, getProxyServer
from time import sleep

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument('-a', '--answerdefault', help='Pass default answer to questions/choices in the application. Example Y, N', required=False)
argParser.add_argument('-c', '--croninterval', help='Pass interval in seconds to wait before the program is run again with same parameters', required=False)
argParser.add_argument('-d', '--download', action='store_true', help='Only download Stock data in .pkl file (No analysis will be run)', required=False)
argParser.add_argument('-e', '--exit', action='store_true', help='Exit right after executing just once', required=False)
argParser.add_argument('-o', '--options', help='Pass selected options in the <MainMenu>:<SubMenu>:<SubMenu>:etc. format. For example: ./pkscreener.py -a Y -o X:12:10 -e will run the screener with answer Y as default choice to questions and scan with menu choices: Scanners > Nifty (All Stocks) > Closing at least 2%% up since last 3 day', required=False)
argParser.add_argument('-p', '--prodbuild', action='store_true', help='Run in production-build mode', required=False)
argParser.add_argument('-t', '--testbuild', action='store_true', help='Run in test-build mode', required=False)
argParser.add_argument('-l', '--log', action='store_true', help='Run with full logging enabled', required=False)
argParser.add_argument('-v', action='store_true')        # Dummy Arg for pytest -v
args = argParser.parse_args()

configManager = ConfigManager.tools()

def setupLogger(shouldLog=False):
    if not shouldLog:
        return
    log_file_path = os.path.join(tempfile.gettempdir(),'logs.log')
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    print(f'Logs will be written to: {log_file_path}')
    log.setup_custom_logger('pkscreener', log.logging.DEBUG, trace=False, log_file_path=log_file_path, filter=None)

if __name__ == "__main__":
    if sys.platform.startswith('darwin'):
        multiprocessing.set_start_method('fork')
 
    if args.log:
        setupLogger(True)
    if args.prodbuild:
        disableSysOut()

    Utility.tools.clearScreen()
    if not configManager.checkConfigFile():
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    if args.testbuild and not args.prodbuild:
        print(colorText.BOLD + colorText.FAIL +"[+] Started in TestBuild mode!" + colorText.END)
        main(testBuild=True, startupoptions=args.options, defaultConsoleAnswer=args.answerdefault)
    elif args.download:
        print(colorText.BOLD + colorText.FAIL +"[+] Download ONLY mode! Stocks will not be screened!" + colorText.END)
        main(downloadOnly=True, startupoptions=args.options, defaultConsoleAnswer=args.answerdefault)
    else:
        try:
            startupOptions= args.options
            defaultAnswer = args.answerdefault
            cronInterval = args.croninterval
            while True:
                if cronInterval is not None and str(cronInterval).isnumeric():
                    sleepUntilNextExecution = not Utility.tools.isTradingTime()
                    while sleepUntilNextExecution:
                        print(colorText.BOLD + colorText.FAIL + ("SecondsAfterClosingTime[%d] SecondsBeforeMarketOpen [%d]. Next run at [%s]" % (
                            int(Utility.tools.secondsAfterCloseTime()), int(Utility.tools.secondsBeforeOpenTime()),str(Utility.tools.nextRunAtDateTime(bufferSeconds=3600, cronWaitSeconds=int(args.croninterval))))) + colorText.END)
                        if (Utility.tools.secondsAfterCloseTime() >= 3600) and (Utility.tools.secondsAfterCloseTime() <= (3600 + 1.5 * int(args.croninterval))):
                            sleepUntilNextExecution = False
                        if (Utility.tools.secondsBeforeOpenTime() <= -3600) and (Utility.tools.secondsBeforeOpenTime() >= (-3600 - 1.5 * int(args.croninterval))):
                            sleepUntilNextExecution = False
                        sleep(int(cronInterval))
                    print(colorText.BOLD + colorText.GREEN +
                      "=> Going to fetch again!" + colorText.END, end='\r', flush=True)
                    sleep(3)
                    main(startupoptions=startupOptions, defaultConsoleAnswer=defaultAnswer, testing=(args.testbuild and args.prodbuild))
                else:
                    main(startupoptions=startupOptions, defaultConsoleAnswer=defaultAnswer, testing=(args.testbuild and args.prodbuild))
                    startupOptions= None
                    defaultAnswer = None
                    cronInterval = None
                if args.exit:
                    break
        except Exception as e:
            raise e
            # if isDevVersion == OTAUpdater.developmentVersion:
            #     raise(e)
            # input(colorText.BOLD + colorText.FAIL +
            #     "[+] Press any key to Exit!" + colorText.END)
            # sys.exit(0)
