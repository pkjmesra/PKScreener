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
import sys
import sysconfig
import platform
import uuid
import requests

argParser = argparse.ArgumentParser()
required = False
argParser.add_argument(
    "-a",
    "--setoutput",
    help="set output for GITHUB_OUTPUT env variable",
    required=required,
)
argParser.add_argument(
    "-b",
    "--setmultilineoutput",
    help="set multiline out for GITHUB_OUTPUT env variable",
    required=required,
)
argParser.add_argument("-c", "--fetchurl", help="fetch given url", required=required)
argParser.add_argument(
    "-d",
    "--getreleaseurl",
    action="store_true",
    help="get latest release url",
    required=required,
)
argParser.add_argument(
    "-w",
    "--whatsnew",
    action="store_true",
    help="Whats new in this release",
    required=required,
)
argParser.add_argument(
    "--lastReleasedVersion",
    help="the string containing the last released version",
    required=required,
)
argsv = argParser.parse_known_args()
args = argsv[0]

args.getreleaseurl = True

def aset_output(name, value):
    if "GITHUB_OUTPUT" in os.environ.keys():
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            print(f"{name}={value}", file=fh)


def bset_multiline_output(name, value):
    if "GITHUB_OUTPUT" in os.environ.keys():
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            delimiter = uuid.uuid1()
            print(f"{name}<<{delimiter}", file=fh)
            print(value, file=fh)
            print(delimiter, file=fh)


# set_multiline_output("key_name", "my_multiline_string_value")
# set_output("key_name", "value")


def cfetchURL(key, url):
    resp = requests.get(url, timeout=2)
    bset_multiline_output(key, resp.json())
    return resp

def get_platform():
    """Return a string with current platform (system and machine architecture).

    This attempts to improve upon `sysconfig.get_platform` by fixing some
    issues when running a Python interpreter with a different architecture than
    that of the system (e.g. 32bit on 64bit system, or a multiarch build),
    which should return the machine architecture of the currently running
    interpreter rather than that of the system (which didn't seem to work
    properly). The reported machine architectures follow platform-specific
    naming conventions (e.g. "x86_64" on Linux, but "x64" on Windows).

    Example output strings for common platforms:

        darwin_(ppc|ppc64|i368|x86_64|arm64)
        linux_(i686|x86_64|armv7l|aarch64)
        windows_(x86|x64|arm32|arm64)

    """

    system = platform.system().lower()
    machine = sysconfig.get_platform()
    machineArch = sysconfig.get_platform().split("-")[-1].lower()
    useableArch = machineArch
    is_64bit = sys.maxsize > 2 ** 32

    if system == "darwin": # get machine architecture of multiarch binaries
        if any([x in machineArch for x in ("fat", "intel", "universal")]):
            machineArch = platform.machine().lower()

    elif system == "linux":  # fix running 32bit interpreter on 64bit system
        if not is_64bit and machineArch == "x86_64":
            machineArch = "i686"
        elif not is_64bit and machineArch == "aarch64":
                machineArch = "armv7l"

    elif system == "windows": # return more precise machine architecture names
        if machineArch == "amd64":
            machineArch = "x64"
        elif machineArch == "win32":
            if is_64bit:
                machineArch = platform.machine().lower()
            else:
                machineArch = "x86"

    # some more fixes based on examples in https://en.wikipedia.org/wiki/Uname
    if not is_64bit and machineArch in ("x86_64", "amd64"):
        if any([x in system for x in ("cygwin", "mingw", "msys")]):
            machineArch = "i686"
        else:
            machineArch = "i386"
    inContainer = os.environ.get("PKSCREENER_DOCKER", "").lower() in ("yes", "y", "on", "true", "1")
    sysVersion = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    sysVersion = sysVersion if not inContainer else f"{sysVersion} (Docker)"
    useableArch = "arm64" if any([x in machineArch for x in ("aarch64", "arm64", "arm")]) else "x64"
    return f"Python {sysVersion}, {system}_{machineArch}: {machine}",machine, system, machineArch, useableArch

def dget_latest_release_url():
    _,_,_,_,machineArch = get_platform()
    exe_name = f"pkscreenercli_{machineArch}.bin"
    try:
        resp = cfetchURL(
            "ReleaseResponse",
            "https://api.github.com/repos/pkjmesra/PKScreener/releases/latest",
        )
        url = ""
        
        if "Windows" in platform.system():
            exe_name = "pkscreenercli.exe"
        elif "Darwin" in platform.system():
            exe_name = f"pkscreenercli_{machineArch}.run"
        else:
            exe_name = f"pkscreenercli_{machineArch}.bin"
        FoundMatch = False
        for asset in resp.json()["assets"]:
            url = asset["browser_download_url"]
            if url.endswith(exe_name):
                aset_output("DOWNLOAD_URL", url)
                FoundMatch = True
                break
        if not FoundMatch:
            print(f"Did not find any match for {machineArch}")
            # Fallback: construct URL for the expected binary
            rel_version = resp.json().get("tag_name", "")
            url = f"https://github.com/pkjmesra/PKScreener/releases/download/{rel_version}/{exe_name}"
            aset_output("DOWNLOAD_URL", url)
        rel_version = url.split("/")[-2]
    except:
        if args.lastReleasedVersion is not None:
            rel_version = args.lastReleasedVersion
            url = f"https://github.com/pkjmesra/PKScreener/releases/download/{rel_version}/{exe_name}"
            aset_output("DOWNLOAD_URL", url)
        pass
    aset_output("LAST_RELEASE_VERSION", rel_version)
    return url

def whatsNew():
    url = "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/release.md"
    md = requests.get(url,timeout=2)
    txt = md.text
    txt = txt.split("New?")[1]
    txt = txt.split("## Older Releases")[0]
    txt = txt.replace("* ", "- ").replace("`", "").strip()
    txt = txt + "\n"
    bset_multiline_output("WHATS_NEW_IN_THIS_RELEASE",txt)
    return txt

def lastReleasedVersionFromWhatsNew():
      wNew = whatsNew()
      releaseVersion = wNew.split("[")[1].split("]")[0]
      return releaseVersion.replace("v","")

if args.getreleaseurl:
    if args.lastReleasedVersion is None or args.lastReleasedVersion == '':
        args.lastReleasedVersion = lastReleasedVersionFromWhatsNew()
    print(dget_latest_release_url())
if args.whatsnew:
    print(whatsNew())
if args.setoutput is not None:
    aset_output(args.setoutput.split(",")[0], args.setoutput.split(",")[1])
if args.setmultilineoutput is not None:
    bset_multiline_output(
        args.setmultilineoutput.split(",")[0], args.setmultilineoutput.split(",")[1]
    )
if args.fetchurl is not None:
    cfetchURL(args.fetchurl.split(",")[0], args.fetchurl.split(",")[1])
