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
import os.path
import tempfile
from datetime import datetime, timezone

import pandas as pd
import pytz


def resolveFilePath(fileName):
    if fileName is None:
        fileName = ""
    dirPath = os.path.join(tempfile.gettempdir(), "pkscreener")
    filePath = os.path.join(dirPath, fileName)
    safe_open_w(filePath)
    return filePath


def get_last_modified_datetime(file_path):
    last_modified = datetime.utcfromtimestamp(os.path.getmtime(file_path))
    return utc_to_ist(last_modified)


def utc_to_ist(utc_dt):
    return (
        pytz.utc.localize(utc_dt)
        .replace(tzinfo=timezone.utc)
        .astimezone(tz=pytz.timezone("Asia/Kolkata"))
    )


def cacheFile(bData, fileName):
    filePath = resolveFilePath(fileName)
    with open(filePath, "wb") as f:
        f.write(bData)


def findFile(fileName):
    filePath = resolveFilePath(fileName)
    try:
        with open(filePath, "rb") as f:
            bData = f.read()
        return bData, filePath, get_last_modified_datetime(filePath)
    except Exception:
        return None, filePath, None


def saveData(data, fileName):
    if not len(data) > 0 or fileName == "" or fileName is None:
        return
    filePath = resolveFilePath(fileName)
    try:
        data.to_pickle(filePath)
    except Exception:
        # print(e)
        pass


def readData(fileName):
    if fileName == "" or fileName is None:
        return
    filePath = resolveFilePath(fileName)
    unpickled_df = None
    try:
        unpickled_df = pd.read_pickle(filePath)
        return unpickled_df, filePath, get_last_modified_datetime(filePath)
    except Exception:
        # print(e)
        pass
    return None, filePath, None


def safe_open_w(path):
    """Open "path" for writing, creating any parent directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # return open(path, 'wb')
