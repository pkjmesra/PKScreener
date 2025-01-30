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
from enum import Enum

from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from pkscreener.classes.ConfigManager import tools, parser
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.Pikey import PKPikey
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger
from pkscreener.classes import Utility
from pkscreener.classes.MenuOptions import menus

class ValidationResult(Enum):
    Success = 0
    BadUserID = 1
    BadOTP = 2
    Trial = 3

class PKUserRegistration(SingletonMixin, metaclass=SingletonType):
    def __init__(self):
        super(tools, self).__init__()
        self._userID = 0
        self._otp = 0

    @classmethod
    def populateSavedUserCreds(self):
        configManager = tools()
        configManager.getConfig(parser)
        PKUserRegistration.userID = configManager.userID
        PKUserRegistration.otp = configManager.otp

    @property
    def userID(self):
        return self._userID

    @userID.setter
    def userID(self, newuserID):
        self._userID = newuserID

    @property
    def otp(self):
        return self._otp
    
    @otp.setter
    def otp(self, newotp):
        self._otp = newotp

    @classmethod
    def validateToken(self):
        try:
            if "RUNNER" in os.environ.keys():
                return True, ValidationResult.Success
            PKPikey.removeSavedFile(f"{PKUserRegistration.userID}")
            resp = Utility.tools.tryFetchFromServer(cache_file=f"{PKUserRegistration.userID}.pdf",directory="results/Data",hideOutput=True, branchName="SubData")
            if resp is None or resp.status_code != 200:
                return False, ValidationResult.BadUserID
            with open(os.path.join(Archiver.get_user_data_dir(),f"{PKUserRegistration.userID}.pdf"),"wb",) as f:
                f.write(resp.content)
            if not PKPikey.openFile(f"{PKUserRegistration.userID}.pdf",PKUserRegistration.otp):
                return False, ValidationResult.BadOTP
            return True, ValidationResult.Success
        except: # pragma: no cover
            if "RUNNER" in os.environ.keys():
                return True, ValidationResult.Success
            return False, ValidationResult.BadOTP

    @classmethod
    def login(self, trialCount=0):
        try:
            if "RUNNER" in os.environ.keys():
                return ValidationResult.Success
        except: # pragma: no cover
            return ValidationResult.BadUserID
        Utility.tools.clearScreen(userArgs=None, clearAlways=True, forceTop=True)
        configManager = tools()
        configManager.getConfig(parser)
        if configManager.userID is not None and len(configManager.userID) > 0:
            PKUserRegistration.populateSavedUserCreds()
            if PKUserRegistration.validateToken()[0]:
                return ValidationResult.Success
        if trialCount >= 1:
            return PKUserRegistration.presentTrialOptions()

        OutputControls().printOutput(f"[+] {colorText.GREEN}PKScreener will always remain free and open source!{colorText.END}\n[+] {colorText.FAIL}PKScreener does offer certain premium/paid features!{colorText.END}\n[+] {colorText.GREEN}Please use {colorText.END}{colorText.WARN}@nse_pkscreener_bot{colorText.END}{colorText.GREEN} in telegram app on \n    your mobile phone to request your {colorText.END}{colorText.WARN}userID{colorText.END}{colorText.GREEN} and {colorText.END}{colorText.WARN}OTP{colorText.END}{colorText.GREEN} to login:\n{colorText.END}")
        username = None
        if configManager.userID is not None and len(configManager.userID) >= 1:
            username = input(f"[+] Your UserID from telegram: (Default: {colorText.GREEN}{configManager.userID}{colorText.END}): ") or configManager.userID
        else:
            username = input(f"[+] {colorText.GREEN}Your UserID from telegram: {colorText.END}")
        if username is None or len(username) <= 0:
            OutputControls().printOutput(f"{colorText.WARN}[+] We urge you to register on telegram (/OTP on @nse_pkscreener_bot) and then login to use PKScreener!{colorText.END}\n")
            OutputControls().printOutput(f"{colorText.FAIL}[+] Invalid userID!{colorText.END}\n{colorText.WARN}[+] Maybe try entering the {colorText.END}{colorText.GREEN}UserID{colorText.END}{colorText.WARN} instead of username?{colorText.END}\n[+] {colorText.WARN}If you have purchased a subscription and are still not able to login, please reach out to {colorText.END}{colorText.GREEN}@ItsOnlyPK{colorText.END} {colorText.WARN}on Telegram!{colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
            sleep(5)
            return PKUserRegistration.presentTrialOptions()
        otp = input(f"[+] {colorText.WARN}OTP received on telegram from {colorText.END}{colorText.GREEN}@nse_pkscreener_bot (Use command /otp to get OTP): {colorText.END}") or configManager.otp
        invalidOTP = False
        try:
            otpTest = int(otp)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            invalidOTP = True
            pass
        if otp is None or len(str(otp)) <= 0:
            OutputControls().printOutput(f"{colorText.WARN}[+] We urge you to register on telegram (/OTP on @nse_pkscreener_bot) and then login to use PKScreener!{colorText.END}\n")
            OutputControls().printOutput(f"{colorText.FAIL}[+] Invalid userID/OTP!{colorText.END}\n{colorText.WARN}[+] Maybe try entering the {colorText.END}{colorText.GREEN}UserID{colorText.END}{colorText.WARN} instead of username?{colorText.END}\n[+] {colorText.WARN}If you have purchased a subscription and are still not able to login, please reach out to {colorText.END}{colorText.GREEN}@ItsOnlyPK{colorText.END} {colorText.WARN}on Telegram!{colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
            sleep(5)
            return PKUserRegistration.presentTrialOptions()
    
        if len(str(otp)) <= 5 or invalidOTP:
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
            if userUsedUserID:
                OutputControls().printOutput(f"{colorText.GREEN}[+] Please wait!{colorText.END}\n[+] {colorText.WARN}Validating the OTP. You can press Ctrl+C to exit!{colorText.END}")
                PKUserRegistration.userID = usernameInt
                PKUserRegistration.otp = otp

                validationResult,validationReason = PKUserRegistration.validateToken()
                if not validationResult and validationReason == ValidationResult.BadUserID:
                    OutputControls().printOutput(f"{colorText.FAIL}[+] Invalid userID!{colorText.END}\n{colorText.WARN}[+] Maybe try entering the {colorText.END}{colorText.GREEN}UserID{colorText.END}{colorText.WARN} instead of username?{colorText.END}\n[+] {colorText.WARN}If you have purchased a subscription and are still not able to login, please reach out to {colorText.END}{colorText.GREEN}@ItsOnlyPK{colorText.END} {colorText.WARN}on Telegram!{colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
                    sleep(5)
                    return PKUserRegistration.presentTrialOptions()
                if not validationResult and validationReason == ValidationResult.BadOTP:
                    OutputControls().printOutput(f"{colorText.FAIL}[+] Invalid OTP!{colorText.END}\n[+] {colorText.GREEN}If you have purchased a subscription and are still not able to login, please reach out to @ItsOnlyPK on Telegram!{colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
                    sleep(5)
                    return PKUserRegistration.login(trialCount=trialCount+1)
                if validationResult and validationReason == ValidationResult.Success:
                    # Remember the userID for future login
                    configManager.userID = str(PKUserRegistration.userID)
                    configManager.otp = str(PKUserRegistration.otp)
                    configManager.setConfig(parser,default=True,showFileCreatedText=False)
                    Utility.tools.clearScreen(userArgs=None, clearAlways=True, forceTop=True)
                    return validationReason
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e: # pragma: n`o cover
            default_logger().debug(e, exc_info=True)
            pass
        OutputControls().printOutput(f"{colorText.WARN}[+] Invalid userID or OTP!{colorText.END}\n{colorText.GREEN}[+] May be try entering the {'UserID instead of username?' if userUsedUserID else 'Username instead of userID?'} {colorText.END}\n[+] {colorText.FAIL}Please try again or press Ctrl+C to exit!{colorText.END}")
        sleep(3)
        return PKUserRegistration.login(trialCount=trialCount+1)

    @classmethod
    def presentTrialOptions(self):
        m = menus()
        m.renderUserType()
        userTypeOption = input(colorText.FAIL + "  [+] Select option: ") or "1"
        if str(userTypeOption).upper() in ["1"]:
            return PKUserRegistration.login(trialCount=0)
        elif str(userTypeOption).upper() in ["2"]:
            return ValidationResult.Trial
        sys.exit(0)
    