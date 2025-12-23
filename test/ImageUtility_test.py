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
import pandas as pd
import pytest
from PIL import Image, ImageFont, ImageDraw

from pkscreener.classes.ImageUtility import PKImageTools

import unittest
from unittest.mock import patch, MagicMock, ANY

class TestPKImageTools(unittest.TestCase):

    @patch('PIL.ImageDraw.Draw')
    @patch('PIL.Image.new')
    def test_getsize_multiline(self, mock_image_new, mock_draw):
        # Arrange
        mock_font = MagicMock()
        mock_draw.return_value.multiline_textbbox.return_value = (0, 0, 100, 50)

        # Act
        width, height = PKImageTools.getsize_multiline(mock_font, "Sample Text")

        # Assert
        self.assertEqual(width, 100)
        self.assertEqual(height, 50)
        mock_draw.assert_called()

    @patch('PIL.ImageFont.truetype')
    def test_getsize(self, mock_truetype):
        # Arrange
        mock_font = MagicMock()
        mock_font.getbbox.return_value = (0, 0, 200, 100)

        # Act
        width, height = PKImageTools.getsize(mock_font, "Sample Text")

        # Assert
        self.assertEqual(width, 100)
        self.assertEqual(height, 200)

    @patch('PIL.Image.open')
    @patch('os.path.isfile', return_value=True)
    @patch('PKDevTools.classes.Archiver.get_user_outputs_dir', return_value="/fake/path")
    @patch('pkscreener.classes.Utility.tools.tryFetchFromServer')
    @patch('PIL.ImageFont.truetype')
    @patch('PIL.ImageDraw.ImageDraw.text')
    @patch('pkscreener.classes.ImageUtility.PKImageTools.getsize_multiline', return_value=(500,500))
    def test_add_quick_watermark(self, mock_mult,mock_draw, mock_font, mock_fetch, mock_get_outputs, mock_isfile, mock_open):
        # Arrange
        source_image = Image.new("RGB", (500, 500), (255, 255, 255))
        mock_font.return_value = ImageFont.load_default()
        mock_font.return_value.getbbox.return_value = (0,0,500,500)
        mock_fetch.return_value = MagicMock(status_code=200, content=b"dummy")
        # Act
        watermarked_image = PKImageTools.addQuickWatermark(source_image, dataSrc="Test Source")

        # Assert
        self.assertIsInstance(watermarked_image, Image.Image)
        mock_font.assert_called()
        mock_open.assert_called()

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_removeAllColorStyles_string(self, mock_colorText):
        # Mock color styles
        mock_colorText.HEAD = "\033[95m"
        mock_colorText.END = "\033[0m"
        mock_colorText.BOLD = "\033[1m"

        # Test input string with color codes
        colored_string = f"{mock_colorText.HEAD}Hello{mock_colorText.END}, {mock_colorText.BOLD}World!{mock_colorText.END}"
        cleaned_string = PKImageTools.removeAllColorStyles(colored_string)

        # Ensure all color codes are removed
        self.assertEqual(cleaned_string, "Hello, World!")

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_removeAllColorStyles_dataframe(self, mock_colorText):
        # Mock color styles
        mock_colorText.FAIL = "\033[91m"
        mock_colorText.GREEN = "\033[92m"
        mock_colorText.END = "\033[0m"

        # Create a DataFrame with color codes
        df = pd.DataFrame({
            "Col1": [f"{mock_colorText.FAIL}Error{mock_colorText.END}", "Warning"],
            "Col2": [f"{mock_colorText.GREEN}Success{mock_colorText.END}", "Info"]
        })

        cleaned_df = PKImageTools.removeAllColorStyles(df)

        # Ensure color codes are removed
        expected_df = pd.DataFrame({
            "Col1": ["Error", "Warning"],
            "Col2": ["Success", "Info"]
        })
        pd.testing.assert_frame_equal(cleaned_df, expected_df)

    def test_removeAllColorStyles_plain_string(self):
        # Test a string without color codes (should remain unchanged)
        plain_string = "Hello, World!"
        cleaned_string = PKImageTools.removeAllColorStyles(plain_string)
        self.assertEqual(cleaned_string, plain_string)

    def test_removeAllColorStyles_plain_dataframe(self):
        # Test a DataFrame without color codes (should remain unchanged)
        df = pd.DataFrame({"Col1": ["Text1", "Text2"], "Col2": ["MoreText1", "MoreText2"]})
        cleaned_df = PKImageTools.removeAllColorStyles(df)
        pd.testing.assert_frame_equal(cleaned_df, df)

    def test_removeAllColorStyles_invalid_input(self):
        # Ensure non-string and non-DataFrame inputs return unchanged
        self.assertEqual(PKImageTools.removeAllColorStyles(42), 42)
        self.assertEqual(PKImageTools.removeAllColorStyles(None), None)
        self.assertEqual(PKImageTools.removeAllColorStyles(["Hello", "World"]), ["Hello", "World"])

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_getCellColors(self, mock_colorText):
        # Mock color styles
        mock_colorText.HEAD = "\033[95m"
        mock_colorText.BOLD = "\033[1m"
        mock_colorText.END = "\033[0m"
        mock_colorText.BLUE = "\033[94m"
        mock_colorText.GREEN = "\033[92m"
        mock_colorText.BRIGHTGREEN = "\033[92;1m"
        mock_colorText.WARN = "\033[93m"
        mock_colorText.BRIGHTYELLOW = "\033[93;1m"
        mock_colorText.FAIL = "\033[91m"
        mock_colorText.BRIGHTRED = "\033[91;1m"
        mock_colorText.WHITE = "\033[97m"

        # Test a styled string
        cell_styled_value = f"{mock_colorText.BLUE}Text{mock_colorText.END} and {mock_colorText.GREEN}Green{mock_colorText.END} cells"
        
        # Expected results after cleaning styles
        expected_colors = ["blue", "darkgreen"]
        expected_values = ["Text", " and Green"]

        # Act
        cell_fill_colors, cleaned_values = PKImageTools.getCellColors(cell_styled_value)

        # Assert
        self.assertEqual(cell_fill_colors, expected_colors)
        self.assertEqual(cleaned_values, expected_values)

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_getCellColors_no_colors(self, mock_colorText):
        # Test a string without color codes
        cell_styled_value = "This is a plain text cell"
        
        # Act
        cell_fill_colors, cleaned_values = PKImageTools.getCellColors(cell_styled_value)

        # Assert
        self.assertEqual(cell_fill_colors, ["black"])  # Default color
        self.assertEqual(cleaned_values, [cell_styled_value])

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_getCellColors_multiple_colors(self, mock_colorText):
        # Mock color styles
        mock_colorText.HEAD = "\033[95m"
        mock_colorText.END = "\033[0m"
        mock_colorText.BLUE = "\033[94m"
        mock_colorText.GREEN = "\033[92m"
        mock_colorText.WARN = "\033[93m"

        # Test a string with multiple colors
        cell_styled_value = f"{mock_colorText.BLUE}BlueText{mock_colorText.END} and {mock_colorText.GREEN}GreenText{mock_colorText.END} in {mock_colorText.WARN}Yellow{mock_colorText.END}"

        # Expected results after cleaning styles
        expected_colors = ["blue", "darkgreen", "darkyellow"]
        expected_values = ["BlueText", " and GreenText", " in Yellow"]

        # Act
        cell_fill_colors, cleaned_values = PKImageTools.getCellColors(cell_styled_value)

        # Assert
        self.assertEqual(cell_fill_colors, expected_colors)
        self.assertEqual(cleaned_values, expected_values)

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_getCellColors_default_color(self, mock_colorText):
        # Test an empty string to return the default color (black)
        cell_styled_value = ""
        
        # Act
        cell_fill_colors, cleaned_values = PKImageTools.getCellColors(cell_styled_value)

        # Assert
        self.assertEqual(cell_fill_colors, ["black"])
        self.assertEqual(cleaned_values, [""])

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_getCellColors_invalid_input(self, mock_colorText):
        # Test an invalid input that should return the same value and default color
        cell_styled_value = 42  # Invalid input (integer)
        
        # Act
        cell_fill_colors, cleaned_values = PKImageTools.getCellColors(cell_styled_value)

        # Assert
        self.assertEqual(cell_fill_colors, ["black"])  # Default color
        self.assertEqual(cleaned_values, ["42"])  # Same value

    @patch('PKDevTools.classes.ColorText.colorText')
    def test_getCellColors_invalid_color(self, mock_colorText):
        # Mock color styles
        mock_colorText.HEAD = "\033[95m"
        mock_colorText.END = "\033[0m"
        mock_colorText.INVALID = "\033[99m"  # Invalid color code

        # Test a string with an invalid color
        cell_styled_value = f"{mock_colorText.INVALID}InvalidText{mock_colorText.END} and valid text"

        # Expected results after cleaning styles
        expected_colors = ["black"]
        expected_values = ["\x1b[99mInvalidText\x1b[0m and valid text"]

        # Act
        cell_fill_colors, cleaned_values = PKImageTools.getCellColors(cell_styled_value)

        # Assert
        self.assertEqual(cell_fill_colors, expected_colors)
        self.assertEqual(cleaned_values, expected_values)

    @patch('builtins.max', return_value=5)
    @patch('PIL.Image.new')
    @patch('PIL.ImageFont.truetype')
    @patch('PIL.ImageDraw.Draw')
    @patch('os.path.isfile', return_value=True)
    @patch('pkscreener.classes.ImageUtility.PKImageTools.addQuickWatermark')
    @patch('PKDevTools.classes.Archiver.get_user_outputs_dir', return_value='/fake/dir')
    @pytest.mark.skip(reason="API has changed")
    @patch('pkscreener.classes.Utility.tools.tryFetchFromServer')
    def test_tableToImage_success(self, mock_fetch,mock_get_dir, mock_add_watermark, mock_isfile, mock_draw, mock_font, mock_image_new,mock_max):
        # Arrange
        mock_image = MagicMock()
        mock_image_new.return_value = mock_image
        mock_add_watermark.return_value = mock_image
        mock_font.return_value = ImageFont.load_default()
        mock_draw.return_value = MagicMock()
        mock_draw.return_value.multiline_textbbox.return_value = (0,0,500,500)
        mock_fetch.return_value = MagicMock(status_code=200, content=b"dummy")
        
        table = "Sample Table"
        styled_table = "Styled Table"
        filename = "output.png"
        label = "Sample Label"

        # Act
        PKImageTools.tableToImage(table, styled_table, filename, label)

        # Assert
        mock_image.save.assert_called_once_with(filename, format="JPEG", bitmap_format="JPEG", optimize=True, quality=20)
        mock_add_watermark.assert_called()
        # mock_draw.text.assert_called()

    @patch('builtins.max', return_value=5)
    @patch('PIL.Image.new')
    @patch('PIL.ImageFont.truetype')
    @pytest.mark.skip(reason="PIL warnings issue")
    @patch('PIL.ImageDraw.Draw')
    @patch('os.path.isfile', return_value=True)
    @patch('pkscreener.classes.ImageUtility.PKImageTools.addQuickWatermark')
    def test_tableToImage_empty_table(self, mock_add_watermark, mock_draw, mock_font, mock_image_new, mock_isfile,mock_max):
        # Arrange
        mock_image = MagicMock()
        mock_image_new.return_value = mock_image
        mock_add_watermark.return_value = mock_image
        mock_font.return_value = ImageFont.load_default()
        mock_draw.return_value = MagicMock()

        table = ""
        styled_table = ""
        filename = "output_empty.png"
        label = "Empty Label"

        # Act
        PKImageTools.tableToImage(table, styled_table, filename, label)

        # Assert
        mock_image.save.assert_called_once_with(filename, format="JPEG", bitmap_format="JPEG", optimize=True, quality=20)
        mock_add_watermark.assert_called()
        # mock_draw.text.assert_called()  # Make sure drawing is called, even if it's empty

    @patch('builtins.max', return_value=5)
    @patch('PIL.Image.new')
    @patch('PIL.ImageFont.truetype')
    @patch('PIL.ImageDraw.Draw')
    @patch('os.path.isfile', return_value=True)
    @patch('pkscreener.classes.ImageUtility.PKImageTools.addQuickWatermark')
    @patch('PKDevTools.classes.log.emptylogger.debug')
    def test_tableToImage_error_handling(self,mock_debug,mock_add_watermark, mock_draw, mock_font, mock_image_new, mock_isfile,mock_max):
        # Arrange
        mock_image = MagicMock()
        mock_image_new.return_value = mock_image
        mock_add_watermark.return_value = mock_image
        mock_font.return_value = ImageFont.load_default()
        mock_draw.return_value = MagicMock()

        # Simulate error during image creation
        mock_image.save.side_effect = IOError("Failed to save image")

        table = "Sample Table"
        styled_table = "Styled Table"
        filename = "output_error.png"
        label = "Sample Label"

        # Act & Assert
        PKImageTools.tableToImage(table, styled_table, filename, label)
        mock_debug.assert_called() # because it raised an error and was caught and logged

    @patch('textwrap.TextWrapper.wrap')
    def test_wrapFitLegendText(self, mock_wrap):
        # Arrange
        mock_wrap.return_value = ["This is a wrapped line", "Another wrapped line"]
        table = "Sample Table"
        backtest_summary = "Summary"
        legend_text = "This is a long legend text that needs wrapping."
        
        # Act
        wrapped_text = PKImageTools.wrapFitLegendText(table=table, backtestSummary=backtest_summary, legendText=legend_text)
        
        # Assert
        self.assertEqual(wrapped_text, "This is a wrapped line\nAnother wrapped line")

    def test_getDefaultColors(self):
        # Arrange & Act
        bgColor, gridColor, artColor, menuColor = PKImageTools.getDefaultColors()

        # Assert
        self.assertIn(bgColor, ["white", "black"])
        self.assertIn(gridColor, ["white", "black"])
        self.assertIn(artColor, ["blue", "indigo", "green", "red", "yellow", "orange", "violet"])
        self.assertEqual(menuColor, "red")

    @patch('pkscreener.classes.ImageUtility.PKImageTools.fetcher.fetchURL')
    @patch('PKDevTools.classes.Archiver.findFile')
    def test_setupReportFont(self, mock_find_file, mock_fetch):
        # Arrange
        mock_find_file.return_value = (None, "fake/path", None)
        mock_fetch.return_value = MagicMock(status_code=200, content=b"dummy")
        
        # Act
        with self.assertRaises(FileNotFoundError):
            font_path = PKImageTools.setupReportFont()

        # Assert
        mock_fetch.assert_called_once()
        # self.assertEqual(font_path, "fake/path")

    def test_getLegendHelpText(self):
        # Arrange
        table = "Sample Table"
        backtest_summary = "Summary"
        
        # Act
        legend_text = PKImageTools.getLegendHelpText(table, backtest_summary)

        # Assert
        self.assertIn("1.Stock", legend_text)
        self.assertIn("Breakout level", legend_text)

    def test_getRepoHelpText(self):
        # Arrange
        table = "Sample Table"
        backtest_summary = "Summary"
        
        # Act
        repo_text = PKImageTools.getRepoHelpText(table, backtest_summary)

        # Assert
        self.assertIn("Source: https://GitHub.com/pkjmesra/pkscreener/", repo_text)
        self.assertIn("Understanding this report:", repo_text)

    def test_roundOff(self):
        # Test rounding off to 2 decimal places
        result = PKImageTools.roundOff(12.34567, 2)
        self.assertEqual(result, "12.35")
        
        # Test rounding off to 0 decimal places (integer)
        result = PKImageTools.roundOff(12.34567, 0)
        self.assertEqual(result, '12')
        
        # Test rounding with invalid string input (should remain unchanged)
        result = PKImageTools.roundOff("invalid", 2)
        self.assertEqual(result, "invalid")

    def test_stockNameFromDecoratedName(self):
        # Arrange
        decorated_name = "\x1B]8;;https://example.com\x1B\\StockName"
        
        # Act
        clean_name = PKImageTools.stockNameFromDecoratedName(decorated_name)

        # Assert
        self.assertEqual(clean_name, "StockName")

        # Test for None input (should raise TypeError)
        with self.assertRaises(TypeError):
            PKImageTools.stockNameFromDecoratedName(None)
