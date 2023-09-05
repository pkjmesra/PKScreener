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
# import argparse
import os
import platform
from time import sleep

# argParser = argparse.ArgumentParser()
# required = False
# argParser.add_argument("-m", "--message", help="Commit message", required=required)
# argParser.add_argument(
#     "-b", "--branch", help="Origin branch name to push to", required=required
# )
# args = argParser.parse_known_args()

def commitTempOutcomes(reportName)
    if "Windows" not in platform.system():
        return
    try:
        if len(os.environ['BACKTEST_NAME']) == 0 or len(os.environ['RUNNER']) == 0:
            return
    except Exception as e:
        return

    execOSCommand("rmdir /s /q Backtest-Reports")
    sleep(1)
    execOSCommand("mkdir Backtest-Reports")
    execOSCommand("copy 'PKScreener_*.html' 'Backtest-Reports'")
    sleep(1)
    execOSCommand("git config user.name github-actions")
    execOSCommand("git config user.email github-actions@github.com")
    execOSCommand("git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'")
    execOSCommand("git remote update")
    execOSCommand("git fetch")
    sleep(1)
    execOSCommand("git checkout -b gh-pages origin/gh-pages")
    sleep(1)
    execOSCommand("git pull")
    sleep(2)
    execOSCommand(f"git add Backtest-Reports/PKScreener_{reportName}_backtest_result_StockSorted.html --force")
    execOSCommand(f"git add Backtest-Reports/PKScreener_{reportName}_Summary_StockSorted.html --force")
    sleep(1)
    execOSCommand(f"git commit -m 'GitHub-Action-Workflow-Backtest-Reports-({reportName})'")
    execOSCommand("git push -v -u origin +gh-pages")
    sleep(3)

def execOSCommand(command):
    try:
        os.system(command)
    except Exception as e:
        pass
