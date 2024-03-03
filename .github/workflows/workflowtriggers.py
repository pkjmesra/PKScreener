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
import datetime
import os
import sys
from time import sleep

import pandas as pd
import pytz
import requests
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.Committer import Committer
from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher

argParser = argparse.ArgumentParser()
required = False
argParser.add_argument(
    "-b",
    "--backtests",
    action="store_true",
    help="Trigger backtests if true",
    required=required,
)
argParser.add_argument(
    "--branchname",
    help="branch name for check-in, check-out",
    required=required,
)
argParser.add_argument(
    "--cleanuphistoricalscans",
    help="clean up historical scan results from github server commits",
    required=required,
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument(
    "-f",
    "--force",
    help="Force launch scan/backtests",
    required=required,
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument(
    "-i",
    "--intraday",
    action="store_true",
    help="Trigger backtests for intraday if true",
    required=required,
)
argParser.add_argument(
    "-l",
    "--local",
    help="Launch locally",
    required=required,
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument(
    "-m",
    "--misc",
    help="Miscellaneous tasks that may have to be run",
    required=required,
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument(
    "-r",
    "--report",
    action="store_true",
    help="Generate backtest-report main page if true",
    required=required,
)
argParser.add_argument(
    "-s",
    "--scans",
    action="store_true",
    help="Trigger scans if true",
    required=required,
)
argParser.add_argument(
    "-s0",
    "--skiplistlevel0",
    help="skip list of menus for level 0 menus",
    required=required,
)
argParser.add_argument(
    "-s1",
    "--skiplistlevel1",
    help="skip list of menus for level 1 menus",
    required=required,
)
argParser.add_argument(
    "-s2",
    "--skiplistlevel2",
    help="skip list of menus for level 2 menus",
    required=required,
)
argParser.add_argument(
    "-s3",
    "--skiplistlevel3",
    help="skip list of menus for level 3 menus",
    required=required,
)
argParser.add_argument(
    "-s4",
    "--skiplistlevel4",
    help="skip list of menus for level 4 menus",
    required=required,
)
argParser.add_argument(
    "--scanDaysInPast",
    help="Number of days in the past for which scan has to be run",
    required=required,
)
argParser.add_argument(
    "-t",
    "--triggerRemotely",
    help="Launch Remote trigger",
    required=required,
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument("-u", "--user", help="Telegram user id", required=required)
argParser.add_argument(
    "--updateholidays",
    help="Force update holidays",
    required=required,
    action=argparse.BooleanOptionalAction,
)
argParser.add_argument(
    "-x",
    "--reScanForZeroSize",
    help="Re scan if the existing file size of the previous scan is zero",
    required=required,
    action=argparse.BooleanOptionalAction,
)

argsv = argParser.parse_known_args()
args = argsv[0]
originalStdOut = sys.stdout
original__stdout = sys.__stdout__

# args.force = True
# args.misc = True
# args.scans = True
# args.report = True
# args.intraday = True
# args.updateholidays = True
# args.backtests = True
# args.cleanuphistoricalscans = True
# args.local = True
# args.triggerRemotely = True
# args.scanDaysInPast = 7
# args.reScanForZeroSize = True
# args.user = "-1001785195297"
# args.skiplistlevel0 = "S,T,E,U,Z,H,Y,B,G"
# args.skiplistlevel1 = "W,N,E,M,Z,0,2,3,4,6,7,9,10,13"
# args.skiplistlevel2 = "0,22,26,27,28,29,30,31,42,M,Z"
# args.skiplistlevel3 = "0"
# args.skiplistlevel4 = "0"
# args.branchname = "actions-data-download"

from pkscreener.classes.MenuOptions import MenuRenderStyle, menus

m0 = menus()
m1 = menus()
m2 = menus()
m3 = menus()
m4 = menus()
objectDictionary = {}
nse = nseStockDataFetcher()

def aset_output(name, value):
    if "GITHUB_OUTPUT" in os.environ.keys():
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            print(f"{name}={value}", file=fh)
try:
    today = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
    marketStatus, _ ,tradeDate = nse.capitalMarketStatus()
    aset_output("MARKET_STATUS", marketStatus)
    aset_output("MARKET_TRADED_TODAY", "1" if (today == tradeDate) else "0")
except:
    marketStatus ,tradeDate = None,None
    pass

noActionableArguments = not args.report and \
                        not args.scans and \
                        not args.backtests and \
                        not args.cleanuphistoricalscans and \
                        not args.updateholidays
if args.skiplistlevel0 is None:
    args.skiplistlevel0 = ",".join(["S", "T", "E", "U", "Z", "B", "H", "Y", "G"])
if args.skiplistlevel1 is None:
    args.skiplistlevel1 = ",".join(["W,N,E,M,Z,0,1,2,3,4,5,6,7,8,9,10,11,13"])
if args.skiplistlevel2 is None:
    args.skiplistlevel2 = ",".join(["0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,42,M,Z"])
if args.skiplistlevel3 is None:
    args.skiplistlevel3 = ",".join(["0,1,2,3,4,5,6,7"])
if args.skiplistlevel4 is None:
    args.skiplistlevel4 = ",".join(["0"])

if noActionableArguments:
    # By default, just generate the report
    args.report = True
    args.skiplistlevel0 = "S,T,E,U,Z,H,Y,X,G" 
    args.skiplistlevel1 = "W,N,E,M,Z,0,2,3,4,6,7,9,10,13"
    args.skiplistlevel2 = "0,21,22,26,27,28,29,30,42,M,Z"
    args.skiplistlevel3 = "0"
    args.skiplistlevel4 = "0"

# Find the top level menus, skipping those in the provided list
cmds0 = m0.renderForMenu(
    selectedMenu=None,
    skip=args.skiplistlevel0.split(","),
    asList=True,
    renderStyle=MenuRenderStyle.STANDALONE,
)
counter = 1
# Iterate through the top level menus
for mnu0 in cmds0:
    p0 = mnu0.menuKey.upper()
    selectedMenu = m0.find(p0)
    # Find the first level menus, skipping those in the provided list
    cmds1 = m1.renderForMenu(
        selectedMenu=selectedMenu,
        skip=args.skiplistlevel1.split(","),
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    for mnu1 in cmds1:
        p1 = mnu1.menuKey.upper()
        selectedMenu = m1.find(p1)
        # Find the 2nd level menus, skipping those in the provided list
        cmds2 = m2.renderForMenu(
            selectedMenu=selectedMenu,
            skip=args.skiplistlevel2.split(","),
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        for mnu2 in cmds2:
            p2 = mnu2.menuKey.upper()
            if p2 == "0":
                continue
            if p2 in ["6", "7", "21"]:
                selectedMenu = m2.find(p2)
                # Find the 3rd level menus, skipping those in the provided list
                cmds3 = m3.renderForMenu(
                    selectedMenu=selectedMenu,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=args.skiplistlevel3.split(","),
                )
                for mnu3 in cmds3:
                    p3 = mnu3.menuKey.upper()
                    if p3 == "0":
                        continue
                    if p3 in [ "7"] and p2 not in ["21"]:
                        selectedMenu = m3.find(p3)
                        # Find the 2nd level menus, skipping those in the provided list
                        cmds4 = m4.renderForMenu(
                            selectedMenu=selectedMenu,
                            skip=args.skiplistlevel4.split(","),
                            asList=True,
                            renderStyle=MenuRenderStyle.STANDALONE,
                        )
                        for mnu4 in cmds4:
                            p4 = mnu4.menuKey.upper()
                            if p4 == "0":
                                continue
                            p_all = f"{p0}_{p1}_{p2}_{p3}_{p4}"
                            if p_all.endswith("_"):
                                p_all = p_all[:-1]
                            objectDictionary[counter] = {
                                "td2": [
                                    mnu1.menuText.strip(),
                                    mnu2.menuText.strip(),
                                    mnu3.menuText.strip(),
                                    mnu4.menuText.strip(),
                                ],
                                "td3": p_all,
                            }
                            counter += 1
                    else:
                        p_all = f"{p0}_{p1}_{p2}_{p3}"
                        if p_all.endswith("_"):
                            p_all = p_all[:-1]
                        objectDictionary[counter] = {
                            "td2": [
                                mnu1.menuText.strip(),
                                mnu2.menuText.strip(),
                                mnu3.menuText.strip(),
                            ],
                            "td3": p_all,
                        }
                        counter += 1
            else:
                p_all = f"{p0}_{p1}_{p2}"
                if p_all.endswith("_"):
                    p_all = p_all[:-1]
                objectDictionary[counter] = {
                    "td2": [mnu1.menuText.strip(), mnu2.menuText.strip()],
                    "td3": p_all,
                }
                counter += 1


def generateBacktestReportMainPage():
    generated_date = f"Auto-generated as of {PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H:%M:%S IST')}"
    HTMLHEAD_TEXT = """
    <!DOCTYPE html><html>
        <head>
            <script type='application/javascript' src='pkscreener/classes/tableSorting.js' ></script>
            <style type='text/css'>
                body, table {background-color: black; color: white;} 
                table, th, td {border: 1px solid white;}
                th {cursor: pointer; color:white; text-decoration:underline;}
                .r {color:red;font-weight:bold;}
                .br {border-color:green;border-width:medium;}
                .g {color:lightgreen;font-weight:bold;} 
                .w {color:white;font-weight:bold;}
                .y {color:yellow;}
                .bg {background-color:darkslategrey;}
                .bb {background-color:black;}
                input#searchReports { width: 220px; }
                table thead tr th { background-color: black; position: sticky; z-index: 100; top: 0; }
            </style>
        </head>
        <body>
            <span style='background-color:black; color:white;' >
            <span>1. Backtest, Summary and Insights Reports for All Nifty Stocks over the last 30-trading-sessions-periods</span><br />
            <span>2. Stock-wise report (Click on the link in the <span class='r'>'Stock-wise Report'</span> column) for a given scan strategy shows what profit/loss one would have incurred following that strategy over that given x-trading-period. The percentages are actual gains/losses.</span><br />
            <span>3. Summary report (Click on the link in the <span class='r'>'Summary Report'</span> column) shows the overall correctness of the strategy outcome for a given period and then overall for all periods combined altogether in the last row. For example, 80 percent in summary report means, the prediction under that strategy was correct 80 percent of the time.</span><br />
            <span>4. <a style="color:white;" href='Backtest-Reports/PKScreener_S_InsightsSummary_ScannerSorted.html' target='_blank'>Insights</a> (Click on the link in the <span class='r'>'Insights'</span> column) shows the summary of specific pattern, RSI value, or any other strategy within that scan type that gave the returns (for an investment of 10k) for respective periods.</span><br />
            <span>5. This report is just the summary of correctness of predictions for all scan types respectively at one place.</span><br />
            <span><b>Disclaimer: Only for learning purposes! Use at your own risk!</b></span><br />
    """
    HTMLHEAD_TEXT = f"{HTMLHEAD_TEXT}<span class='g'>{generated_date}</span><br />"
    HTMLHEAD_TEXT = HTMLHEAD_TEXT + """
            <input type="checkbox" id="chkActualNumbers" name="chkActualNumbers" value="0">
            <label for="chkActualNumbers">Sort by actual numbers (Stocks + Date combinations of results. Higher the count, better the prediction reliability)</label><br>
            <input 
                type="text" 
                id="searchReports" 
                onkeyup="searchReportsByAny()" 
                placeholder="Search for backtest reports.." 
                title="Type in a name ID">
            <table id='resultsTable' style='' >
                <thead><tr class="header">
                    <th>Srl #</th>
                    <th>Report Name</th>
                    <th>Stock-wise Report</th>
                    <th>Summary Report</th>
                    <th>Insights</th>
                    <th>1-Pd</th>
                    <th>2-Pd</th>
                    <th>3-Pd</th>
                    <th>4-Pd</th>
                    <th>5-Pd</th>
                    <th>10-Pd</th>
                    <th>15-Pd</th>
                    <th>22-Pd</th>
                    <th>30-Pd</th>
                    <th>Overall</th>
                    <th>Generated Date</th>
                    <th>Time Taken(sec)</th>
                </tr></thead>"""
    HTMLFOOTER_TEXT = """
            </table>
        </body>
    </html>
    """
    TR_OPENER = "\n            <tr id='{}' class='{}'>"
    TR_CLOSER = "            </tr>\n"
    TD_GENERAL = "\n                <td>{}</td>"
    TD_GENERAL_OPEN = "\n                {}"
    TD_LINK = "\n                <td><a style='color:white;' href='https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{}{}_{}Sorted.html' target='_blank'>{}</a></td>"

    f = open(
        os.path.join(
            os.getcwd(), f"BacktestReports{'Intraday' if args.intraday else ''}.html"
        ),
        "w",
    )
    f.write(HTMLHEAD_TEXT)
    tr_class = 'bb'
    for key in objectDictionary.keys():
        td2 = " > <br />".join(objectDictionary[key]["td2"])
        td3 = objectDictionary[key]["td3"]
        oneline_summary_file = (
            f"PKScreener_{td3}{'_i' if args.intraday else ''}_OneLine_Summary.html"
        )
        oneline_summary = "<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>"
        if os.path.isfile(f"Backtest-Reports/{oneline_summary_file}"):
            try:
                with open(f"Backtest-Reports/{oneline_summary_file}", "r") as sf:
                    oneline_summary = sf.read()
            except Exception:# pragma: no cover
                pass
        category = '_'.join(str(td3).split("_")[:2])
        f.writelines(
            [
                f"{TR_OPENER}".format(str(td3),tr_class + f' {category}'),
                f"{TD_GENERAL}".format(str(key)),
                f"{TD_GENERAL}".format(
                    f"{td2}{' (Intraday)' if args.intraday else ''}"
                ),
                f"{TD_LINK}".format(
                    td3,
                    f"{'_i' if args.intraday else ''}_backtest_result",
                    "Stock",
                    td3,
                ),
                f"{TD_LINK}".format(
                    td3, f"{'_i' if args.intraday else ''}_Summary", "Stock", td3
                ),
                f"{TD_LINK}".format(
                    td3, f"{'_i' if args.intraday else ''}_Insights", "Date", td3
                ),
                f"{TD_GENERAL_OPEN}".format(oneline_summary),
                TR_CLOSER,
            ]
        )
        tr_class = 'bg' if tr_class == 'bb' else 'bb'
    f.write(HTMLFOOTER_TEXT)
    f.close()


def run_workflow(workflow_name, postdata, option=""):
    owner, repo = "pkjmesra", "PKScreener"
    ghp_token = ""
    # from PKDevTools.classes.Telegram import get_secrets
    # _, _, _, ghp_token = get_secrets()
    
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
        print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))}: Something went wrong while triggering {workflow_name}")
    return resp

def cleanuphistoricalscans(scanDaysInPast=270):
    removedFileCount = 0
    options = "X:"
    for key in objectDictionary.keys():
        scanOptions = f'{objectDictionary[key]["td3"]}_D_D_D'
        branch = "actions-data-download"
        if args.branchname is None:
            args.branchname = branch
        scanOptions = objectDictionary[key]["td3"]
        options = f'{scanOptions.replace("_",":").replace("B:","X:")}:D:D:D'.replace("::",":")
        daysInPast = scanDaysInPast
        while daysInPast >=251:
            exists, fileSize, fileName = scanResultExists(options,daysInPast,True)
            if exists or fileSize >=0:
                os.remove(fileName)
                Committer.execOSCommand(f"git rm {fileName}")
                removedFileCount += 1
            daysInPast -=1
    if removedFileCount > 0:
        tryCommitOutcomes(options, pathSpec=None, delete=True)

def triggerScanWorkflowActions(launchLocal=False, scanDaysInPast=0):
    # original_stdout = sys.stdout
    # original__stdout = sys.__stdout__
    commitFrequency = [21,34,55,89,144,200]
    for key in objectDictionary.keys():
        scanOptions = f'{objectDictionary[key]["td3"]}_D_D_D_D_D'
        branch = "main"
        options = f'{scanOptions.replace("_",":").replace("B:","X:")}:D:D:D'.replace("::",":")
        if launchLocal:
            # from pkscreener import pkscreenercli
            # from pkscreener.pkscreenercli import argParser as agp
            daysInPast = scanDaysInPast
            while daysInPast >=0:
                # sys.stdout = originalStdOut
                # sys.__stdout__ = original__stdout
                if not scanResultExists(options,daysInPast,args.reScanForZeroSize)[0]:
                    os.environ["RUNNER"]="LOCAL_RUN_SCANNER"
                    os.system("export RUNNER='LOCAL_RUN_SCANNER'")
                    stringArgs = f"-a Y -e -p -o {options} --backtestdaysagoc {daysInPast} --maxdisplayresults 500 -v"
                    os.system(f"python3 pkscreener/pkscreenercli.py {stringArgs}")
                    # ag = agp.parse_known_args(args=["-p","-e", "-a", "Y", "-o", options, "--backtestdaysago",str(daysInPast),"--maxdisplayresults","500","-v"])[0]
                    # pkscreenercli.args = ag
                    # pkscreenercli.pkscreenercli()
                if daysInPast in commitFrequency:
                    tryCommitOutcomes(options)
                daysInPast -=1
            tryCommitOutcomes(options)
        else:
            resp = triggerRemoteScanAlertWorkflow(scanOptions, branch)
            if resp.status_code == 204:
                sleep(5)
            else:
                break

def triggerRemoteScanAlertWorkflow(scanOptions, branch):
    cmd_options = scanOptions.replace("_",":")
    if args.user is None or len(args.user) == 0:
        args.user = ""
        postdata = (
                    '{"ref":"'
                    + branch
                    + '","inputs":{"user":"'
                    + f"{args.user}"
                    + '","params":"'
                    + f'-a Y -e -p -o {cmd_options}'
                    + '","ref":"main"}}'
                )
    else:
        postdata = (
                    '{"ref":"'
                    + branch
                    + '","inputs":{"user":"'
                    + f"{args.user}"
                    + '","params":"'
                    + f'-a Y -e -p -u {args.user} -o {cmd_options}'
                    + '","ref":"main"}}'
                )

    resp = run_workflow("w8-workflow-alert-scan_generic.yml", postdata,cmd_options)
    return resp

def triggerHistoricalScanWorkflowActions(scanDaysInPast=0):
    defaultS1 = "W,N,E,M,Z,0,2,3,4,6,7,9,10,13" if args.skiplistlevel1 is None else args.skiplistlevel1
    defaultS2 = "42,0,22,26,27,28,29,30,31,M,Z" if args.skiplistlevel2 is None else args.skiplistlevel2
    runForIndices = [12,5,8,1,11,14]
    runForOptions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,24,25]
    runForIndicesStr = ",".join(str(x) for x in runForIndices)
    runForOptionsStr = ",".join(str(x) for x in runForOptions)
    branch = "actions-data-download"
    skip1List = defaultS1.split(",")
    skip2List = defaultS2.split(",")
    runForIndices = runForIndicesStr.split(",")
    runForOptions = runForOptionsStr.split(",")
    for index in runForIndices:
        if index not in skip1List:
            for option in runForOptions:
                if option not in skip2List:
                    skip2ListStr = ",".join(skip2List)
                    skip1ListStr = ",".join(skip1List)
                    postdata = (
                                '{"ref":"'
                                + branch
                                + '","inputs":{"installtalib":"N","skipDownload":"Y","scanOptions":"'
                                + f'--scanDaysInPast {scanDaysInPast} -s2 {skip2ListStr} -s1 {skip1ListStr} -s0 S,T,E,U,Z,H,Y,B,G -s3 {str(0)} -s4 {str(0)} --branchname actions-data-download --scans --local -f","name":"X_{index}_{option}"'
                                + ',"cleanuphistoricalscans":"N"}'
                                + '}'
                                )
                    resp = run_workflow("w9-workflow-download-data.yml", postdata,f"X_{index}_{option}")
                    if resp.status_code == 204:
                        sleep(60)
                    else:
                        continue
    # Finally trigger clean up of historical results
    postdata = (
        '{"ref":"'
        + branch
        + '","inputs":{"installtalib":"N","skipDownload":"Y","scanOptions":"'
        + '--scanDaysInPast 251 -s0 S,T,E,U,Z,H,Y,B,G -s1 W,N,E,M,Z,0,2,3,4,6,7,9,10,13 -s2 0,22,26,27,28,29,30,42,M,Z -s3 0 -s4 0 --branchname actions-data-download","name":"X_Cleanup"'
        + (',"cleanuphistoricalscans":"Y"}')
        + '}'
        )
    resp = run_workflow("w9-workflow-download-data.yml", postdata, "X_Cleanup")
    
    
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
        Committer.commitTempOutcomes(addPath=scanResultFilesPath,commitMessage=f"[Temp-Commit-{choices}]",branchName=args.branchname)

def scanOutputDirectory(backtest=False):
    dirName = 'actions-data-scan' if not backtest else "Backtest-Reports"
    outputFolder = os.path.join(os.getcwd(),dirName)
    if not os.path.isdir(outputFolder):
        print("This must be run with actions-data-download or gh-pages branch checked-out")
        print("Creating actions-data-scan directory now...")
        os.makedirs(os.path.dirname(os.path.join(os.getcwd(),f"{dirName}{os.sep}")), exist_ok=True)
    return outputFolder

def scanChoices(options, backtest=False):
    choices = getFormattedChoices(options).replace("B:30","X").replace("B_30","X").replace("B","X").replace("G","X")
    return choices if not backtest else choices.replace("X","B")

def scanResultExists(options, nthDay=0,returnFalseIfSizeZero=True):
    choices = scanChoices(options)
    curr = PKDateUtilities.nthPastTradingDateStringFromFutureDate(nthDay)
    if isinstance(curr, datetime.datetime):
        today = curr.strftime("%Y-%m-%d")
    else:
        today = curr
    outputFolder = scanOutputDirectory()
    fileName = f"{outputFolder}{os.sep}{choices}_{today}.txt"
    # print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))} : Checking for {fileName}")
    fileSize = -1
    if os.path.isfile(fileName):
        if returnFalseIfSizeZero:
            fileSize = os.path.getsize(fileName)
            if fileSize <= 2:
                print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))} : Saved scan result size is 0 : {fileName}")
            else:
                # print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))} : Skipping. Latest scan result already exists : {fileName}")
                return True,fileSize,fileName
        else:
            # print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))} : Skipping. Latest scan result already exists: {fileName}")
            return True,fileSize,fileName
    print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))} : Scanning for {choices}_{today}")
    return False, fileSize,fileName

def triggerGithubPagesDeploymentAction():
    branch = "main"
    postdata = (
        '{"ref":"'
        + branch
        + '"}'
    )
    resp = run_workflow("gh-pages-deployment.yml", postdata,"gh-pages-deployment")
    if resp.status_code == 204:
        sleep(5)

def triggerBacktestWorkflowActions(launchLocal=False):
    dfs = []
    existing_df = None
    try:
        # Let's first deploy the existing branch changes, so that we do not re-run the same backtests
        # that were already updated today
        triggerGithubPagesDeploymentAction()
        dfs = pd.read_html("https://pkjmesra.github.io/PKScreener/BacktestReports.html",encoding="UTF-8", attrs = {'id': 'resultsTable'})
    except:
        pass
    if len(dfs) > 0:
        df = dfs[0]
        if len(df) > 0:
            existing_df= df
    deploymentCounter = 0
    for key in objectDictionary.keys():
        scanOptions = objectDictionary[key]["td3"]
        options = f'{scanOptions.replace("_",":").replace("B:","")}:D:D:D'.replace("::",":")
        if not shouldRunBacktests(scanOptions,existing_df):
            continue
        if launchLocal:
            from pkscreener import pkscreenercli
            from pkscreener.pkscreenercli import argParser as agp

            options = "B:30:{0}".format(options)
            ag = agp.parse_known_args(args=["-e", "-a", "Y", "-o", options, "-v"])[0]
            pkscreenercli.args = ag
            pkscreenercli.pkscreenercli()
            # sys.stdout = originalStdOut
            # sys.__stdout__ = original__stdout
            choices = f'PKScreener_{scanChoices(options, True).replace("X","B")}'
            scanResultFilesPath = f"{os.path.join(scanOutputDirectory(backtest=True),choices)}_*.html"
            if args.branchname is not None:
                Committer.commitTempOutcomes(addPath=scanResultFilesPath,commitMessage=f"[Temp-Commit] WorkflowTrigger{choices}",branchName=args.branchname)
        else:
            branch = "main"
            postdata = (
                '{"ref":"'
                + branch
                + '","inputs":{"user":"'
                + f"{args.user}"
                + '","runson":"'
                + f'{"ubuntu-20.04" if key % 2 == 0 else "windows-latest"}'
                + '","params":"'
                + f'{options}{" -i 1m" if args.intraday else ""}'
                + '","name":"'
                + f'{scanOptions}{"_i" if args.intraday else ""}'
                + '","intraday":"'
                + f'{"-i" if args.intraday else ""}'
                + '"}}'
            )
            resp = run_workflow("w13-workflow-backtest_generic.yml", postdata,options)
            if resp.status_code == 204:
                sleep(5)
            else:
                break
        deploymentCounter += 1
        if deploymentCounter >= 35:
            deploymentCounter = 0
            triggerGithubPagesDeploymentAction()

    cmt_msg = "Strategy_Report"
    branch = "gh-pages"
    postdata = (
        '{"ref":"'
        + branch
        + '","inputs":{"user":"'
        + "-1001785195297"
        + '","params":"'
        + f'-a Y -e -p -o S:S'
        + f'","ref":"{branch}"'
        + ',"postrun":"'
        + f'git config user.name github-actions && git config user.email github-actions@github.com && git pull && git commit -m {cmt_msg} && git push -v -u origin +{branch}'
        + '"}}')
    resp = run_workflow("w8-workflow-alert-scan_generic.yml", postdata,"S:")
    if launchLocal:
        sys.exit(0)

def shouldRunBacktests(backtestName="",df=None):
    shouldRun = True
    if df is not None:
        gen_date_row = df[df["Insights"] == backtestName]
        if gen_date_row is not None:
            try:
                shouldRun = not (str(gen_date_row["Generated Date"].iloc[0]) == today.replace("-","/"))
            except Exception as e: # Ptobably the given backtest has never been run yet
                print(f"Error for {backtestName}\n{e}")
                pass
    return shouldRun

def getFormattedChoices(options):
    isIntraday = args.intraday
    selectedChoice = options.split(":")
    choices = ""
    for choice in selectedChoice:
        if len(choice) > 0 and choice != 'D':
            if len(choices) > 0:
                choices = f"{choices}_"
            choices = f"{choices}{choice}"
    if choices.endswith("_"):
        choices = choices[:-1]
    choices = f"{choices}{'_i' if isIntraday else ''}"
    return choices

def updateHolidays():
    _, raw = nse.updatedHolidays()
    if raw is None or len(raw) == 0:
        return
    import json
    holidays_file = os.path.join(os.getcwd(),".github/dependencies/nse-holidays.json")
    with open(holidays_file, "w", encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False, indent=4)
    Committer.execOSCommand(f"git add {holidays_file} -f")
    Committer.commitTempOutcomes(holidays_file,"Update-Holidays","main")

def shouldRunWorkflow():
    return marketStatus == "Open" or today == tradeDate or (not PKDateUtilities.isTodayHoliday()[0] and PKDateUtilities.isTradingWeekday()) or args.force

def triggerMiscellaneousTasks():
    today_date = PKDateUtilities.currentDateTime()
    if today_date.date() == PKDateUtilities.firstTradingDateOfMonth(today_date):
        # Trigger mutual fund reports that must have been updated yesterday
        branch = "main"
        # Shares bought/sold by Mutual Funds/FIIs
        # MF/FIIs Net Ownership Increased
        scanList = ["X:12:21:1", "X:12:21:3"]
        for scanOptions in scanList:
            resp = triggerRemoteScanAlertWorkflow(scanOptions, branch)
            if resp.status_code == 204:
                sleep(5)

if args.report:
    generateBacktestReportMainPage()
if args.backtests:
    if shouldRunWorkflow():
        triggerBacktestWorkflowActions(args.local)
if args.misc:
    # Perform miscellaneous adhoc tasks that may be rule dependent
    triggerMiscellaneousTasks()
if args.scans:
    if shouldRunWorkflow():
        daysInPast = 0
        if args.scanDaysInPast is not None:
            daysInPast = int(args.scanDaysInPast)
        if args.triggerRemotely:
            triggerHistoricalScanWorkflowActions(scanDaysInPast=daysInPast)
        else:
            triggerScanWorkflowActions(args.local, scanDaysInPast=daysInPast)
if args.cleanuphistoricalscans:
    daysInPast = 270
    if args.scanDaysInPast is not None:
        daysInPast = int(args.scanDaysInPast)
    cleanuphistoricalscans(daysInPast)
if args.updateholidays:
    updateHolidays()

print(f"{datetime.datetime.now(pytz.timezone('Asia/Kolkata'))}: All done!")
sys.exit(0)
