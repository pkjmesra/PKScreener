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
import platform
import subprocess
import sys
from datetime import timedelta

from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.OutputControls import OutputControls

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes import VERSION

class OTAUpdater:
    developmentVersion = "d"
    _configManager = ConfigManager.tools()
    _tools = Fetcher.screenerStockDataFetcher(_configManager)
    configManager = _configManager
    fetcher = _tools

    # Download and replace exe through other process for Windows
    def updateForWindows(url):
        if url is None or len(url) == 0:
            return
        batFile = (
            """@echo off
color a
echo   [+] pkscreener Software Updater!
echo   [+] Downloading Software Update...
echo   [+] This may take some time as per your Internet Speed, Please Wait...
curl -o pkscreenercli.exe -L """
            + url
            + """
echo   [+] Newly downloaded file saved in %cd%
echo   [+] Software Update Completed! Run'pkscreenercli.exe' again as usual to continue..
pause
del updater.bat & exit
        """
        )
        f = open("updater.bat", "w")
        f.write(batFile)
        f.close()
        subprocess.Popen("start updater.bat", shell=True)
        sys.exit(0)

    # Download and replace bin through other process for Linux
    def updateForLinux(url):
        if url is None or len(url) == 0:
            return
        from PKDevTools.classes.System import PKSystem
        _,_,_,_,sysArch = PKSystem.get_platform()
        bashFile = (
            """#!/bin/bash
echo ""
echo "  [+] Starting PKScreener updater, Please Wait..."
sleep 3
echo "  [+] pkscreener Software Updater!"
echo "  [+] Downloading Software Update..."
echo "  [+] This may take some time as per your Internet Speed, Please Wait..."
wget -q """
            + url
            + """ -O pkscreenercli_"""
            + sysArch
            + """.bin
echo "  [+] Newly downloaded file saved in $(pwd)"
chmod +x pkscreenercli_"""
            + sysArch
            + """.bin
echo "  [+] Update Completed! Run 'pkscreenercli_"""
            + sysArch 
            + """.bin' again as usual to continue.."
rm updater.sh
        """
        )
        f = open("updater.sh", "w")
        f.write(bashFile)
        f.close()
        subprocess.Popen("bash updater.sh", shell=True)
        sys.exit(0)

        # Download and replace run through other process for Mac

    def updateForMac(url):
        if url is None or len(url) == 0:
            return
        from PKDevTools.classes.System import PKSystem
        _,_,_,_,sysArch = PKSystem.get_platform()
        bashFile = (
            """#!/bin/bash
echo ""
echo "  [+] Starting PKScreener updater, Please Wait..."
sleep 3
echo "  [+] pkscreener Software Updater!"
echo "  [+] Downloading Software Update..."
echo "  [+] This may take some time as per your Internet Speed, Please Wait..."
curl -o pkscreenercli_"""
            + sysArch
            + """.run -L """
            + url
            + """
echo "  [+] Newly downloaded file saved in $(pwd)"
chmod +x pkscreenercli_"""
            + sysArch
            + """.run
echo "  [+] Update Completed! Run 'pkscreenercli_"""
            + sysArch
            + """.run' again as usual to continue.."
rm updater.sh
        """
        )
        f = open("updater.sh", "w")
        f.write(bashFile)
        f.close()
        subprocess.Popen("bash updater.sh", shell=True)
        sys.exit(0)

    # Parse changelog from release.md
    def showWhatsNew():
        url = "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/release.md"
        md = OTAUpdater.fetcher.fetchURL(url)
        txt = md.text
        txt = txt.split("New?")[1]
        txt = txt.split("## Older Releases")[0]
        txt = txt.replace("* ", "- ").replace("`", "").strip()
        return txt + "\n"

    def get_latest_release_info():
        resp = OTAUpdater.fetcher.fetchURL(
            "https://api.github.com/repos/pkjmesra/PKScreener/releases/latest"
        )  
        size = 0
        from PKDevTools.classes.System import PKSystem
        _,_,_,_,sysArch = PKSystem.get_platform()
        if "Windows" in platform.system():
            exe_name = "pkscreenercli.exe"
        elif "Darwin" in platform.system():
            exe_name = f"pkscreenercli_{sysArch}.run"
        else:
            exe_name = f"pkscreenercli_{sysArch}.bin"
        for asset in resp.json()["assets"]:
            url = asset["browser_download_url"]
            if url.endswith(exe_name):
                OTAUpdater.checkForUpdate.url = url
                size = int(asset["size"] / (1024 * 1024))
                break
        return resp, size

    # Check for update and download if available
    def checkForUpdate(VERSION=VERSION, skipDownload=False):
        OTAUpdater.checkForUpdate.url = None
        resp = None
        updateType = "minor"
        try:
            now_components = str(VERSION).split(".")
            now_major_minor = ".".join([now_components[0], now_components[1]])
            now = float(now_major_minor)
            resp, size = OTAUpdater.get_latest_release_info()
            tag = resp.json()["tag_name"]
            version_components = tag.split(".")
            major_minor = ".".join([version_components[0], version_components[1]])
            last_release = float(major_minor)
            prod_update = False
            if last_release > now:
                updateType = "major"
                prod_update = True
            elif last_release == now and (
                len(now_components) < len(version_components)
            ):
                # Must be the weekly update over the last major.minor update
                prod_update = True
            elif last_release == now and (
                len(now_components) == len(version_components)
            ):
                if float(now_components[2]) < float(version_components[2]):
                    prod_update = True
                elif float(now_components[2]) == float(version_components[2]):
                    if float(now_components[3]) < float(version_components[3]):
                        prod_update = True
            inContainer = os.environ.get("PKSCREENER_DOCKER", "").lower() in ("yes", "y", "on", "true", "1")
            if inContainer:
                # We're running in docker container
                size = 90
            if prod_update:
                if skipDownload:
                    OutputControls().printOutput(
                        colorText.GREEN
                        + f"      [+] A {updateType} software update (v{tag} [{size} MB]) is available. Check out with the menu option U."
                        + colorText.END
                    )
                    return
                OutputControls().printOutput(
                    colorText.WARN
                    + "  [+] What's New in this Update?\n"
                    + colorText.END
                    + colorText.GREEN
                    + OTAUpdater.showWhatsNew()
                    + colorText.END
                )
                try:
                    action = input(
                            colorText.FAIL
                            + (
                                f"\n  [+] New {updateType} Software update (v%s) available. Download Now (Size: %dMB)? [Y/N]: "
                                % (str(tag), size)
                            )
                        ) or "y"
                except (EOFError, OSError): # user pressed enter
                    action = "y"
                    pass
                if action is not None and action.lower() == "y":
                    if inContainer:
                        OutputControls().printOutput(
                                colorText.WARN
                                + f"  [+] You are running in docker. Please use\n  [+]{colorText.END} {colorText.GREEN}docker pull pkjmesra/pkscreener:latest{colorText.END} {colorText.WARN}to pull the latest image, followed by\n  [+]{colorText.END} {colorText.GREEN}docker run -it pkjmesra/pkscreener:latest{colorText.END} {colorText.WARN}to run in the container.{colorText.END}"
                            )
                        from time import sleep
                        sleep(5)
                        sys.exit(0)
                    else:
                        try:
                            if "Windows" in platform.system():
                                OTAUpdater.updateForWindows(OTAUpdater.checkForUpdate.url)
                            elif "Darwin" in platform.system():
                                OTAUpdater.updateForMac(OTAUpdater.checkForUpdate.url)
                            else:
                                OTAUpdater.updateForLinux(OTAUpdater.checkForUpdate.url)
                        except KeyboardInterrupt:
                            raise KeyboardInterrupt
                        except Exception as e:  # pragma: no cover
                            default_logger().debug(e, exc_info=True)
                            OutputControls().printOutput(
                                colorText.WARN
                                + "  [+] Error occured while updating!"
                                + colorText.END
                            )
                            raise (e)
            elif not prod_update and not skipDownload:
                if tag.lower() == VERSION.lower():
                    OutputControls().printOutput(
                        colorText.GREEN
                        + (
                            "  [+] No new update available. You have the latest version (v%s) !"
                            % VERSION
                        )
                        + colorText.END
                    )
                else:
                    if float(now_components[0]) > float(version_components[0]) or \
                        float(now_components[1]) > float(version_components[1]) or \
                        float(now_components[2]) > float(version_components[2]) or \
                        float(now_components[3]) > float(version_components[3]):
                        OutputControls().printOutput(
                            colorText.FAIL
                            + (f"  [+] This version (v{VERSION}) is in Development! Thanks for trying out!")
                            + colorText.END
                        )
                        return OTAUpdater.developmentVersion
                    else:
                        OutputControls().printOutput(
                        colorText.GREEN
                        + (
                            "  [+] No new update available. You have the latest version (v%s) !"
                            % VERSION
                        )
                        + colorText.END
                    )
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            if OTAUpdater.checkForUpdate.url is not None:
                OutputControls().printOutput(e)
                OutputControls().printOutput(
                    colorText.BLUE
                    + (
                        "  [+] Download update manually from %s\n"
                        % OTAUpdater.checkForUpdate.url
                    )
                    + colorText.END
                )
            else:
                OTAUpdater.checkForUpdate.url = (
                    "  [+] No exe/bin/run file as an update available!"
                )
            if resp is not None and resp.json()["message"] == "Not Found":
                OutputControls().printOutput(
                    colorText.FAIL
                    + OTAUpdater.checkForUpdate.url
                    + colorText.END
                )
            if not skipDownload:
                OutputControls().printOutput(e)
                OutputControls().printOutput(
                    colorText.FAIL
                    + "  [+] Failure while checking update!"
                    + colorText.END,
                )
        return
