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
import sys
import os
from time import sleep

from pkscreener.classes.ConfigManager import tools, parser
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from pkscreener.classes.DBManager import DBManager
from PKDevTools.classes.log import default_logger

class PKUserRegistration:
    def login():
        return True
        try:
            dbManager = DBManager()
            if "RUNNER" in os.environ.keys() or dbManager.shouldSkipLoading():
                return True
        except: # pragma: no cover
            return True
        from pkscreener.classes import Utility
        Utility.tools.clearScreen(userArgs=None, clearAlways=True, forceTop=True)
        configManager = tools()
        configManager.getConfig(parser)
        OutputControls().printOutput(f"[+] {colorText.GREEN}PKScreener will always remain free and open source!{colorText.END}\n[+] {colorText.GREEN}Please use {colorText.END}{colorText.WARN}@nse_pkscreener_bot{colorText.END}{colorText.GREEN} in telegram app on \n    your mobile phone to request your {colorText.END}{colorText.WARN}userID{colorText.END}{colorText.GREEN} and {colorText.END}{colorText.WARN}OTP{colorText.END}{colorText.GREEN} to login:\n{colorText.END}")
        username = None
        if configManager.userID is not None and len(configManager.userID) >= 1:
            username = input(f"[+] Your Username or UserID from telegram: (Default: {colorText.GREEN}{configManager.userID}{colorText.END}): ") or configManager.userID
        else:
            username = input(f"[+] {colorText.GREEN}Your Username or UserID from telegram: {colorText.END}")
        if username is None or len(username) <= 0:
            OutputControls().printOutput(f"{colorText.WARN}[+] You MUST register or login to use PKScreener!{colorText.END}\n[+] {colorText.FAIL}Exiting now!{colorText.END}")
            sleep(5)
            sys.exit(0)
        otp = input(f"[+] {colorText.WARN}OTP received on telegram from {colorText.END}{colorText.GREEN}@nse_pkscreener_bot (Use command /otp to get OTP): {colorText.END}")
        invalidOTP = False
        try:
            otpTest = int(otp)
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            invalidOTP = True
            pass
        if otp is None or len(str(otp)) <= 5 or invalidOTP:
            OutputControls().printOutput(f"{colorText.WARN}[+] Please enter a valid OTP!{colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
            sleep(3)
            return PKUserRegistration.login()
        try:
            userUsedUserID = False
            try:
                usernameInt = int(username)
                userUsedUserID = True
            except: # pragma: no cover
                userUsedUserID = False
                pass

            if dbManager.validateOTP(username,str(otp)):
                configManager.userID = username
                configManager.setConfig(parser,default=True,showFileCreatedText=False)
                Utility.tools.clearScreen(userArgs=None, clearAlways=True, forceTop=True)
                return True
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        OutputControls().printOutput(f"{colorText.WARN}[+] Invalid userID/username or OTP!{colorText.END}\n{colorText.GREEN}[+] May be try entering the {'UserID instead of username?' if userUsedUserID else 'Username instead of userID?'} {colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
        sleep(3)
        return PKUserRegistration.login()
