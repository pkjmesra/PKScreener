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
import sys
import os
from pkscreener.classes.MenuOptions import menu, menus
from pkscreener.classes.PKDemoHandler import PKDemoHandler
from pkscreener.classes.PKUserRegistration import PKUserRegistration, ValidationResult
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.UserSubscriptions import PKUserSusbscriptions, PKSubscriptionModel

class PKPremiumHandler:

    @classmethod
    def hasPremium(self,mnu:menu):
        findingPremium = True
        consideredMenu = mnu
        isPremium = consideredMenu.isPremium #False
        # while findingPremium:
        #     findingPremium = not consideredMenu.isPremium
        #     if findingPremium:
        #         if consideredMenu.parent is not None:
        #             consideredMenu = consideredMenu.parent
        #         else:
        #             findingPremium = False
        #     else:
        #         isPremium = True
        return (PKPremiumHandler.showPremiumDemoOptions(mnu) == ValidationResult.Success) or ("RUNNER" in os.environ.keys()) if isPremium else (not isPremium)
    
    @classmethod
    def showPremiumDemoOptions(self,mnu):
        from pkscreener.classes import Utility
        result, reason = PKUserRegistration.validateToken()
        Utility.tools.clearScreen(forceTop=True)
        if result and reason == ValidationResult.Success:
            return reason
        elif not result and reason == ValidationResult.BadOTP:
            return PKUserRegistration.login(trialCount=1)
        else:
            OutputControls().printOutput(f"[+] {colorText.GREEN}{mnu.menuText}{colorText.END}\n[+] {colorText.WARN}This is a premium/paid feature.{colorText.END}\n[+] {colorText.WARN}You do not seem to have a paid subscription to PKScreener or you are not logged-in. Please login!!{colorText.END}\n[+] {colorText.GREEN}If you would like to subscribe, please pay UPI: PKScreener@APL{colorText.END}\n[+] {colorText.GREEN}Or, Use GitHub sponsor link to sponsor: https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra{colorText.END}\n[+] {colorText.WARN}Or, Drop a message to {colorText.END}{colorText.GREEN}@ItsOnlyPK{colorText.END}{colorText.WARN} on telegram{colorText.END}\n[+] {colorText.WARN}Follow instructions in the response message to{colorText.END} {colorText.GREEN}/OTP on @nse_pkscreener_bot on telegram{colorText.END} {colorText.WARN}for subscription details!{colorText.END}")
            m = menus()
            m.renderUserDemoMenu()
            userDemoOption = input(colorText.FAIL + "  [+] Select option: ") or "1"
            if str(userDemoOption).upper() in ["1"]:
                PKDemoHandler.demoForMenu(mnu)
                input("\n\nPress any key to exit ...")
            elif str(userDemoOption).upper() in ["3"]:
                return PKUserRegistration.login()
            elif str(userDemoOption).upper() in ["2"]:
                # Show instructions to subscribe
                subscriptionModelNames = f"\n\n[+] {colorText.GREEN}Following basic and premium subscription models are available. {colorText.END}\n[+] {colorText.GREEN}Premium subscription allows for unlimited premium scans:{colorText.END}\n"
                for name,value in PKUserSusbscriptions().subscriptionKeyValuePairs.items():
                    if name == PKSubscriptionModel.No_Subscription.name:
                        subscriptionModelNames = f"{subscriptionModelNames}\n[+]{colorText.WARN} {name} : ₹ {value} (Only Basic Scans are free){colorText.END}\n"
                    else:
                        subscriptionModelNames = f"{subscriptionModelNames}\n[+]{colorText.GREEN} {name.ljust(15)} : ₹ {value}{colorText.END}\n"
                subscriptionModelNames = f"{subscriptionModelNames}\n[+] {colorText.WARN}Please pay to subscribe:{colorText.END}\n[+] {colorText.GREEN}1. Using UPI(India) to {colorText.END}{colorText.FAIL}PKScreener@APL{colorText.END} or\n[+] {colorText.GREEN}2. Proudly sponsor: https://github.com/sponsors/pkjmesra?frequency=recurring&sponsor=pkjmesra\n{colorText.END}[+] {colorText.WARN}Please drop a message to @ItsOnlyPK on Telegram after paying to enable subscription!{colorText.END}\n\n"
                OutputControls().printOutput(subscriptionModelNames)
                input("\n\nPress any key to exit and pay...")
            sys.exit(0)
        return False
