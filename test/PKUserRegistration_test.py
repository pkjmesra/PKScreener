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
import unittest
from unittest.mock import patch, MagicMock
import pytest

# Import the class to be tested
from pkscreener.classes.PKUserRegistration import PKUserRegistration, ValidationResult

class TestPKUserRegistration(unittest.TestCase):

    def setUp(self):
        """Set up mock environment and inputs for testing."""
        self.mock_config = MagicMock()
        self.mock_menu = MagicMock()
        self.mock_userID = "12345"
        self.mock_otp = "67890"
        self.mock_user_registration = PKUserRegistration()
        self.mock_user_registration.userID = self.mock_userID
        self.mock_user_registration.otp = self.mock_otp

    @patch("os.environ", {"RUNNER": "True"})
    def test_validateToken_runner_mode(self):
        """Test validateToken in RUNNER mode."""
        result, reason = PKUserRegistration.validateToken()
        self.assertTrue(result)
        self.assertEqual(reason, ValidationResult.Success)

    @patch("PKDevTools.classes.Pikey.PKPikey.removeSavedFile")
    @patch("pkscreener.classes.Utility.tools.tryFetchFromServer", return_value=MagicMock(status_code=200, content=b"PDF content"))
    @patch("PKDevTools.classes.Pikey.PKPikey.openFile", return_value=True)
    @patch("time.sleep")
    def test_validateToken_success(self,mock_sleep, mock_tryFetchFromServer, mock_openFile, mock_removeSavedFile):
        """Test validateToken when the user has a valid token."""
        result, reason = PKUserRegistration.validateToken()
        self.assertTrue(result)
        self.assertEqual(reason, ValidationResult.Success)

    @patch("PKDevTools.classes.Pikey.PKPikey.removeSavedFile")
    @patch("pkscreener.classes.Utility.tools.tryFetchFromServer", return_value=MagicMock(status_code=404))
    @patch("time.sleep")
    def test_validateToken_bad_userID(self, mock_sleep, mock_tryFetchFromServer, mock_removeSavedFile):
        """Test validateToken when user ID is invalid."""
        result, reason = PKUserRegistration.validateToken()
        self.assertFalse(result)
        self.assertEqual(reason, ValidationResult.BadUserID)

    @patch("PKDevTools.classes.Pikey.PKPikey.removeSavedFile")
    @patch("pkscreener.classes.Utility.tools.tryFetchFromServer", return_value=MagicMock(status_code=200, content=b"PDF content"))
    @patch("PKDevTools.classes.Pikey.PKPikey.openFile", return_value=False)
    @patch("time.sleep")
    def test_validateToken_bad_otp(self, mock_sleep, mock_tryFetchFromServer, mock_openFile, mock_removeSavedFile):
        """Test validateToken when OTP is invalid."""
        result, reason = PKUserRegistration.validateToken()
        self.assertFalse(result)
        self.assertEqual(reason, ValidationResult.BadOTP)

    # @patch("builtins.input", return_value="12345")  # Mock user input for username
    # @patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen")
    # @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    # @patch("time.sleep")
    # def test_login_success(self, mock_sleep, mock_printOutput, mock_clearScreen, mock_input):
    #     """Test login when the user provides a valid userID and OTP."""
    #     with patch.object(PKUserRegistration, "validateToken", return_value=(True, ValidationResult.Success)):
    #         result = PKUserRegistration.login(trialCount=0)
    #         self.assertEqual(result, ValidationResult.Success)

    @patch("builtins.input", return_value="123456")  # Mock user input for username
    @patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen")
    @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    @patch("time.sleep")
    def test_login_invalid_userID(self, mock_sleep,mock_printOutput, mock_clearScreen, mock_input):
        """Test login when the user provides an invalid userID."""
        with patch.object(PKUserRegistration, "validateToken", return_value=(False, ValidationResult.BadUserID)):
            with pytest.raises(SystemExit):
                result = PKUserRegistration.login(trialCount=0)
                self.assertEqual(result, ValidationResult.BadUserID)

    @patch("builtins.input", return_value="678907")  # Mock OTP input
    @patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen")
    @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    @patch("time.sleep")
    def test_login_invalid_otp(self,mock_sleep, mock_printOutput, mock_clearScreen, mock_input):
        """Test login when the OTP provided is invalid."""
        with patch.object(PKUserRegistration, "validateToken", return_value=(False, ValidationResult.BadOTP)):
            with pytest.raises(SystemExit):
                result = PKUserRegistration.login(trialCount=0)
                self.assertEqual(result, ValidationResult.BadOTP)

    @patch("builtins.input", return_value="2")  # Mock input for trial option selection
    @patch("sys.exit")  # Prevent exit from stopping tests
    @patch("time.sleep")
    def test_presentTrialOptions(self, mock_sleep, mock_exit, mock_input):
        """Test presentTrialOptions method."""
        result = PKUserRegistration.presentTrialOptions()
        self.assertEqual(result, ValidationResult.Trial)

