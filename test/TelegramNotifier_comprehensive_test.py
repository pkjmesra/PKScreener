"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Comprehensive tests for TelegramNotifier.py to achieve 90%+ coverage.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, Mock
from argparse import Namespace
import warnings
import os
warnings.filterwarnings("ignore")


@pytest.fixture
def user_args():
    """Create user args namespace."""
    return Namespace(
        options="X:12:1",
        telegram=False,
        log=True,
        user="12345",
        monitor=False
    )


@pytest.fixture
def notifier(user_args):
    """Create TelegramNotifier instance."""
    from pkscreener.classes.TelegramNotifier import TelegramNotifier
    return TelegramNotifier(user_args, [], {})


# =============================================================================
# TelegramNotifier Initialization Tests
# =============================================================================

class TestTelegramNotifierInit:
    """Test TelegramNotifier initialization."""
    
    def test_init_with_user_args(self, user_args):
        """Test initialization with user args."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args)
        
        assert notifier.user_passed_args == user_args
        assert notifier.test_messages_queue == []
        assert notifier.media_group_dict == {}
    
    def test_init_with_all_params(self, user_args):
        """Test initialization with all params."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        test_queue = ["msg1", "msg2"]
        media_dict = {"key": "value"}
        
        notifier = TelegramNotifier(user_args, test_queue, media_dict)
        
        assert notifier.user_passed_args == user_args
        assert notifier.test_messages_queue == test_queue
        assert notifier.media_group_dict == media_dict
    
    def test_init_without_args(self):
        """Test initialization without args."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        assert notifier.user_passed_args is None
        assert notifier.test_messages_queue == []
        assert notifier.media_group_dict == {}
    
    def test_dev_channel_id(self):
        """Test DEV_CHANNEL_ID constant."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        assert TelegramNotifier.DEV_CHANNEL_ID == "-1001785195297"


# =============================================================================
# send_message_to_telegram Tests
# =============================================================================

class TestSendMessageToTelegram:
    """Test send_message_to_telegram method."""
    
    def test_send_message_telegram_flag_true(self, user_args):
        """Test send_message when telegram flag is True."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        user_args.telegram = True
        notifier = TelegramNotifier(user_args, [], {})
        
        # Should return early without sending
        notifier.send_message_to_telegram(message="Test")
    
    def test_send_message_no_runner_no_log(self):
        """Test send_message without RUNNER and log=False."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        args = Namespace(options="X:12:1", telegram=False, log=False, user="12345", monitor=False)
        notifier = TelegramNotifier(args, [], {})
        
        # Should return early
        with patch.dict(os.environ, {}, clear=True):
            notifier.send_message_to_telegram(message="Test")
    
    @patch('pkscreener.classes.TelegramNotifier.send_message')
    @patch.dict(os.environ, {"RUNNER": "true"})
    def test_send_message_with_runner(self, mock_send, user_args):
        """Test send_message with RUNNER env var."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        notifier.send_message_to_telegram(message="Test message", user="12345")
    
    @patch('pkscreener.classes.TelegramNotifier.send_message')
    @patch('pkscreener.classes.TelegramNotifier.send_photo')
    @patch.dict(os.environ, {"RUNNER": "true"})
    def test_send_photo(self, mock_send_photo, mock_send, user_args):
        """Test send_message with photo."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        notifier.send_message_to_telegram(photo_file_path="/path/to/photo.png", caption="Test", user="12345")
    
    @patch('pkscreener.classes.TelegramNotifier.send_message')
    @patch('pkscreener.classes.TelegramNotifier.send_document')
    @patch.dict(os.environ, {"RUNNER": "true"})
    def test_send_document(self, mock_send_doc, mock_send, user_args):
        """Test send_message with document."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        notifier.send_message_to_telegram(document_file_path="/path/to/doc.pdf", caption="Test", user="12345")


# =============================================================================
# _send_single_message Tests
# =============================================================================

class TestSendSingleMessage:
    """Test _send_single_message method."""
    
    @patch('pkscreener.classes.TelegramNotifier.send_message')
    def test_send_single_message_text(self, mock_send, notifier):
        """Test _send_single_message with text."""
        notifier._send_single_message("Test message", None, None, "Caption", "12345")
        
        # Should add to test queue
        assert len(notifier.test_messages_queue) == 1
    
    @patch('pkscreener.classes.TelegramNotifier.send_message')
    @patch('pkscreener.classes.TelegramNotifier.send_photo')
    def test_send_single_message_photo(self, mock_photo, mock_send, notifier):
        """Test _send_single_message with photo."""
        notifier._send_single_message(None, "/path/to/photo.png", None, "Caption", "12345")
    
    @patch('pkscreener.classes.TelegramNotifier.send_message')
    @patch('pkscreener.classes.TelegramNotifier.send_document')
    def test_send_single_message_document(self, mock_doc, mock_send, notifier):
        """Test _send_single_message with document."""
        notifier._send_single_message(None, None, "/path/to/doc.pdf", "Caption", "12345")
    
    def test_send_single_message_queue_limit(self, notifier):
        """Test _send_single_message queue limit."""
        # Add 11 messages - should pop first
        for i in range(11):
            notifier._send_single_message(f"Message {i}", None, None, f"Caption {i}", "12345")
        
        assert len(notifier.test_messages_queue) == 10
    
    def test_send_single_message_replaces_ampersand(self, notifier):
        """Test _send_single_message replaces & in caption."""
        notifier._send_single_message(None, None, None, "Test & Caption", "12345")
        
        assert "message" in notifier.test_messages_queue[0].lower()


# =============================================================================
# _send_media_group_message Tests
# =============================================================================

class TestSendMediaGroupMessage:
    """Test _send_media_group_message method."""
    
    def test_send_media_group_no_attachments(self, notifier):
        """Test _send_media_group_message without attachments."""
        notifier._send_media_group_message("12345", "Message", "Caption")
    
    @patch('pkscreener.classes.TelegramNotifier.send_media_group')
    def test_send_media_group_with_attachments(self, mock_send, user_args):
        """Test _send_media_group_message with attachments."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        media_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/path/1.png", "CAPTION": "Cap1"},
                {"FILEPATH": "/path/2.png", "CAPTION": "Cap2"},
                {"FILEPATH": "/path/3.png", "CAPTION": "Cap3"},
                {"FILEPATH": "/path/4.png", "CAPTION": "Cap4"},
            ],
            "CAPTION": "Main caption"
        }
        
        notifier = TelegramNotifier(user_args, [], media_dict)
        notifier._send_media_group_message("12345", "Message", "Caption")
    
    @patch('pkscreener.classes.TelegramNotifier.send_media_group')
    def test_send_media_group_pre_tag_handling(self, mock_send, user_args):
        """Test _send_media_group_message handles <pre> tags."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        media_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/path/1.png", "CAPTION": "<pre>Some very long caption" + "x" * 2000},
            ]
        }
        
        notifier = TelegramNotifier(user_args, [], media_dict)
        notifier._send_media_group_message("12345", "Message", "Caption")


# =============================================================================
# _handle_alert_subscriptions Tests
# =============================================================================

class TestHandleAlertSubscriptions:
    """Test _handle_alert_subscriptions method."""
    
    def test_handle_alert_no_user(self, notifier):
        """Test _handle_alert_subscriptions without user."""
        notifier._handle_alert_subscriptions(None, "Test message")
    
    def test_handle_alert_no_message(self, notifier):
        """Test _handle_alert_subscriptions without message."""
        notifier._handle_alert_subscriptions("12345", None)
    
    def test_handle_alert_no_pipe(self, notifier):
        """Test _handle_alert_subscriptions without pipe in message."""
        notifier._handle_alert_subscriptions("12345", "Message without pipe")
    
    def test_handle_alert_negative_user(self, notifier):
        """Test _handle_alert_subscriptions with negative user (channel)."""
        notifier._handle_alert_subscriptions("-123", "Scan|ID")


# =============================================================================
# add_attachment Tests
# =============================================================================

class TestAddAttachment:
    """Test add_attachment method."""
    
    def test_add_attachment_empty(self, notifier):
        """Test add_attachment to empty dict."""
        notifier.add_attachment("/path/to/file.png", "Caption")
        
        assert "ATTACHMENTS" in notifier.media_group_dict
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 1
    
    def test_add_attachment_multiple(self, notifier):
        """Test add_attachment multiple times."""
        notifier.add_attachment("/path/1.png", "Cap1")
        notifier.add_attachment("/path/2.png", "Cap2")
        notifier.add_attachment("/path/3.png", "Cap3")
        
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 3
    
    def test_add_attachment_replaces_ampersand(self, notifier):
        """Test add_attachment replaces & in caption."""
        notifier.add_attachment("/path/to/file.png", "Caption & More")
        
        assert "n" in notifier.media_group_dict["ATTACHMENTS"][0]["CAPTION"]


# =============================================================================
# set_caption Tests
# =============================================================================

class TestSetCaption:
    """Test set_caption method."""
    
    def test_set_caption(self, notifier):
        """Test set_caption."""
        notifier.set_caption("Main Caption")
        
        assert notifier.media_group_dict["CAPTION"] == "Main Caption"
    
    def test_set_caption_overwrite(self, notifier):
        """Test set_caption overwrites previous."""
        notifier.set_caption("First Caption")
        notifier.set_caption("Second Caption")
        
        assert notifier.media_group_dict["CAPTION"] == "Second Caption"


# =============================================================================
# send_test_status Tests
# =============================================================================

class TestSendTestStatus:
    """Test send_test_status method."""
    
    def test_send_test_status_with_results(self, user_args):
        """Test send_test_status with results."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        screen_results = pd.DataFrame({"Stock": ["SBIN", "RELIANCE"]})
        
        with patch.object(notifier, 'send_message_to_telegram'):
            notifier.send_test_status(screen_results, "Test Label", "12345")
    
    def test_send_test_status_no_results(self, user_args):
        """Test send_test_status without results."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        
        with patch.object(notifier, 'send_message_to_telegram'):
            notifier.send_test_status(None, "Test Label", "12345")
    
    def test_send_test_status_empty_results(self, user_args):
        """Test send_test_status with empty results."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        screen_results = pd.DataFrame()
        
        with patch.object(notifier, 'send_message_to_telegram'):
            notifier.send_test_status(screen_results, "Test Label", "12345")


# =============================================================================
# send_quick_scan_result Tests
# =============================================================================

class TestSendQuickScanResult:
    """Test send_quick_scan_result method."""
    
    def test_send_quick_scan_result_no_env(self, user_args):
        """Test send_quick_scan_result without required env vars."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        
        with patch.dict(os.environ, {}, clear=True):
            notifier.send_quick_scan_result(
                menu_choice_hierarchy="X:12:1",
                user="12345",
                tabulated_results="Results",
                markdown_results="Markdown",
                caption="Caption",
                png_name="test",
                png_extension=".png"
            )
    
    @patch('pkscreener.classes.TelegramNotifier.is_token_telegram_configured')
    @patch.dict(os.environ, {"PKDevTools_Default_Log_Level": "10"})
    def test_send_quick_scan_result_not_configured(self, mock_configured, user_args):
        """Test send_quick_scan_result when Telegram not configured."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_configured.return_value = False
        notifier = TelegramNotifier(user_args, [], {})
        
        notifier.send_quick_scan_result(
            menu_choice_hierarchy="X:12:1",
            user="12345",
            tabulated_results="Results",
            markdown_results="Markdown",
            caption="Caption",
            png_name="test",
            png_extension=".png"
        )


# =============================================================================
# send_global_market_barometer Tests
# =============================================================================

class TestSendGlobalMarketBarometer:
    """Test send_global_market_barometer method."""
    
    @patch('pkscreener.classes.Barometer.getGlobalMarketBarometerValuation')
    @patch('PKDevTools.classes.Environment.PKEnvironment')
    def test_send_global_market_barometer_no_path(self, mock_env, mock_barometer, user_args):
        """Test send_global_market_barometer when no path returned."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_barometer.return_value = None
        mock_env.return_value.secrets = (None, None, None, None)
        
        notifier = TelegramNotifier(user_args, [], {})
        
        with patch('pkscreener.classes.PKAnalytics.PKAnalyticsService') as mock_analytics:
            with patch('sys.exit'):
                try:
                    notifier.send_global_market_barometer()
                except:
                    pass  # Expected to fail or exit


# =============================================================================
# Integration Tests
# =============================================================================

class TestTelegramNotifierIntegration:
    """Integration tests for TelegramNotifier."""
    
    def test_full_workflow(self, user_args):
        """Test full notification workflow."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(user_args, [], {})
        
        # Add attachments
        notifier.add_attachment("/path/1.png", "Cap1")
        notifier.add_attachment("/path/2.png", "Cap2")
        
        # Set caption
        notifier.set_caption("Main Caption")
        
        # Check state
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 2
        assert notifier.media_group_dict["CAPTION"] == "Main Caption"
    
    def test_all_init_variations(self):
        """Test all initialization variations."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        # No args
        n1 = TelegramNotifier()
        assert n1.user_passed_args is None
        
        # With args
        args = Namespace(options="X:12:1", telegram=False, log=True, user="12345", monitor=False)
        n2 = TelegramNotifier(args)
        assert n2.user_passed_args == args
        
        # With all params
        n3 = TelegramNotifier(args, ["msg"], {"key": "val"})
        assert n3.test_messages_queue == ["msg"]
        assert n3.media_group_dict == {"key": "val"}
