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
from time import sleep

import requests

argParser = argparse.ArgumentParser()
required = False
argParser.add_argument("-s0","--skiplistlevel0", help="skip list of menus for level 0 menus", required=required)
argParser.add_argument("-s1","--skiplistlevel1", help="skip list of menus for level 1 menus", required=required)
argParser.add_argument("-s2","--skiplistlevel2",help="skip list of menus for level 2 menus", required=required)
argParser.add_argument("-s3","--skiplistlevel3",help="skip list of menus for level 3 menus", required=required)
argParser.add_argument("-r","--report", action="store_true", help="Generate backtest-report main page if true", required=required)
argParser.add_argument("-s","--scans", action="store_true", help="Trigger scans if true", required=required)
argParser.add_argument("-b","--backtests", action="store_true", help="Trigger backtests if true", required=required)
argParser.add_argument("-i","--intraday", action="store_true", help="Trigger backtests for intraday if true", required=required)
argParser.add_argument("-u","--user", help="Telegram user id", required=required)

argsv = argParser.parse_known_args()
args = argsv[0]

from pkscreener.classes.MenuOptions import MenuRenderStyle, menus


m0 = menus()
m1 = menus()
m2 = menus()
m3 = menus()
objectDictionary = {}

# args.report = True 
# args.intraday = True
# args.backtests = True
# args.user="-1001785195297" 
# args.skiplistlevel0 ="S,T,E,U,Z,H,Y,X"
# args.skiplistlevel1 ="W,N,E,M,Z,0,1,2,3,4,5,6,7,8,9,10,11,13" 
# args.skiplistlevel2 ="0,21,22,23,24,25,26,27,28,42,M,Z"

if args.skiplistlevel0 is None:
    args.skiplistlevel0 = ",".join(["S", "T", "E", "U", "Z", "X", "H", "Y"])
if args.skiplistlevel1 is None:
    args.skiplistlevel1 = ",".join(["W,N,E,M,Z,0,1,2,3,4,5,6,7,8,9,10,11,13"])
if args.skiplistlevel2 is None:
    args.skiplistlevel2 = ",".join(["0,21,22,23,24,25,26,27,28,42,M,Z"])
if args.skiplistlevel3 is None:
    args.skiplistlevel3 = ",".join(["0"])
if not args.report and not args.scans and not args.backtests:
    # By default, just generate the report
    args.report = True

cmds0 = m0.renderForMenu(
        selectedMenu=None,
        skip=args.skiplistlevel0.split(","),
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
counter = 1
for mnu0 in cmds0:
    p0 = mnu0.menuKey.upper()
    selectedMenu = m0.find(p0)
    cmds1 = m1.renderForMenu(
        selectedMenu=selectedMenu,
        skip=args.skiplistlevel1.split(","),
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    for mnu1 in cmds1:
        p1 = mnu1.menuKey.upper()
        selectedMenu = m1.find(p1)
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
            if p2 in ["6", "7"]:
                selectedMenu = m2.find(p2)
                cmds3 = m3.renderForMenu(
                    selectedMenu=selectedMenu,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=args.skiplistlevel3.split(","),
                )
                for mnu3 in cmds3:
                    p3 = mnu3.menuKey.upper()
                    p_all = f"{p0}_{p1}_{p2}_{p3}"
                    if p_all.endswith('_'):
                        p_all = p_all[:-1]
                    objectDictionary[counter] = {"td2":[mnu1.menuText.strip(),mnu2.menuText.strip(),mnu3.menuText.strip()],
                                                 "td3":p_all}
                    counter += 1
            else:
                p_all = f"{p0}_{p1}_{p2}"
                if p_all.endswith('_'):
                    p_all = p_all[:-1]
                objectDictionary[counter] = {"td2":[mnu1.menuText.strip(),mnu2.menuText.strip()],
                                                 "td3":p_all}
                counter += 1


def generateBacktestReportMainPage():
    HTMLHEAD_TEXT="""
    <html>
        <body>
            <span>1. Backtest and Summary Reports for All Nifty Stocks over the last 30-trading-sessions-periods</span><br />
            <span>2. Backtest report for a given scan strategy shows what profit/loss one would have incurred following that strategy over that given x-trading-period.</span><br />
            <span>3. Summary report shows the overall correctness of the strategy outcome for a given period and then overall for all periods combined altogether in the last row.</span><br />
            <span><b>Disclaimer: Only for learning purposes! Use at your own risk!</b>></span><br />
            <table border="1px">
                <tr>
                    <th>Srl #</th>
                    <th>Report Name</th>
                    <th>Stock-wise Report</th>
                    <th>Summary Report</th>
                </tr>"""
    HTMLFOOTER_TEXT = """
            </table>
        </body>
    </html>
    """
    TR_OPENER = "\n            <tr>"
    TR_CLOSER = "            </tr>\n"
    TD_GENERAL="\n                <td>{}</td>"
    TD_LINK="\n                <td><a href='https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{}{}_StockSorted.html' target='_blank'>{}</a></td>"

    f = open(os.path.join(os.getcwd(),f"BacktestReports{'Intraday' if args.intraday else ''}.html"), "w")
    f.write(HTMLHEAD_TEXT)
    for key in objectDictionary.keys():
        td2 = " > <br />".join(objectDictionary[key]["td2"])
        td3 = objectDictionary[key]["td3"]
        f.writelines([TR_OPENER,
                    f"{TD_GENERAL}".format(str(key)),
                    f"{TD_GENERAL}".format(f"{td2}{' (Intraday)' if args.intraday else ''}"),
                    f"{TD_LINK}".format(td3,f"{'_i' if args.intraday else ''}_backtest_result",td3),
                    f"{TD_LINK}".format(td3,f"{'_i' if args.intraday else ''}_Summary",td3),
                    TR_CLOSER
                    ])
    f.write(HTMLFOOTER_TEXT)
    f.close()

def run_workflow(workflow_name,postdata):
    owner, repo="pkjmesra", "PKScreener"
    ghp_token = ""
    if "GITHUB_TOKEN" in os.environ.keys():
        ghp_token = os.environ['GITHUB_TOKEN']
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_name}/dispatches"
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {ghp_token}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, data=postdata, headers=headers, timeout=4)
    if resp.status_code==204:
        print(f"Workflow {workflow_name} Triggered!")
    else:
        print(f"Something went wrong while triggering {workflow_name}")
    return resp

def triggerScanWorkflowActions():
    for key in objectDictionary.keys():
        scanOptions = objectDictionary[key]["td3"]
        branch = "main"
        if args.user is None or len(args.user) == 0:
            args.user = ""
            postdata = '{"ref":"'+branch+'","inputs":{"user":"'+f'{args.user}'+'","params":"'+f'-a Y -e -p -o {scanOptions.replace("_",":")}'+'","ref":"main"}}'
        else:
            postdata = '{"ref":"'+branch+'","inputs":{"user":"'+f'{args.user}'+'","params":"'+f'-a Y -e -p -u {args.user} -o {scanOptions.replace("_",":")}'+'","ref":"main"}}'

        resp = run_workflow("w8-workflow-alert-scan_generic.yml",postdata)
        if resp.status_code==204:
            sleep(5)
        else:
            break

def triggerBacktestWorkflowActions():
    for key in objectDictionary.keys():
        scanOptions = objectDictionary[key]["td3"]
        branch = "main"
        options = scanOptions.replace("_",":").replace("B:","")
        postdata = '{"ref":"'+branch+'","inputs":{"user":"'+f'{args.user}'+'","params":"'+f'{options}{" -i 5m" if args.intraday else ""}'+'","name":"'+f'{scanOptions}{"_i" if args.intraday else ""}'+'"}}'
        resp = run_workflow("w13-workflow-backtest_generic.yml",postdata)
        if resp.status_code==204:
            sleep(5)
        else:
            break

if args.report:
    generateBacktestReportMainPage()
if args.backtests:
    triggerBacktestWorkflowActions()
if args.scans:
    triggerScanWorkflowActions()
