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
import os

from pkscreener.classes.PKPremiumHandler import PKPremiumHandler
from pkscreener.classes.PKUserRegistration import PKUserRegistration, ValidationResult
from pkscreener.classes.PKDemoHandler import PKDemoHandler
from PKDevTools.classes.OutputControls import OutputControls

class TestPKPremiumHandler(unittest.TestCase):

    def setUp(self):
        """Set up mock menu objects for testing."""
        self.mock_menu = MagicMock()
        self.mock_menu.isPremium = False
        self.mock_menu.menuText = "Test Menu"

    @patch.object(PKUserRegistration, "validateToken", return_value=(True, ValidationResult.Success))
    @patch.dict(os.environ, {"RUNNER": "True"})
    def test_hasPremium_runner_mode(self, mock_validateToken):
        """Test hasPremium() with RUNNER mode enabled."""
        result = PKPremiumHandler.hasPremium(self.mock_menu)
        self.assertTrue(result, "RUNNER mode should allow premium access.")

    @patch.object(PKUserRegistration, "validateToken", return_value=(False, ValidationResult.BadOTP))
    def test_hasPremium_no_premium(self, mock_validateToken):
        """Test hasPremium() when the user does not have premium access."""
        result = PKPremiumHandler.hasPremium(self.mock_menu)
        self.assertTrue(result, "Non-premium users should pass for a non-premium menu.")

    @patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen")
    @patch.object(PKUserRegistration, "validateToken", return_value=(False, ValidationResult.BadOTP))
    @patch.object(PKUserRegistration, "login", return_value=ValidationResult.Success)
    def test_showPremiumDemoOptions_login_attempt(self, mock_login, mock_validateToken, mock_clearScreen):
        """Test showPremiumDemoOptions() when user needs to log in."""
        result = PKPremiumHandler.showPremiumDemoOptions(self.mock_menu)
        self.assertEqual(result, ValidationResult.Success, "User should log in successfully.")

    @patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen")
    @patch.object(PKUserRegistration, "validateToken", return_value=(False, ValidationResult.BadUserID))
    @patch.object(OutputControls, "printOutput")
    @patch("builtins.input", return_value="1")  # Simulate user choosing the demo option
    @patch.object(PKDemoHandler, "demoForMenu")
    @patch("sys.exit")  # Prevent exit from stopping tests
    def test_showPremiumDemoOptions_demo(self, mock_exit, mock_demo, mock_input, mock_printOutput, mock_validateToken, mock_clearScreen):
        """Test showPremiumDemoOptions() when user selects demo option."""
        PKPremiumHandler.showPremiumDemoOptions(self.mock_menu)
        mock_demo.assert_called_once()
        mock_exit.assert_called_once()

    @patch("pkscreener.classes.ConsoleUtility.PKConsoleTools.clearScreen")
    @patch.object(PKUserRegistration, "validateToken", return_value=(False, ValidationResult.BadUserID))
    @patch.object(OutputControls, "printOutput")
    @patch("builtins.input", return_value="2")  # Simulate user choosing subscription option
    @patch("sys.exit")  # Prevent exit from stopping tests
    def test_showPremiumDemoOptions_subscription(self, mock_exit, mock_input, mock_printOutput, mock_validateToken, mock_clearScreen):
        """Test showPremiumDemoOptions() when user selects subscription details."""
        PKPremiumHandler.showPremiumDemoOptions(self.mock_menu)
        mock_printOutput.assert_called()
        mock_exit.assert_called_once()
