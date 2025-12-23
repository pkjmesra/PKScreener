"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for PKAnalytics.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import warnings
import os
warnings.filterwarnings("ignore")


class TestPKAnalyticsServiceCoverage:
    """Comprehensive tests for PKAnalyticsService."""
    
    def test_pkanalytics_singleton(self):
        """Test PKAnalyticsService is singleton."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc1 = PKAnalyticsService()
        svc2 = PKAnalyticsService()
        
        assert svc1 is svc2
    
    def test_pkanalytics_init_attributes(self):
        """Test PKAnalyticsService initialization sets attributes."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        
        assert hasattr(svc, 'locationInfo')
        assert hasattr(svc, 'os')
        assert hasattr(svc, 'os_version')
        assert hasattr(svc, 'app_version')
        assert hasattr(svc, 'start_time')
        assert hasattr(svc, 'isRunner')
        assert hasattr(svc, 'onefile')
        assert hasattr(svc, 'username')
        assert hasattr(svc, 'configManager')
    
    def test_collect_metrics_disabled(self):
        """Test collectMetrics when analytics disabled."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = False
        
        # Should return early
        svc.collectMetrics()
    
    def test_collect_metrics_enabled(self):
        """Test collectMetrics when analytics enabled."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        
        with patch.object(svc, 'getUserName', return_value="test_user"):
            with patch.object(svc, 'getApproxLocationInfo', return_value={"city": "Test"}):
                with patch.object(svc, 'send_event'):
                    svc.collectMetrics()
    
    def test_get_username_success(self):
        """Test getUserName returns username."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        
        username = svc.getUserName()
        
        assert username is not None
        assert len(username) > 0
    
    @patch('os.getlogin', return_value=None)
    @patch.dict(os.environ, {"username": "test_user"})
    def test_get_username_fallback_username_env(self, mock_login):
        """Test getUserName falls back to username env var."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.username = ""
        
        # Force branch by setting None return
        with patch('os.getlogin', return_value=""):
            username = svc.getUserName()
            # Should get some username
            assert username is not None
    
    @patch('os.getlogin', side_effect=OSError("No login"))
    def test_get_username_exception(self, mock_login):
        """Test getUserName handles exception."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        
        username = svc.getUserName()
        # Should return fallback
        assert username is not None
    
    @patch('PKDevTools.classes.Fetcher.fetcher.fetchURL')
    def test_get_approx_location_info(self, mock_fetch):
        """Test getApproxLocationInfo."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        mock_response = MagicMock()
        mock_response.text = '{"city": "Mumbai", "country": "IN"}'
        mock_fetch.return_value = mock_response
        
        svc = PKAnalyticsService()
        result = svc.getApproxLocationInfo()
        
        assert result is not None
    
    def test_send_event_disabled(self):
        """Test send_event when analytics disabled."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = False
        
        # Should return early
        svc.send_event("test_event")
    
    @patch('PKDevTools.classes.pubsub.publisher.PKUserService.send_event')
    def test_send_event_enabled(self, mock_send):
        """Test send_event when analytics enabled."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        svc.locationInfo = {"city": "Mumbai", "country": "IN"}
        
        svc.send_event("test_event")
        
        # Should call PKUserService.send_event
        mock_send.assert_called_once()
    
    @patch('PKDevTools.classes.pubsub.publisher.PKUserService.send_event')
    def test_send_event_with_params(self, mock_send):
        """Test send_event with additional params."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        svc.locationInfo = {"city": "Mumbai"}
        
        svc.send_event("test_event", params={"custom_key": "custom_value"})
        
        mock_send.assert_called_once()
    
    @patch('PKDevTools.classes.pubsub.publisher.PKUserService.send_event')
    @patch.dict(os.environ, {"RUNNER": "true"})
    def test_send_event_is_runner(self, mock_send):
        """Test send_event when running in GitHub Actions."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        svc.isRunner = True
        svc.locationInfo = {"city": "Mumbai"}
        
        with patch('os.popen') as mock_popen:
            mock_popen.return_value.read.return_value = "pkjmesra"
            svc.send_event("test_event")
    
    @patch('PKDevTools.classes.pubsub.publisher.PKUserService.send_event')
    def test_send_event_location_string(self, mock_send):
        """Test send_event when locationInfo is string."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        svc.locationInfo = "string_location"  # Should trigger collectMetrics
        
        # Mock collectMetrics to set locationInfo as dict
        def mock_collect(*args, **kwargs):
            svc.locationInfo = {"city": "Test"}
        
        with patch.object(svc, 'collectMetrics', side_effect=mock_collect):
            svc.send_event("test_event")
    
    def test_version_attribute(self):
        """Test VERSION is imported correctly."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        from pkscreener.classes import VERSION
        
        svc = PKAnalyticsService()
        
        assert svc.app_version == VERSION
    
    @patch('os.getlogin', return_value="")
    @patch.dict(os.environ, {}, clear=True)
    def test_get_username_multiple_fallbacks(self, mock_login):
        """Test getUserName goes through multiple fallbacks."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.username = ""
        
        # Mock to simulate empty returns
        with patch.dict(os.environ, {"username": "", "USER": "", "USERPROFILE": ""}):
            with patch('getpass.getuser', return_value="fallback_user"):
                username = svc.getUserName()
                assert username is not None
    
    @patch('PKDevTools.classes.pubsub.publisher.PKUserService.send_event')
    @patch('os.popen')
    def test_send_event_runner_git_success(self, mock_popen, mock_send):
        """Test send_event with runner git commands."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        # Setup mock for popen
        mock_result = MagicMock()
        mock_result.read.return_value = "test_value\n"
        mock_popen.return_value = mock_result
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        svc.isRunner = True
        svc.locationInfo = {"city": "Mumbai"}
        
        svc.send_event("test_event")
        
        mock_send.assert_called_once()
    
    @patch('PKDevTools.classes.pubsub.publisher.PKUserService.send_event')
    @patch('os.popen', side_effect=Exception("Git error"))
    def test_send_event_runner_git_exception(self, mock_popen, mock_send):
        """Test send_event handles git exception."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        
        svc = PKAnalyticsService()
        svc.configManager.enableUsageAnalytics = True
        svc.isRunner = True
        svc.locationInfo = {"city": "Mumbai"}
        
        # Should not raise despite git exception
        svc.send_event("test_event")
        
        mock_send.assert_called_once()
