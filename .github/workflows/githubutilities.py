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
import platform
import uuid

import requests

argParser = argparse.ArgumentParser()
required = False
argParser.add_argument("-a","--setoutput", help="set output for GITHUB_OUTPUT env variable", required=required)
argParser.add_argument("-b", "--setmultilineoutput", help="set multiline out for GITHUB_OUTPUT env variable", required=required)
argParser.add_argument("-c","--fetchurl",help="fetch given url", required=required)
argParser.add_argument("-d","--getreleaseurl", action="store_true", help="get latest release url", required=required)

argsv = argParser.parse_known_args()
args = argsv[0]

def aset_output(name, value):
    if "GITHUB_OUTPUT" in os.environ.keys():
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f'{name}={value}', file=fh)


def bset_multiline_output(name, value):
    if "GITHUB_OUTPUT" in os.environ.keys():
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            delimiter = uuid.uuid1()
            print(f'{name}<<{delimiter}', file=fh)
            print(value, file=fh)
            print(delimiter, file=fh)

# set_multiline_output("key_name", "my_multiline_string_value")
# set_output("key_name", "value")

def cfetchURL(key, url):
    resp = requests.get(url, timeout=2)
    bset_multiline_output(key,resp.json())
    return resp

def dget_latest_release_url():
    resp = cfetchURL("ReleaseResponse", "https://api.github.com/repos/pkjmesra/PKScreener/releases/latest")
    if "Windows" in platform.system():
        url = resp.json()["assets"][1]["browser_download_url"]
        aset_output("DOWNLOAD_URL",url)
    elif "Darwin" in platform.system():
        url = resp.json()["assets"][2]["browser_download_url"]
        aset_output("DOWNLOAD_URL",url)
    else:
        url = resp.json()["assets"][0]["browser_download_url"]
        aset_output("DOWNLOAD_URL",url)
    return url

if args.getreleaseurl:
    print(dget_latest_release_url())
if args.setoutput is not None:
    aset_output(args.setoutput.split(",")[0],args.setoutput.split(",")[1])
if args.setmultilineoutput is not None:
    bset_multiline_output(args.setmultilineoutput.split(",")[0],args.setmultilineoutput.split(",")[1])
if args.fetchurl is not None:
    cfetchURL(args.fetchurl.split(",")[0],args.fetchurl.split(",")[1])
