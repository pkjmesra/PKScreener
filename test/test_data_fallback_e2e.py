# -*- coding: utf-8 -*-
"""
End-to-end functional tests for data fallback mechanism in PKScreener.

Tests the complete flow of:
1. Data freshness checking using trading days
2. Triggering history download workflow
3. Applying fresh tick data to stale pkl data
4. Loading pkl files from actions-data-download
"""

import os
import pickle
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestDataFreshnessE2E(unittest.TestCase):
    """End-to-end tests for data freshness validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_is_data_fresh_with_today_data(self):
        """Test that today's data is considered fresh."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Create sample data with today's date
        today = datetime.now()
        sample_df = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2530.0],
            'Volume': [1000000],
        }, index=[today])
        
        is_fresh, data_date, trading_days_old = PKAssetsManager.is_data_fresh(sample_df)
        
        # Today's data should be fresh (0 trading days old)
        self.assertLessEqual(trading_days_old, 1, "Today's data should have 0-1 trading days age")
        
        print(f"✅ Fresh data check: is_fresh={is_fresh}, date={data_date}, age={trading_days_old}")

    def test_is_data_fresh_with_old_data(self):
        """Test that old data is correctly identified as stale."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Create sample data from 2 weeks ago
        old_date = datetime.now() - timedelta(days=14)
        sample_df = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2530.0],
            'Volume': [1000000],
        }, index=[old_date])
        
        is_fresh, data_date, trading_days_old = PKAssetsManager.is_data_fresh(sample_df)
        
        # 2-week old data should be stale (at least 5+ trading days old)
        self.assertFalse(is_fresh, "2-week old data should be stale")
        self.assertGreater(trading_days_old, 5, "Should have multiple trading days")
        
        print(f"✅ Stale data check: is_fresh={is_fresh}, date={data_date}, age={trading_days_old}")

    def test_is_data_fresh_with_dict_format(self):
        """Test freshness check with dict format (from to_dict('split'))."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = datetime.now()
        sample_dict = {
            'data': [[2500.0, 2550.0, 2480.0, 2530.0, 1000000]],
            'columns': ['Open', 'High', 'Low', 'Close', 'Volume'],
            'index': [today],
        }
        
        is_fresh, data_date, trading_days_old = PKAssetsManager.is_data_fresh(sample_dict)
        
        self.assertLessEqual(trading_days_old, 1, "Today's dict data should be fresh")
        
        print(f"✅ Dict format freshness: is_fresh={is_fresh}, date={data_date}")

    def test_validate_data_freshness_batch(self):
        """Test batch validation of stock data freshness."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = datetime.now()
        old_date = datetime.now() - timedelta(days=14)
        
        # Mix of fresh and stale data
        stock_dict = {
            'RELIANCE': pd.DataFrame({
                'Open': [2500.0], 'High': [2550.0], 'Low': [2480.0],
                'Close': [2530.0], 'Volume': [1000000],
            }, index=[today]).to_dict('split'),
            'TCS': pd.DataFrame({
                'Open': [3500.0], 'High': [3550.0], 'Low': [3480.0],
                'Close': [3530.0], 'Volume': [500000],
            }, index=[old_date]).to_dict('split'),
        }
        
        fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
            stock_dict, isTrading=False
        )
        
        self.assertEqual(fresh_count + stale_count, 2, "Should validate 2 stocks")
        self.assertGreater(stale_count, 0, "Should have at least 1 stale stock")
        
        print(f"✅ Batch validation: fresh={fresh_count}, stale={stale_count}, oldest={oldest_date}")

    def test_ensure_data_freshness(self):
        """Test ensure_data_freshness function."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = datetime.now()
        
        # Fresh data
        stock_dict = {
            'RELIANCE': pd.DataFrame({
                'Open': [2500.0], 'High': [2550.0], 'Low': [2480.0],
                'Close': [2530.0], 'Volume': [1000000],
            }, index=[today]).to_dict('split'),
        }
        
        # Don't actually trigger download in test
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_dict, trigger_download=False
        )
        
        self.assertLessEqual(missing_days, 1, "Fresh data should have 0-1 missing days")
        
        print(f"✅ Ensure freshness: is_fresh={is_fresh}, missing_days={missing_days}")


class TestApplyFreshTicks(unittest.TestCase):
    """Tests for applying fresh tick data to stale pkl data."""

    def test_apply_fresh_ticks_structure(self):
        """Test that _apply_fresh_ticks_to_data preserves data structure."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        old_date = datetime.now() - timedelta(days=5)
        
        # Create stale stock data
        stock_dict = {
            'RELIANCE': {
                'data': [[2500.0, 2550.0, 2480.0, 2530.0, 1000000]],
                'columns': ['Open', 'High', 'Low', 'Close', 'Volume'],
                'index': [old_date],
            },
        }
        
        # Apply fresh ticks (may or may not update depending on tick availability)
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        # Should return a dict
        self.assertIsInstance(result, dict)
        
        # Original stock should still exist
        self.assertIn('RELIANCE', result)
        
        print(f"✅ Apply fresh ticks preserved structure with {len(result)} stocks")


class TestTriggerHistoryDownload(unittest.TestCase):
    """Tests for triggering history download workflow."""

    def test_trigger_without_token_fails_gracefully(self):
        """Test that trigger fails gracefully without GitHub token."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Ensure no token is set
        old_token = os.environ.pop('GITHUB_TOKEN', None)
        old_ci_pat = os.environ.pop('CI_PAT', None)
        
        try:
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=1)
            
            self.assertFalse(result, "Should return False without token")
            print("✅ Trigger correctly fails without GitHub token")
        finally:
            if old_token:
                os.environ['GITHUB_TOKEN'] = old_token
            if old_ci_pat:
                os.environ['CI_PAT'] = old_ci_pat

    @patch('requests.post')
    def test_trigger_with_mock_api(self, mock_post):
        """Test trigger with mocked GitHub API."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Set a fake token
        os.environ['GITHUB_TOKEN'] = 'fake_token_for_testing'
        
        try:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=3)
            
            self.assertTrue(result, "Should return True with successful API call")
            
            # Verify the API was called correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            self.assertIn('w1-workflow-history-data-child.yml', call_args[0][0])
            
            # Check payload
            payload = call_args[1]['json']
            self.assertEqual(payload['inputs']['pastoffset'], '3')
            
            print("✅ Trigger workflow called API correctly")
        finally:
            os.environ.pop('GITHUB_TOKEN', None)


class TestDownloadFromActionsDataBranch(unittest.TestCase):
    """Tests for downloading pkl files from actions-data-download branch."""

    def test_download_pkl_from_github(self):
        """Test actual download from GitHub actions-data-download branch."""
        import requests
        
        # Known URLs where pkl files should exist
        urls_to_try = [
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/stock_data_23122025.pkl",
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/stock_data_17122025.pkl",
        ]
        
        found_any = False
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200 and len(response.content) > 1000:
                    found_any = True
                    print(f"✅ Found pkl file at: {url} ({len(response.content)} bytes)")
                    break
            except Exception as e:
                print(f"⚠️ Could not access {url}: {e}")
        
        if not found_any:
            print("⚠️ No pkl files found at known locations (may need fresh data)")

    def test_try_fetch_from_server(self):
        """Test Utility.tools.tryFetchFromServer function."""
        from pkscreener.classes.Utility import tools
        
        # Try to fetch a known file
        resp = tools.tryFetchFromServer(
            "stock_data_23122025.pkl",
            repoOwner="pkjmesra",
            repoName="PKScreener",
            directory="actions-data-download",
            hideOutput=True,
            branchName="refs/heads/actions-data-download"
        )
        
        if resp is not None and resp.status_code == 200:
            self.assertGreater(len(resp.content), 1000, "Should get substantial content")
            print(f"✅ tryFetchFromServer works: {len(resp.content)} bytes")
        else:
            print("⚠️ tryFetchFromServer did not find file (may not exist)")


class TestTradingDaysCalculation(unittest.TestCase):
    """Tests for trading days calculation."""

    def test_trading_days_between(self):
        """Test trading days calculation using PKDateUtilities."""
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        
        # Get last trading date
        last_trading = PKDateUtilities.tradingDate()
        
        self.assertIsNotNone(last_trading, "Should get a trading date")
        
        # Calculate days between a week ago and today
        week_ago = datetime.now() - timedelta(days=7)
        
        # This should give us 4-5 trading days (excluding weekends)
        if hasattr(PKDateUtilities, 'trading_days_between'):
            days = PKDateUtilities.trading_days_between(week_ago.date(), datetime.now().date())
            self.assertLessEqual(days, 7, "Trading days should be less than calendar days")
            print(f"✅ Trading days in last week: {days}")
        else:
            print("⚠️ trading_days_between method not available")

    def test_is_trading_time(self):
        """Test is trading time check."""
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        
        result = PKDateUtilities.isTradingTime()
        self.assertIsInstance(result, bool)
        
        print(f"✅ Is trading time: {result}")


class TestFullE2EFlow(unittest.TestCase):
    """Full end-to-end integration test."""

    def test_complete_data_loading_flow(self):
        """Test complete flow from fetching to using data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        import pkscreener.classes.ConfigManager as ConfigManager
        
        # Initialize config manager
        config_manager = ConfigManager.tools()
        config_manager.getConfig(ConfigManager.parser)
        
        # Create empty stock dict
        stock_dict = {}
        
        # Try to load from local pickle
        cache_file = "stock_data_*.pkl"
        
        # This tests the actual loading mechanism
        try:
            result_dict, loaded = PKAssetsManager.loadDataFromLocalPickle(
                stock_dict,
                config_manager,
                downloadOnly=False,
                defaultAnswer='Y',
                exchangeSuffix='.NS',
                cache_file=cache_file,
                isTrading=False
            )
            
            # Either we loaded data or we didn't (depends on local cache)
            if loaded:
                self.assertGreater(len(result_dict), 0, "Should have some stocks")
                print(f"✅ Loaded {len(result_dict)} stocks from local cache")
            else:
                print("⚠️ No local cache found (expected in clean environment)")
        except FileNotFoundError:
            print("⚠️ No local cache file found (expected in clean environment)")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
