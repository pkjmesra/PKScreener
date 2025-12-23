#!/usr/bin/env python
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
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""Simple inline keyboard bot with multiple CallbackQueryHandlers.

This Bot uses the Application class to handle the bot.
First, a few callback functions are defined as callback query handler. Then, those functions are
passed to the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot that uses inline keyboard that has multiple CallbackQueryHandlers arranged in a
ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line to stop the bot.
"""
import os
import html
import json
import logging
import re
import sys
import threading
try:
    import thread
except ImportError:
    import _thread as thread

import traceback
from datetime import datetime
from time import sleep
from telegram import __version__ as TG_VER
# from telegram.constants import ParseMode

start_time = datetime.now()
MINUTES_2_IN_SECONDS = 120
OWNER_USER = "Itsonlypk"
APOLOGY_TEXT = "Apologies! The @nse_pkscreener_bot is NOT available for the time being! We are working with our host GitHub and other data source providers to sort out pending invoices and restore the services soon! Thanks for your patience and support! 🙏"

from pkscreener.classes import VERSION
from PKDevTools.classes.Environment import PKEnvironment
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.MarketHours import MarketHours
from PKDevTools.classes.UserSubscriptions import PKUserSusbscriptions, PKSubscriptionModel
from PKDevTools.classes.GmailReader import PKGmailReader
from pkscreener.classes.MenuOptions import MenuRenderStyle, menu, menus,MAX_MENU_OPTION
from pkscreener.classes.WorkflowManager import run_workflow
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.PKAnalytics import PKAnalyticsService
from PKDevTools.classes.FunctionTimeouts import ping
try:
    from PKDevTools.classes.DBManager import DBManager
    from PKDevTools.classes.UserSubscriptions import PKUserSusbscriptions
except: # pragma: no cover
    pass

monitor_proc = None
configManager = ConfigManager.tools()
bot_available=True

# try:
#     from telegram import __version_info__
# except ImportError:
#     __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

# if __version_info__ < (20, 0, 0, "alpha", 1):
#     raise RuntimeError(
#         f"This example is not compatible with your current PTB version {TG_VER}. To view the "
#         f"{TG_VER} version of this example, "
#         f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
#     )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin

class PKLocalCache(SingletonMixin, metaclass=SingletonType):
    def __init__(self):
        super(PKLocalCache, self).__init__()
        self.registeredIDs = []

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# # State definitions for top level conversation
# SELECTING_ACTION, ADDING_MEMBER, ADDING_SELF, DESCRIBING_SELF = map(chr, range(4))
# # State definitions for second level conversation
# SELECTING_LEVEL, SELECTING_GENDER = map(chr, range(4, 6))
# # State definitions for descriptions conversation
# SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# # Meta states
# STOPPING, SHOWING = map(chr, range(8, 10))
# # Shortcut for ConversationHandler.END
# END = ConversationHandler.END
# Stages
START_ROUTES, END_ROUTES = map(chr, range(2)) #range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)

m0 = menus()
m1 = menus()
m2 = menus()
m3 = menus()
m4 = menus()
int_timer = None
_updater = None
QR_CODE_PAYMENT_LINK="upi://pay?pa=PKSCREENER@APL&pn=PKSCREENER&tn=undefined&am=undefined"

TOP_LEVEL_SCANNER_MENUS = ["X", "B", "MI","DV", "P"] # 
TOP_LEVEL_SCANNER_SKIP_MENUS = ["M", "S", "F", "G", "C", "T", "D", "I", "E", "U", "L", "Z", "P"] # Last item will be skipped.
TOP_LEVEL_MARKUP_SKIP_MENUS = TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1]
TOP_LEVEL_MARKUP_SKIP_MENUS.extend(["X","P","B"])
INDEX_SKIP_MENUS_1_To_4 = ["W","E","M","Z","0","5","6","7","8","9","10","11","12","13","14","S","15"]
INDEX_SKIP_MENUS_5_TO_9 = ["W","E","M","Z","N","0","1","2","3","4","10","11","12","13","14","S","15"]
INDEX_SKIP_MENUS_10_TO_15 = ["W","E","M","Z","N","0","1","2","3","4","5","6","7","8","9","S"]
SCANNER_SKIP_MENUS_1_TO_6 = ["0","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_7_TO_12 = ["0","1","2","3","4","5","6","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_13_TO_18 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_19_TO_25 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_26_TO_31 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_32_TO_37 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_38_TO_43 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_MENUS_WITH_NO_SUBMENUS = ["1","2","3","10","11","12","13","14","15","16","17","18","19","20","21","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45"]
SCANNER_MENUS_WITH_SUBMENU_SUPPORT = ["6", "7", "21","22","30","32","33","40"]
SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT = {"6":[ "7","10"], "7":[ "3","6","7","9"],}

INDEX_COMMANDS_SKIP_MENUS_SCANNER = ["W", "E", "M", "Z", "S"]
INDEX_COMMANDS_SKIP_MENUS_BACKTEST = ["W", "E", "M", "Z", "S", "N", "0", "15"]
PIPED_SCAN_SKIP_COMMAND_MENUS =["2", "3", "M", "0", "4"]
PIPED_SCAN_SKIP_INDEX_MENUS =["W","N","E","S","0","Z","M","15"]
UNSUPPORTED_COMMAND_MENUS =["22","M","Z","0",str(MAX_MENU_OPTION)]
SUPPORTED_COMMAND_MENUS = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45"]
user_states = {}

def registerUser(user,forceFetch=False):
    otpValue, subsModel,subsValidity,alertUser = 0,0,None,None
    if user is not None and (user.id not in PKLocalCache().registeredIDs or forceFetch):
        dbManager = DBManager()
        otpValue, subsModel,subsValidity,alertUser = dbManager.getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
        if str(otpValue).strip() != '0' and user.id not in PKLocalCache().registeredIDs:
            PKLocalCache().registeredIDs.append(user.id)
    return otpValue, subsModel,subsValidity,alertUser

def loadRegisteredUsers():
    dbManager = DBManager()
    users = dbManager.getUsers(fieldName="userid")
    userIDs = [user.userid for user in users]
    PKLocalCache().registeredIDs.extend(userIDs)

def isInMarketHours():
    now = PKDateUtilities.currentDateTime()
    marketStartTime = PKDateUtilities.currentDateTime(simulate=True,hour=MarketHours().openHour,minute=MarketHours().openMinute)
    marketCloseTime = PKDateUtilities.currentDateTime(simulate=True,hour=MarketHours().closeHour,minute=MarketHours().closeMinute)
    # We are in between market open and close hours
    return not PKDateUtilities.isTodayHoliday()[0] and now >= marketStartTime and now <= marketCloseTime

def initializeIntradayTimer():
    try:
        if (not PKDateUtilities.isTodayHoliday()[0]):
            now = PKDateUtilities.currentDateTime()
            marketStartTime = PKDateUtilities.currentDateTime(simulate=True,hour=MarketHours().openHour,minute=MarketHours().openMinute-1)
            marketCloseTime = PKDateUtilities.currentDateTime(simulate=True,hour=MarketHours().closeHour,minute=MarketHours().closeMinute)
            marketOpenAnHourandHalfPrior = PKDateUtilities.currentDateTime(simulate=True,hour=MarketHours().openHour-2,minute=MarketHours().openMinute+30)
            if now < marketStartTime and now >= marketOpenAnHourandHalfPrior: # Telegram bot might keep running beyond an hour. So let's start watching around 7:45AM
                difference = (marketStartTime - now).total_seconds() + 1
                global int_timer
                int_timer = threading.Timer(difference, launchIntradayMonitor, args=[])
                int_timer.start()
            elif now >= marketStartTime and now <= marketCloseTime:
                launchIntradayMonitor()
    except Exception as e: # pragma: no cover
        logger.error(e)
        launchIntradayMonitor()
        pass

def sanitiseTexts(text):
    MAX_MSG_LENGTH = 4096
    if len(text) > MAX_MSG_LENGTH:
        return text[:MAX_MSG_LENGTH]
    return text

def updateSubscription(userid,subvalue,subtype = "add"):
    workflow_name = "w18-workflow-sub-data.yml"
    branch = "main"
    updatedResults = None
    try:
        workflow_postData  = (
            '{"ref":"'
            + branch
            + '","inputs":{"userid":"'
            + f"{userid}"
            + '","subtype":"'
            + f"{subtype}"
            + '","subvalue":"'
            + f"{subvalue}"
            + '"}}'
        )
        ghp_token = PKEnvironment().allSecrets["PKG"]
        resp = run_workflow(workflowType="O",repo="PKScreener",owner="pkjmesra",branch=branch,ghp_token=ghp_token,workflow_name=workflow_name,workflow_postData=workflow_postData)
        if resp is not None and resp.status_code != 204:
            updatedResults = f"{updatedResults} Uh oh! We ran into a problem enabling your subscription.\nPlease reach out to @ItsOnlyPK to resolve."
    except Exception as e:
        logger.error(e)
        updatedResults = f"{updatedResults} Uh oh! We ran into a problem enabling your subscription.\nPlease reach out to @ItsOnlyPK to resolve."
        pass
    return updatedResults

def matchUTR(update: Update, context: CallbackContext) -> str:
    global bot_available
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    logger.info("User %s started the conversation.", user.first_name)
    if not bot_available:
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        updatedResults = APOLOGY_TEXT
    
    if bot_available:
        msg = update.effective_message
        try:
            m = re.match(r"\s*/([0-9a-zA-Z-]+)\s*(.*)", msg.text)
            cmd = m.group(1).lower()
            args = [arg for arg in re.split(r"\s+", m.group(2)) if len(arg)]
        except:
            pass
            return start(update,context)
        if len(args) > 0: # UTR
            matchedTran = PKGmailReader.matchUTR(utr=args[0])
            if matchedTran is not None:
                updatedResults = f"We have found the following transaction for the provided UTR:\n{matchedTran}\nYour subscription is being enabled soon!\nPlease check with /OTP in the next couple of minutes!\nThank you for trusting PKScreener!"
                try:
                    results = updateSubscription(user.id,int(float(matchedTran.get("amountPaid"))))
                    if results is not None:
                        updatedResults = results
                except Exception as e:
                    logger.error(e)
                    updatedResults = f"{updatedResults} Uh oh! We ran into a problem enabling your subscription.\nPlease reach out to @ItsOnlyPK to resolve."
                    pass
            else:
                updatedResults = "We could not find any transaction details with the provided UTR.\nUPI transaction reference number is a 12-digit alphanumeric/numeric code that serves as a unique identifier for transactions. It is also known as the Unique Transaction Reference (UTR) number.\nYou can find your UPI reference number in the UPI-enabled app you used to make the transaction.\nFor example, you can find your UPI reference number in the History section of Google Pay. \nIn the Paytm app, you can find it by clicking View Details.\nIf you still cannot find it, please drop a message with transaction details/snapshot to @ItsOnlyPK to enable subscription."
        else:
            updatedResults = "Did you forget to include the UTR number with /Check ?\nYou should use it like this:\n/Check UTR_Here\nUPI transaction reference number is a 12-digit alphanumeric/numeric code that serves as a unique identifier for transactions. It is also known as the Unique Transaction Reference (UTR) number.\nYou can find your UPI reference number in the UPI-enabled app you used to make the transaction.\nFor example, you can find your UPI reference number in the History section of Google Pay. \nIn the Paytm app, you can find it by clicking View Details.\nIf you still cannot find it, please drop a message with transaction details/snapshot to @ItsOnlyPK to enable subscription."
    update.message.reply_text(sanitiseTexts(updatedResults), reply_markup=default_markup(user=user),parse_mode="HTML")
    shareUpdateWithChannel(update=update, context=context, optionChoices=f"/otp\n{updatedResults}")
    return START_ROUTES

def editMessageText(query,editedText,reply_markup):
    # .replace(microsecond=0).isoformat()
    editedText = f"PKScreener <b>v{VERSION}</b>\n{PKDateUtilities.currentDateTime()}:\n{editedText}"
    if query is not None and hasattr(query, "edit_message_text"):
        query.edit_message_text(text=editedText, reply_markup=reply_markup,parse_mode="HTML")

def otp(update: Update, context: CallbackContext) -> str:
    viewSubscriptionOptions(update,context,sendOTP=True)
    return START_ROUTES
    
def start(update: Update, context: CallbackContext, updatedResults=None, monitorIndex=0,chosenBotMenuOption="") -> str:
    """Send message on `/start`."""
    global bot_available
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    logger.info("User %s started the conversation.", user.first_name)
    if not bot_available:
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        updatedResults = APOLOGY_TEXT
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    if bot_available:
        reply_markup = default_markup(user=user,monitorIndex=monitorIndex)
        cmds = m0.renderForMenu(
            selectedMenu=None,
            skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
    else:
        reply_markup = None

    if updatedResults is None:
        cmdText = "\n/otp : To generate an OTP to login to PKScreener desktop console\n/check UPI_UTR_HERE_After_Making_Payment : To share transaction reference number to automatically enable subscription after making payment via UPI\n"
        for cmd in cmds:
            if cmd.menuKey not in TOP_LEVEL_MARKUP_SKIP_MENUS:
                cmdText = f"{cmdText}\n{cmd.commandTextKey()} : {cmd.commandTextLabel()}"
        tosDisclaimerText = "By using this Software, you agree to\n[+] having read through the <a href='https://pkjmesra.github.io/PKScreener/Disclaimer.txt'>Disclaimer</a>\n[+] and accept <a href='https://pkjmesra.github.io/PKScreener/tos.txt'>Terms Of Service</a> of PKScreener.\n[+] If that is not the case, you MUST immediately terminate using PKScreener and exit now!\n"
        menuText = f"Welcome {user.first_name}, {(user.username)}!\n{tosDisclaimerText}Please choose a menu option by selecting a button from below.{cmdText}"
        try:
            if updateCarrier is not None and hasattr(updateCarrier, "data") and updateCarrier.data is not None and updateCarrier.data == "CP":
                menuText = f"Piped Scanners are available using /P . Click on this /P to begin using piped scanners. To use other scanners, choose a menu option by selecting a button from below.\n{cmdText}"
        except Exception as e: # pragma: no cover
            logger.error(e)
            pass
        menuText = f"{menuText}\nClick /start if you want to restart the session."
    else:
        if not isUserSubscribed(user):
            updatedResults = f"Thank you for choosing Intraday Monitor!\nThis scan request is, however, protected and is only available to premium subscribers. It seems like you are not subscribed to the paid/premium subscription to PKScreener.\nPlease checkout all premium options by sending out a request:\n/OTP\nFor basic/unpaid users, you can try out the following:\n/X_0 StockCode1,StockCode2,etc.\n/X_N\n/X_1"
            updatedResults = f"{updatedResults}\nClick /start if you want to restart the session."
        chosenBotMenuOption = f"{chosenBotMenuOption}\nInt. Monitor. MonitorIndex:{monitorIndex}\n{updatedResults}"
        menuText = updatedResults
    # Send message with text and appended InlineKeyboard
    if update.callback_query is not None:
        sendUpdatedMenu(
            menuText=menuText, update=update, context=context, reply_markup=reply_markup, replaceWhiteSpaces=(updatedResults is None)
        )
    elif update.message is not None:
        update.message.reply_text(
            sanitiseTexts(menuText),
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    if Channel_Id is not None and len(str(Channel_Id)) > 0:
        context.bot.send_message(
            chat_id=int(f"-{Channel_Id}"),
            text=f"Name: {user.first_name}, Username:@{user.username} with ID: {str(user.id)} started using the bot!\n{chosenBotMenuOption}",
            parse_mode="HTML",
        )
    registerUser(user)
    # Tell ConversationHandler that we're in state `FIRST` now
    return START_ROUTES

def removeMonitorFile():
    from PKDevTools.classes import Archiver
    configManager.getConfig(ConfigManager.parser)
    filePath = os.path.join(Archiver.get_user_data_dir(), "monitor_outputs")
    index = 0
    while index < configManager.maxDashboardWidgetsPerRow*configManager.maxNumResultRowsInMonitor:
        try:
            os.remove(f"{filePath}_{index}.txt")
        except Exception as e: # pragma: no cover
            logger.error(e)
            pass
        index += 1

def launchIntradayMonitor():
    from PKDevTools.classes import Archiver
    global int_timer
    if int_timer is not None:
        int_timer.cancel()
    filePath = os.path.join(Archiver.get_user_data_dir(), "monitor_outputs")
    result_outputs = ""
    if (PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]) or ("PKDevTools_Default_Log_Level" in os.environ.keys() or sys.argv[0].endswith(".py")):
        result_outputs = "Starting up the monitor for this hour. Please try again after 30-40 seconds."
    else:
        result_outputs = f"{PKDateUtilities.currentDateTime()}\nIntraday Monitor is available only during the NSE trading hours! Please try during the next trading session."
        try:
            removeMonitorFile()
        except Exception as e: # pragma: no cover
            logger.error(e)
            pass
        return result_outputs, filePath

    appLogsEnabled = ("PKDevTools_Default_Log_Level" in os.environ.keys() or sys.argv[0].endswith(".py"))
    # User wants an Int. Monitor
    from PKDevTools.classes.System import PKSystem
    _,_,_,_,sysArch = PKSystem.get_platform()
    launcher = f"/home/runner/work/PKScreener/PKScreener/pkscreenercli_{sysArch}.bin" if "MONITORING_BOT_RUNNER" in os.environ.keys() else "pkscreener"
    launcher = f"python3.12 {launcher}" if launcher.endswith(".py") else launcher
    
    try:
        from subprocess import Popen
        global monitor_proc
        if monitor_proc is None or monitor_proc.poll() is not None: # Process finished from an earlier launch
            # Let's remove the old file(s) so that the new app can begin to run
            # If we don't remove, it might just exit assuming that there's another instance
            # already running.
            removeMonitorFile()
            appArgs = [f"{launcher}","-a","Y","-m","X","--telegram",]
            if appLogsEnabled:
                appArgs.append("-l")
            else:
                appArgs.append("-p")
            monitor_proc = Popen(appArgs)
            logger.info(f"{launcher} -a Y -m 'X' -p --telegram launched")
        else:
            result_outputs = "Intraday Monitor is already running/launching, but the results are being prepared. Try again in the next few seconds."
            logger.info(f"{launcher} -a Y -m 'X' -p --telegram already running")
    except Exception as e: # pragma: no cover
        result_outputs = "Hmm...It looks like you caught us taking a break! Try again later :-)"
        logger.info(f"{launcher} -a Y -m 'X' -p --telegram could not be launched")
        logger.error(e)
        pass
    return result_outputs, filePath

def XDevModeHandler(update: Update, context: CallbackContext) -> str:
    """Show new choice of buttons"""
    query = update.callback_query
    data = query.data.upper().replace("CX", "X").replace("CB", "B").replace("CG", "G").replace("CMI", "MI").replace("CDV","DV")
    if data[0:2] not in TOP_LEVEL_SCANNER_MENUS:
        return start(update, context)
    if data.startswith("DV"):
        # Dev Mode
        devModeIndex = int(data.split("_")[1])
        if devModeIndex == 0: # Enable/Disable intraday monitor along with logging
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                del os.environ['PKDevTools_Default_Log_Level']
                configManager.maxNumResultRowsInMonitor = 2
                configManager.logsEnabled = False
            else:
                # Switch config file
                configManager.maxNumResultRowsInMonitor = 3
                configManager.logsEnabled = True
                os.environ["PKDevTools_Default_Log_Level"] = str(logging.INFO)
            configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
            chosenBotMenuOption = configManager.showConfigFile(defaultAnswer='Y')
            if monitor_proc is not None:
                try:
                    monitor_proc.kill()
                except Exception as e: # pragma: no cover
                    logger.error(e)
                    pass
            
            launchIntradayMonitor()
            start(update, context,chosenBotMenuOption=chosenBotMenuOption)
        elif devModeIndex == 1: # Restart the bot service
            resp = run_workflow(None, None,None, workflowType="R")
            start(update, context,chosenBotMenuOption=f"{resp.status_code}: {resp.text}")
    return START_ROUTES

def PScanners(update: Update, context: CallbackContext) -> str:
    """Show new choice of buttons"""
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    query = update.callback_query
    if query is None:
        start(update, context)
        return START_ROUTES
    data = query.data.upper().replace("C", "")
    if data[0:2] not in TOP_LEVEL_SCANNER_MENUS:
        # Someone is trying to send commands we do not support
        return start(update, context)
    global bot_available
    if not bot_available:
        # Bot is running but is running in unavailable mode.
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        start(update, context)
        return START_ROUTES
    
    ########################### Scanners ##############################
    midSkip = "13" if data == "P" else "N"
    skipMenus = [midSkip]
    skipMenus.extend(PIPED_SCAN_SKIP_COMMAND_MENUS)
    # Create the menu text labels
    menuText = (
        m1.renderForMenu(
            m0.find(data),
            skip=skipMenus,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        .replace("     ", "")
        .replace("    ", "")
        .replace("  ", "")
        .replace("\t", "")
        .replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"")
    )
    menuText = f"{menuText}\n\nH > Home"
    # menuText = f"{menuText}\n\nP2 > More Options"

    # Create the menu buttons
    mns = m1.renderForMenu(
        m0.find(data),
        skip=skipMenus,
        asList=True,
    )
    mns.append(menu().create("H", "Home", 2))
    # mns.append(menu().create("P2", "Next", 2))
    inlineMenus = []
    query.answer()
    for mnu in mns:
        inlineMenus.append(
            InlineKeyboardButton(
                mnu.menuKey, callback_data=str(f"{query.data}_{mnu.menuKey}")
            )
        )
    keyboard = [inlineMenus]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menuText = f"{menuText}\nClick /start if you want to restart the session."
    editMessageText(query=query,editedText=menuText,reply_markup=reply_markup)
    registerUser(user)
    return START_ROUTES

def addNewButtonsToReplyMarkup(reply_markup, buttonKeyTextDict={}):
    # Get the existing inline keyboard
    keyboard = reply_markup.inline_keyboard if reply_markup else []
    inlineMenus = []  # Temporary list to hold a row of buttons
    for key, value in buttonKeyTextDict.items():
        inlineMenus.append(InlineKeyboardButton(f"{value}", callback_data=f"{key}"))
        # Add row of 2 buttons when full
        if len(inlineMenus) == 2:
            keyboard.append(inlineMenus)
            inlineMenus = []  # Reset row
    # Append any remaining buttons (if not forming a full row)
    if inlineMenus:
        keyboard.append(inlineMenus)
    return InlineKeyboardMarkup(keyboard)

def cancelAlertSubscription(update:Update,context:CallbackContext):
    global bot_available
    updatedResults= ""
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    scanId = updateCarrier.data.upper().replace("CAN_", "")
    logger.info("User %s started the conversation.", user.first_name)
    if not bot_available:
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        updatedResults = APOLOGY_TEXT
    reply_markup=default_markup(user=user)
    try:
        dbManager = DBManager()
        result = dbManager.removeScannerJob(user.id,scanId)
        if result:
            updatedResults = f"<b>{scanId}</b> has been successfully removed from your alert subscription(s). If you re-subscribe, the associated charges will be deducted from your alerts remaining balance. For any feedback, please reach out to @ItsOnlyPK. You can use the <b>Subscriptions</b> button below to check/view your existing subscriptions. We thank you for your support and trust! Keep exploring!"
        else:
            updatedResults = f"We encountered some <b>error</b> while trying to remove <b>{scanId}</b> from your alert subscription(s). Please try again or reach out to @ItsOnlyPK with feedback. If you re-subscribe, the associated charges will be deducted from your alerts remaining balance. You can use the <b>Subscriptions</b> button below to check/view your existing subscriptions. We thank you for your support and trust! Keep exploring!"
        if hasattr(updateCarrier, "reply_text"):
            updateCarrier.reply_text(text=sanitiseTexts(updatedResults), reply_markup=reply_markup,parse_mode="HTML")
        elif hasattr(updateCarrier, "edit_message_text"):
            editMessageText(query=updateCarrier,editedText=sanitiseTexts(updatedResults),reply_markup=reply_markup)
        shareUpdateWithChannel(update=update, context=context, optionChoices=f"/CAN_{scanId}_{user.id}\n{updatedResults}")
    except Exception as e: # pragma: no cover
        logger.error(e)
        pass
    return START_ROUTES

def viewSubscriptionOptions(update:Update,context:CallbackContext,sendOTP=False):
    global bot_available
    updateCarrier = None
    updatedResults= ""
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    logger.info("User %s started the conversation.", user.first_name)
    if not bot_available:
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        updatedResults = APOLOGY_TEXT
    
    reply_markup=default_markup(user=user)
    if bot_available:
        try:
            otpValue = 0
            alertUser = None
            dbManager = DBManager()
            otpValue, subsModel,subsValidity,alertUser = registerUser(user,forceFetch=True)
            scannerJobsSubscribed = ""
            if alertUser is not None and len(alertUser.scannerJobs) > 0:
                scannerJobsSubscribed = ", ".join(alertUser.scannerJobs)
                if len(scannerJobsSubscribed) > 0:
                    scannerJobsSubscribed = f"Subscribed to [{scannerJobsSubscribed}]"
        except Exception as e: # pragma: no cover
            logger.error(e)
            pass
        userText = f"<b>UserID</b> : <code>{user.id}</code>"
        try:
            subscriptionModelNames = "\n<pre>Following basic and premium subscription models are available. Premium subscription allows for unlimited premium scans:\n"
            for name,value in PKUserSusbscriptions().subscriptionKeyValuePairs.items():
                if name == PKSubscriptionModel.No_Subscription.name:
                    subscriptionModelNames = f"{subscriptionModelNames}\n₹ {str(value).ljust(6)}: {name} (Only Basic Scans are free)\n"
                else:
                    subscriptionModelNames = f"{subscriptionModelNames}\n₹ {str(value).ljust(6)}: {name}"
            subscriptionModelNames = f"{subscriptionModelNames}</pre>\nPlease pay to subscribe:\n1. Using UPI(India) to <a href='https://tinyurl.com/v7h3t233'>PKScreener@APL</a> or\n2. Proudly <a href='https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra'><b>sponsor</b></a>\nPlease send\n/check UPI_UTR_HERE_After_Making_Payment to share transaction reference number to automatically enable subscription after making payment via UPI\n. If it is not auto-enabled, please drop a message to @ItsOnlyPK on Telegram after paying to enable subscription manually."

            subscriptionModelName = PKUserSusbscriptions().subscriptionValueKeyPairs[subsModel]
            if subscriptionModelName != PKSubscriptionModel.No_Subscription.name:
                subscriptionModelName = f"{subscriptionModelName} (Expires on: {subsValidity})"
        except Exception as e:
            logger.error(e)
            subscriptionModelName = PKSubscriptionModel.No_Subscription.name
            pass
        if sendOTP:
            if otpValue == 0:
                updatedResults = f"We are having difficulty generating OTP for your {userText}. Please try again later or reach out to @ItsOnlyPK."
            else:
                updatedResults = f"Please use the following to login to PKScreener:\n{userText}\n<b>OTP</b>     : <code>{otpValue}</code>\nCurrent subscription : <b>{subscriptionModelName}</b>.\nCurrent alerts balance: <b>₹ {alertUser.balance if alertUser is not None else 0}</b> {scannerJobsSubscribed}. {subscriptionModelNames}"
        else:
            updatedResults = f"Current subscription: <b>{subscriptionModelName}</b>.\nCurrent alerts balance: <b>₹ {alertUser.balance if alertUser is not None else 0}</b> {scannerJobsSubscribed}. {subscriptionModelNames}"
        
        #Add new buttons with alert subscription options to cancel
        if alertUser is not None and len(alertUser.scannerJobs) > 0:
            buttonDict = {}
            for scannerJob in alertUser.scannerJobs:
                if len(scannerJob) > 0:
                    buttonDict[f"CAN_{scannerJob}"] = f"Stop {scannerJob} 🔔"
            reply_markup = addNewButtonsToReplyMarkup(reply_markup,buttonDict)

    if hasattr(updateCarrier, "reply_text"):
        updateCarrier.reply_text(text=sanitiseTexts(updatedResults), reply_markup=reply_markup,parse_mode="HTML")
    elif hasattr(updateCarrier, "edit_message_text"):
        editMessageText(query=updateCarrier,editedText=sanitiseTexts(updatedResults),reply_markup=reply_markup)
    shareUpdateWithChannel(update=update, context=context, optionChoices=f"/otp\n{updatedResults}")
    return START_ROUTES

def subscribeToScannerAlerts(update: Update, context: CallbackContext) -> str:
    """Show Subscription options, check if user has paid or already subscribed"""
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    query = update.callback_query
    if query is None:
        start(update, context)
        return START_ROUTES
    scanId = query.data.upper().replace("SUB_", "").strip()
    global bot_available
    if not bot_available:
        # Bot is running but is running in unavailable mode.
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        start(update, context)
        return START_ROUTES
    dbManager = DBManager()
    alertUser = dbManager.alertsForUser(int(user.id))
    query.answer()
    menuText = ""
    requiredBalance = 40 if str(scanId).upper().startswith("P") else 31
    # upi://pay?pa=PKScreener@APL&pn=PKScreener&cu=INR
    payWall = "Please pay to subscribe:\n1. Using UPI(India) to <a href='https://tinyurl.com/v7h3t233'>PKScreener@APL</a> or\n2. Proudly <a href='https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra'>sponsor</a>\nPlease use\n/check UPI_UTR_HERE_After_Making_Payment to share transaction reference number to automatically update your balance after making payment via UPI.\nAfter that you can try re-subscribing!\nIf you still face any problem, please drop a message to @ItsOnlyPK along with UTR and Scan details on Telegram after paying to enable subscription manually."
    if alertUser is not None and alertUser.balance >= 0:
        # User has some balance
        if len(alertUser.scannerJobs) > 0:
            # User is already subscribed to some alerts
            if str(scanId) in alertUser.scannerJobs:
                menuText = f"You are already subscribed to {scanId} ! Alerts will be delivered as and when they are raised during market hours on a market-open day. <b>You need to subscribe every morning for any spcific alert.</b>"
                kickOffScannerJobIfNotKickedOff(scanId,user,dbManager,requiredBalance,alertUser)
            else:
                if  alertUser.balance < requiredBalance:
                    # Insufficient balance
                    menuText = f"You need at least <b>₹ {requiredBalance}</b> to subscribe to <b>{scanId} alerts for a day</b> ! Your current balance <b>₹ {alertUser.balance}</b> is <b>insufficient</b>. {payWall}"
                else:
                    menuText = kickOffScannerJobIfNotKickedOff(scanId,user,dbManager,requiredBalance,alertUser)
    
    elif alertUser is None or alertUser.balance == 0:
        # Either user is not subscribed or has 0 balance
        menuText = f"You need at least <b>₹ {requiredBalance}</b> to subscribe to <b>{scanId} alerts for a day</b> ! Your current balance <b>₹ 0</b> is <b>insufficient</b>. {payWall}"

    menuText = f"{menuText}\nClick /start if you want to restart the session."
    editMessageText(query=query,editedText=sanitiseTexts(menuText),reply_markup=default_markup(user=user))
    return START_ROUTES
        
def kickOffScannerJobIfNotKickedOff(scanId,user,dbManager,requiredBalance,alertUser):
    # Sufficient balance to subscribe to scanId
    needsNewJobKickedOff = False
    menuText = ""
    subscribed = False
    subscribedUsers = dbManager.usersForScannerJobId(scannerJobId=scanId)
    isMarketOpen = True
    try:
        isMarketOpen = isInMarketHours()
    except:
        pass
    if subscribedUsers is None or len(subscribedUsers) == 0 and isMarketOpen:
        # This is the first user who's requesting this scanner
        needsNewJobKickedOff = True
    if alertUser is None or str(scanId) not in alertUser.scannerJobs:
        subscribed = dbManager.updateAlertSubscriptionModel(user.id,requiredBalance,scanId)
    if subscribed:
        menuText = f"You have been added to receive the alerts for <b>{scanId}</b>. Please note that it is valid only for today during Market Hours and resets right after that. <b>You will need to re-subscribe again if you need it on the next market open day</b>. Thank you for trusting PKScreener!"
        if needsNewJobKickedOff:
            run_workflow(f"{scanId}_{user.id}", str(user.id), f'--systemlaunched -a y -m {str(scanId).upper().replace("_",":")}', workflowType="S")
    else:
        menuText = "We encountered an error updating your subscription! Please reach out to @ItsOnlyPK on Telegram with your UTR and subscription scanner details."
    return menuText

def XScanners(update: Update, context: CallbackContext) -> str:
    """Show new choice of buttons"""
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    query = update.callback_query
    if query is None:
        start(update, context)
        return START_ROUTES
    data = query.data.upper().replace("C", "")
    if data[0:2] not in TOP_LEVEL_SCANNER_MENUS:
        # Someone is trying to send commands we do not support
        return start(update, context)
    global bot_available
    if not bot_available:
        # Bot is running but is running in unavailable mode.
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        start(update, context)
        return START_ROUTES
    ########################### Intraday Monitor ##############################
    if data.startswith("MI"): # Intraday monitor
        monitorIndex = int(data.split("_")[1])
        result_outputs, filePath = launchIntradayMonitor()
        filePath = f"{filePath}_{monitorIndex}.txt"
        monitorIndex += 1
        if monitorIndex >= configManager.maxDashboardWidgetsPerRow*configManager.maxNumResultRowsInMonitor:
            monitorIndex = 0
        try:
            if os.path.exists(filePath):
                f = open(filePath, "r")
                result_outputs = f.read()
                f.close()
            start(update, context, updatedResults=result_outputs,monitorIndex=monitorIndex)
            return START_ROUTES
        except Exception as e: # pragma: no cover
            result_outputs = "Hmm...It looks like you caught us taking a break! Try again later :-)\nCycleTime shows how much it's taking us to download latest data and then perform each cycle of analysis for all configured scanners. We may be downloading the latest data right now."
            logger.info(e)
            logger.info(f"Could not read {filePath}")
            start(update, context, updatedResults=result_outputs,monitorIndex=monitorIndex)
            return START_ROUTES

    ########################### Scanners ##############################
    midSkip = "13" if data == "X" else "N"
    skipMenus = [midSkip]
    skipMenus.extend(INDEX_SKIP_MENUS_1_To_4)
    # Create the menu text labels
    menuText = (
        m1.renderForMenu(
            m0.find(data),
            skip=skipMenus,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        .replace("     ", "")
        .replace("    ", "")
        .replace("  ", "")
        .replace("\t", "")
        .replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"")
    )
    menuText = f"{menuText}\n\nH > Home"
    menuText = f"{menuText}\n\nP2 > More Options"

    # Create the menu buttons
    mns = m1.renderForMenu(
        m0.find(data),
        skip=skipMenus,
        asList=True,
    )
    mns.append(menu().create("H", "Home", 2))
    mns.append(menu().create("P2", "Next", 2))
    inlineMenus = []
    query.answer()
    for mnu in mns:
        inlineMenus.append(
            InlineKeyboardButton(
                mnu.menuKey, callback_data=str(f"{query.data}_{mnu.menuKey}")
            )
        )
    keyboard = [inlineMenus]
    reply_markup = InlineKeyboardMarkup(keyboard)
    menuText = f"{menuText}\nClick /start if you want to restart the session."
    editMessageText(query=query,editedText=sanitiseTexts(menuText),reply_markup=reply_markup)
    registerUser(user)
    return START_ROUTES

def getinlineMenuListRow(keyboardRows=[]):
    for list in keyboardRows:
        if len(list) <= 7:
            return list

def Level2(update: Update, context: CallbackContext) -> str:
    """Show new choice of buttons"""
    keyboardRows = []
    index = 0
    while index <= 10:
        keyboardRows.append([])
        index += 1

    menuText = "Hmm...It looks like you caught us taking a break! Try again later :-)"
    mns = []
    updateCarrier = None
    shouldSendUpdate = False
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user

    query = update.callback_query
    query.answer()
    preSelection = (
        query.data.upper().replace("C", "")
    )
    selection = preSelection.split("_")
    preSelection = f"{selection[0]}_{selection[1]}"
    if (selection[0].upper() not in TOP_LEVEL_SCANNER_MENUS):
        start(update, context)
        return START_ROUTES
    global bot_available
    if not bot_available:
        # Bot is running but is running in unavailable mode.
        # Sometimes, either the payment does not go through or 
        # it takes time to process the last month's payment if
        # done in the past 24 hours while the last date was today.
        # If that happens, we won't be able to run bots or scanners
        # without incurring heavy charges. Let's run in the 
        # unavailable mode instead until this gets fixed.
        start(update, context)
        return START_ROUTES
    if selection[len(selection)-1].upper() == "H": # Home button
        start(update, context)
        return START_ROUTES
    
    reply_markup = default_markup(user=user)
    if (len(selection) == 2 and selection[0] in ["X","B"] and selection[1] in ["P1","P2","P3"]) or \
        (len(selection) == 4 and selection[0] in ["P"] and selection[3] in ["P1","P2","P3"]): # Piped scan index options
        nextOption = ""
        if selection[1] == "P2" or (selection[0] in ["P"] and selection[3] == "P2"):
            skipMenus = INDEX_SKIP_MENUS_5_TO_9
            nextOption = "P3"
        elif selection[1] == "P3" or (selection[0] in ["P"] and selection[3] == "P3"):
            skipMenus = INDEX_SKIP_MENUS_10_TO_15
            nextOption = "P1"
        elif selection[1] == "P1" or (selection[0] in ["P"] and selection[3] == "P1"):
            skipMenus = INDEX_SKIP_MENUS_1_To_4
            nextOption = "P2"
        # Create the menu text labels
        menuText = (
            m1.renderForMenu(
                m0.find(selection[0] if selection[0] not in ["P"] else "X"),
                skip=skipMenus,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            .replace("     ", "")
            .replace("    ", "")
            .replace("  ", "")
            .replace("\t", "")
            .replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"")
        )
        menuText = f"{menuText}\n\nH > Home"
        menuText = f"{menuText}\n\n{nextOption} > More Options"

        # Create the menu buttons
        mns = m1.renderForMenu(
            m0.find(selection[0] if selection[0] not in ["P"] else "X"),
            skip=skipMenus,
            asList=True,
        )
        mns.append(menu().create("H", "Home", 2))
        mns.append(menu().create(f"{nextOption}", "More Options", 2))
        query.answer()
        for mnu in mns:
            activeInlineRow = getinlineMenuListRow(keyboardRows)
            activeInlineRow.append(
                InlineKeyboardButton(mnu.menuKey, callback_data=str(f"C{(selection[0]+'_'+selection[1]+'_'+selection[2]) if selection[0] in ["P"] else selection[0]}_{mnu.menuKey}")))

        keyboard = keyboardRows
        reply_markup = InlineKeyboardMarkup(keyboard)
        menuText = f"{menuText}\nClick /start if you want to restart the session."
        editMessageText(query=query,editedText=sanitiseTexts(menuText),reply_markup=reply_markup)
        return START_ROUTES
    if len(selection) == 2 or (len(selection) == 3 and selection[2] == "P"):
        if str(selection[1]).isnumeric():
            # It's only level 2
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_1_TO_6,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP1 > More options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_1_TO_6,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P1", "More Options", 2))
            mns.append(menu().create("H", "Home", 2))
        elif selection[1] in ["P1", "N"]:
            selection.extend(["", ""])
    elif len(selection) == 3:
        if selection[2] == "P1":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_7_TO_12,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP2 > More Options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_7_TO_12,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P2", "More Options", 2))
            mns.append(menu().create("H", "Home", 2))
        elif selection[2] == "P2":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_13_TO_18,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP3 > More Options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_13_TO_18,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P3", "More Options", 2))
            mns.append(menu().create("H", "Home", 2))
        elif selection[2] == "P3":
            skipMenusP3 = ["22" if selection[0] in ["X","B"] else 'M'] # #22 not in X, but should be available in P
            skipMenusP3.extend(SCANNER_SKIP_MENUS_19_TO_25)
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=skipMenusP3,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP4 > More Options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=skipMenusP3,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P4", "More Options", 2))
            mns.append(menu().create("H", "Home", 2))
        elif selection[2] == "P4":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_26_TO_31,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP5 > More Options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_26_TO_31,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P5", "More Options", 2))
            mns.append(menu().create("H", "Home", 2))
        elif selection[2] == "P5":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_32_TO_37,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP6 > More Options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_32_TO_37,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P6", "More Options", 2))
            mns.append(menu().create("H", "Home", 2))
        elif selection[2] == "P6":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_38_TO_43,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP > More options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_38_TO_43,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("H", "Home", 2))
            mns.append(menu().create("P", "More Options", 2))
        elif str(selection[2]).isnumeric() and selection[0].lower() not in ["p"]:
            preSelection = f"{selection[0]}_{selection[1]}_{selection[2]}"
            if selection[2] in SCANNER_MENUS_WITH_SUBMENU_SUPPORT:
                menuText = m3.renderForMenu(
                    m2.find(selection[2]),
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0","M","Z"],
                )
                mns = m3.renderForMenu(
                    m2.find(selection[2]),
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0","M","Z"],
                )
                menuText = f"{menuText}\n\nH > Home"
                menuText = f"{menuText}\nClick /start if you want to restart the session."
                mns.append(menu().create("H", "Home", 2))
            else:
                if selection[2] == "4":  # Last N days
                    selection.extend(["D", ""])
                elif selection[2] == "5":  # RSI range
                    selection.extend(["D", "D"])
                elif selection[2] == "8":  # CCI range
                    selection.extend(["D", "D"])
                elif selection[2] == "9":  # Vol gainer ratio
                    selection.extend(["D", ""])
                elif selection[2] in SCANNER_MENUS_WITH_NO_SUBMENUS:  # Vol gainer ratio
                    selection.extend(["", ""])
    elif len(selection) == 4:
        preSelection = (
            query.data.upper().replace("C", "")
        )
    optionChoices = ""
    if len(selection) <= 3 and mns is not None:
        for mnu in mns:
            activeInlineRow = getinlineMenuListRow(keyboardRows)
            activeInlineRow.append(
                InlineKeyboardButton(
                    mnu.menuKey,
                    callback_data="C" + str(f"{preSelection}_{mnu.menuKey}"),
                )
            )
        keyboard = keyboardRows
        reply_markup = InlineKeyboardMarkup(keyboard)
    if (len(selection) >= 4 and selection[0].lower() not in ["p"]) or (len(selection) >= 3 and selection[0].lower() in ["p"]):
        if len(selection) == 4:
            if selection[2] in SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT.keys() and selection[3] in SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT[selection[2]]:
                m0.renderForMenu(
                    selectedMenu=None,
                    skip=TOP_LEVEL_SCANNER_SKIP_MENUS,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                )
                selectedMenu = m0.find(selection[0].upper())
                m1.renderForMenu(
                    selectedMenu=selectedMenu,
                    skip=(
                        INDEX_COMMANDS_SKIP_MENUS_SCANNER
                        if ("x_" in preSelection.lower() or "p_" in preSelection.lower())
                        else INDEX_COMMANDS_SKIP_MENUS_BACKTEST
                    ),
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                )
                selectedMenu = m1.find(selection[1].upper())
                m2.renderForMenu(
                    selectedMenu=selectedMenu,
                    skip=UNSUPPORTED_COMMAND_MENUS,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                )
                if selection[2] in SCANNER_MENUS_WITH_SUBMENU_SUPPORT:
                    selectedMenu = m2.find(selection[2].upper())
                    m3.renderForMenu(
                        selectedMenu=selectedMenu,
                        skip=["0","M","Z"],
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                    )
                    selectedMenu = m3.find(selection[3].upper())
                    menuText = m4.renderForMenu(
                        selectedMenu=selectedMenu,
                        renderStyle=MenuRenderStyle.STANDALONE,
                        skip=["0","M","Z"],
                    )
                    mns = m4.renderForMenu(
                        selectedMenu=selectedMenu,
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                        skip=["0","M","Z"],
                    )
                    menuText = f"{menuText}\n\nH > Home"
                    mns.append(menu().create("H", "Home", 3))
                    menuText = f"{menuText}\nClick /start if you want to restart the session."
            if mns is not None:
                for mnu in mns:
                    activeInlineRow = getinlineMenuListRow(keyboardRows)
                    activeInlineRow.append(InlineKeyboardButton(mnu.menuKey,callback_data="C" + str(f"{preSelection}_{mnu.menuKey}"),))
                keyboard = keyboardRows
                reply_markup = InlineKeyboardMarkup(keyboard)
            if len(mns) == 0:
                menuText = ''
        elif len(selection) > 4 or (len(selection) >= 3 and selection[0].lower() in ["p"]):
            if (selection[0] in 'P' and ((len(selection) >= 4 and len(selection[3]) == 0) or (len(selection) == 3 and str(selection[2]).isnumeric()))):
                preSelection = query.data.upper().replace("C", "")
                skipMenus = ["N"]
                skipMenus.extend(INDEX_SKIP_MENUS_1_To_4)
                # Create the menu text labels
                menuText = (
                    m1.renderForMenu(
                        m0.find("X"),
                        skip=skipMenus,
                        renderStyle=MenuRenderStyle.STANDALONE,
                    )
                    .replace("     ", "")
                    .replace("    ", "")
                    .replace("  ", "")
                    .replace("\t", "")
                    .replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"")
                )
                menuText = f"{menuText}\n\nH > Home"
                menuText = f"{menuText}\n\nP2 > More Options"

                # Create the menu buttons
                mns = m1.renderForMenu(
                    m0.find("X"),
                    skip=skipMenus,
                    asList=True,
                )
                mns.append(menu().create("H", "Home", 2))
                mns.append(menu().create("P2", "Next", 2))
                inlineMenus = []
                query.answer()
                for mnu in mns:
                    inlineMenus.append(
                        InlineKeyboardButton(
                            mnu.menuKey, callback_data=str(f"C{preSelection}_{mnu.menuKey}")
                        )
                    )
                keyboard = [inlineMenus]
                reply_markup = InlineKeyboardMarkup(keyboard)
            elif len(mns) == 0:
                menuText = ''
        
        if menuText is None or len(menuText) == 0:
            optionChoices = (
                f"{selection[0]} > {selection[1]} > {selection[2]} > {selection[3]}".replace(" > >","").strip()
            )
            optionChoices = f"{optionChoices}{f' > {selection[4]}' if len(selection) > 4 else ''}".replace(" > >","").strip()
            expectedTime = f"{'10 to 15' if '> 15' in optionChoices else '1 to 2'}"
            menuText = f"Thank you for choosing {optionChoices.replace(' >  > ','')}. You will receive the notification/results in about {expectedTime} minutes. It generally takes 1-2 minutes for NSE (2000+) stocks and 10-15 minutes for NASDAQ (7300+).\nPKScreener had been free for a long time, but owing to cost/budgeting issues, only a basic set of features will always remain free for everyone. Consider donating to help cover the basic server costs or subscribe to premium, if not subscribed yet:\nUPI (India): <a href='https://tinyurl.com/v7h3t233'>PKScreener@APL</a>\nor <a href='https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra'>sponsor</a>"

            reply_markup = default_markup(user=user)
            options = ":".join(selection)
            shouldSendUpdate = launchScreener(
                options=options,
                user=query.from_user,
                context=context,
                optionChoices=optionChoices,
                update=update,
            )
            if not shouldSendUpdate:
                registerUser(user)
                return START_ROUTES
        try:
            if optionChoices != "" and Channel_Id is not None and len(str(Channel_Id)) > 0:
                context.bot.send_message(
                    chat_id=int(f"-{Channel_Id}"),
                    text=f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> submitted scan request <b>{optionChoices}</b> to the bot!",
                    parse_mode="HTML",
                )
        except Exception as e:# pragma: no cover
            logger.error(e)
            start(update, context)
    menuText =  menuText.replace("\n     ","\n").replace("\n    ","\n").replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"")
    if not str(optionChoices.upper()).startswith("B"):
        sendUpdatedMenu(
            menuText=menuText, update=update, context=context, reply_markup=reply_markup
        )
        scanRequest = optionChoices.replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
        sendSubscriptionOption(update,context,scanRequest)
    registerUser(user)
    return START_ROUTES

def handleHousekeeping(update: Update, context: CallbackContext) -> str:
    updateCarrier = None
    menuText = "Not implemented yet..."
    shouldSendUpdate = False
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    query = update.callback_query
    query.answer()
    preSelection = (query.data.upper().replace("C", ""))
    selection = preSelection.split("_")[1]
    if query is None:
        start(update, context)
        return START_ROUTES
    reply_markup = default_markup(user)
    dbMgr = DBManager()
    if selection == "GAU":
        activeUsers = dbMgr.getUsers(fieldName="userId")
        if activeUsers is not None:
            menuText = f"Number of all registered users in the DB: {len(activeUsers)}"
    elif selection == "GAP":
        payingUsers = dbMgr.getPayingUsers()
        if payingUsers is not None and len(payingUsers) > 0:
            menuText = "Here are all the paying users:"
            menuText = f"{menuText}\n{"UserID".ljust(10,'#')} : {"UserName".ljust(10,'#')} : {"Subs.".ljust(5,'#')} : {"Bal.".ljust(5,'#')}"
            for payingUser in payingUsers:
                menuText = f"{menuText}\n{str(payingUser.userid).ljust(10,'#')} : {str(payingUser.username).ljust(10,'#')} : {str(payingUser.subscriptionmodel).ljust(5,'#')} : {str(payingUser.balance).ljust(5,'#')}"
    elif selection == "UUB":
        user_states[user.id] = f"{selection}_awaiting_input_1"  # Set user state
        menuText = "Please enter a userID for whom to update balance:"
    elif selection in ["EUS", "DUS"]:
        user_states[user.id] = f"{selection}_awaiting_input_1"  # Set user state
        menuText = "Please enter a userID for whom to update subscription:"
    elif selection == "GAS":
        scanners = dbMgr.scannerJobsWithActiveUsers()
        if scanners is not None:
            if len(scanners) > 0:
                menuText = f"Number of all scans running today in the DB: {len(scanners)}"
                for scanner in scanners:
                    scanID = scanner.scannerId
                    subUsers = ", ".join(scanner.userIds)
                    menuText = f"{menuText}\nScanner: {scanID} : Users: {subUsers}"
            else:
                menuText = "No users are subscribed for alerts today!"
    editMessageText(query=query,editedText=menuText,reply_markup=reply_markup)
    return START_ROUTES

def default_markup(user=None,monitorIndex=0):
    mns = m0.renderForMenu(selectedMenu=None,
            skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
    if (PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]) or ("PKDevTools_Default_Log_Level" in os.environ.keys()) or sys.argv[0].endswith(".py"):
        mns.append(menu().create(f"MI_{monitorIndex}", "👩‍💻 🚀 Intraday Monitor", 2))
    hskMenus = []
    if user is not None and user.username == OWNER_USER:
        hskMenus.append(menu().create(f"DV_0", ("✅ Enable Logging" if not configManager.logsEnabled else "🚫 Disable Logging"), 2))
        hskMenus.append(menu().create(f"DV_1", "🔄 Restart Bot", 2))
        hskMenus.append(menu().create(f"HSK_GAU", "Get Active Users", 2))
        hskMenus.append(menu().create(f"HSK_GAP", "Get Paying Users", 2))
        hskMenus.append(menu().create(f"HSK_GAS", "Get Alerting Users", 2))
        hskMenus.append(menu().create(f"HSK_EUS", "Enable User Subs", 2))
        hskMenus.append(menu().create(f"HSK_DUS", "Disable User Subs", 2))
        hskMenus.append(menu().create(f"HSK_UUB", "Update User Balance", 2))

    keyboard = []
    inlineMenus = []
    lastRowMenus = []
    rowIndex = 0
    # https://emojidb.org/otp-emojis
    iconDict = {"X":"🕵️‍♂️ 🔍 ","B":"📈 🎯 ","P":"🧨 💥 ","MI":"","DV":"","VS":"🔔 📣 ","start":"🟢 🏁 ", "HS":"🕵️‍♂️ ","otp":"🔐 "}
    for mnu in mns:
        if mnu.menuKey[0:2] in TOP_LEVEL_SCANNER_MENUS:
            rowIndex +=1
            inlineMenus.append(
                InlineKeyboardButton(
                    iconDict.get(str(mnu.menuKey[0:2])) + mnu.menuText.split("(")[0],
                    callback_data="C" + str(mnu.menuKey),
                )
            )
            if rowIndex % 2 == 0:
                keyboard.append(inlineMenus)
                inlineMenus = []
    lastRowMenus.append(
        InlineKeyboardButton(
            iconDict.get("VS") + "Subscriptions",
            callback_data="VS_",
        )
    )
    lastRowMenus.append(
        InlineKeyboardButton(
            iconDict.get("start") + "Start",
            callback_data="start",
        )
    )
    lastRowMenus.append(
        InlineKeyboardButton(
            iconDict.get("otp") + "Get OTP",
            callback_data="OTP",
        )
    )
    if len(inlineMenus) > 0:
        keyboard.append(inlineMenus)
    keyboard.append(lastRowMenus)
    rowIndex = 0
    inlineMenus = []
    for hskMenu in hskMenus:
        rowIndex +=1
        inlineMenus.append(
            InlineKeyboardButton(
                iconDict.get(str(hskMenu.menuKey[0:2])) + hskMenu.menuText.split("(")[0],
                callback_data="C" + str(hskMenu.menuKey),
            )
        )
        if rowIndex % 2 == 0:
            keyboard.append(inlineMenus)
            inlineMenus = []
    if len(inlineMenus) > 0:
        keyboard.append(inlineMenus)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def sendUpdatedMenu(menuText, update: Update, context, reply_markup, replaceWhiteSpaces=True):
    try:
        menuText.replace("     ", "").replace("    ", "").replace("\t", "").replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"") if replaceWhiteSpaces else menuText
        menuText = f"{menuText}\nClick /start if you want to restart the session." if "/start" not in menuText else menuText
        editMessageText(query=update.callback_query,editedText=sanitiseTexts(menuText),reply_markup=reply_markup)
    except Exception as e:# pragma: no cover
        logger.log(e)
        start(update, context)

def isUserSubscribed(user):
    if user is not None:
        return PKUserSusbscriptions.userSubscribed(userID=str(user.id))
    return False

def launchScreener(options, user, context, optionChoices, update):
    try:
        scanRequest = optionChoices.replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
        userSubs = isUserSubscribed(user)
        try:
            PKAnalyticsService().send_event("bot_scan",{"bot_userid":str(user.id), "bot_username":str(user.username),"scan_id":str(scanRequest),"user_subscribed":userSubs})
        except Exception as e:
            pass
        if not userSubs:
            basicSubscriptions = ["X_0","X_N","X_1_"]
            isBasicScanRequest = False
            for basicSub in basicSubscriptions:
                if basicSub in scanRequest:
                    isBasicScanRequest = True
                    break
            if not isBasicScanRequest:
                responseText = f"Thank you for choosing {scanRequest}!\nThis {'Backtest' if str(scanRequest).startswith('B') else 'Scan'} request is, however, protected and is only available to premium subscribers. It seems like you are not subscribed to the paid/premium subscription to PKScreener.\nPlease checkout all premium options by sending out a request:\n/OTP\nFor basic/unpaid users, you can try out the following:\n/X_0 StockCode1,StockCode2,etc.\n/X_N\n/X_1\n"
                if update is not None and update.message is not None:
                    update.message.reply_text(sanitiseTexts(responseText),reply_markup=default_markup(user=user),parse_mode="HTML")
                else:
                    responseText = f"{responseText}\nClick /start if you want to restart the session."
                editMessageText(query=update.callback_query,editedText=sanitiseTexts(responseText),reply_markup=default_markup(user=user))
                shareUpdateWithChannel(update=update, context=context, optionChoices=responseText)
                sendSubscriptionOption(update,context,scanRequest)
                return False

        if str(optionChoices.upper()).startswith("B"):
            optionChoices = optionChoices.replace(" ", "").replace(">", "_").replace(":","_").replace("_D","")
            while optionChoices.endswith("_"):
                optionChoices = optionChoices[:-1]
            if str(optionChoices).split("_")[2] == "6" and str(optionChoices).split("_")[3] == "7":
                optionChoices = f"{optionChoices}_3" # Lorenzian Any/All
            responseText = f"Thank you for choosing {optionChoices}!\nHere are the results:\nInsights: https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{optionChoices}_Insights_DateSorted.html"
            responseText = f"{responseText}\nSummary: https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{optionChoices}_Summary_StockSorted.html"
            responseText = f"{responseText}\nStock-wise: https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{optionChoices}_backtest_result_StockSorted.html"
            responseText = f"{responseText}\nOther Reports: https://pkjmesra.github.io/PKScreener/BacktestReports.html"
            if update is not None and update.message is not None:
                update.message.reply_text(sanitiseTexts(responseText),reply_markup=default_markup(user=user),parse_mode="HTML")
            else:
                responseText = f"{responseText}\nClick /start if you want to restart the session."
                editMessageText(query=update.callback_query,editedText=sanitiseTexts(responseText),reply_markup=default_markup(user=user))
            shareUpdateWithChannel(
                update=update, context=context, optionChoices=optionChoices
            )
            return True
            # run_workflow(optionChoices, str(user.id), str(options.upper()))
        elif str(optionChoices.upper()).startswith("G"):
            optionChoices = optionChoices.replace(" ", "").replace(">", "_")
            while optionChoices.endswith("_"):
                optionChoices = optionChoices[:-1]
            options = options.upper().replace("G", "G:3").replace("::", ":D:D:D")
            run_workflow(
                optionChoices, str(user.id), str(options.upper()), workflowType="G"
            )
            return True
        else: #str(optionChoices.upper()).startswith("X") or str(optionChoices.upper()).startswith("P"):
            optionChoices = optionChoices.replace(" ", "").replace(">", "_")
            while optionChoices.endswith("_"):
                optionChoices = optionChoices[:-1]
            run_workflow(
                optionChoices, str(user.id), str(options.upper().replace(":7:3:4",":7:3:0.008:4")), workflowType="X"
            )
            return True
            # Popen(
            #     [
            #         "pkscreener",
            #         "-a",
            #         "Y",
            #         "-e",
            #         "-p",
            #         "-o",
            #         str(options.upper()),
            #         "-u",
            #         str(user.id),
            #     ]
            # )
    except Exception as e: # pragma: no cover
        import traceback
        traceback.print_exc()
        print(e)
        start(update, context)


def BBacktests(update: Update, context: CallbackContext) -> str:
    """Show new choice of buttons"""
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Try Scanners", callback_data=str("CX")),
            # InlineKeyboardButton("Growth of 10k", callback_data=str("CG")),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    responseText = "Backtesting NOT implemented yet in this Bot!\nYou can use backtesting by downloading the software from https://github.com/pkjmesra/PKScreener/"
    responseText = f"{responseText}\nClick /start if you want to restart the session."
    editMessageText(query=query,editedText=sanitiseTexts(responseText),reply_markup=default_markup(user=user))
    registerUser(user)
    return START_ROUTES

def sendSubscriptionOption(update:Update,context:CallbackContext,scanId):
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    reply_markup = {
        "inline_keyboard": [
            [{"text": f"Yes! Subscribe", "callback_data": f"SUB_{scanId}"}]
        ],
    }
    message=f"🔴 <b>Please check your current alerts, balance and subscriptions using /OTP before subscribing for alerts</b>.🔴 If you are not already subscribed to this alert, would you like to subscribe to this (<b>{scanId}</b>) automated scan alert for a day during market hours (NSE - IST timezone)? You will need to pay ₹ {'40' if str(scanId).upper().startswith('P') else '31'} (One time) for automated alerts to <b>{scanId}</b> all day on the day of subscription. 🔴 If you say <b>Yes</b>, the corresponding charges will be deducted from your alerts balance!🔴"
    if len(str(scanId).strip()) > 0 and not str(scanId).startswith("B"):
        context.bot.send_message(
            chat_id=user.id, text=message, reply_markup=reply_markup, parse_mode="HTML"
        )
    
def end(update: Update, context: CallbackContext) -> str:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    query.answer()
    responseText = "See https://github.com/pkjmesra/PKScreener/ for more details or join https://t.me/PKScreener. \nSee you next time!"
    responseText = f"{responseText}\nClick /start if you want to restart the session."
    editMessageText(query=query,editedText=sanitiseTexts(responseText),reply_markup=default_markup(query.from_user))
    return ConversationHandler.END


# This can be your own ID, or one for a developer group/channel.
# You can use the /start command of this bot to see your chat id.
chat_idADMIN = 123456789
Channel_Id = 12345678
GROUP_CHAT_ID = 1001907892864


def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)
    global start_time
    timeSinceStarted = datetime.now() - start_time
    if (
        "telegram.error.Conflict" in tb_string
    ):  # A newer 2nd instance was registered. We should politely shutdown.
        if (
            timeSinceStarted.total_seconds() >= MINUTES_2_IN_SECONDS
        ):  # shutdown only if we have been running for over 2 minutes.
            # This also prevents this newer instance to get shutdown.
            # Instead the older instance will shutdown
            print(
                f"Stopping due to conflict after running for {timeSinceStarted.total_seconds()/60} minutes."
            )
            try:
                global int_timer
                if int_timer is not None:
                    int_timer.cancel()
            except: # pragma: no cover
                pass
                #https://github.com/python-telegram-bot/python-telegram-bot/issues/209
                # if _updater is not None:
                #     _updater.stop() # Calling stop from within a handler will cause deadlock
            try:
                # context.dispatcher.stop()
                thread.interrupt_main() # causes ctrl + c
                # sys.exit(0)
            except RuntimeError:
                pass
            except SystemExit:
                thread.interrupt_main()
            # sys.exit(0)
        else:
            print("Other instance running!")
            # context.application.run_polling(allowed_updates=Update.ALL_TYPES)
    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    try:
        # Finally, send the message
        if "telegram.error.Conflict" not in message and Channel_Id is not None and len(str(Channel_Id)) > 0:
            context.bot.send_message(
                chat_id=int(f"-{Channel_Id}"), text=message, parse_mode="HTML"
            )
    except Exception:# pragma: no cover
        try:
            if "telegram.error.Conflict" not in tb_string and Channel_Id is not None and len(str(Channel_Id)) > 0:
                context.bot.send_message(
                    chat_id=int(f"-{Channel_Id}"),
                    text=tb_string,
                    parse_mode="HTML",
                )
        except Exception:# pragma: no cover
            print(tb_string)


def command_handler(update: Update, context: CallbackContext) -> None:
    if _shouldAvoidResponse(update):
        return
    global bot_available
    if not bot_available:
        start(update, context)
        return START_ROUTES
    updateCarrier = None
    if update is None:
        return
    else:
        if hasattr(update, "callback_query") and update.callback_query is not None:
            updateCarrier = update.callback_query
        if hasattr(update, "message") and update.message is not None:
            updateCarrier = update.message
        if hasattr(update, "effective_message") and update.effective_message is not None:
            updateCarrier = update.effective_message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user

    msg = update.effective_message
    try:
        m = re.match(r"\s*/([0-9a-zA-Z_-]+)\s*(.*)", msg.text)
        cmd = m.group(1).lower()
        args = [arg for arg in re.split(r"\s+", m.group(2)) if len(arg)]
    except:
        pass
        return start(update,context)
    if cmd.startswith("cx_") or cmd.startswith("cb_") or cmd.startswith("cg_"):
        Level2(update=update, context=context)
        return START_ROUTES
    if cmd.startswith("cx") or cmd.startswith("cb") or cmd.startswith("cg"):
        XScanners(update=update, context=context)
        return START_ROUTES
    if cmd.startswith("cz"):
        end(update=update, context=context)
        return END_ROUTES

    if cmd == "start":
        start(update=update, context=context)
        return START_ROUTES
    if cmd == "help":
        help_command(update=update, context=context)
        return START_ROUTES
    cmdText = ""
    cmdText = f"{cmdText}\n/X_0 STOCK_CODE_HERE To get the stock analysis of an individual Stock"
    cmdText = f"{cmdText}\n/X_0 STOCK_CODE1,STOCK_CODE2 To get the stock analysis of multiple individual Stocks"
    cmdText = f"{cmdText}\n/F_0 STOCK_CODE1,STOCK_CODE2 To find which all scanners had these stock codes(Reverse look up)"

    if cmd.upper() in TOP_LEVEL_SCANNER_MENUS:
        shareUpdateWithChannel(update=update, context=context,optionChoices=msg)
        m0.renderForMenu(
            selectedMenu=None,
            skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        selectedMenu = m0.find(cmd.upper())
        cmds = m1.renderForMenu(
            selectedMenu=selectedMenu,
            skip=(INDEX_COMMANDS_SKIP_MENUS_SCANNER  if cmd in ["x"] else (INDEX_COMMANDS_SKIP_MENUS_BACKTEST if cmd in ["b"] else PIPED_SCAN_SKIP_COMMAND_MENUS)),
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        for cmd in cmds:
            if cmd in ["N", "0"]:
                continue
            cmdText = (
                f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
            )
        if cmd in ["x"]:
            cmdText = f"{cmdText}\n\nFor option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN\n or \n/X_0_0 SBIN\nand hit send where SBIN is the NSE stock code.For multiple stocks, you can type in \n/X_0 SBIN,ICICIBANK,OtherStocks\nYou can put in any number of stocks separated by space or comma(,)."
        """Send a message when the command /help is issued."""
        cmdText = f"{cmdText}\nClick /start if you want to restart the session."
        update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
        return START_ROUTES

    if update.message is None:
        help_command(update=update, context=context)
        return START_ROUTES

    if "x_0" in cmd or "x_0_0" in cmd or "b_0" in cmd or "g_0" in cmd or "f_0" in cmd:
        shareUpdateWithChannel(update=update, context=context,optionChoices=msg)
        shouldScan = False
        if len(args) > 0:
            shouldScan = True
            selection = [
                cmd.split("_")[0].upper(),
                "0",
                "0",
                f"{','.join(args)}".replace(" ", ""),
            ]
        if shouldScan:
            options = ":".join(selection)
            result = launchScreener(
                options=options,
                user=update.message.from_user,
                context=context,
                optionChoices=cmd.upper(),
                update=update,
            )
            if result:
                sendRequestSubmitted(cmd.upper(), update=update, context=context)
                scanRequest = cmd.upper().replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
                sendSubscriptionOption(update,context,scanRequest)
            return START_ROUTES
        else:
            if cmd in ["x"]:
                cmdText = "For option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN or /X_0_0 SBIN and hit send where SBIN is the NSE stock code.For multiple stocks, you can type in /X_0 SBIN,ICICIBANK,OtherStocks . You can put in any number of stocks separated by space or comma(,)."
            """Send a message when the command /help is issued."""
            cmdText = f"{cmdText}\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
            return START_ROUTES

    if "p_" in cmd:
        shareUpdateWithChannel(update=update, context=context,optionChoices=msg)
        selection = cmd.split("_")
        if len(selection) == 2:
            m0.renderForMenu(
                selectedMenu=None,
                skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m0.find(selection[0].upper())
            m1.renderForMenu(
                selectedMenu=selectedMenu,
                skip=PIPED_SCAN_SKIP_COMMAND_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m1.find(selection[1].upper())
            cmds = m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=UNSUPPORTED_COMMAND_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            for cmd in cmds:
                cmdText = (
                    f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                )
            cmdText = f"{cmdText}\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
            return START_ROUTES
        elif len(selection) == 3:
            m0.renderForMenu(
                selectedMenu=None,
                skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            cmds = m1.renderForMenu(m0.find(key="X"),skip=PIPED_SCAN_SKIP_INDEX_MENUS,asList=True,renderStyle=MenuRenderStyle.STANDALONE)
            for indexCmd in cmds:
                cmdText = (
                    f"{cmdText}\n\n/{cmd.upper()}{indexCmd.commandTextKey().replace('/X','')} for Piped scan of {indexCmd.commandTextLabel().replace('Scanners >',cmd.upper()+' >')}"
                )
            cmdText = f"{cmdText}\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
            return START_ROUTES
        elif len(selection) == 4:
            options = ":".join(selection)
            result = launchScreener(
                options=options.upper(),
                user=update.message.from_user,
                context=context,
                optionChoices=cmd.upper(),
                update=update,
            )
            if result:
                sendRequestSubmitted(cmd.upper(), update=update, context=context)
                scanRequest = cmd.upper().replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
                sendSubscriptionOption(update,context,scanRequest)
            return START_ROUTES
        
    if "x_" in cmd or "b_" in cmd or "g_" in cmd:
        shareUpdateWithChannel(update=update, context=context,optionChoices=msg)
        selection = cmd.split("_")
        if len(selection) == 2:
            m0.renderForMenu(
                selectedMenu=None,
                skip=TOP_LEVEL_SCANNER_SKIP_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m0.find(selection[0].upper())
            m1.renderForMenu(
                selectedMenu=selectedMenu,
                skip=(
                    INDEX_COMMANDS_SKIP_MENUS_SCANNER
                    if "x_" in cmd
                    else INDEX_COMMANDS_SKIP_MENUS_BACKTEST
                ),
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m1.find(selection[1].upper())
            if "x_" in cmd and selectedMenu.menuKey == "N":  # Nifty prediction
                options = ":".join(selection)
                result = launchScreener(
                    options=options,
                    user=update.message.from_user,
                    context=context,
                    optionChoices=cmd.upper(),
                    update=update,
                )
                if result:
                    sendRequestSubmitted(cmd.upper(), update=update, context=context)
                    scanRequest = cmd.upper().replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
                    sendSubscriptionOption(update,context,scanRequest)
                return START_ROUTES
            elif (
                "x_" in cmd and selectedMenu.menuKey == "0"
            ):  # a specific stock by name
                cmdText = "For option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN or /X_0_0 SBIN and hit send where SBIN is the NSE stock code.For multiple stocks, you can type in /X_0 SBIN,ICICIBANK,OtherStocks. You can put in any number of stocks separated by space or comma(,)."
                """Send a message when the command /help is issued."""
                cmdText = f"{cmdText}\nClick /start if you want to restart the session."
                update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
                return START_ROUTES
            cmds = m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=UNSUPPORTED_COMMAND_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            for cmd in cmds:
                cmdText = (
                    f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                )
            cmdText = f"{cmdText}\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
            return START_ROUTES
        elif len(selection) == 3:
            m0.renderForMenu(
                selectedMenu=None,
                skip=TOP_LEVEL_SCANNER_SKIP_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m0.find(selection[0].upper())
            m1.renderForMenu(
                selectedMenu=selectedMenu,
                skip=(
                    INDEX_COMMANDS_SKIP_MENUS_SCANNER
                    if "x_" in cmd
                    else INDEX_COMMANDS_SKIP_MENUS_BACKTEST
                ),
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m1.find(selection[1].upper())
            m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=UNSUPPORTED_COMMAND_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            if selection[2] in SCANNER_MENUS_WITH_SUBMENU_SUPPORT:
                selectedMenu = m2.find(selection[2].upper())
                cmds = m3.renderForMenu(
                    selectedMenu=selectedMenu,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0","M","Z"],
                )
                for cmd in cmds:
                    cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                cmdText = f"{cmdText}\nClick /start if you want to restart the session."
                update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
                return START_ROUTES
            else:
                if selection[2] == "4":  # Last N days
                    selection.extend(["D", ""])
                elif selection[2] == "5":  # RSI range
                    selection.extend(["D", "D"])
                elif selection[2] == "8":  # CCI range
                    selection.extend(["D", "D"])
                elif selection[2] == "9":  # Vol gainer ratio
                    selection.extend(["D", ""])
                elif selection[2] in SUPPORTED_COMMAND_MENUS:
                    selection.extend(["", ""])
        if len(selection) >= 4:
            if len(selection) == 4:
                if selection[2] in SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT.keys() and selection[3] in SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT[selection[2]]:
                    m0.renderForMenu(
                        selectedMenu=None,
                        skip=TOP_LEVEL_SCANNER_SKIP_MENUS,
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                    )
                    selectedMenu = m0.find(selection[0].upper())
                    m1.renderForMenu(
                        selectedMenu=selectedMenu,
                        skip=(
                            INDEX_COMMANDS_SKIP_MENUS_SCANNER
                            if "x_" in cmd
                            else INDEX_COMMANDS_SKIP_MENUS_BACKTEST
                        ),
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                    )
                    selectedMenu = m1.find(selection[1].upper())
                    m2.renderForMenu(
                        selectedMenu=selectedMenu,
                        skip=UNSUPPORTED_COMMAND_MENUS,
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                    )
                    if selection[2] in SCANNER_MENUS_WITH_SUBMENU_SUPPORT:
                        selectedMenu = m2.find(selection[2].upper())
                        m3.renderForMenu(
                            selectedMenu=selectedMenu,
                            skip=["0","M","Z"],
                            asList=True,
                            renderStyle=MenuRenderStyle.STANDALONE,
                        )
                        selectedMenu = m3.find(selection[3].upper())
                        cmds = m4.renderForMenu(
                            selectedMenu=selectedMenu,
                            asList=True,
                            renderStyle=MenuRenderStyle.STANDALONE,
                            skip=["0","M","Z"],
                        )
                        for cmd in cmds:
                            cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                        cmdText = f"{cmdText}\nClick /start if you want to restart the session."
                        update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"),reply_markup=default_markup(user=user),parse_mode="HTML")
                        return START_ROUTES

            options = ":".join(selection)
            result = launchScreener(
                options=options,
                user=update.message.from_user,
                context=context,
                optionChoices=cmd.upper(),
                update=update,
            )
            if result:
                sendRequestSubmitted(cmd.upper(), update=update, context=context)
                scanRequest = cmd.upper().replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
                sendSubscriptionOption(update,context,scanRequest)
            return START_ROUTES
    if cmd == "y" or cmd == "h":
        shareUpdateWithChannel(update=update, context=context,optionChoices=msg)
        from pkscreener.globals import showSendConfigInfo, showSendHelpInfo
        if cmd == "y":
            showSendConfigInfo(defaultAnswer='Y',user=str(update.message.from_user.id))
        elif cmd == "h":
            showSendHelpInfo(defaultAnswer='Y',user=str(update.message.from_user.id))
        return START_ROUTES
    update.message.reply_text(sanitiseTexts(f"{cmd.upper()} : Not implemented yet!"),reply_markup=default_markup(user=user),parse_mode="HTML")
    help_command(update=update, context=context)


def sendRequestSubmitted(optionChoices, update, context):
    updateCarrier = None
    if update is None:
        return
    else:
        if hasattr(update, "callback_query") and update.callback_query is not None:
            updateCarrier = update.callback_query
        if hasattr(update, "message") and update.message is not None:
            updateCarrier = update.message
        if hasattr(update, "effective_message") and update.effective_message is not None:
            updateCarrier = update.effective_message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user
    menuText = f"Thank you for choosing {optionChoices}. You will receive the notification/results in about 1-2 minutes! \nConsider donating to help keep this project going:\nUPI: <a href='https://tinyurl.com/v7h3t233'>PKScreener@APL</a> \nor <a href='https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra'>sponsor</a>"
    update.message.reply_text(sanitiseTexts(menuText),reply_markup=default_markup(user=user),parse_mode="HTML")
    # help_command(update=update, context=context)
    shareUpdateWithChannel(
        update=update, context=context, optionChoices=optionChoices
    )


def shareUpdateWithChannel(update, context, optionChoices=""):
    query = update.message or update.callback_query
    message = f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> began using ({optionChoices}) the bot!"
    if Channel_Id is not None and len(str(Channel_Id)) > 0:
        context.bot.send_message(
            chat_id=int(f"-{Channel_Id}"), text=message, parse_mode="HTML"
        )


def help_command(update: Update, context: CallbackContext) -> None:
    if _shouldAvoidResponse(update):
        return
    global bot_available
    if not bot_available:
        start(update, context)
        return START_ROUTES
    updateCarrier = None
    if update is None:
        return
    else:
        if update.callback_query is not None:
            updateCarrier = update.callback_query
        if update.message is not None:
            updateCarrier = update.message
        if updateCarrier is None:
            return
    # Get user that sent /start and log his name
    user = updateCarrier.from_user

    if user.id in user_states and user.username.lower() == OWNER_USER.lower():
        if "_awaiting_input_1" in user_states[user.id]:
            hskCmd = user_states[user.id].split("_")[0]
            user_states[user.id] = f"{hskCmd}_awaiting_input_2_{updateCarrier.text}"
            update.message.reply_text(f"{'Balance' if hskCmd == 'UUB' else 'Subscription'} to be updated for entered userID: {updateCarrier.text} ✅\nPlease enter the {'Balance' if hskCmd == 'UUB' else 'Subscription'} value:")
            return START_ROUTES
        elif "_awaiting_input_2_" in user_states[user.id]:
            hskCmd = user_states[user.id].split("_")[0]
            userID = user_states[user.id].split("_")[-1]
            results = updateSubscription(int(userID),float(updateCarrier.text),subtype="remove" if hskCmd=="DUS" else "add")
            if results is None:
                update.message.reply_text(f"✅ {'Balance' if hskCmd == 'UUB' else 'Subscription'} update for userID: {userID} with {'Balance' if hskCmd == 'UUB' else 'Subscription'} value: {updateCarrier.text} triggered!\nPlease check with Get Paying users in a few minutes!")
            # Clear user state
            del user_states[user.id]
            return START_ROUTES

    cmds = m0.renderForMenu(
        selectedMenu=None,
        skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    cmdText = "/otp to generate an OTP to login to PKScreener desktop console\n/check UPI_UTR_HERE_After_Making_Payment to share transaction reference number to automatically enable subscription after making payment via UPI"
    for cmd in cmds:
        if cmd.menuKey not in TOP_LEVEL_MARKUP_SKIP_MENUS:
            cmdText = f"{cmdText}\n{cmd.commandTextKey()} : {cmd.commandTextLabel()}"
    
    """Send a message when the command /help is issued."""
    if update is not None and update.message is not None:
        update.message.reply_text(
            sanitiseTexts(f"You can begin by typing in /start (Recommended) and hit send!\nOR\nChoose an option:\n{cmdText}\nWe recommend you start by clicking on this /start"),
            reply_markup=default_markup(user=user),parse_mode="HTML"
        )  #  \n\nThis bot restarts every hour starting at 5:30am IST until 10:30pm IST to keep it running on free servers. If it does not respond, please try again in a minutes to avoid the restart duration!
        query = update.message
        message = f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> began using the bot!"
        if Channel_Id is not None and len(str(Channel_Id)) > 0:
            context.bot.send_message(
                chat_id=int(f"-{Channel_Id}"), text=message, parse_mode="HTML"
            )
    registerUser(user)

def _shouldAvoidResponse(update):
    sentFrom = []
    if update.callback_query is not None:
        sentFrom.append(abs(update.callback_query.from_user.id))
    if update.message is not None and update.message.from_user is not None:
        sentFrom.append(abs(update.message.from_user.id))
        if update.message.from_user.username is not None:
            sentFrom.append(update.message.from_user.username)
    if update.channel_post is not None:
        if update.channel_post.chat is not None:
            sentFrom.append(abs(update.channel_post.chat.id))
            if update.channel_post.chat.username is not None:
                sentFrom.append(update.channel_post.chat.username)
        if update.channel_post.sender_chat is not None:
            sentFrom.append(abs(update.channel_post.sender_chat.id))
            sentFrom.append(update.channel_post.sender_chat.username)
    if update.edited_channel_post is not None:
        sentFrom.append(abs(update.edited_channel_post.sender_chat.id))

    if (
        abs(int(Channel_Id)) in sentFrom
        or abs(int(GROUP_CHAT_ID)) in sentFrom
        or "GroupAnonymousBot" in sentFrom
        or "PKScreener" in sentFrom
        or "PKScreeners" in sentFrom
    ):
        # We want to avoid sending any help message back to channel
        # or group in response to our own messages
        return True
    return False


def addCommandsForMenuItems(application):
    # Add commands for x_0, x_0_0 and f_0
    application.add_handler(CommandHandler("X_0", command_handler))
    application.add_handler(CommandHandler("X_0_0", command_handler))
    application.add_handler(CommandHandler("F_0", command_handler))
    cmds0 = m0.renderForMenu(
        selectedMenu=None,
        skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    cmds3p = m4.renderForMenu(m0.find(key="X"),skip=PIPED_SCAN_SKIP_INDEX_MENUS,asList=True,renderStyle=MenuRenderStyle.STANDALONE)
    for mnu0 in cmds0:
        p0 = mnu0.menuKey.upper()
        application.add_handler(CommandHandler(p0, command_handler))
        selectedMenu = m0.find(p0)
        cmds1 = m1.renderForMenu(
            selectedMenu=selectedMenu,
            skip=(
                INDEX_COMMANDS_SKIP_MENUS_SCANNER if p0 == "X" else (INDEX_COMMANDS_SKIP_MENUS_BACKTEST if p0 == "B" else PIPED_SCAN_SKIP_COMMAND_MENUS)
            ),
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        for mnu1 in cmds1:
            p1 = mnu1.menuKey.upper()
            if p1 in ["N", "0"]:
                if p1 in ["N"]:
                    application.add_handler(
                        CommandHandler(f"{p0}_{p1}", command_handler)
                    )
                continue
            application.add_handler(CommandHandler(f"{p0}_{p1}", command_handler))
            selectedMenu = m1.find(p1)
            cmds2 = m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=UNSUPPORTED_COMMAND_MENUS,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            for mnu2 in cmds2:
                p2 = mnu2.menuKey.upper()
                application.add_handler(
                    CommandHandler(f"{p0}_{p1}_{p2}", command_handler)
                )
                if p0 in ["P"]:
                    for indexCmd in cmds3p:
                        p3 = indexCmd.menuKey.upper()
                        application.add_handler(
                            CommandHandler(f"{p0}_{p1}_{p2}_{p3}", command_handler)
                        )
                if (p2 in SCANNER_MENUS_WITH_SUBMENU_SUPPORT and p0 in ["X", "B"]):
                    selectedMenu = m2.find(p2)
                    cmds3 = m3.renderForMenu(
                        selectedMenu=selectedMenu,
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                        skip=["0","M","Z"],
                    )
                    for mnu3 in cmds3:
                        p3 = mnu3.menuKey.upper()
                        application.add_handler(
                            CommandHandler(f"{p0}_{p1}_{p2}_{p3}", command_handler)
                        )
                        if p2 in SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT.keys() and p3 in SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT[p2]:
                            selectedMenu = m3.find(p3)
                            cmds4 = m4.renderForMenu(
                                selectedMenu=selectedMenu,
                                asList=True,
                                renderStyle=MenuRenderStyle.STANDALONE,
                                skip=["0","M","Z"],
                            )
                            if cmds4 is not None and len(cmds4) > 0:
                                for mnu4 in cmds4:
                                    p4 = mnu4.menuKey.upper()
                                    application.add_handler(
                                        CommandHandler(f"{p0}_{p1}_{p2}_{p3}_{p4}", command_handler)
                                    )

# def send_stuff(context: CallbackContext):
#   job = context.job

#   keyboard = [ 
#     [   
#         InlineKeyboardButton("NEVER", callback_data="NEVER"),
#         InlineKeyboardButton("UNLIKELY", callback_data="UNLIKELY")
#     ],  
#     [   
#         InlineKeyboardButton("MEH", callback_data="MEH"),
#         InlineKeyboardButton("MAYBE", callback_data="MAYBE")
#     ],  
#     [   
#         InlineKeyboardButton("YES", callback_data="YES"),
#         InlineKeyboardButton("ABSOLUTELY", callback_data="ABSOLUTELY")
#     ],  
#     [   
#         InlineKeyboardButton("RATHER NOT SAY", callback_data="UNKNOWN")
#     ]   
#   ]

#   reply_markup = InlineKeyboardMarkup(keyboard)

#   context.bot.send_photo(job.context, photo=open(PATH+thefile, 'rb'))
#   # return values of send_message are saved in the 'msg' var
#   msg = context.bot.send_message(job.context, text='RATE', reply_markup=reply_markup)

#   # the following job is created every time the send_stuff function is called
#   context.job_queue.run_once(
#     callback=cleanup,
#     when=5,
#     context=msg,
#     name='cleanup'
#   )

# # the function called by the job
# def cleanup(context: CallbackContext):
#   job = context.job

#   context.bot.edit_message_text(
#     chat_id=job.context.chat.id,
#     text='NO ANSWER PROVIDED',
#     message_id=job.context.message_id
#   )

@ping(interval=300,instance=PKAnalyticsService(),prefix="bot_")
def runpkscreenerbot(availability=True) -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    global chat_idADMIN, Channel_Id, bot_available, _updater
    bot_available = availability
    Channel_Id, TOKEN, chat_idADMIN, GITHUB_TOKEN = PKEnvironment().secrets
    # TOKEN = '1234567'
    # Channel_Id = 1001785195297
    # application = Application.builder().token(TOKEN).build()
    application = Updater(TOKEN)
    _updater = application
    # Get the dispatcher to register handlers
    dispatcher = application.dispatcher
    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      CommandHandler("otp", otp),
                      CommandHandler("check", matchUTR)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(XScanners, pattern="^" + str("CX") + "$"),
                CallbackQueryHandler(otp, pattern="^" + str("OTP") + "$"),
                CallbackQueryHandler(XScanners, pattern="^" + str("CB") + "$"),
                CallbackQueryHandler(PScanners, pattern="^" + str("CP") + "$"),
                CallbackQueryHandler(XScanners, pattern="^" + str("CMI_")),
                CallbackQueryHandler(XDevModeHandler, pattern="^" + str("CDV_")),
                # CallbackQueryHandler(XScanners, pattern="^" + str("CG") + "$"),
                CallbackQueryHandler(Level2, pattern="^" + str("CX_")),
                CallbackQueryHandler(Level2, pattern="^" + str("CB_")),
                CallbackQueryHandler(Level2, pattern="^" + str("CP_")),
                CallbackQueryHandler(subscribeToScannerAlerts, pattern="^" + str("SUB_")),
                CallbackQueryHandler(viewSubscriptionOptions, pattern="^" + str("VS_")),
                CallbackQueryHandler(cancelAlertSubscription, pattern="^" + str("CAN_")),
                CallbackQueryHandler(handleHousekeeping, pattern="^" + str("CHSK_")),
                # CallbackQueryHandler(Level2, pattern="^" + str("CG_")),
                CallbackQueryHandler(end, pattern="^" + str("CZ") + "$"),
                CallbackQueryHandler(start, pattern="^"),
            ],
            END_ROUTES: [],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    for handler in conv_handler.entry_points:
        dispatcher.add_handler(handler)
    for handler in conv_handler.states[START_ROUTES]:
        dispatcher.add_handler(handler)
    # dispatcher.add_handler(CommandHandler("otp", otp))
    # dispatcher.add_handler(CommandHandler("check", matchUTR))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, help_command)
    )
    # application.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, command_handler))
    # application.add_handler(MessageHandler(filters.COMMAND, command_handler))
    # Add ConversationHandler to application that will be used for handling updates
    addCommandsForMenuItems(dispatcher)
    # dispatcher.add_handler(conv_handler)
    # ...and the error handler
    dispatcher.add_error_handler(error_handler)
    if bot_available:
        # Run the intraday monitor
        initializeIntradayTimer()
        loadRegisteredUsers()
    # Run the bot until the user presses Ctrl-C
    # application.run_polling(allowed_updates=Update.ALL_TYPES)
    # Start the Bot
    application.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    application.idle()


if __name__ == "__main__":
    runpkscreenerbot()
