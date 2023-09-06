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
import platform
from unittest.mock import patch

import pytest

from pkscreener.classes.ColorText import colorText
from pkscreener.classes.OtaUpdater import OTAUpdater


def getPlatformSpecificDetails(jsonDict):
    url = ""
    platName = ""
    platforms = {0:"Linux",1:"Windows", 2:"Darwin"}
    platformNames = {"Linux":"Linux","Windows":"Windows", "Darwin":"Mac"}
    for key in platforms.keys():
        if platforms[key] in platform.system():
            url = jsonDict["assets"][key]["browser_download_url"]
            platName = platformNames[platforms[key]]
            break
    if url == "":
        url = jsonDict["assets"][0]["browser_download_url"]
        platName = platformNames[platforms[0]]
    return url, platName

# Positive test case: Test updateForWindows function
def test_updateForWindows():
    url = "https://example.com/update.exe"
    with patch("subprocess.Popen") as mock_popen:
        with pytest.raises((SystemExit)):
            OTAUpdater.updateForWindows(url)
            mock_popen.assert_called_with("start updater.bat", shell=True)

# Positive test case: Test updateForLinux function
def test_updateForLinux():
    url = "https://example.com/update.bin"
    with patch("subprocess.Popen") as mock_popen:
        with pytest.raises((SystemExit)):
            OTAUpdater.updateForLinux(url)
            mock_popen.assert_called_with("bash updater.sh", shell=True)

# Positive test case: Test updateForMac function
def test_updateForMac():
    url = "https://example.com/update.run"
    with patch("subprocess.Popen") as mock_popen:
        with pytest.raises((SystemExit)):
            OTAUpdater.updateForMac(url)
            mock_popen.assert_called_with("bash updater.sh", shell=True)

# Positive test case: Test showWhatsNew function
def test_showWhatsNew():
    expected_output = "What's new in this update?\n"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.text = f"What's New?\n{expected_output}## Older Releases"
        output = OTAUpdater.showWhatsNew()
        assert output == expected_output

# Positive test case: Test checkForUpdate function with prod_update = True
def test_checkForUpdate_prod_update():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "2.0.0",
            "assets": [
                {"browser_download_url": "https://example.com/update3.run", "size": 300},
                {"browser_download_url": "https://example.com/update1.exe", "size": 100},
                {"browser_download_url": "https://example.com/update2.bin", "size": 200},
            ],
        }
        url, platName = getPlatformSpecificDetails(mock_get.return_value.json.return_value)
        with patch("builtins.input", return_value="y"):
            with patch(f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}") as mock_updateForPlatform:
                OTAUpdater.checkForUpdate(VERSION)
                mock_updateForPlatform.assert_called_with(url)

# Positive test case: Test checkForUpdate function with prod_update = False
def test_checkForUpdate_not_prod_update():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "1.0.0",
            "assets": [
                {"browser_download_url": "https://example.com/update3.run", "size": 300},
                {"browser_download_url": "https://example.com/update1.exe", "size": 100},
                {"browser_download_url": "https://example.com/update2.bin", "size": 200},
            ],
        }
        url, platName = getPlatformSpecificDetails(mock_get.return_value.json.return_value)
        with patch("builtins.input", return_value="y"):
            with patch(f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}") as mock_updateForPlatform:
                with pytest.raises((Exception)):
                    OTAUpdater.checkForUpdate(VERSION)
                    assert not mock_updateForPlatform.called

# Negative test case: Test checkForUpdate function with exception
def test_checkForUpdate_exception():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        with patch("requests.get") as mock_requests_get:
            mock_get.side_effect = Exception("Error")
            mock_requests_get.side_effect = Exception("Error")
            mock_get.return_value.json.return_value = {
                "tag_name": "1.0.0",
                "assets": [
                    {"browser_download_url": "https://example.com/update3.run", "size": 300},
                    {"browser_download_url": "https://example.com/update1.exe", "size": 100},
                    {"browser_download_url": "https://example.com/update2.bin", "size": 200},
                ],
            }
            url, platName = getPlatformSpecificDetails(mock_get.return_value.json.return_value)
            with patch("builtins.input", return_value="y"):
                with patch(f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}") as mock_updateForPlatform:
                    with patch("builtins.print") as mock_print:
                        OTAUpdater.checkForUpdate(VERSION)
                        assert not mock_updateForPlatform.called
                        mock_print.assert_called_with(
                            colorText.BOLD
                            + colorText.FAIL
                            + "[+] Failure while checking update!"
                            + colorText.END)

# Positive test case: Test checkForUpdate function with skipDownload = True
def test_checkForUpdate_skipDownload():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "2.0.0",
            "assets": [
                {"browser_download_url": "https://example.com/update3.run", "size": 300},
                {"browser_download_url": "https://example.com/update1.exe", "size": 100},
                {"browser_download_url": "https://example.com/update2.bin", "size": 200},
            ],
        }
        with patch("pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew") as mock_showWhatsNew:
            with patch("builtins.input", return_value="n"):
                url, platName = getPlatformSpecificDetails(mock_get.return_value.json.return_value)
                with patch(f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}") as mock_updateForPlatform:
                    OTAUpdater.checkForUpdate(VERSION, skipDownload=True)
                    assert mock_showWhatsNew.called
                    assert not mock_updateForPlatform.called

# Positive test case: Test checkForUpdate function with no update available
def test_checkForUpdate_no_update():
    VERSION = "1.0.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "1.0.0.0",
            "assets": [
                {"browser_download_url": "https://example.com/update3.run", "size": 300},
                {"browser_download_url": "https://example.com/update1.exe", "size": 100},
                {"browser_download_url": "https://example.com/update2.bin", "size": 200},
            ],
        }
        url, platName = getPlatformSpecificDetails(mock_get.return_value.json.return_value)
        with patch("pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew") as mock_showWhatsNew:
            with patch(f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}") as mock_updateForPlatform:
                OTAUpdater.checkForUpdate(VERSION)
                assert not mock_showWhatsNew.called
                assert not mock_updateForPlatform.called

# Negative test case: Test checkForUpdate function with "Not Found" response
def test_checkForUpdate_not_found():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {"message": "Not Found"}
        with patch("pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew") as mock_showWhatsNew:
            OTAUpdater.checkForUpdate(VERSION)
            assert not mock_showWhatsNew.called

# Negative test case: Test checkForUpdate function with exception and url not None
def test_checkForUpdate_exception_url_not_none():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.side_effect = Exception("Error")
        OTAUpdater.checkForUpdate.url = "https://example.com/update.exe"
        with patch("pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew") as mock_showWhatsNew:
            OTAUpdater.checkForUpdate(VERSION)
            assert not mock_showWhatsNew.called

# Negative test case: Test checkForUpdate function with exception and url None
def test_checkForUpdate_exception_url_none():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.side_effect = Exception("Error")
        OTAUpdater.checkForUpdate.url = None
        with patch("pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew") as mock_showWhatsNew:
            OTAUpdater.checkForUpdate(VERSION)
            assert not mock_showWhatsNew.called

def test_get_latest_release_info():
    resp, size = OTAUpdater.get_latest_release_info()
    assert resp is not None
    assert size > 0
    assert OTAUpdater.checkForUpdate.url is not None