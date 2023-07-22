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