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
import os
from PKDevTools.classes.Environment import PKEnvironment
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.Fetcher import screenerStockDataFetcher

configManager = ConfigManager.tools()


def run_workflow(command, user, options, workflowType="B"):
    owner = os.popen('git ls-remote --get-url origin | cut -d/ -f4').read().replace("\n","")
    repo = os.popen('git ls-remote --get-url origin | cut -d/ -f5').read().replace(".git","").replace("\n","")
    branch = "main"
    timestamp = int(PKDateUtilities.currentDateTimestamp())
    if workflowType == "B":
        workflow_name = "w13-workflow-backtest_generic.yml"
        options = f'{options.replace("B:","")}:D:D:D:D:D'.replace("::",":")
        data = (
            '{"ref":"'
            + branch
            + '","inputs":{"user":"'
            + f"{user}"
            + '","params":"'
            + f"{options}"
            + '","name":"'
            + f"{command}"
            + '"}}'
        )
    elif workflowType == "X" or workflowType == "G" or workflowType == "P":
        workflow_name = "w8-workflow-alert-scan_generic.yml"
        if user is None or len(user) == 0:
            user = ""
            data = (
                '{"ref":"'
                + branch
                + '","inputs":{"user":"'
                + f"{user}"
                + '","params":"'
                + f'-a Y -e --triggertimestamp {timestamp} -p -o {options.replace("_",":")}:D:D:D:D:D'.replace("::",":")
                + '","ref":"main"}}'
            )
        else:
            data = (
                '{"ref":"'
                + branch
                + '","inputs":{"user":"'
                + f"{user}"
                + '","params":"'
                + f'-a Y -e --triggertimestamp {timestamp} -p -u {user} -o {options.replace("_",":")}:D:D:D:D:D'.replace("::",":")
                + '","ref":"main"}}'
            )
    elif workflowType == "R": #Restart bot
        workflow_name = "w3-workflow-bot.yml"
        data = (
                '{"ref":"'
                + branch
                + '","inputs":{"branch-name":"main","cliOptions":""}}'
            )
    _, _, _, ghp_token = PKEnvironment().secrets
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_name}/dispatches"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {ghp_token}",
        "Content-Type": "application/json",
    }

    fetcher = screenerStockDataFetcher(configManager)
    resp = fetcher.postURL(url, data=data, headers=headers)
    if resp.status_code == 204:
        OutputControls().printOutput(f"Workflow {workflow_name} Triggered!")
    else:
        OutputControls().printOutput(f"Something went wrong while triggering {workflow_name}")
    return resp


# resp = run_workflow("B_12_1","-1001785195297","B:12:1")
