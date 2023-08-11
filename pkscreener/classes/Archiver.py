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
import tempfile
import os, os.path
import pandas as pd
def saveData(data, fileName):
    if not len(data) > 0 or fileName == '' or fileName is None:
        return
    dirPath = os.path.join(tempfile.gettempdir(),'pkscreener')
    filePath = os.path.join(dirPath,fileName)
    try:
        safe_open_w(filePath)
        data.to_pickle(filePath)
    except Exception as e:
        # print(e)
        pass

def readData(fileName):
    if fileName == '' or fileName is None:
        return
    dirPath = os.path.join(tempfile.gettempdir(),'pkscreener')
    filePath = os.path.join(dirPath,fileName)
    unpickled_df = None
    try:
        safe_open_w(filePath)
        unpickled_df = pd.read_pickle(filePath)
    except Exception as e:
        # print(e)
        pass
    return unpickled_df

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # return open(path, 'wb')