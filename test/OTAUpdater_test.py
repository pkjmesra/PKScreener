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
from unittest.mock import patch
from time import sleep
import pytest
import subprocess
from PKDevTools.classes.ColorText import colorText

from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes import VERSION

def getPlatformSpecificDetails(jsonDict):
    url = ""
    platName = ""
    platforms = {0: "Darwin", 1: "Windows", 2: "Linux"}
    platformNames = {"Linux": "Linux", "Windows": "Windows", "Darwin": "Mac"}
    for key in platforms.keys():
        if platforms[key] in platform.system():
            url = jsonDict["assets"][key]["browser_download_url"]
            platName = platformNames[platforms[key]]
            break
    if url == "":
        url = jsonDict["assets"][0]["browser_download_url"]
        platName = platformNames[platforms[0]]
    return url, platName

# Positive test case: Test checkForUpdate function with skipDownload = True
def test_checkForUpdate_skipDownload():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "2.0.0",
            "assets": [
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.run",
                    "size": 1024*1024*100,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli.exe",
                    "size": 1024*1024*200,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.bin",
                    "size": 1024*1024*300,
                },
            ],
        }
        
        with patch(
            "pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew"
        ) as mock_showWhatsNew:
            with patch("builtins.input", return_value="n"):
                url, platName = getPlatformSpecificDetails(
                    mock_get.return_value.json.return_value
                )
                with patch(
                    f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}"
                ) as mock_updateForPlatform:
                    OTAUpdater.checkForUpdate(VERSION, skipDownload=True)
                    mock_showWhatsNew.assert_not_called
                    assert not mock_updateForPlatform.called
                    
# Positive test case: Test updateForWindows function
def test_updateForWindows():
    url = "https://example.com/update.exe"
    with patch("subprocess.Popen") as mock_popen:
        with pytest.raises((SystemExit)):
            OTAUpdater.updateForWindows(url)
            mock_popen.assert_called_with("start updater.bat", shell=True)
    os.remove("updater.bat")


# Positive test case: Test updateForLinux function
def test_updateForLinux():
    url = "https://example.com/update.bin"
    with patch("subprocess.Popen") as mock_popen:
        with pytest.raises((SystemExit)):
            OTAUpdater.updateForLinux(url)
            mock_popen.assert_called_with("bash updater.sh", shell=True)
    os.remove("updater.sh")


# Positive test case: Test updateForMac function
def test_updateForMac():
    url = "https://example.com/update.run"
    with patch("subprocess.Popen") as mock_popen:
        with pytest.raises((SystemExit)):
            OTAUpdater.updateForMac(url)
            mock_popen.assert_called_with("bash updater.sh", shell=True)
    os.remove("updater.sh")


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
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.run",
                    "size": 1024*1024*300,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli.exe",
                    "size": 1024*1024*100,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.bin",
                    "size": 1024*1024*200,
                },
            ],
        }
        url, platName = getPlatformSpecificDetails(
            mock_get.return_value.json.return_value
        )
        from PKDevTools.classes import System
        patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
        with patch("builtins.input", return_value="y"):
            with patch(
                f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}"
            ) as mock_updateForPlatform:
                OTAUpdater.checkForUpdate(VERSION)
                mock_updateForPlatform.assert_called_with(url)


# Positive test case: Test checkForUpdate function with prod_update = False
def test_checkForUpdate_not_prod_update():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "1.0.0",
            "assets": [
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.run",
                    "size": 1024*1024*300,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli.exe",
                    "size": 1024*1024*100,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.bin",
                    "size": 1024*1024*200,
                },
            ],
        }
        url, platName = getPlatformSpecificDetails(
            mock_get.return_value.json.return_value
        )
        from PKDevTools.classes import System
        patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
        with patch("builtins.input", return_value="y"):
            with patch(
                f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}"
            ) as mock_updateForPlatform:
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
                    {
                        "browser_download_url": "https://example.com/pkscreenercli_arm64.run",
                        "size": 1024*1024*300,
                    },
                    {
                        "browser_download_url": "https://example.com/pkscreenercli.exe",
                        "size": 1024*1024*100,
                    },
                    {
                        "browser_download_url": "https://example.com/pkscreenercli_arm64.bin",
                        "size": 1024*1024*200,
                    },
                ],
            }
            url, platName = getPlatformSpecificDetails(
                mock_get.return_value.json.return_value
            )
            from PKDevTools.classes import System
            patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
            with patch("builtins.input", return_value="y"):
                with patch(
                    f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}"
                ) as mock_updateForPlatform:
                    with patch("builtins.print") as mock_print:
                        OTAUpdater.checkForUpdate(VERSION)
                        assert not mock_updateForPlatform.called
                        mock_print.assert_called_with(
                            colorText.FAIL
                            + "  [+] Failure while checking update!"
                            + colorText.END,
                            sep=' ', end='\n', flush=False
                        )


# Positive test case: Test checkForUpdate function with no update available
def test_checkForUpdate_no_update():
    VERSION = "1.0.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "tag_name": "1.0.0.0",
            "assets": [
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.run",
                    "size": 300,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli.exe",
                    "size": 100,
                },
                {
                    "browser_download_url": "https://example.com/pkscreenercli_arm64.bin",
                    "size": 200,
                },
            ],
        }
        url, platName = getPlatformSpecificDetails(
            mock_get.return_value.json.return_value
        )
        from PKDevTools.classes import System
        patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
        with patch(
            "pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew"
        ) as mock_showWhatsNew:
            with patch(
                f"pkscreener.classes.OtaUpdater.OTAUpdater.updateFor{platName}"
            ) as mock_updateForPlatform:
                OTAUpdater.checkForUpdate(VERSION)
                assert not mock_showWhatsNew.called
                assert not mock_updateForPlatform.called


# Negative test case: Test checkForUpdate function with "Not Found" response
def test_checkForUpdate_not_found():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.return_value.json.return_value = {"message": "Not Found"}
        with patch(
            "pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew"
        ) as mock_showWhatsNew:
            OTAUpdater.checkForUpdate(VERSION)
            assert not mock_showWhatsNew.called


# Negative test case: Test checkForUpdate function with exception and url not None
def test_checkForUpdate_exception_url_not_none():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.side_effect = Exception("Error")
        OTAUpdater.checkForUpdate.url = "https://example.com/update.exe"
        with patch(
            "pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew"
        ) as mock_showWhatsNew:
            OTAUpdater.checkForUpdate(VERSION)
            assert not mock_showWhatsNew.called


# Negative test case: Test checkForUpdate function with exception and url None
def test_checkForUpdate_exception_url_none():
    VERSION = "1.0.0"
    with patch("requests_cache.CachedSession.get") as mock_get:
        mock_get.side_effect = Exception("Error")
        OTAUpdater.checkForUpdate.url = None
        with patch(
            "pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew"
        ) as mock_showWhatsNew:
            OTAUpdater.checkForUpdate(VERSION)
            assert not mock_showWhatsNew.called


# def test_get_latest_release_info():
#     resp, size = OTAUpdater.get_latest_release_info()
#     assert resp is not None
#     assert size > 0
#     assert OTAUpdater.checkForUpdate.url is not None

def test_get_latest_release_info(mocker):
    # Mock the response from the fetchURL function
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "assets": [
            {"browser_download_url": "https://example.com/pkscreenercli_arm64.run", "size": 1048576},
            {"browser_download_url": "https://example.com/pkscreenercli.exe", "size": 2097152},
            {"browser_download_url": "https://example.com/pkscreenercli_arm64.bin", "size": 3145728},
        ]
    }
    from PKDevTools.classes import System
    mocker.patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
    mocker.patch.object(OTAUpdater.fetcher, "fetchURL", return_value=mock_resp)

    # Mock the platform.system() function
    mocker.patch.object(platform, "system", return_value="Windows")

    # Call the function under test
    resp, size = OTAUpdater.get_latest_release_info()

    # Assert the expected values
    assert resp == mock_resp
    assert size == 2

def test_get_latest_release_info_linux(mocker):
    # Mock the response from the fetchURL function
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "assets": [
            {"browser_download_url": "https://example.com/pkscreenercli_arm64.run", "size": 1048576},
            {"browser_download_url": "https://example.com/pkscreenercli.exe", "size": 2097152},
            {"browser_download_url": "https://example.com/pkscreenercli_arm64.bin", "size": 3145728},
        ],
        "tag_name": ".".join(VERSION.split(".")[:-1]) + "." +str(int(VERSION.split(".")[-1]) +1)
    }
    from PKDevTools.classes import System
    mocker.patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
    mocker.patch.object(OTAUpdater.fetcher, "fetchURL", return_value=mock_resp)

    # Mock the platform.system() function
    mocker.patch.object(platform, "system", return_value="Linux")

    # Call the function under test
    resp, size = OTAUpdater.get_latest_release_info()

    # Assert the expected values
    assert resp == mock_resp
    assert size >= 0
    with patch("pkscreener.classes.OtaUpdater.OTAUpdater.showWhatsNew") as mock_showWhatsNew:
        with patch("pkscreener.classes.OtaUpdater.OTAUpdater.updateForLinux"):
            patch("builtins.input", return_value="y")
            OTAUpdater.checkForUpdate(skipDownload=False)
            assert mock_showWhatsNew.called
            mock_resp.json.return_value["tag_name"] = ".".join(VERSION.split(".")[:-2]) + "." +str(int(VERSION.split(".")[-2]) +1) + "." +str(int(VERSION.split(".")[-1]) +1)
            OTAUpdater.checkForUpdate(skipDownload=False)
            assert mock_showWhatsNew.called
            mock_resp.json.return_value["tag_name"] = ".".join(VERSION.split(".")[:-1]) + "." +str(int(VERSION.split(".")[-1]) +1) 
            OTAUpdater.checkForUpdate(VERSION=".".join(VERSION.split(".")[:-1]),skipDownload=False)
            assert mock_showWhatsNew.called

def test_checkForUpdate_prod_update_1(mocker):
    # Mock the response from get_latest_release_info
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "tag_name": "1.2.0.0",
        "message": "Something interesting"
    }
    mocker.patch.object(OTAUpdater, "get_latest_release_info", return_value=(mock_resp, 1024))
    mocker.patch.object(OTAUpdater, "showWhatsNew", return_value="Some exciting new features!")
    # Mock the platform.system() function
    mocker.patch.object(platform, "system", return_value="Windows")

    # Mock the input() function
    patch("builtins.input", return_value="y")

    # Mock the updateForWindows function
    mocker.patch.object(OTAUpdater, "updateForWindows")

    # with pytest.raises(Exception):
    # Call the function under test
    result = OTAUpdater.checkForUpdate(VERSION="1.1.0.0")
    # Assert the expected behavior
    assert result is None
    OTAUpdater.updateForWindows.assert_called_once_with(OTAUpdater.checkForUpdate.url)

def test_checkForUpdate_prod_update_2(mocker):
    # Mock the response from get_latest_release_info
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "tag_name": "1.2.0.0",
        "assets": [
            {"browser_download_url": "https://example.com/pkscreenercli_arm64.run", "size": 1048576},
            {"browser_download_url": "https://example.com/pkscreenercli.exe", "size": 2097152},
            {"browser_download_url": "https://example.com/pkscreenercli_arm64.bin", "size": 3145728},
        ],
        "message": "Something interesting"
    }
    from PKDevTools.classes import System
    mocker.patch.object(System.PKSystem,"get_platform", return_value=("","","","","arm64"))
    mocker.patch.object(OTAUpdater.fetcher, "fetchURL", return_value=mock_resp)
    mocker.patch.object(OTAUpdater, "showWhatsNew", return_value="Showing Mocked What's new!")
    # Mock the platform.system() function
    mocker.patch.object(platform, "system", return_value="Windows")
    # Mock the input() function
    # Mock the updateForWindows function
    mock_popen = mocker.patch.object(subprocess, "Popen")
    with patch("builtins.input", return_value="Y"):
        with pytest.raises(SystemExit):
            # Call the function under test
            result = OTAUpdater.checkForUpdate(VERSION="1.1.0.0")
            # Assert the expected behavior
            assert result is None
            sleep(2)
            mock_popen.assert_called_once_with("start updater.bat",shell=True)

        with pytest.raises(SystemExit):
            mocker.patch.object(platform, "system", return_value="Darwin")
            OTAUpdater.checkForUpdate(VERSION="1.1.0.0")
            mock_popen.assert_called_with("bash updater.sh",shell=True)
            
        with pytest.raises(SystemExit):
            mocker.patch.object(platform, "system", return_value="Linux")
            OTAUpdater.checkForUpdate(VERSION="1.1.0.0")
            mock_popen.assert_called_with("bash updater.sh",shell=True)

def test_checkForUpdate_no_update_1(mocker):
    # Mock the response from get_latest_release_info
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "tag_name": "1.1.0.0"
    }
    mocker.patch.object(OTAUpdater, "get_latest_release_info", return_value=(mock_resp, 1024))

    # Mock the platform.system() function
    mocker.patch.object(platform, "system", return_value="Windows")
    mock_updateForWindows = mocker.patch.object(OTAUpdater, "updateForWindows")
    # Call the function under test
    result = OTAUpdater.checkForUpdate(VERSION="1.1.0.0")

    # Assert the expected behavior
    assert result is None
    assert mock_updateForWindows.call_count == 0

def test_checkForUpdate_dev_mode(mocker):
    # Mock the response from get_latest_release_info
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "tag_name": "1.2.0.0"
    }
    mocker.patch.object(OTAUpdater, "get_latest_release_info", return_value=(mock_resp, 1024))

    # Mock the platform.system() function
    mocker.patch.object(platform, "system", return_value="Windows")
    mock_updateForWindows = mocker.patch.object(OTAUpdater, "updateForWindows")

    # Call the function under test
    result = OTAUpdater.checkForUpdate(VERSION="1.2.0.1")

    # Assert the expected behavior
    assert result == OTAUpdater.developmentVersion
    assert mock_updateForWindows.call_count == 0