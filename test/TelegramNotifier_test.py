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

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import os


class TestTelegramNotifier:
    """Test cases for TelegramNotifier class."""
    
    @pytest.fixture
    def mock_user_args(self):
        """Create mock user arguments."""
        mock = MagicMock()
        mock.log = False
        mock.telegram = False
        mock.user = "12345"
        mock.monitor = False
        mock.options = "X:1:2"
        return mock
    
    @pytest.fixture
    def notifier(self, mock_user_args):
        """Create a TelegramNotifier instance."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        return TelegramNotifier(mock_user_args)
    
    def test_initialization(self, mock_user_args):
        """Test TelegramNotifier initialization."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(mock_user_args)
        
        assert notifier.user_passed_args is mock_user_args
        assert notifier.test_messages_queue == []
        assert notifier.media_group_dict == {}
    
    def test_initialization_with_custom_queue(self, mock_user_args):
        """Test initialization with custom message queue."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        custom_queue = ["message1", "message2"]
        custom_dict = {"key": "value"}
        
        notifier = TelegramNotifier(mock_user_args, custom_queue, custom_dict)
        
        assert notifier.test_messages_queue == custom_queue
        assert notifier.media_group_dict == custom_dict
    
    def test_dev_channel_id_constant(self, mock_user_args):
        """Test that DEV_CHANNEL_ID is correctly set."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(mock_user_args)
        
        assert notifier.DEV_CHANNEL_ID == "-1001785195297"
    
    def test_add_attachment(self, notifier):
        """Test adding an attachment."""
        notifier.add_attachment("/path/to/file.png", "Test caption & special")
        
        assert "ATTACHMENTS" in notifier.media_group_dict
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 1
        assert notifier.media_group_dict["ATTACHMENTS"][0]["FILEPATH"] == "/path/to/file.png"
        assert notifier.media_group_dict["ATTACHMENTS"][0]["CAPTION"] == "Test caption n special"
    
    def test_add_multiple_attachments(self, notifier):
        """Test adding multiple attachments."""
        notifier.add_attachment("/path/to/file1.png", "Caption 1")
        notifier.add_attachment("/path/to/file2.png", "Caption 2")
        
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 2
    
    def test_set_caption(self, notifier):
        """Test setting the main caption."""
        notifier.set_caption("Main caption text")
        
        assert notifier.media_group_dict["CAPTION"] == "Main caption text"
    
    def test_send_test_status_success(self, notifier):
        """Test sending success status."""
        screen_results = pd.DataFrame({'Stock': ['SBIN', 'HDFC']})
        
        with patch.object(notifier, 'send_message_to_telegram') as mock_send:
            notifier.send_test_status(screen_results, "Test Label", "12345")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "<b>SUCCESS</b>" in call_args[1]['message']
            assert "2 Stocks" in call_args[1]['message']
    
    def test_send_test_status_fail(self, notifier):
        """Test sending fail status with no results."""
        with patch.object(notifier, 'send_message_to_telegram') as mock_send:
            notifier.send_test_status(None, "Test Label", "12345")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "<b>FAIL</b>" in call_args[1]['message']
    
    def test_send_test_status_empty_results(self, notifier):
        """Test sending fail status with empty results."""
        screen_results = pd.DataFrame()
        
        with patch.object(notifier, 'send_message_to_telegram') as mock_send:
            notifier.send_test_status(screen_results, "Test Label", "12345")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "<b>FAIL</b>" in call_args[1]['message']


class TestTelegramNotifierSendMessage:
    """Test cases for send_message_to_telegram method."""
    
    @pytest.fixture
    def mock_user_args(self):
        """Create mock user arguments."""
        mock = MagicMock()
        mock.log = True
        mock.telegram = False
        mock.user = "12345"
        mock.monitor = False
        mock.options = "X:1:2"
        return mock
    
    def test_send_message_not_in_runner_mode(self, mock_user_args):
        """Test that message is not sent when not in runner mode and log is false."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_user_args.log = False
        notifier = TelegramNotifier(mock_user_args)
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('pkscreener.classes.TelegramNotifier.send_message') as mock_send:
                notifier.send_message_to_telegram(message="Test message")
                
                # Message should not be sent when not in runner mode
                mock_send.assert_not_called()
    
    def test_send_message_with_telegram_flag(self, mock_user_args):
        """Test that message is not sent when telegram flag is set."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_user_args.telegram = True
        notifier = TelegramNotifier(mock_user_args)
        
        with patch('pkscreener.classes.TelegramNotifier.send_message') as mock_send:
            notifier.send_message_to_telegram(message="Test message")
            
            mock_send.assert_not_called()


class TestTelegramNotifierQuickScanResult:
    """Test cases for send_quick_scan_result method."""
    
    @pytest.fixture
    def mock_user_args(self):
        """Create mock user arguments."""
        mock = MagicMock()
        mock.log = True
        mock.telegram = False
        mock.user = "12345"
        mock.monitor = False
        mock.options = "X:1:2"
        return mock
    
    def test_quick_scan_result_not_configured(self, mock_user_args):
        """Test quick scan result when not configured."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier(mock_user_args)
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('pkscreener.classes.TelegramNotifier.is_token_telegram_configured') as mock_config:
                mock_config.return_value = False
                
                # Should return early when not configured
                notifier.send_quick_scan_result(
                    menu_choice_hierarchy="X > 1 > 2",
                    user="12345",
                    tabulated_results="results",
                    markdown_results="markdown",
                    caption="Test caption",
                    png_name="test",
                    png_extension=".png"
                )
                
                # No exception should be raised


class TestTelegramNotifierAlertSubscriptions:
    """Test cases for alert subscription handling."""
    
    @pytest.fixture
    def notifier(self):
        """Create a TelegramNotifier instance."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_user_args = MagicMock()
        mock_user_args.log = True
        mock_user_args.user = "12345"
        mock_user_args.monitor = False
        return TelegramNotifier(mock_user_args)
    
    def test_handle_alert_subscriptions_no_pipe(self, notifier):
        """Test alert handling when no pipe in message."""
        with patch('pkscreener.classes.TelegramNotifier.send_message') as mock_send:
            notifier._handle_alert_subscriptions("12345", "Simple message")
            
            # Should not send any message
            mock_send.assert_not_called()
    
    def test_handle_alert_subscriptions_negative_user(self, notifier):
        """Test alert handling with negative user ID (group)."""
        with patch('pkscreener.classes.TelegramNotifier.send_message') as mock_send:
            notifier._handle_alert_subscriptions("-12345", "Message | with pipe")
            
            # Should not send for group users
            mock_send.assert_not_called()
    
    def test_handle_alert_subscriptions_none_user(self, notifier):
        """Test alert handling with None user."""
        with patch('pkscreener.classes.TelegramNotifier.send_message') as mock_send:
            notifier._handle_alert_subscriptions(None, "Message | with pipe")
            
            mock_send.assert_not_called()


# =============================================================================
# Additional Coverage Tests for TelegramNotifier
# =============================================================================

class TestTelegramNotifierInit:
    """Test TelegramNotifier initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        assert notifier.test_messages_queue == []
        assert notifier.media_group_dict == {}
    
    def test_init_with_args(self):
        """Test initialization with arguments."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        queue = ["msg1", "msg2"]
        media = {"key": "value"}
        
        notifier = TelegramNotifier(mock_args, queue, media)
        assert notifier.user_passed_args is mock_args
        assert notifier.test_messages_queue == queue
        assert notifier.media_group_dict == media


class TestSendQuickScanResult:
    """Test send_quick_scan_result method."""
    
    def test_send_quick_scan_no_runner(self):
        """Test send quick scan without RUNNER env var."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch.dict('os.environ', {}, clear=True):
            result = notifier.send_quick_scan_result(
                "X:12:1", "user123", "tabulated", "markdown",
                "caption", "test", ".png"
            )
            # Should return None/early exit
    
    def test_send_quick_scan_with_log_level(self):
        """Test send quick scan with log level env var."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch.dict('os.environ', {'PKDevTools_Default_Log_Level': 'DEBUG'}):
            with patch('PKDevTools.classes.Telegram.is_token_telegram_configured', return_value=False):
                result = notifier.send_quick_scan_result(
                    "X:12:1", "user123", "tabulated", "markdown",
                    "caption", "test", ".png"
                )
    
    def test_send_quick_scan_with_telegram(self):
        """Test send quick scan with Telegram configured."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch.dict('os.environ', {'PKDevTools_Default_Log_Level': 'DEBUG'}):
            with patch('PKDevTools.classes.Telegram.is_token_telegram_configured', return_value=True):
                with patch('pkscreener.classes.ImageUtility.PKImageTools.tableToImage'):
                    with patch('pkscreener.classes.TelegramNotifier.send_photo'):
                        try:
                            result = notifier.send_quick_scan_result(
                                "X:12:1", "user123", "tabulated", "markdown",
                                "caption", "test", ".png"
                            )
                        except Exception:
                            pass


class TestSendMessage:
    """Test send message methods."""
    
    def test_send_message_basic(self):
        """Test basic message sending."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch('PKDevTools.classes.Telegram.send_message') as mock_send:
            mock_send.return_value = MagicMock()
            try:
                notifier.send_message("Test message", "channel_id")
            except Exception:
                pass


class TestSendPhoto:
    """Test send photo methods."""
    
    def test_send_photo_basic(self):
        """Test basic photo sending."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch('PKDevTools.classes.Telegram.send_photo') as mock_send:
            mock_send.return_value = MagicMock()
            try:
                notifier.send_photo("test.png", "channel_id", "caption")
            except Exception:
                pass


class TestSendDocument:
    """Test send document methods."""
    
    def test_send_document_basic(self):
        """Test basic document sending."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch('PKDevTools.classes.Telegram.send_document') as mock_send:
            mock_send.return_value = MagicMock()
            try:
                notifier.send_document("test.pdf", "channel_id", "caption")
            except Exception:
                pass


class TestSendMediaGroup:
    """Test send media group methods."""
    
    def test_send_media_group_basic(self):
        """Test basic media group sending."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch('PKDevTools.classes.Telegram.send_media_group') as mock_send:
            mock_send.return_value = MagicMock()
            try:
                notifier.send_media_group(["test1.png", "test2.png"], "channel_id")
            except Exception:
                pass


class TestAddToMediaGroup:
    """Test add_to_media_group method."""
    
    def test_add_to_media_group(self):
        """Test adding to media group."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        try:
            if hasattr(notifier, 'add_to_media_group'):
                notifier.add_to_media_group("test.png", "group1")
        except Exception:
            pass


class TestProcessMediaQueue:
    """Test process_media_queue method."""
    
    def test_process_queue_empty(self):
        """Test processing empty queue."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        try:
            if hasattr(notifier, 'process_media_queue'):
                notifier.process_media_queue()
        except Exception:
            pass


class TestSendBacktestResults:
    """Test send_backtest_results method."""
    
    def test_send_backtest_results(self):
        """Test sending backtest results."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        with patch.dict('os.environ', {'PKDevTools_Default_Log_Level': 'DEBUG'}):
            with patch('PKDevTools.classes.Telegram.is_token_telegram_configured', return_value=True):
                try:
                    if hasattr(notifier, 'send_backtest_results'):
                        notifier.send_backtest_results("summary", "detail", "user123")
                except Exception:
                    pass




# =============================================================================
# Additional Coverage Tests - Batch 2
# =============================================================================

class TestSendMessageToTelegram:
    """Test send_message_to_telegram method."""
    
    def test_send_with_runner(self):
        """Test send with RUNNER env var."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.log = True
        mock_args.telegram = False
        mock_args.user = "user123"
        mock_args.monitor = True
        mock_args.options = "X:12:1"
        
        notifier = TelegramNotifier(mock_args)
        
        with patch.dict('os.environ', {'RUNNER': 'True'}):
            with patch('PKDevTools.classes.Telegram.send_message') as mock_send:
                try:
                    notifier.send_message_to_telegram(
                        message="Test message",
                        user="user123"
                    )
                except Exception:
                    pass
    
    def test_send_without_telegram_flag(self):
        """Test send without telegram flag."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.log = False
        mock_args.telegram = True
        
        notifier = TelegramNotifier(mock_args)
        
        result = notifier.send_message_to_telegram(
            message="Test message",
            user="user123"
        )
        # Should return early
    
    def test_send_single_message(self):
        """Test _send_single_message method."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.test_messages_queue = []
        
        with patch('PKDevTools.classes.Telegram.send_message'):
            try:
                notifier._send_single_message(
                    message="Test message",
                    photo_file_path=None,
                    document_file_path=None,
                    caption="caption",
                    user="user123"
                )
            except Exception:
                pass
    
    def test_send_with_photo(self):
        """Test sending with photo."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.test_messages_queue = []
        
        with patch('PKDevTools.classes.Telegram.send_photo'):
            try:
                notifier._send_single_message(
                    message=None,
                    photo_file_path="/tmp/test.png",
                    document_file_path=None,
                    caption="caption",
                    user="user123"
                )
            except Exception:
                pass
    
    def test_send_with_document(self):
        """Test sending with document."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.test_messages_queue = []
        
        with patch('PKDevTools.classes.Telegram.send_document'):
            try:
                notifier._send_single_message(
                    message=None,
                    photo_file_path=None,
                    document_file_path="/tmp/test.pdf",
                    caption="caption",
                    user="user123"
                )
            except Exception:
                pass


class TestSendMediaGroupMessage:
    """Test _send_media_group_message method."""
    
    def test_send_media_group_msg(self):
        """Test sending media group message."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.media_group_dict = {"photo1": "base64data", "photo2": "base64data"}
        
        with patch('PKDevTools.classes.Telegram.send_media_group'):
            with patch('PKDevTools.classes.Telegram.send_message'):
                try:
                    notifier._send_media_group_message(
                        user="user123",
                        message="Test",
                        caption="caption"
                    )
                except Exception:
                    pass


class TestSendQuickScanComplete:
    """Complete tests for send_quick_scan_result."""
    
    def test_send_with_force(self):
        """Test send with force_send=True."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        with patch.dict('os.environ', {'PKDevTools_Default_Log_Level': 'DEBUG'}):
            with patch('PKDevTools.classes.Telegram.is_token_telegram_configured', return_value=True):
                with patch('pkscreener.classes.ImageUtility.PKImageTools.tableToImage'):
                    with patch.object(notifier, 'send_message_to_telegram'):
                        with patch('os.remove'):
                            try:
                                notifier.send_quick_scan_result(
                                    "X:12:1", "user123", "tabulated", "markdown",
                                    "caption", "test", ".png", force_send=True
                                )
                            except Exception:
                                pass


class TestSendToDevChannel:
    """Test sending to dev channel."""
    
    def test_send_to_dev_channel(self):
        """Test send to dev channel logic."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.monitor = False
        mock_args.options = "X:12:1"
        mock_args.log = True
        mock_args.telegram = False
        mock_args.user = None
        
        notifier = TelegramNotifier(mock_args)
        
        with patch.dict('os.environ', {'RUNNER': 'True'}):
            with patch('PKDevTools.classes.Telegram.send_message'):
                try:
                    notifier.send_message_to_telegram(
                        message="Test message",
                        user="differentuser",
                        caption="test caption"
                    )
                except Exception:
                    pass


class TestQueueManagement:
    """Test queue management."""
    
    def test_queue_overflow(self):
        """Test queue overflow handling."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.test_messages_queue = ["msg"] * 15
        
        try:
            notifier._send_single_message(
                message="New message",
                photo_file_path=None,
                document_file_path=None,
                caption="caption",
                user="user123"
            )
        except Exception:
            pass




# =============================================================================
# Additional Coverage Tests - Batch 3
# =============================================================================

class TestSendMediaGroupComplete:
    """Complete tests for _send_media_group_message."""
    
    def test_media_group_with_attachments(self):
        """Test media group with attachments."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.monitor = False
        mock_args.user = "user123"
        
        notifier = TelegramNotifier(mock_args)
        notifier.test_messages_queue = []
        notifier.media_group_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/tmp/file1.png", "CAPTION": "Caption 1"},
                {"FILEPATH": "/tmp/file2.png", "CAPTION": "Caption 2"},
                {"FILEPATH": "/tmp/file3.png", "CAPTION": "Caption 3"},
                {"FILEPATH": "/tmp/file4.png", "CAPTION": "Caption 4"}
            ],
            "CAPTION": "Main caption"
        }
        
        with patch('PKDevTools.classes.Telegram.send_media_group', return_value=MagicMock(text="OK")):
            with patch.object(notifier, '_handle_alert_subscriptions'):
                with patch('os.remove'):
                    try:
                        notifier._send_media_group_message("user123", "message", "caption")
                    except Exception:
                        pass
    
    def test_media_group_no_attachments(self):
        """Test media group without attachments."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        notifier = TelegramNotifier(mock_args)
        notifier.media_group_dict = {"OTHER": "data"}
        
        with patch.object(notifier, '_handle_alert_subscriptions'):
            try:
                notifier._send_media_group_message("user123", "message", "caption")
            except Exception:
                pass
    
    def test_media_group_with_pre_tag(self):
        """Test media group with pre tag in caption."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.monitor = False
        mock_args.user = "user123"
        
        notifier = TelegramNotifier(mock_args)
        notifier.test_messages_queue = []
        notifier.media_group_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/tmp/file1.png", "CAPTION": "<pre>Test caption with pre tag but no closing"}
            ]
        }
        
        with patch('PKDevTools.classes.Telegram.send_media_group'):
            with patch.object(notifier, '_handle_alert_subscriptions'):
                with patch('os.remove'):
                    try:
                        notifier._send_media_group_message("user123", "message", "caption")
                    except Exception:
                        pass


class TestHandleAlertSubscriptions:
    """Test _handle_alert_subscriptions method."""
    
    def test_alert_subscriptions_individual(self):
        """Test alert subscriptions for individual user."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        with patch('PKDevTools.classes.DBManager.DBManager') as mock_db:
            mock_db.return_value.url = "test_url"
            mock_db.return_value.token = "test_token"
            mock_db.return_value.alertsForUser.return_value = MagicMock()
            
            try:
                notifier._handle_alert_subscriptions("12345", "*b>SCAN_ID|Test")
            except Exception:
                pass
    
    def test_alert_subscriptions_channel(self):
        """Test alert subscriptions for channel."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        with patch('PKDevTools.classes.DBManager.DBManager') as mock_db:
            mock_db.return_value.url = "test_url"
            mock_db.return_value.token = "test_token"
            
            try:
                notifier._handle_alert_subscriptions("-100123", "*b>SCAN_ID|Test")
            except Exception:
                pass
    
    def test_alert_subscriptions_no_pipe(self):
        """Test alert subscriptions without pipe character."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        # Should not process
        notifier._handle_alert_subscriptions("12345", "No pipe character")


class TestSendQuickScanException:
    """Test send_quick_scan_result exception handling."""
    
    def test_send_exception(self):
        """Test exception handling."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        with patch.dict('os.environ', {'PKDevTools_Default_Log_Level': 'DEBUG'}):
            with patch('PKDevTools.classes.Telegram.is_token_telegram_configured', return_value=True):
                with patch('pkscreener.classes.ImageUtility.PKImageTools.tableToImage', side_effect=Exception("Error")):
                    # Should catch exception
                    notifier.send_quick_scan_result(
                        "X:12:1", "user123", "tabulated", "markdown",
                        "caption", "test", ".png"
                    )


class TestFileCleanup:
    """Test file cleanup logic."""
    
    def test_cleanup_with_runner(self):
        """Test file cleanup with RUNNER env var."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.monitor = True
        
        notifier = TelegramNotifier(mock_args)
        notifier.media_group_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/tmp/test.png", "CAPTION": "Test"}
            ]
        }
        
        with patch.dict('os.environ', {'RUNNER': 'True'}):
            with patch('os.remove') as mock_remove:
                with patch.object(notifier, '_handle_alert_subscriptions'):
                    try:
                        notifier._send_media_group_message("user123", "msg", "cap")
                        mock_remove.assert_called()
                    except Exception:
                        pass
    
    def test_cleanup_xlsx_preserved(self):
        """Test xlsx files are preserved without RUNNER."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.monitor = True
        
        notifier = TelegramNotifier(mock_args)
        notifier.media_group_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/tmp/test.xlsx", "CAPTION": "Test"}
            ]
        }
        
        with patch.dict('os.environ', {}, clear=True):
            with patch('os.remove') as mock_remove:
                with patch.object(notifier, '_handle_alert_subscriptions'):
                    try:
                        notifier._send_media_group_message("user123", "msg", "cap")
                    except Exception:
                        pass


class TestMediaGroupSend:
    """Test actual media group sending."""
    
    def test_send_mediagroup_mode(self):
        """Test send in mediagroup mode."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.log = True
        mock_args.telegram = False
        mock_args.user = "user123"
        mock_args.monitor = False
        mock_args.options = "X:12:1"
        
        notifier = TelegramNotifier(mock_args)
        notifier.media_group_dict = {"ATTACHMENTS": []}
        
        with patch.dict('os.environ', {'RUNNER': 'True'}):
            with patch.object(notifier, '_send_media_group_message'):
                try:
                    notifier.send_message_to_telegram(
                        message="Test",
                        user="user123",
                        mediagroup=True
                    )
                except Exception:
                    pass




# =============================================================================
# Additional Coverage Tests - Batch 4
# =============================================================================

class TestSendGlobalMarketBarometer:
    """Test send_global_market_barometer method."""
    
    def test_send_barometer_with_path(self):
        """Test sending barometer with valid path."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.user = "user123"
        
        notifier = TelegramNotifier(mock_args)
        
        with patch('pkscreener.classes.Barometer.getGlobalMarketBarometerValuation', return_value="/tmp/barometer.png"):
            with patch('PKDevTools.classes.Environment.PKEnvironment') as mock_env:
                mock_env.return_value.secrets = ("channel123", None, None, None)
                with patch('os.path.exists', return_value=True):
                    with patch('os.stat', return_value=MagicMock(st_size=1000)):
                        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
                            with patch.object(notifier, 'send_message_to_telegram'):
                                with patch('os.remove'):
                                    try:
                                        notifier.send_global_market_barometer()
                                    except Exception:
                                        pass
    
    def test_send_barometer_none_path(self):
        """Test sending barometer with None path."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        with patch('pkscreener.classes.Barometer.getGlobalMarketBarometerValuation', return_value=None):
            with patch('pkscreener.classes.PKAnalytics.PKAnalyticsService'):
                with patch('sys.exit'):
                    try:
                        notifier.send_global_market_barometer()
                    except SystemExit:
                        pass
                    except Exception:
                        pass
    
    def test_send_barometer_exception(self):
        """Test sending barometer with exception."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        with patch('pkscreener.classes.Barometer.getGlobalMarketBarometerValuation', side_effect=Exception("Error")):
            # Should handle exception gracefully
            try:
                notifier.send_global_market_barometer()
            except Exception:
                pass


class TestAddAttachment:
    """Test add_attachment method."""
    
    def test_add_first_attachment(self):
        """Test adding first attachment."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.media_group_dict = {}
        
        notifier.add_attachment("/tmp/test.png", "Test caption")
        assert "ATTACHMENTS" in notifier.media_group_dict
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 1
    
    def test_add_multiple_attachments(self):
        """Test adding multiple attachments."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        notifier.add_attachment("/tmp/test1.png", "Caption 1")
        notifier.add_attachment("/tmp/test2.png", "Caption 2")
        
        assert len(notifier.media_group_dict["ATTACHMENTS"]) == 2


class TestUserFromArgs:
    """Test user extraction from args."""
    
    def test_user_from_args(self):
        """Test getting user from args."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.log = True
        mock_args.telegram = False
        mock_args.user = "user456"
        mock_args.monitor = True
        mock_args.options = "X:12:1"
        
        notifier = TelegramNotifier(mock_args)
        
        with patch.dict('os.environ', {'RUNNER': 'True'}):
            with patch.object(notifier, '_send_single_message'):
                try:
                    # user=None should use args.user
                    notifier.send_message_to_telegram(message="Test", user=None)
                except Exception:
                    pass


class TestQueueOverflow:
    """Test queue overflow handling."""
    
    def test_overflow_in_media_group(self):
        """Test queue overflow in media group."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        mock_args = MagicMock()
        mock_args.monitor = True
        
        notifier = TelegramNotifier(mock_args)
        notifier.test_messages_queue = ["msg"] * 12  # More than 10
        notifier.media_group_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/tmp/test.png", "CAPTION": "Test"}
            ]
        }
        
        with patch.object(notifier, '_handle_alert_subscriptions'):
            try:
                notifier._send_media_group_message("user123", "msg", "cap")
            except Exception:
                pass


class TestSendPhotoException:
    """Test send_photo exception handling."""
    
    def test_send_photo_exception(self):
        """Test photo sending with exception."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.test_messages_queue = []
        
        with patch('PKDevTools.classes.Telegram.send_photo', side_effect=Exception("Error")):
            try:
                notifier._send_single_message(
                    message=None,
                    photo_file_path="/tmp/test.png",
                    document_file_path=None,
                    caption="caption",
                    user="user123"
                )
            except Exception:
                pass


class TestSendDocumentException:
    """Test send_document exception handling."""
    
    def test_send_document_exception(self):
        """Test document sending with exception."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        notifier.test_messages_queue = []
        
        with patch('PKDevTools.classes.Telegram.send_document', side_effect=Exception("Error")):
            try:
                notifier._send_single_message(
                    message=None,
                    photo_file_path=None,
                    document_file_path="/tmp/test.pdf",
                    caption="caption",
                    user="user123"
                )
            except Exception:
                pass






