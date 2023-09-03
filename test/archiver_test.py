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
from unittest.mock import patch

import pandas as pd
import pytest
import pytz

from pkscreener.classes.Archiver import (cacheFile, findFile,
                                         get_last_modified_datetime, readData,
                                         resolveFilePath, safe_open_w,
                                         saveData, utc_to_ist)


# Positive test case: fileName is not None
def test_resolveFilePath_positive():
    fileName = "test_file.txt"
    expected_dirPath = os.path.join(tempfile.gettempdir(), "pkscreener")
    expected_filePath = os.path.join(expected_dirPath, fileName)
    
    result = resolveFilePath(fileName)
    
    assert result == expected_filePath

# Positive test case: fileName is None
def test_resolveFilePath_positive_fileName_none():
    fileName = None
    expected_dirPath = os.path.join(tempfile.gettempdir(), "pkscreener")
    expected_filePath = os.path.join(expected_dirPath, "")
    
    result = resolveFilePath(fileName)
    
    assert result == expected_filePath

# Positive test case: file exists
def test_get_last_modified_datetime_positive():
    f = open("test_file.txt","wb")
    f.close()
    file_path = "test_file.txt"
    expected_last_modified = utc_to_ist(datetime.utcfromtimestamp(os.path.getmtime(file_path)))
    
    result = get_last_modified_datetime(file_path)
    
    assert result == expected_last_modified

# Positive test case: convert UTC to IST
def test_utc_to_ist_positive():
    utc_dt = datetime(2023, 1, 1, 12, 0, 0)
    expected_ist_dt = pytz.utc.localize(utc_dt).replace(tzinfo=timezone.utc).astimezone(tz=pytz.timezone("Asia/Kolkata"))
    
    result = utc_to_ist(utc_dt)
    
    assert result == expected_ist_dt

# Positive test case: cache file
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_cacheFile_positive(mock_resolveFilePath):
    bData = b"test data"
    fileName = "test_file.txt"
    expected_filePath = "test_file.txt"
    f = open("test_file.txt","wb")
    f.write(bData)
    f.close()
    mock_resolveFilePath.return_value = expected_filePath
    
    cacheFile(bData, fileName)
    
    mock_resolveFilePath.assert_called_once_with(fileName)
    with open(expected_filePath, "rb") as f:
        assert f.read() == bData

# Positive test case: file exists
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_findFile_positive(mock_resolveFilePath):
    fileName = "test_file.txt"
    expected_filePath = "test_file.txt"
    expected_bData = b"test data"
    f = open("test_file.txt","wb")
    f.write(expected_bData)
    f.close()
    # expected_last_modified = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
    mock_resolveFilePath.return_value = expected_filePath
    with open(expected_filePath, "wb") as f:
        f.write(expected_bData)
    
    result_bData, result_filePath, result_last_modified = findFile(fileName)
    
    mock_resolveFilePath.assert_called_once_with(fileName)
    assert result_bData == expected_bData
    assert result_filePath == expected_filePath
    # assert result_last_modified == expected_last_modified

# Positive test case: save data
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_saveData_positive(mock_resolveFilePath):
    data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    fileName = "test_file.pkl"
    expected_filePath = "test_file.pkl"
    mock_resolveFilePath.return_value = expected_filePath
    
    saveData(data, fileName)
    
    mock_resolveFilePath.assert_called_once_with(fileName)
    result_data = pd.read_pickle(expected_filePath)
    assert result_data.equals(data)

# Positive test case: read data
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_readData_positive(mock_resolveFilePath):
    data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    fileName = "test_file.pkl"
    expected_filePath = "test_file.pkl"
    mock_resolveFilePath.return_value = expected_filePath
    data.to_pickle(expected_filePath)
    
    result_data, result_filePath, result_last_modified = readData(fileName)
    
    mock_resolveFilePath.assert_called_once_with(fileName)
    assert result_data.equals(data)
    assert result_filePath == expected_filePath
    # assert result_last_modified == datetime.utcfromtimestamp(os.path.getmtime(expected_filePath))

# Negative test case: fileName is empty
def test_resolveFilePath_negative_fileName_empty():
    fileName = ""
    
    result = resolveFilePath(fileName)
    
    assert result is not None

# Negative test case: file does not exist
def test_get_last_modified_datetime_negative():
    file_path = "nonexistent_file.txt"
    
    with pytest.raises(FileNotFoundError):
        get_last_modified_datetime(file_path)

# Negative test case: convert None to IST
def test_utc_to_ist_negative():
    utc_dt = None
    
    with pytest.raises(AttributeError):
        utc_to_ist(utc_dt)

# Negative test case: cache file with invalid file path
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_cacheFile_negative(mock_resolveFilePath):
    bData = b"test data"
    fileName = "test_file.txt"
    expected_filePath = "path/to/test_file.txt"
    mock_resolveFilePath.return_value = expected_filePath
    
    with pytest.raises(FileNotFoundError):
        cacheFile(bData, fileName)

# Negative test case: file does not exist
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_findFile_negative(mock_resolveFilePath):
    fileName = "nonexistent_file.txt"
    expected_filePath = "path/to/nonexistent_file.txt"
    mock_resolveFilePath.return_value = expected_filePath
    
    result_bData, result_filePath, result_last_modified = findFile(fileName)
    
    mock_resolveFilePath.assert_called_once_with(fileName)
    assert result_bData is None
    assert result_filePath == expected_filePath
    assert result_last_modified is None

# Negative test case: save empty data
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_saveData_negative_empty_data(mock_resolveFilePath):
    data = pd.DataFrame()
    fileName = "test_file.pkl"
    mock_resolveFilePath.return_value = "path/to/test_file.pkl"
    
    saveData(data, fileName)
    
    mock_resolveFilePath.assert_not_called()

# Negative test case: read empty data
@patch("pkscreener.classes.Archiver.resolveFilePath")
def test_readData_negative_empty_data(mock_resolveFilePath):
    fileName = "test_file.pkl"
    mock_resolveFilePath.return_value = "path/to/test_file.pkl"
    
    result_data, result_filePath, result_last_modified = readData(fileName)
    
    mock_resolveFilePath.assert_called_once_with(fileName)
    assert result_data is None
    assert result_filePath == "path/to/test_file.pkl"
    assert result_last_modified is None

# Edge test case: fileName is a long string
def test_resolveFilePath_edge_long_fileName():
    fileName = "a" * 1000
    expected_dirPath = os.path.join(tempfile.gettempdir(), "pkscreener")
    expected_filePath = os.path.join(expected_dirPath, fileName)
    
    result = resolveFilePath(fileName)
    
    assert result == expected_filePath

# Edge test case: fileName is a space
def test_resolveFilePath_edge_space_fileName():
    fileName = " "
    expected_dirPath = os.path.join(tempfile.gettempdir(), "pkscreener")
    expected_filePath = os.path.join(expected_dirPath, fileName)
    
    result = resolveFilePath(fileName)
    
    assert result == expected_filePath