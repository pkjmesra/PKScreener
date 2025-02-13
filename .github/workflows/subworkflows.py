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
import requests
import sys
import pytz
from time import sleep

from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.UserSubscriptions import PKUserSusbscriptions,PKSubscriptionModel
from PKDevTools.classes.DBManager import DBManager
from PKDevTools.classes import Archiver
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher

MORNING_ALERT_HOUR = 9
MORNING_ALERT_MINUTE = 13

argParser = argparse.ArgumentParser()
required = False

argParser.add_argument(
    "--branchname",
    help="branch name for check-in, check-out",
    required=required,
)
argParser.add_argument(
    "--resetscanners",
    action="store_true",
    help="Triggers daily scanner jobs reset",
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
    "--triggeralertscanners",
    help="Triggers alert scanner jobs for all users",
    required=required,
)
argParser.add_argument(
    "--userid",
    help="Telegram userID for a user",
    required=required,
)
argsv = argParser.parse_known_args()
args = argsv[0]

def aset_output(name, value):
    if "GITHUB_OUTPUT" in os.environ.keys():
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            print(f"{name}={value}", file=fh)
try:
    if __name__ == '__main__':
        nse = nseStockDataFetcher()
        marketStatusFromNSE = ""
        willTradeOnDate = False
        wasTradedToday = False
        today = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
        marketStatus, _ ,tradeDate = nse.capitalMarketStatus()
        try:
            from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus
            import multiprocessing
            NSEMarketStatus(multiprocessing.Manager().dict(),None).startMarketMonitor()
            sleep(10)
            marketStatusFromNSE = NSEMarketStatus({},None).status
            willTradeOnDate = PKDateUtilities.willNextTradeOnDate()
            wasTradedToday = PKDateUtilities.wasTradedOn()
        except Exception as e: # pragma: no cover
            print(e)
            pass
        aset_output("MARKET_STATUS", marketStatus)
        aset_output("MARKET_TRADED_TODAY", "1" if (today in [tradeDate] or willTradeOnDate or wasTradedToday) else "0")
except:
    marketStatus ,tradeDate = None,None
    pass

def shouldRunWorkflow():
    return (marketStatus == "Open" or marketStatusFromNSE == "Open") or (today in [tradeDate] or willTradeOnDate or wasTradedToday) or (not PKDateUtilities.isTodayHoliday()[0] and PKDateUtilities.isTradingWeekday()) or args.force

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

    def run_workflow(workflow_name, postdata, option=""):
        owner = os.popen('git ls-remote --get-url origin | cut -d/ -f4').read().replace("\n","")
        repo = os.popen('git ls-remote --get-url origin | cut -d/ -f5').read().replace(".git","").replace("\n","")
        ghp_token = ""
        # from PKDevTools.classes.Environment import PKEnvironment
        # _, _, _, ghp_token = PKEnvironment().secrets
        
        if "GITHUB_TOKEN" in os.environ.keys():
            ghp_token = os.environ["GITHUB_TOKEN"]
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_name}/dispatches"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {ghp_token}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, data=postdata, headers=headers, timeout=4)
        if resp.status_code == 204:
            print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))}: Workflow {option} {workflow_name} Triggered!")
        else:
            print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))}: [{resp.status_code}] Something went wrong while triggering {workflow_name}")
        return resp
    
    def triggerRemoteScanAlertWorkflow(scanOptions, branch):
        cmd_options = scanOptions.replace("_",":")
        if 'ALERT_TRIGGER' in os.environ.keys() and os.environ["ALERT_TRIGGER"] == 'Y':
            alertTrigger = 'Y'
        else:
            alertTrigger = 'N'
        postdata = (
                    '{"ref":"'
                    + branch
                    + '","inputs":{"user":"'
                    + f"{args.user}"
                    + '","params":"'
                    + f'{cmd_options}'
                    + f'","ref":"{branch}","alertTrigger":"'
                    + f"{alertTrigger}"
                    + '"}}'
                )
        resp = run_workflow("w8-workflow-alert-scan_generic.yml", postdata,cmd_options)
        return resp

    def triggerOneOnOneAlertScanWorkflowActions():
        branch = "main"

        # If the job got triggered before, let's wait until alert time (3 min for job setup, so effectively it will be 9:40am)
        while (PKDateUtilities.currentDateTime() < PKDateUtilities.currentDateTime(simulate=True,hour=MORNING_ALERT_HOUR,minute=MORNING_ALERT_MINUTE)):
            sleep(60) # Wait for alert time

        if "ALERT_TRIGGER" not in os.environ.keys():
            try:
                os.remove(os.path.join(os.getcwd(),".env.dev"))
            except:
                pass
            try:
                os.remove(os.path.join(os.getcwd(),f"pkscreener{os.sep}.env.dev"))
            except:
                pass
        dbManager = DBManager()
        scannerJobs = dbManager.scannerJobsWithActiveUsers()
        for scannerJob in scannerJobs:
            print(f"Launching {scannerJob.scannerId}")
            options = f'--systemlaunched -a Y -m {scannerJob.scannerId.replace("_",":")}'
            resp = triggerRemoteScanAlertWorkflow(options, branch)
            if resp.status_code == 204:
                sleep(5)
            else:
                break
        print(f"All scanner jobs launched!")

    def resetUserScannnerAlertJobs():
        dbManager = DBManager()
        dbManager.resetScannerJobs()

    def triggerSubscriptionsUpdate():
        PKUserSusbscriptions.updateSubscriptions()
        pathSpec = f"{os.path.join(Archiver.get_user_data_dir(),'*.pdf')}"
        tryCommitOutcomes(options="UpdateSubscriptions",pathSpec=pathSpec,delete=True)

    def triggerAddSubscription():
        PKUserSusbscriptions.updateSubscription(userID=args.userid,subscription=PKUserSusbscriptions.subscriptionModelFromValue(int(args.subscriptionvalue)))
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
    if args.resetscanners:
        resetUserScannnerAlertJobs()
    if args.triggeralertscanners:
        triggerOneOnOneAlertScanWorkflowActions()

    print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))}: All done!")
    sys.exit(0)
