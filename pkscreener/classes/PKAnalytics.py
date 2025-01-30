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

import os
import base64
from sys import platform
import platform
import getpass
import git
import json
import io

from PKDevTools.classes.Fetcher import fetcher
from PKDevTools.classes.Utils import random_user_agent
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes import Archiver
import git.repo

class PKAnalyticsService():
    def collectMetrics(self,user=None):
        try:
            userName = self.getUserName()
            metrics = self.getApproxLocationInfo()
            dateTime = str(PKDateUtilities.currentDateTime())
            metrics["dateTime"] = dateTime
            metrics["userName"] = userName
            if "readme" in metrics.keys():
                del metrics['readme']
            self.tryCommitAnalytics(userDict=metrics,username=userName)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            pass

    def getUserName(self):
        try:
            username = os.getlogin()
            if username is None or len(username) == 0:
                username = os.environ.get('username') if platform.startswith("win") else os.environ.get("USER")
                if username is None or len(username) == 0:
                    username = os.environ.get('USERPROFILE')
                    if username is None or len(username) == 0:
                        username = os.path.expandvars("%userprofile%") if platform.startswith("win") else getpass.getuser()
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except: # pragma: no cover
            username = f"Unidentified-{platform.system()}"
            pass
        return username

    def getApproxLocationInfo(self):
        try:
            url = 'http://ipinfo.io/json'
            f = fetcher()
            response = f.fetchURL(url=url,timeout=5,headers={'user-agent': f'{random_user_agent()}'})
            data = json.loads(response.text)
        except: # pragma: no cover
            data = {"locationInfo":f"Unidentified-{platform.system()}"}
            pass
        return data
    
    def tryCommitAnalytics(self, userDict={},username="Unidentified"):
        repo_clone_url = "https://github.com/pkjmesra/PKUserAnalytics.git"
        local_repo = os.path.join(Archiver.get_user_data_dir(),"PKUserAnalytics")
        try:
            test_branch = "main"
            repo = git.Repo.clone_from(repo_clone_url, local_repo)
            repo.git.checkout(test_branch)
        except Exception as e: # pragma: no cover
            repo = git.Repo(local_repo)
            repo.git.checkout(test_branch)
            pass
        remote = git.remote.Remote(repo=repo,name="origin")
        repo.git.reset('--hard','origin/main')
        remote.pull()
        # write to file in working directory
        scanResultFilesPath = os.path.join(local_repo, f"users-{PKDateUtilities.currentDateTime().strftime('%Y-%m-%d')}.txt")
        records = {}
        existingUserRecords = [userDict]
        mode = "rb+" if os.path.exists(scanResultFilesPath) else "wb+"
        with open(scanResultFilesPath, mode) as f:
            allUsers = f.read()
            if allUsers is not None and len(allUsers) > 0:
                allUsers = base64.b64decode(allUsers).decode("utf-8").replace("'","\"")
                records = json.loads(allUsers)
                if records is None:
                    records = {}
                existingUserRecords = records.get(username)
                if existingUserRecords is not None:
                    existingUserRecords.append(userDict)
                else:
                    existingUserRecords = [userDict]
            records[username] = existingUserRecords
            encoded = base64.b64encode(bytes(str(records).replace("'","\""), "utf-8"))
            f.writelines(io.BytesIO(encoded))
        repo.index.add([scanResultFilesPath])
        repo.index.commit("[User-Analytics]")
        remote = git.remote.Remote(repo=repo,name="origin")
        remote.push()
