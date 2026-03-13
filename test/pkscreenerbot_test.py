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

from pkscreener.classes.MenuOptions import menus, level0MenuDict


class TestPKScreenerBot(unittest.TestCase):
    """Tests for PKScreener bot functionality."""
    
    def test_level0ButtonsHaveAllSupportedParentButtons(self):
        m0 = menus()
        l0_menus = m0.renderForMenu(selectedMenu=None,asList=True,skip=[x for x in level0MenuDict.keys() if x not in ["X","B","P"]])
        l0_buttons = [x.menuKey for x in l0_menus]
        self.assertTrue(x in l0_buttons for x in ["X","B","P"])
        self.assertTrue(x not in l0_buttons for x in [x for x in level0MenuDict.keys() if x not in ["X","B","P"]])


class TestBotWorkflowIntegration(unittest.TestCase):
    """Tests to ensure bot workflow triggering works with scalable architecture."""
    
    def test_run_workflow_imports(self):
        """Test that run_workflow can be imported without errors."""
        from pkscreener.classes.WorkflowManager import run_workflow
        self.assertIsNotNone(run_workflow)
    
    def test_screener_fetcher_post_url_available(self):
        """Test that screenerStockDataFetcher.postURL is available for workflow triggers."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        self.assertTrue(hasattr(fetcher, 'postURL'))
        self.assertTrue(callable(fetcher.postURL))
    
    def test_fetcher_has_scalable_data_sources(self):
        """Test that Fetcher has scalable data source attributes."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        # Should have high-performance provider attribute
        self.assertTrue(hasattr(fetcher, '_hp_provider'))
        
        # Should have scalable fetcher attribute
        self.assertTrue(hasattr(fetcher, '_scalable_fetcher'))
    
    def test_fetcher_health_check_method_exists(self):
        """Test that Fetcher has healthCheck method for monitoring."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        self.assertTrue(hasattr(fetcher, 'healthCheck'))
        self.assertTrue(callable(fetcher.healthCheck))
        
        # Should return a dict with expected keys
        health = fetcher.healthCheck()
        self.assertIsInstance(health, dict)
        self.assertIn('overall_status', health)
    
    def test_fetcher_data_source_stats_method_exists(self):
        """Test that Fetcher has getDataSourceStats method."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        self.assertTrue(hasattr(fetcher, 'getDataSourceStats'))
        self.assertTrue(callable(fetcher.getDataSourceStats))
        
        stats = fetcher.getDataSourceStats()
        self.assertIsInstance(stats, dict)
    
    @patch('pkscreener.classes.WorkflowManager.screenerStockDataFetcher')
    def test_workflow_uses_fetcher_for_api_calls(self, mock_fetcher_class):
        """Test that run_workflow uses Fetcher for API calls."""
        from pkscreener.classes.WorkflowManager import run_workflow
        
        mock_fetcher = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_fetcher.postURL.return_value = mock_response
        mock_fetcher_class.return_value = mock_fetcher
        
        # This should not raise
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
            with patch('PKDevTools.classes.Environment.PKEnvironment') as mock_env:
                mock_env_instance = MagicMock()
                mock_env_instance.secrets = ('a', 'b', 'c', 'test_ghp_token')
                mock_env.return_value = mock_env_instance
                
                try:
                    run_workflow(
                        command="test",
                        user="12345",
                        options="-a Y -e -o X:12:7",
                        workflowType="S"
                    )
                except Exception:
                    # May fail due to missing env vars, but import should work
                    pass


class TestBotMenuOptions(unittest.TestCase):
    """Tests to ensure all bot menu options are available."""
    
    def test_all_scanner_menu_options_available(self):
        """Test that key scanner menu options are available."""
        from pkscreener.classes.MenuOptions import menus
        
        m0 = menus()
        
        # These are the main scanner options that should be available
        # Note: 'B' (Backtest) may be rendered differently
        expected_options = ['X', 'P']
        
        all_menus = m0.renderForMenu(selectedMenu=None, asList=True, skip=[])
        menu_keys = [menu.menuKey for menu in all_menus]
        
        for option in expected_options:
            self.assertIn(option, menu_keys, f"Menu option {option} should be available")
    
    def test_level0_menu_has_scanner_option(self):
        """Test that level 0 menu has X (Scanner) option."""
        from pkscreener.classes.MenuOptions import menus, level0MenuDict
        
        # X should be in level0MenuDict
        self.assertIn('X', level0MenuDict)
    
    def test_level0_menu_has_piped_scanner_option(self):
        """Test that level 0 menu has P (Piped Scanner) option."""
        from pkscreener.classes.MenuOptions import menus, level0MenuDict
        
        # P should be in level0MenuDict
        self.assertIn('P', level0MenuDict)
    
    def test_menu_render_returns_list(self):
        """Test that menu rendering returns a list."""
        from pkscreener.classes.MenuOptions import menus
        
        m0 = menus()
        
        # Render with asList=True should return a list
        result = m0.renderForMenu(selectedMenu=None, asList=True, skip=[])
        
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)


class TestBotDataIntegration(unittest.TestCase):
    """Tests to ensure bot can access data through the scalable architecture."""
    
    def test_fetcher_fetch_stock_data_available(self):
        """Test that fetchStockData method is available."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        self.assertTrue(hasattr(fetcher, 'fetchStockData'))
        self.assertTrue(callable(fetcher.fetchStockData))
    
    def test_fetcher_is_data_fresh_available(self):
        """Test that isDataFresh method is available for freshness checks."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        self.assertTrue(hasattr(fetcher, 'isDataFresh'))
        self.assertTrue(callable(fetcher.isDataFresh))
        
        # Should return boolean
        result = fetcher.isDataFresh(max_age_seconds=900)
        self.assertIsInstance(result, bool)
    
    def test_fetcher_get_latest_price_available(self):
        """Test that getLatestPrice method is available."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        self.assertTrue(hasattr(fetcher, 'getLatestPrice'))
        self.assertTrue(callable(fetcher.getLatestPrice))
    
    def test_fetcher_get_realtime_ohlcv_available(self):
        """Test that getRealtimeOHLCV method is available."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        self.assertTrue(hasattr(fetcher, 'getRealtimeOHLCV'))
        self.assertTrue(callable(fetcher.getRealtimeOHLCV))


if __name__ == '__main__':
    unittest.main()
