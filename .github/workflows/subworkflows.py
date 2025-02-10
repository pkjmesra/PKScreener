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
import argparse
import os
import datetime
import sys
import pytz
from time import sleep

from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.UserSubscriptions import PKUserSusbscriptions,PKSubscriptionModel
from PKDevTools.classes import Archiver

argParser = argparse.ArgumentParser()
required = False

argParser.add_argument(
    "--branchname",
    help="branch name for check-in, check-out",
    required=required,
)
argParser.add_argument(
    "--updatesubscriptions",
    action="store_true",
    help="Triggers subscription update",
    required=required,
)
argParser.add_argument(
    "--addsubscription",
    action="store_true",
    help="Triggers subscription update for a user",
    required=required,
)
argParser.add_argument(
    "--removesubscription",
    action="store_true",
    help="Triggers subscription update for a user",
    required=required,
)
argParser.add_argument(
    "--subscriptionvalue",
    help="Subscription value for the user",
    required=required,
)
argParser.add_argument(
    "--userid",
    help="Telegram userID for a user",
    required=required,
)
argsv = argParser.parse_known_args()
args = argsv[0]

if __name__ == '__main__':
    def scanOutputDirectory(backtest=False):
        dirName = 'actions-data-scan' if not backtest else "Backtest-Reports"
        outputFolder = os.path.join(os.getcwd(),dirName)
        if not os.path.isdir(outputFolder):
            print("This must be run with actions-data-download or gh-pages branch checked-out")
            print("Creating actions-data-scan directory now...")
            os.makedirs(os.path.dirname(os.path.join(os.getcwd(),f"{dirName}{os.sep}")), exist_ok=True)
        return outputFolder

    def getFormattedChoices(options):
        selectedChoice = options.split(":")
        choices = ""
        for choice in selectedChoice:
            if len(choice) > 0 and choice != 'D':
                if len(choices) > 0:
                    choices = f"{choices}_"
                choices = f"{choices}{choice}"
        if choices.endswith("_"):
            choices = choices[:-1]
        return choices

    def scanChoices(options, backtest=False):
        choices = getFormattedChoices(options).replace("B:30","X").replace("B_30","X").replace("B","X").replace("G","X")
        return choices if not backtest else choices.replace("X","B")

    def tryCommitOutcomes(options,pathSpec=None,delete=False):
        choices = scanChoices(options)
        if delete:
            choices =f"Cleanup-{choices}"
        if pathSpec is None:
            scanResultFilesPath = f"{os.path.join(scanOutputDirectory(),choices)}_*.txt"
        else:
            scanResultFilesPath = pathSpec
            if delete:
                scanResultFilesPath = f"-A {scanResultFilesPath}"

        if args.branchname is not None:
            Committer.commitTempOutcomes(addPath=scanResultFilesPath,commitMessage=f"[Temp-Commit-{choices}]",branchName=args.branchname, showStatus=True)

    def triggerSubscriptionsUpdate():
        PKUserSusbscriptions.updateSubscriptions()
        pathSpec = f"{os.path.join(Archiver.get_user_data_dir(),'*.pdf')}"
        tryCommitOutcomes(options="UpdateSubscriptions",pathSpec=pathSpec,delete=True)

    def triggerAddSubscription():
        PKUserSusbscriptions.updateSubscription(userID=args.userid,subscription=PKSubscriptionModel.subscriptionModelFromValue(int(args.subscriptionvalue)))
        pathSpec = f"{os.path.join(Archiver.get_user_data_dir(),'*.pdf')}"
        tryCommitOutcomes(options=f"AddSubscriptionFor-{args.userid}",pathSpec=pathSpec,delete=False)
        print("Added Sub Data")

    def triggerRemoveSubscription():
        print("Removing Sub data now")
        PKUserSusbscriptions.updateSubscription(userID=args.userid,subscription=PKSubscriptionModel.No_Subscription)
        pathSpec = f"{os.path.join(Archiver.get_user_data_dir(),'*.pdf')}"
        tryCommitOutcomes(options=f"RemoveSubscriptionFor-{args.userid}",pathSpec=pathSpec,delete=True)
        print("Removed Sub Data")

    if args.updatesubscriptions:
        triggerSubscriptionsUpdate()
    if args.addsubscription:
        triggerAddSubscription()
    if args.removesubscription:
        triggerRemoveSubscription()

    print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))}: All done!")
    sys.exit(0)
