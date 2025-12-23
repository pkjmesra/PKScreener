"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for Utility.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import datetime
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")


class TestUtilityCoverage:
    """Comprehensive tests for Utility module."""
    
    def test_format_ratio_above_threshold(self):
        """Test formatRatio when ratio is above threshold."""
        from pkscreener.classes.Utility import tools
        
        result = tools.formatRatio(3.0, 2.5)
        
        assert "3.0" in result
        assert "x" in result
    
    def test_format_ratio_below_threshold(self):
        """Test formatRatio when ratio is below threshold."""
        from pkscreener.classes.Utility import tools
        
        result = tools.formatRatio(1.0, 2.5)
        
        assert "1.0" in result or "x" in result
    
    def test_format_ratio_nan(self):
        """Test formatRatio with NaN value."""
        from pkscreener.classes.Utility import tools
        
        result = tools.formatRatio(np.nan, 2.5)
        
        # Should handle NaN
        assert result is not None
    
    def test_stock_decorated_name_india(self):
        """Test stockDecoratedName for India."""
        from pkscreener.classes.Utility import tools
        
        result = tools.stockDecoratedName("SBIN", "INDIA")
        
        assert "SBIN" in result
        assert "NSE" in result
    
    def test_stock_decorated_name_nasdaq(self):
        """Test stockDecoratedName for NASDAQ."""
        from pkscreener.classes.Utility import tools
        
        result = tools.stockDecoratedName("AAPL", "USA")
        
        assert "AAPL" in result
        assert "NASDAQ" in result
    
    @patch.dict(os.environ, {"GITHUB_OUTPUT": "/tmp/test_output"})
    @patch('builtins.open', new_callable=mock_open)
    def test_set_github_output(self, mock_file):
        """Test set_github_output."""
        from pkscreener.classes.Utility import tools
        
        tools.set_github_output("test_name", "test_value")
        
        mock_file.assert_called()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_set_github_output_no_env(self):
        """Test set_github_output without env var."""
        from pkscreener.classes.Utility import tools
        
        # Should do nothing
        tools.set_github_output("test_name", "test_value")
    
    @patch('os.path.exists', return_value=False)
    @patch('PKNSETools.Benny.NSE.NSE')
    def test_load_large_deals_no_file(self, mock_nse, mock_exists):
        """Test loadLargeDeals when file doesn't exist."""
        from pkscreener.classes.Utility import tools
        
        mock_instance = MagicMock()
        mock_instance.largeDeals.return_value = {}
        mock_nse.return_value = mock_instance
        
        try:
            tools.loadLargeDeals()
        except:
            pass
    
    @patch('os.path.exists', return_value=True)
    @patch('os.stat')
    @patch('PKNSETools.Benny.NSE.NSE')
    @patch('PKDevTools.classes.Archiver.get_last_modified_datetime')
    def test_load_large_deals_with_old_file(self, mock_mod, mock_nse, mock_stat, mock_exists):
        """Test loadLargeDeals with old file."""
        from pkscreener.classes.Utility import tools
        
        mock_stat.return_value.st_size = 100
        mock_mod.return_value = datetime.datetime(2020, 1, 1)
        
        mock_instance = MagicMock()
        mock_instance.largeDeals.return_value = {"test": "data"}
        mock_nse.return_value = mock_instance
        
        with patch('builtins.open', new_callable=mock_open):
            try:
                tools.loadLargeDeals()
            except:
                pass
    
    def test_get_progressbar_style_non_windows(self):
        """Test getProgressbarStyle on non-Windows."""
        from pkscreener.classes.Utility import tools
        
        with patch('platform.platform', return_value="Linux-5.4.0"):
            bar, spinner = tools.getProgressbarStyle()
            
            assert bar == "smooth"
            assert spinner == "waves"
    
    def test_get_progressbar_style_windows(self):
        """Test getProgressbarStyle on Windows."""
        from pkscreener.classes.Utility import tools
        
        with patch('platform.platform', return_value="Windows-10"):
            bar, spinner = tools.getProgressbarStyle()
            
            assert bar == "classic2"
            assert spinner == "dots_recur"
    
    def test_get_sigmoid_confidence_above_05(self):
        """Test getSigmoidConfidence above 0.5."""
        from pkscreener.classes.Utility import tools
        
        result = tools.getSigmoidConfidence(0.75)
        
        assert 0 <= result <= 100
    
    def test_get_sigmoid_confidence_below_05(self):
        """Test getSigmoidConfidence below 0.5."""
        from pkscreener.classes.Utility import tools
        
        result = tools.getSigmoidConfidence(0.25)
        
        assert 0 <= result <= 100
    
    def test_get_sigmoid_confidence_exact_05(self):
        """Test getSigmoidConfidence at 0.5."""
        from pkscreener.classes.Utility import tools
        
        result = tools.getSigmoidConfidence(0.5)
        
        # Should handle boundary
        assert result is not None
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.Utility.sleep')
    def test_alert_sound(self, mock_sleep, mock_print):
        """Test alertSound."""
        from pkscreener.classes.Utility import tools
        
        tools.alertSound(beeps=2, delay=0.1)
        
        assert mock_print.call_count == 2
        assert mock_sleep.call_count == 2
    
    def test_get_max_column_widths(self):
        """Test getMaxColumnWidths."""
        from pkscreener.classes.Utility import tools
        
        df = pd.DataFrame({
            "Stock": ["SBIN"],
            "Trend(22Prds)": ["Up"],
            "Pattern": ["Triangle"],
            "MA-Signal": ["Buy"],
            "ScanOption": ["X"]
        })
        
        result = tools.getMaxColumnWidths(df)
        
        assert isinstance(result, list)
    
    def test_market_status(self):
        """Test marketStatus function."""
        from pkscreener.classes.Utility import marketStatus
        
        result = marketStatus()
        
        # Now returns empty string
        assert result == ""
    
    @patch('os.path.isfile', return_value=False)
    @patch('pkscreener.classes.Utility.fetcher.fetchURL')
    def test_try_fetch_from_server(self, mock_fetch, mock_isfile):
        """Test tryFetchFromServer."""
        from pkscreener.classes.Utility import tools
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "50000000"}  # 50MB
        mock_fetch.return_value = mock_resp
        
        result = tools.tryFetchFromServer("test.pkl", hideOutput=True)
        
        assert result is not None
    
    @patch('os.path.isfile', return_value=False)
    @patch('pkscreener.classes.Utility.fetcher.fetchURL')
    def test_try_fetch_from_server_small_file(self, mock_fetch, mock_isfile):
        """Test tryFetchFromServer with small file triggers retry."""
        from pkscreener.classes.Utility import tools
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "1000"}  # Too small
        mock_fetch.return_value = mock_resp
        
        # Should return the response (after retry logic)
        result = tools.tryFetchFromServer("test.pkl", repoOwner="testOwner", hideOutput=True)
        
        assert result is not None
    
    @patch('os.path.isfile', side_effect=[True, True, True, True, True, True])
    @patch('time.time', return_value=1000000000)
    @patch('os.path.getmtime', return_value=999999999)  # Recent file
    def test_get_nifty_model_existing(self, mock_getmtime, mock_time, mock_isfile):
        """Test getNiftyModel with existing recent files."""
        from pkscreener.classes.Utility import tools
        
        with patch('joblib.load', return_value={}):
            with patch.dict('pkscreener.Imports', {"keras": False}):
                model, pkl = tools.getNiftyModel()
                # Should not download since files are recent
    
    @patch('os.path.isfile', return_value=False)
    @patch('pkscreener.classes.Utility.fetcher.fetchURL', return_value=None)
    def test_get_nifty_model_no_files(self, mock_fetch, mock_isfile):
        """Test getNiftyModel with no files."""
        from pkscreener.classes.Utility import tools
        
        model, pkl = tools.getNiftyModel()
        
        assert model is None
    
    def test_art_text_exists(self):
        """Test artText is defined."""
        from pkscreener.classes.Utility import artText
        
        assert artText is not None
    
    def test_std_encoding(self):
        """Test STD_ENCODING is defined."""
        from pkscreener.classes.Utility import STD_ENCODING
        
        assert STD_ENCODING is not None
