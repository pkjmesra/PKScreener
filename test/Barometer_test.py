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
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


class TestBarometerConstants(unittest.TestCase):
    """Test module-level constants and imports."""

    def test_query_selector_timeout(self):
        """Test QUERY_SELECTOR_TIMEOUT constant."""
        from pkscreener.classes.Barometer import QUERY_SELECTOR_TIMEOUT
        self.assertEqual(QUERY_SELECTOR_TIMEOUT, 1000)

    def test_configManager_exists(self):
        """Test configManager is loaded."""
        from pkscreener.classes.Barometer import configManager
        self.assertIsNotNone(configManager)


class TestTakeScreenshotFunction(unittest.TestCase):
    """Test takeScreenshot async function - lines 44-86."""

    def test_takeScreenshot_success(self):
        """Test takeScreenshot with mocked page and config."""
        async def run_test():
            from pkscreener.classes import Barometer
            from pkscreener.classes import ConfigManager
            
            # Create mock page with all required async methods
            mock_page = AsyncMock()
            mock_svg_element = MagicMock()
            mock_india_element = MagicMock()
            mock_popover_element = MagicMock()
            
            # Set up querySelector to return different elements for different selectors
            async def mock_query_selector(selector):
                if 'countries' in selector:
                    return mock_svg_element
                elif 'India' in selector:
                    return mock_india_element
                else:
                    return mock_popover_element
            
            mock_page.querySelector = AsyncMock(side_effect=mock_query_selector)
            mock_page.waitFor = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value=800)
            mock_page.click = AsyncMock()
            mock_page.screenshot = AsyncMock()
            
            # Patch configManager with proper attributes
            with patch.object(Barometer.configManager, 'getConfig', MagicMock()):
                with patch.object(Barometer.configManager, 'barometerx', 100, create=True):
                    with patch.object(Barometer.configManager, 'barometery', 100, create=True):
                        with patch.object(Barometer.configManager, 'barometerwidth', 600, create=True):
                            with patch.object(Barometer.configManager, 'barometerheight', 400, create=True):
                                with patch.object(Barometer.configManager, 'barometerwindowwidth', 1920, create=True):
                                    with patch.object(Barometer.configManager, 'barometerwindowheight', 1080, create=True):
                                        with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                                            with patch('os.path.join', return_value='/tmp/test.png'):
                                                with patch('os.path.exists', return_value=True):
                                                    with patch('os.stat') as mock_stat:
                                                        mock_stat.return_value.st_size = 1000
                                                        await Barometer.takeScreenshot(mock_page, 'test.png', 'Performance')
            
            # Verify screenshot was called
            mock_page.screenshot.assert_called_once()
        
        asyncio.run(run_test())


class TestGetScreenshotsFunction(unittest.TestCase):
    """Test getScreenshotsForGlobalMarketBarometer async function - lines 92-127."""

    def test_getScreenshotsForGlobalMarketBarometer_without_puppeteer_path(self):
        """Test without PUPPETEER_EXECUTABLE_PATH."""
        async def run_test():
            from pkscreener.classes import Barometer
            
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_element = MagicMock()
            
            mock_page.goto = AsyncMock()
            mock_page.querySelector = AsyncMock(return_value=mock_element)
            mock_page.waitFor = AsyncMock()
            mock_page.evaluate = AsyncMock()
            mock_page.click = AsyncMock()
            mock_browser.newPage = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            with patch.object(Barometer, 'launch', AsyncMock(return_value=mock_browser)):
                with patch.object(Barometer, 'takeScreenshot', AsyncMock()):
                    with patch.dict(os.environ, {}, clear=False):
                        # Remove PUPPETEER_EXECUTABLE_PATH if present
                        env_copy = os.environ.copy()
                        if 'PUPPETEER_EXECUTABLE_PATH' in env_copy:
                            del env_copy['PUPPETEER_EXECUTABLE_PATH']
                        with patch.dict(os.environ, env_copy, clear=True):
                            await Barometer.getScreenshotsForGlobalMarketBarometer()
            
            mock_browser.close.assert_called_once()
        
        asyncio.run(run_test())

    def test_getScreenshotsForGlobalMarketBarometer_with_puppeteer_path(self):
        """Test with PUPPETEER_EXECUTABLE_PATH set."""
        async def run_test():
            from pkscreener.classes import Barometer
            
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_element = MagicMock()
            
            mock_page.goto = AsyncMock()
            mock_page.querySelector = AsyncMock(return_value=mock_element)
            mock_page.waitFor = AsyncMock()
            mock_page.evaluate = AsyncMock()
            mock_page.click = AsyncMock()
            mock_browser.newPage = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            with patch.object(Barometer, 'launch', AsyncMock(return_value=mock_browser)) as mock_launch:
                with patch.object(Barometer, 'takeScreenshot', AsyncMock()):
                    with patch.dict(os.environ, {'PUPPETEER_EXECUTABLE_PATH': '/usr/bin/chromium'}):
                        await Barometer.getScreenshotsForGlobalMarketBarometer()
            
            mock_browser.close.assert_called_once()
        
        asyncio.run(run_test())


class TestGetGlobalMarketBarometerValuation(unittest.TestCase):
    """Test getGlobalMarketBarometerValuation function - lines 133-176."""

    def test_success_path(self):
        """Test successful execution path."""
        from pkscreener.classes import Barometer
        
        # Mock image processing
        mock_img = MagicMock()
        mock_img.size = (710, 460)
        mock_draw = MagicMock()
        
        # Use a proper async mock that completes
        async def mock_screenshots():
            pass
        
        with patch.object(Barometer, 'getScreenshotsForGlobalMarketBarometer', return_value=mock_screenshots()):
            with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                with patch('pkscreener.classes.Barometer.ImageUtility.PKImageTools.setupReportFont', return_value='font.ttf'):
                    with patch('pkscreener.classes.Barometer.Image.open', return_value=mock_img):
                        with patch('pkscreener.classes.Barometer.Image.new', return_value=mock_img):
                            with patch('pkscreener.classes.Barometer.ImageFont.truetype', return_value=MagicMock()):
                                with patch('pkscreener.classes.Barometer.ImageDraw.Draw', return_value=mock_draw):
                                    with patch('pkscreener.classes.Barometer.ImageUtility.PKImageTools.addQuickWatermark', return_value=mock_img):
                                        with patch('pkscreener.classes.Barometer.ImageUtility.PKImageTools.removeAllColorStyles', return_value='text'):
                                            with patch('pkscreener.classes.Barometer.MarketStatus') as mock_market:
                                                mock_market_instance = MagicMock()
                                                mock_market_instance.getMarketStatus.return_value = 'Open'
                                                mock_market.return_value = mock_market_instance
                                                
                                                with patch('os.path.join', side_effect=lambda *a: '/'.join(a)):
                                                    with patch('os.path.exists', return_value=True):
                                                        with patch('os.stat') as mock_stat:
                                                            mock_stat.return_value.st_size = 5000
                                                            result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNotNone(result)

    def test_async_incomplete_read_error(self):
        """Test handling of IncompleteReadError."""
        from pkscreener.classes import Barometer
        
        async def raise_incomplete():
            raise asyncio.IncompleteReadError(b'', 100)
        
        with patch.object(Barometer, 'getScreenshotsForGlobalMarketBarometer', return_value=raise_incomplete()):
            result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNone(result)

    def test_async_invalid_state_error(self):
        """Test handling of InvalidStateError."""
        from pkscreener.classes import Barometer
        
        async def raise_invalid():
            raise asyncio.InvalidStateError()
        
        with patch.object(Barometer, 'getScreenshotsForGlobalMarketBarometer', return_value=raise_invalid()):
            result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNone(result)

    def test_keyboard_interrupt(self):
        """Test KeyboardInterrupt is re-raised from event loop."""
        from pkscreener.classes import Barometer
        
        # Patch at the event loop level
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_until_complete.side_effect = KeyboardInterrupt
            
            with self.assertRaises(KeyboardInterrupt):
                Barometer.getGlobalMarketBarometerValuation()

    def test_general_exception_in_async(self):
        """Test general exception handling in async call."""
        from pkscreener.classes import Barometer
        
        async def raise_general():
            raise Exception("Browser error")
        
        with patch.object(Barometer, 'getScreenshotsForGlobalMarketBarometer', return_value=raise_general()):
            with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                with patch('pkscreener.classes.Barometer.Image.open') as mock_open:
                    mock_open.side_effect = FileNotFoundError("No image")
                    result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNone(result)

    def test_image_processing_error(self):
        """Test error handling during image processing."""
        from pkscreener.classes import Barometer
        
        async def mock_screenshots():
            pass
        
        with patch.object(Barometer, 'getScreenshotsForGlobalMarketBarometer', return_value=mock_screenshots()):
            with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                with patch('pkscreener.classes.Barometer.ImageUtility.PKImageTools.setupReportFont', return_value='font.ttf'):
                    with patch('pkscreener.classes.Barometer.Image.open') as mock_open:
                        mock_open.side_effect = FileNotFoundError("Image not found")
                        
                        result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNone(result)

    def test_image_processing_general_exception(self):
        """Test general exception during image processing is caught."""
        from pkscreener.classes import Barometer
        
        async def mock_screenshots():
            pass
        
        with patch.object(Barometer, 'getScreenshotsForGlobalMarketBarometer', return_value=mock_screenshots()):
            with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                with patch('pkscreener.classes.Barometer.ImageUtility.PKImageTools.setupReportFont', return_value='font.ttf'):
                    with patch('pkscreener.classes.Barometer.Image.open') as mock_open:
                        mock_open.side_effect = IOError("Cannot open image")
                        
                        result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNone(result)


class TestBarometerIntegrationTests(unittest.TestCase):
    """Integration tests for complete flows."""

    def test_full_flow_mocked(self):
        """Test complete flow with all dependencies mocked."""
        from pkscreener.classes import Barometer
        
        mock_img = MagicMock()
        mock_img.size = (710, 460)
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_until_complete = MagicMock()
            
            with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                with patch('pkscreener.classes.Barometer.ImageUtility') as mock_img_util:
                    mock_img_util.PKImageTools.setupReportFont.return_value = 'font.ttf'
                    mock_img_util.PKImageTools.addQuickWatermark.return_value = mock_img
                    mock_img_util.PKImageTools.removeAllColorStyles.return_value = 'text'
                    
                    with patch('pkscreener.classes.Barometer.Image') as mock_image_class:
                        mock_image_class.open.return_value = mock_img
                        mock_image_class.new.return_value = mock_img
                        
                        with patch('pkscreener.classes.Barometer.ImageFont') as mock_font:
                            mock_font.truetype.return_value = MagicMock()
                            
                            with patch('pkscreener.classes.Barometer.ImageDraw') as mock_draw:
                                mock_draw.Draw.return_value = MagicMock()
                                
                                with patch('pkscreener.classes.Barometer.MarketStatus') as mock_market:
                                    mock_instance = MagicMock()
                                    mock_instance.getMarketStatus.return_value = 'Open'
                                    mock_market.return_value = mock_instance
                                    
                                    with patch('os.path.join', side_effect=lambda *a: '/'.join(a)):
                                        with patch('os.path.exists', return_value=True):
                                            with patch('os.stat') as mock_stat:
                                                mock_stat.return_value.st_size = 5000
                                                result = Barometer.getGlobalMarketBarometerValuation()
        
        self.assertIsNotNone(result)


class TestAsyncFunctionsDirect(unittest.TestCase):
    """Test async functions with asyncio.run."""

    def test_takeScreenshot_execution(self):
        """Test takeScreenshot executes correctly."""
        async def run_test():
            from pkscreener.classes import Barometer
            
            mock_page = AsyncMock()
            mock_element = MagicMock()
            mock_page.querySelector = AsyncMock(return_value=mock_element)
            mock_page.waitFor = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value=800)
            mock_page.click = AsyncMock()
            mock_page.screenshot = AsyncMock()
            
            # Patch at module level
            with patch.object(Barometer.configManager, 'getConfig', MagicMock()):
                with patch.object(Barometer.configManager, 'barometerx', 100, create=True):
                    with patch.object(Barometer.configManager, 'barometery', 100, create=True):
                        with patch.object(Barometer.configManager, 'barometerwidth', 600, create=True):
                            with patch.object(Barometer.configManager, 'barometerheight', 400, create=True):
                                with patch.object(Barometer.configManager, 'barometerwindowwidth', 1920, create=True):
                                    with patch.object(Barometer.configManager, 'barometerwindowheight', 1080, create=True):
                                        with patch('pkscreener.classes.Barometer.Archiver.get_user_data_dir', return_value='/tmp'):
                                            with patch('os.path.join', return_value='/tmp/test.png'):
                                                with patch('os.path.exists', return_value=True):
                                                    with patch('os.stat') as mock_stat:
                                                        mock_stat.return_value.st_size = 1000
                                                        await Barometer.takeScreenshot(mock_page, 'test.png', 'Test')
        
        asyncio.run(run_test())

    def test_getScreenshotsForGlobalMarketBarometer_execution(self):
        """Test getScreenshotsForGlobalMarketBarometer executes correctly."""
        async def run_test():
            from pkscreener.classes import Barometer
            
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_element = MagicMock()
            
            mock_page.goto = AsyncMock()
            mock_page.querySelector = AsyncMock(return_value=mock_element)
            mock_page.waitFor = AsyncMock()
            mock_page.evaluate = AsyncMock()
            mock_page.click = AsyncMock()
            mock_browser.newPage = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            with patch.object(Barometer, 'launch', AsyncMock(return_value=mock_browser)):
                with patch.object(Barometer, 'takeScreenshot', AsyncMock()):
                    await Barometer.getScreenshotsForGlobalMarketBarometer()
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
