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

from PKDevTools.classes.Environment import PKEnvironment
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.MarketHours import MarketHours
from PKDevTools.classes.UserSubscriptions import PKUserSusbscriptions, PKSubscriptionModel
from pkscreener.classes.MenuOptions import MenuRenderStyle, menu, menus,MAX_MENU_OPTION
from pkscreener.classes.WorkflowManager import run_workflow
import pkscreener.classes.ConfigManager as ConfigManager
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

TOP_LEVEL_SCANNER_MENUS = ["X", "B", "MI","DV", "P"]
TOP_LEVEL_SCANNER_SKIP_MENUS = ["M", "S", "F", "G", "C", "T", "D", "I", "E", "U", "L", "Z", "P"] # Last item will be skipped.
INDEX_SKIP_MENUS = ["W","E","M","Z","0","2","3","4","6","7","8","9","10","S","15"]
SCANNER_SKIP_MENUS_1_TO_6 = ["0","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_7_TO_12 = ["0","1","2","3","4","5","6","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_13_TO_18 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_19_TO_25 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","22","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_26_TO_31 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","32","33","34","35","36","37","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_32_TO_37 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","38","39","40","41","42","43","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_SKIP_MENUS_38_TO_43 = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","44","45","M","Z",str(MAX_MENU_OPTION)]
SCANNER_MENUS_WITH_NO_SUBMENUS = ["1","2","3","10","11","12","13","14","15","16","17","18","19","20","21","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45"]
SCANNER_MENUS_WITH_SUBMENU_SUPPORT = ["6", "7", "21", "33"]
SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT = {"6":[ "7","10"], "7":[ "3","6","9"],}

INDEX_COMMANDS_SKIP_MENUS_SCANNER = ["W", "E", "M", "Z", "S"]
INDEX_COMMANDS_SKIP_MENUS_BACKTEST = ["W", "E", "M", "Z", "S", "N", "0", "15"]
PIPED_SCAN_SKIP_COMMAND_MENUS =["2", "3", "M", "0", "4"]
PIPED_SCAN_SKIP_INDEX_MENUS =["W","N","E","S","0","Z","M","15"]
UNSUPPORTED_COMMAND_MENUS =["22","42","M","Z","0",str(MAX_MENU_OPTION)]
SUPPORTED_COMMAND_MENUS = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45"]

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
    except: # pragma: no cover
        launchIntradayMonitor()
        pass

def sanitiseTexts(text):
    MAX_MSG_LENGTH = 4096
    if len(text) > MAX_MSG_LENGTH:
        return text[:MAX_MSG_LENGTH]
    return text

def otp(update: Update, context: CallbackContext) -> str:
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
        try:
            otpValue = 0
            dbManager = DBManager()
            otpValue, subsModel,subsValidity = dbManager.getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
        except Exception as e: # pragma: no cover
            pass
        userText = f"\nUserID: <b>{user.id}</b>"
        try:
            subscriptionModelNames = "\n<pre>Following basic and premium subscription models are available. Premium subscription allows for unlimited premium scans:\n"
            for name,value in PKUserSusbscriptions().subscriptionKeyValuePairs.items():
                if name == PKSubscriptionModel.No_Subscription.name:
                    subscriptionModelNames = f"{subscriptionModelNames}\n{name} : ₹ {value} (Only Basic Scans are free)\n"
                else:
                    subscriptionModelNames = f"{subscriptionModelNames}\n{name.ljust(15)} : ₹ {value}"
            subscriptionModelNames = f"{subscriptionModelNames}</pre>\nPlease pay to subscribe:\n\n1. Using UPI(India) to <b>PKScreener@APL</b> \nor\n2. Proudly <b>sponsor</b>: https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra\n\nPlease drop a message to @ItsOnlyPK on Telegram after paying to enable subscription!"

            subscriptionModelName = PKUserSusbscriptions().subscriptionValueKeyPairs[subsModel]
            if subscriptionModelName != PKSubscriptionModel.No_Subscription.name:
                subscriptionModelName = f"{subscriptionModelName} (Expires on: {subsValidity})"
        except:
            subscriptionModelName = PKSubscriptionModel.No_Subscription.name
            pass
        if otpValue == 0:
            updatedResults = f"We are having difficulty generating OTP for your {userText}. Please try again later."
        else:
            updatedResults = f"Please use your {userText} \nwith the following OTP to login to PKScreener:\n<b>{otpValue}</b>\n\nYour current subscription : <b>{subscriptionModelName}</b>. {subscriptionModelNames}"
    update.message.reply_text(sanitiseTexts(updatedResults), parse_mode="HTML")
    shareUpdateWithChannel(update=update, context=context, optionChoices=f"/otp\n{updatedResults}")
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
        mns = m0.renderForMenu(asList=True)
        if (PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]) or ("PKDevTools_Default_Log_Level" in os.environ.keys()) or sys.argv[0].endswith(".py"):
            mns.append(menu().create(f"MI_{monitorIndex}", "Int. Monitor", 2))
        if user.username == OWNER_USER:
            mns.append(menu().create(f"DV_0", ("✅" if not configManager.logsEnabled else "🚫"), 2))
            mns.append(menu().create(f"DV_1", "🔄", 2))

        inlineMenus = []
        for mnu in mns:
            if mnu.menuKey[0:2] in TOP_LEVEL_SCANNER_MENUS:
                inlineMenus.append(
                    InlineKeyboardButton(
                        mnu.menuText.split("(")[0],
                        callback_data="C" + str(mnu.menuKey),
                    )
                )
        keyboard = [inlineMenus]
        reply_markup = InlineKeyboardMarkup(keyboard)
        cmds = m0.renderForMenu(
            selectedMenu=None,
            skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
    else:
        reply_markup = None

    if updatedResults is None:
        cmdText = "\n/otp to generate an OTP to login to PKScreener desktop console"
        for cmd in cmds:
            cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
        tosDisclaimerText = "By using this Software, you agree to\n[+] having read through the Disclaimer (https://pkjmesra.github.io/PKScreener/Disclaimer.txt)\n[+] and accept Terms Of Service (https://pkjmesra.github.io/PKScreener/tos.txt) of PKScreener.\n\n[+] If that is not the case, you MUST immediately terminate using PKScreener and exit now!\n\n"
        menuText = f"Welcome {user.first_name}, {(user.username)}!\n\n{tosDisclaimerText}Please choose a menu option by selecting a button from below.\n\nYou can also explore a wide variety of all other scanners by typing in \n{cmdText}\n\n OR just use the buttons below to choose."
        try:
            if updateCarrier is not None and updateCarrier.data is not None and updateCarrier.data == "CP":
                menuText = f"Piped Scanners are available using /P . Click on this /P to begin using piped scanners. To use other scanners, choose a menu option by selecting a button from below.\n\nYou can also explore a wide variety of all other scanners by typing in \n{cmdText}\n\n OR just use the buttons below to choose."
        except: # pragma: no cover
            pass
        menuText = f"{menuText}\n\nClick /start if you want to restart the session."
    else:
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
        )
    if Channel_Id is not None and len(str(Channel_Id)) > 0:
        context.bot.send_message(
            chat_id=int(f"-{Channel_Id}"),
            text=f"Name: {user.first_name}, Username:@{user.username} with ID: {str(user.id)} started using the bot!\n{chosenBotMenuOption}",
            parse_mode="HTML",
        )
    DBManager().getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
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
        except: # pragma: no cover
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
        except: # pragma: no cover
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
        logger.info(e)
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
                except: # pragma: no cover
                    pass
            
            launchIntradayMonitor()
            start(update, context,chosenBotMenuOption=chosenBotMenuOption)
        elif devModeIndex == 1: # Restart the bot service
            resp = run_workflow(None, None,None, workflowType="R")
            start(update, context,chosenBotMenuOption=f"{resp.status_code}: {resp.text}")
    return START_ROUTES

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
    data = query.data.upper().replace("CX", "X").replace("CB", "B").replace("CG", "G").replace("CMI", "MI")
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

    midSkip = "13" if data == "X" else "N"
    skipMenus = [midSkip]
    skipMenus.extend(INDEX_SKIP_MENUS)
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
    menuText = menuText + "\n\nH > Home"
    mns = m1.renderForMenu(
        m0.find(data),
        skip=skipMenus,
        asList=True,
    )
    mns.append(menu().create("H", "Home", 2))
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
    if query.message.text == menuText:
        menuText = f"{PKDateUtilities.currentDateTime()}:\n{menuText}"
    menuText = f"{menuText}\n\nClick /start if you want to restart the session."
    query.edit_message_text(text=menuText, reply_markup=reply_markup)
    DBManager().getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
    return START_ROUTES


def Level2(update: Update, context: CallbackContext) -> str:
    """Show new choice of buttons"""
    inlineMenus = []
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
        query.data.upper().replace("CX", "X").replace("CB", "B").replace("CG", "G")
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
    if selection[len(selection)-1].upper() == "H":
        start(update, context)
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
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_19_TO_25,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\n\nP4 > More Options"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_19_TO_25,
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
            menuText = menuText + "\n"
            menuText = menuText + "\nH > Home"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=SCANNER_SKIP_MENUS_38_TO_43,
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("H", "Home", 2))
        elif str(selection[2]).isnumeric():
            preSelection = f"{selection[0]}_{selection[1]}_{selection[2]}"
            if selection[2] in SCANNER_MENUS_WITH_SUBMENU_SUPPORT:
                menuText = m3.renderForMenu(
                    m2.find(selection[2]),
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0"],
                )
                mns = m3.renderForMenu(
                    m2.find(selection[2]),
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0"],
                )
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
            query.data.upper().replace("CX", "X").replace("CB", "B").replace("CG", "G")
        )
    optionChoices = ""
    if len(selection) <= 3 and mns is not None:
        for mnu in mns:
            inlineMenus.append(
                InlineKeyboardButton(
                    mnu.menuKey,
                    callback_data="C" + str(f"{preSelection}_{mnu.menuKey}"),
                )
            )
        keyboard = [inlineMenus]
        reply_markup = InlineKeyboardMarkup(keyboard)
    elif len(selection) >= 4:
        optionChoices = (
            f"{selection[0]} > {selection[1]} > {selection[2]} > {selection[3]}"
        )
        expectedTime = f"{'10 to 15' if '> 15' in optionChoices else '1 to 2'}"
        menuText = f"Thank you for choosing {optionChoices.replace(' >  > ','')}. You will receive the notification/results in about {expectedTime} minutes. It generally takes 1-2 minutes for NSE (2000+) stocks and 10-15 minutes for NASDAQ (7300+).\n\nPKScreener had been free for a long time, but owing to cost/budgeting issues, only a basic set of features will always remain free for everyone. Consider donating to help cover the basic server costs or subscribe to premium, if not subscribed yet:\n\nUPI (India): PKScreener@APL \n\nor\nhttps://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra"

        reply_markup = default_markup(inlineMenus)
        options = ":".join(selection)
        shouldSendUpdate = launchScreener(
            options=options,
            user=query.from_user,
            context=context,
            optionChoices=optionChoices,
            update=update,
        )
        if not shouldSendUpdate:
            DBManager().getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
            return START_ROUTES
    try:
        if optionChoices != "" and Channel_Id is not None and len(str(Channel_Id)) > 0:
            context.bot.send_message(
                chat_id=int(f"-{Channel_Id}"),
                text=f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> submitted scan request <b>{optionChoices}</b> to the bot!",
                parse_mode="HTML",
            )
    except Exception:# pragma: no cover
        start(update, context)
    menuText =  menuText.replace("\n     ","\n").replace("\n    ","\n").replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"")
    if not str(optionChoices.upper()).startswith("B"):
        sendUpdatedMenu(
            menuText=menuText, update=update, context=context, reply_markup=reply_markup
        )
    DBManager().getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
    return START_ROUTES

def default_markup(inlineMenus):
    mns = m0.renderForMenu(asList=True)
    for mnu in mns:
        if mnu.menuKey in TOP_LEVEL_SCANNER_MENUS:
            inlineMenus.append(
                    InlineKeyboardButton(
                        mnu.menuText.split("(")[0],
                        callback_data="C" + str(mnu.menuKey),
                    )
                )
    keyboard = [inlineMenus]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def sendUpdatedMenu(menuText, update: Update, context, reply_markup, replaceWhiteSpaces=True):
    try:
        menuText.replace("     ", "").replace("    ", "").replace("\t", "").replace(colorText.FAIL,"").replace(colorText.END,"").replace(colorText.WHITE,"") if replaceWhiteSpaces else menuText
        menuText = f"{menuText}\n\nClick /start if you want to restart the session." if "/start" not in menuText else menuText
        if update.callback_query.message.text == menuText:
            menuText = f"{PKDateUtilities.currentDateTime()}:\n{menuText}"
        update.callback_query.edit_message_text(
            text=menuText,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception as e:# pragma: no cover
        logger.log(e)
        start(update, context)

def isUserSubscribed(user):
    if user is not None:
        return PKUserSusbscriptions.userSubscribed(userID=str(user.id))
    return False

def launchScreener(options, user, context, optionChoices, update):
    try:
        if not isUserSubscribed(user):
            basicSubscriptions = ["X_0","X_N","X_1"]
            scanRequest = optionChoices.replace(" ", "").replace(">", "_").replace(":","_").replace("_D","").upper()
            isBasicScanRequest = False
            for basicSub in basicSubscriptions:
                if basicSub in scanRequest:
                    isBasicScanRequest = True
                    break
            if not isBasicScanRequest:
                responseText = f"Thank you for choosing {scanRequest}!\n\nThis scan request is,however,protected and is only available to premium subscribers. It seems like you are not subscribed to the paid/premium subscription to PKScreener.\nPlease checkout all premium options by sending out a request:\n\n/OTP\n\nFor basic/unpaid users, you can try out the following:\n /X_0 StockCode1,StockCode2,etc.\n/X_N\n/X_1\n"
                if update is not None and update.message is not None:
                    update.message.reply_text(sanitiseTexts(responseText))
                else:
                    responseText = f"{responseText}\n\nClick /start if you want to restart the session."
                    update.callback_query.edit_message_text(
                        text=responseText,
                        reply_markup=default_markup([]),
                    )
                shareUpdateWithChannel(update=update, context=context, optionChoices=optionChoices)
                return False

        if str(optionChoices.upper()).startswith("B"):
            optionChoices = optionChoices.replace(" ", "").replace(">", "_").replace(":","_").replace("_D","")
            while optionChoices.endswith("_"):
                optionChoices = optionChoices[:-1]
            if str(optionChoices).split("_")[2] == "6" and str(optionChoices).split("_")[3] == "7":
                optionChoices = f"{optionChoices}_3" # Lorenzian Any/All
            responseText = f"Thank you for choosing {optionChoices}!\n\nHere are the results:\n\nInsights: https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{optionChoices}_Insights_DateSorted.html"
            responseText = f"{responseText}\n\nSummary: https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{optionChoices}_Summary_StockSorted.html"
            responseText = f"{responseText}\n\nStock-wise: https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{optionChoices}_backtest_result_StockSorted.html"
            responseText = f"{responseText}\n\nOther Reports: https://pkjmesra.github.io/PKScreener/BacktestReports.html"
            if update is not None and update.message is not None:
                update.message.reply_text(sanitiseTexts(responseText))
            else:
                responseText = f"{responseText}\n\nClick /start if you want to restart the session."
                update.callback_query.edit_message_text(
                    text=responseText,
                    reply_markup=default_markup([]),
                )
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
    responseText = "Backtesting NOT implemented yet in this Bot!\n\n\nYou can use backtesting by downloading the software from https://github.com/pkjmesra/PKScreener/"
    responseText = f"{responseText}\n\nClick /start if you want to restart the session."
    query.edit_message_text(
        text=responseText,
        reply_markup=reply_markup,
    )
    DBManager().getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)
    return START_ROUTES


def end(update: Update, context: CallbackContext) -> str:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    query.answer()
    responseText = "See https://github.com/pkjmesra/PKScreener/ for more details or join https://t.me/PKScreener. \n\n\nSee you next time!"
    responseText = f"{responseText}\n\nClick /start if you want to restart the session."
    query.edit_message_text(
        text=responseText
    )
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
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
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
    msg = update.effective_message
    m = re.match("\s*/([0-9a-zA-Z_-]+)\s*(.*)", msg.text)
    cmd = m.group(1).lower()
    args = [arg for arg in re.split("\s+", m.group(2)) if len(arg)]
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
        shareUpdateWithChannel(update=update, context=context)
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
        cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
        update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
        return START_ROUTES

    if update.message is None:
        help_command(update=update, context=context)
        return START_ROUTES

    if "x_0" in cmd or "x_0_0" in cmd or "b_0" in cmd or "g_0" in cmd or "f_0" in cmd:
        shareUpdateWithChannel(update=update, context=context)
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
            return START_ROUTES
        else:
            if cmd in ["x"]:
                cmdText = "For option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN or /X_0_0 SBIN and hit send where SBIN is the NSE stock code.For multiple stocks, you can type in /X_0 SBIN,ICICIBANK,OtherStocks . You can put in any number of stocks separated by space or comma(,)."
            """Send a message when the command /help is issued."""
            cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
            return START_ROUTES

    if "p_" in cmd:
        shareUpdateWithChannel(update=update, context=context)
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
            cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
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
            cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
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
            return START_ROUTES
        
    if "x_" in cmd or "b_" in cmd or "g_" in cmd:
        shareUpdateWithChannel(update=update, context=context)
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
                return START_ROUTES
            elif (
                "x_" in cmd and selectedMenu.menuKey == "0"
            ):  # a specific stock by name
                cmdText = "For option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN or /X_0_0 SBIN and hit send where SBIN is the NSE stock code.For multiple stocks, you can type in /X_0 SBIN,ICICIBANK,OtherStocks. You can put in any number of stocks separated by space or comma(,)."
                """Send a message when the command /help is issued."""
                cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
                update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
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
            cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
            update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
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
                    skip=["0"],
                )
                for cmd in cmds:
                    cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
                update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
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
                            skip=["0"],
                            asList=True,
                            renderStyle=MenuRenderStyle.STANDALONE,
                        )
                        selectedMenu = m3.find(selection[3].upper())
                        cmds = m4.renderForMenu(
                            selectedMenu=selectedMenu,
                            asList=True,
                            renderStyle=MenuRenderStyle.STANDALONE,
                            skip=["0"],
                        )
                        for cmd in cmds:
                            cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                        cmdText = f"{cmdText}\n\nClick /start if you want to restart the session."
                        update.message.reply_text(sanitiseTexts(f"Choose an option:\n{cmdText}"))
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
            return START_ROUTES
    if cmd == "y" or cmd == "h":
        shareUpdateWithChannel(update=update, context=context)
        from pkscreener.globals import showSendConfigInfo, showSendHelpInfo
        if cmd == "y":
            showSendConfigInfo(defaultAnswer='Y',user=str(update.message.from_user.id))
        elif cmd == "h":
            showSendHelpInfo(defaultAnswer='Y',user=str(update.message.from_user.id))
        # result = launchScreener(
        #     options=f"{cmd.upper()}:",
        #     user=update.message.from_user,
        #     context=context,
        #     optionChoices=cmd.upper(),
        #     update=update,
        # )
        # sendRequestSubmitted(cmd.upper(), update=update, context=context)
        return START_ROUTES
    update.message.reply_text(sanitiseTexts(f"{cmd.upper()} : Not implemented yet!"))
    help_command(update=update, context=context)


def sendRequestSubmitted(optionChoices, update, context):
    menuText = f"Thank you for choosing {optionChoices}. You will receive the notification/results in about 1-2 minutes! \n\nConsider donating to help keep this project going:\nUPI: PKScreener@APL \nor\nhttps://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra"
    update.message.reply_text(sanitiseTexts(menuText))
    help_command(update=update, context=context)
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

    cmds = m0.renderForMenu(
        selectedMenu=None,
        skip=TOP_LEVEL_SCANNER_SKIP_MENUS[:len(TOP_LEVEL_SCANNER_SKIP_MENUS)-1],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    cmdText = "\n/otp to generate an OTP to login to PKScreener desktop console"
    for cmd in cmds:
        cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
    reply_markup = default_markup([])
    
    """Send a message when the command /help is issued."""
    if update is not None and update.message is not None:
        update.message.reply_text(
            sanitiseTexts(f"You can begin by typing in /start (Recommended) and hit send!\n\nOR\n\nChoose an option:\n{cmdText}\n\nWe recommend you start by clicking on this /start")
        )  #  \n\nThis bot restarts every hour starting at 5:30am IST until 10:30pm IST to keep it running on free servers. If it does not respond, please try again in a minutes to avoid the restart duration!
        query = update.message
        message = f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> began using the bot!"
        if Channel_Id is not None and len(str(Channel_Id)) > 0:
            context.bot.send_message(
                chat_id=int(f"-{Channel_Id}"), text=message, parse_mode="HTML"
            )
    DBManager().getOTP(user.id,user.username,f"{user.first_name} {user.last_name}",validityIntervalInSeconds=configManager.otpInterval)


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
                        skip=["0"],
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
                                skip=["0"],
                            )
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
        entry_points=[CommandHandler("start", start),CommandHandler("otp", otp)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(XScanners, pattern="^" + str("CX") + "$"),
                CallbackQueryHandler(XScanners, pattern="^" + str("CB") + "$"),
                CallbackQueryHandler(XScanners, pattern="^" + str("CMI_")),
                CallbackQueryHandler(XDevModeHandler, pattern="^" + str("CDV_")),
                # CallbackQueryHandler(XScanners, pattern="^" + str("CG") + "$"),
                CallbackQueryHandler(Level2, pattern="^" + str("CX_")),
                CallbackQueryHandler(Level2, pattern="^" + str("CB_")),
                CallbackQueryHandler(Level2, pattern="^" + str("CP_")),
                # CallbackQueryHandler(Level2, pattern="^" + str("CG_")),
                CallbackQueryHandler(end, pattern="^" + str("CZ") + "$"),
                CallbackQueryHandler(start, pattern="^"),
            ],
            END_ROUTES: [],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    dispatcher.add_handler(CommandHandler("otp", otp))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, help_command)
    )
    # application.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, command_handler))
    # application.add_handler(MessageHandler(filters.COMMAND, command_handler))
    # Add ConversationHandler to application that will be used for handling updates
    addCommandsForMenuItems(dispatcher)
    dispatcher.add_handler(conv_handler)
    # ...and the error handler
    dispatcher.add_error_handler(error_handler)
    if bot_available:
        # Run the intraday monitor
        initializeIntradayTimer()
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
