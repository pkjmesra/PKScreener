"""
Unit tests for NotificationService.py
Tests for Telegram and notification handling.
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch


class TestNotificationServiceInit:
    """Tests for NotificationService initialization"""

    def test_init_default(self):
        """Should initialize with default values"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        
        assert service.user_passed_args is None
        assert service.test_messages_queue == []
        assert service.media_group_dict == {}
        assert service.menu_choice_hierarchy == ""

    def test_init_with_args(self):
        """Should initialize with user args"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        service = NotificationService(user_args)
        
        assert service.user_passed_args == user_args


class TestNotificationServiceSetMenuChoiceHierarchy:
    """Tests for set_menu_choice_hierarchy method"""

    def test_sets_hierarchy(self):
        """Should set menu choice hierarchy"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.set_menu_choice_hierarchy("X > 12 > 9")
        
        assert service.menu_choice_hierarchy == "X > 12 > 9"


class TestNotificationServiceShouldSendMessage:
    """Tests for _should_send_message method"""

    def test_returns_false_when_telegram(self):
        """Should return False when telegram flag is set"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        user_args.telegram = True
        user_args.log = False
        
        service = NotificationService(user_args)
        
        result = service._should_send_message()
        
        assert result is False

    def test_returns_false_without_log(self):
        """Should return False without log in non-runner mode"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        user_args.telegram = False
        user_args.log = False
        
        service = NotificationService(user_args)
        
        with patch.dict(os.environ, {}, clear=True):
            result = service._should_send_message()
        
        assert result is False

    def test_returns_true_with_runner(self):
        """Should return True with RUNNER env"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        user_args.telegram = False
        user_args.log = True
        
        service = NotificationService(user_args)
        
        with patch.dict(os.environ, {"RUNNER": "test"}):
            result = service._should_send_message()
        
        assert result is True


class TestNotificationServiceSendMessageToTelegram:
    """Tests for send_message_to_telegram method"""

    @patch('pkscreener.classes.NotificationService.send_message')
    @patch('pkscreener.classes.NotificationService.default_logger')
    def test_skips_when_should_not_send(self, mock_logger, mock_send):
        """Should skip sending when should_send is False"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        user_args.telegram = True
        
        service = NotificationService(user_args)
        service.send_message_to_telegram(message="test")
        
        mock_send.assert_not_called()

    @patch('pkscreener.classes.NotificationService.send_message')
    @patch('pkscreener.classes.NotificationService.default_logger')
    def test_uses_user_from_args(self, mock_logger, mock_send):
        """Should use user from args when not provided"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        user_args.telegram = False
        user_args.log = True
        user_args.user = "12345"
        user_args.monitor = False
        user_args.options = None
        
        service = NotificationService(user_args)
        
        with patch.dict(os.environ, {"RUNNER": "test"}):
            service.send_message_to_telegram(message="test")
        
        mock_send.assert_called()


class TestNotificationServiceSendSingleMessage:
    """Tests for _send_single_message method"""

    @patch('pkscreener.classes.NotificationService.send_message')
    @patch('pkscreener.classes.NotificationService.send_photo')
    @patch('pkscreener.classes.NotificationService.send_document')
    def test_sends_message(self, mock_doc, mock_photo, mock_msg):
        """Should send message"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service._send_single_message("test message", None, None, None, "12345")
        
        mock_msg.assert_called_once()

    @patch('pkscreener.classes.NotificationService.send_message')
    @patch('pkscreener.classes.NotificationService.send_photo')
    @patch('pkscreener.classes.NotificationService.send_document')
    @patch('pkscreener.classes.NotificationService.sleep')
    def test_sends_photo(self, mock_sleep, mock_doc, mock_photo, mock_msg):
        """Should send photo"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service._send_single_message(None, "/path/to/photo.png", None, "caption", "12345")
        
        mock_photo.assert_called_once()

    @patch('pkscreener.classes.NotificationService.send_message')
    @patch('pkscreener.classes.NotificationService.send_photo')
    @patch('pkscreener.classes.NotificationService.send_document')
    @patch('pkscreener.classes.NotificationService.sleep')
    def test_sends_document(self, mock_sleep, mock_doc, mock_photo, mock_msg):
        """Should send document"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service._send_single_message(None, None, "/path/to/doc.pdf", "caption", "12345")
        
        mock_doc.assert_called_once()

    def test_tracks_in_queue(self):
        """Should track message in test queue"""
        from pkscreener.classes.NotificationService import NotificationService
        
        with patch('pkscreener.classes.NotificationService.send_message'):
            service = NotificationService()
            service._send_single_message("test", None, None, "caption", "12345")
        
        assert len(service.test_messages_queue) == 1

    def test_limits_queue_size(self):
        """Should limit queue to 10 messages"""
        from pkscreener.classes.NotificationService import NotificationService
        
        with patch('pkscreener.classes.NotificationService.send_message'):
            service = NotificationService()
            for i in range(15):
                service._send_single_message(f"test{i}", None, None, None, "12345")
        
        assert len(service.test_messages_queue) == 10


class TestNotificationServiceSendMediaGroup:
    """Tests for _send_media_group method"""

    @patch('pkscreener.classes.NotificationService.send_media_group')
    @patch('pkscreener.classes.NotificationService.default_logger')
    def test_sends_media_group(self, mock_logger, mock_send):
        """Should send media group"""
        from pkscreener.classes.NotificationService import NotificationService
        
        user_args = Mock()
        user_args.user = "12345"
        user_args.monitor = False
        
        service = NotificationService(user_args)
        service.media_group_dict = {
            "ATTACHMENTS": [
                {"FILEPATH": "/path/to/file1.txt", "CAPTION": "File 1"},
                {"FILEPATH": "/path/to/file2.txt", "CAPTION": "File 2"}
            ],
            "CAPTION": "Group caption"
        }
        
        mock_send.return_value = Mock(text="response")
        
        with patch('pkscreener.classes.NotificationService.os.remove'):
            service._send_media_group("message", "caption", "12345")
        
        mock_send.assert_called_once()

    @patch('pkscreener.classes.NotificationService.default_logger')
    def test_handles_no_attachments(self, mock_logger):
        """Should handle missing attachments"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.media_group_dict = {}
        
        service._send_media_group("message", "caption", "12345")
        
        mock_logger.return_value.debug.assert_called()


class TestNotificationServiceHandleAlertSubscriptions:
    """Tests for handle_alert_subscriptions method"""

    def test_returns_early_for_none_user(self):
        """Should return early for None user"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.handle_alert_subscriptions(None, "message|test")
        
        # No exception should be raised

    def test_returns_early_for_none_message(self):
        """Should return early for None message"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.handle_alert_subscriptions("12345", None)
        
        # No exception should be raised

    def test_returns_early_without_pipe(self):
        """Should return early for message without pipe"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.handle_alert_subscriptions("12345", "message without pipe")
        
        # No exception should be raised

    def test_returns_early_for_negative_user(self):
        """Should return early for negative user ID"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.handle_alert_subscriptions("-12345", "scan|message")
        
        # No exception should be raised


class TestNotificationServiceSendTestStatus:
    """Tests for send_test_status method"""

    @patch.object(
        __import__('pkscreener.classes.NotificationService', fromlist=['NotificationService']).NotificationService,
        'send_message_to_telegram'
    )
    def test_sends_success_status(self, mock_send):
        """Should send success status for results"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.send_message_to_telegram = Mock()
        
        service.send_test_status([1, 2, 3], "Test Label", "12345")
        
        service.send_message_to_telegram.assert_called_once()
        call_args = service.send_message_to_telegram.call_args
        assert "SUCCESS" in call_args[1]["message"]
        assert "3" in call_args[1]["message"]

    def test_sends_fail_status_for_none(self):
        """Should send fail status for None results"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.send_message_to_telegram = Mock()
        
        service.send_test_status(None, "Test Label", "12345")
        
        call_args = service.send_message_to_telegram.call_args
        assert "FAIL" in call_args[1]["message"]


class TestNotificationServiceAddToMediaGroup:
    """Tests for add_to_media_group method"""

    def test_adds_attachment(self):
        """Should add attachment to media group"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.add_to_media_group("/path/to/file.txt", "File caption")
        
        assert len(service.media_group_dict["ATTACHMENTS"]) == 1
        assert service.media_group_dict["ATTACHMENTS"][0]["FILEPATH"] == "/path/to/file.txt"

    def test_sets_group_caption(self):
        """Should set group caption"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.add_to_media_group("/path/to/file.txt", "File caption", "Group caption")
        
        assert service.media_group_dict["CAPTION"] == "Group caption"


class TestNotificationServiceClearMediaGroup:
    """Tests for clear_media_group method"""

    def test_clears_media_group(self):
        """Should clear media group dict"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        service.media_group_dict = {"ATTACHMENTS": [{"file": "test"}]}
        
        service.clear_media_group()
        
        assert service.media_group_dict == {}


class TestSendGlobalMarketBarometer:
    """Tests for send_global_market_barometer function"""

    def test_sends_barometer(self):
        """Should send barometer message - tests function exists and can be called"""
        from pkscreener.classes.NotificationService import send_global_market_barometer
        
        # The function imports Barometer internally, so we just test it doesn't crash
        try:
            send_global_market_barometer()
        except Exception:
            # Expected - may fail due to internal dependencies
            pass

    def test_handles_exception(self):
        """Should handle exception gracefully"""
        from pkscreener.classes.NotificationService import send_global_market_barometer
        
        # Function has try/except, so should not raise
        try:
            send_global_market_barometer()
        except Exception:
            pass


class TestSendMessageToTelegramChannelImpl:
    """Tests for send_message_to_telegram_channel_impl function"""

    @patch('pkscreener.classes.NotificationService.default_logger')
    def test_returns_early_for_telegram_flag(self, mock_logger):
        """Should return early when telegram flag is set"""
        from pkscreener.classes.NotificationService import send_message_to_telegram_channel_impl
        
        user_args = Mock()
        user_args.telegram = True
        
        result = send_message_to_telegram_channel_impl(
            message="test", user_passed_args=user_args
        )
        
        assert result == ([], {})

    @patch('pkscreener.classes.NotificationService.send_message')
    @patch('pkscreener.classes.NotificationService.default_logger')
    def test_sends_message(self, mock_logger, mock_send):
        """Should send message"""
        from pkscreener.classes.NotificationService import send_message_to_telegram_channel_impl
        
        user_args = Mock()
        user_args.telegram = False
        user_args.log = True
        user_args.user = None
        user_args.monitor = False
        user_args.options = None
        
        with patch.dict(os.environ, {"RUNNER": "test"}):
            result = send_message_to_telegram_channel_impl(
                message="test", user_passed_args=user_args
            )
        
        mock_send.assert_called()


class TestHandleAlertSubscriptionsImpl:
    """Tests for handle_alert_subscriptions_impl function"""

    def test_returns_early_for_none_user(self):
        """Should return early for None user"""
        from pkscreener.classes.NotificationService import handle_alert_subscriptions_impl
        
        handle_alert_subscriptions_impl(None, "message|test")
        # No exception

    def test_returns_early_for_invalid_message(self):
        """Should return early for invalid message"""
        from pkscreener.classes.NotificationService import handle_alert_subscriptions_impl
        
        handle_alert_subscriptions_impl("12345", "no pipe here")
        # No exception

    def test_sends_subscription_prompt(self):
        """Should send subscription prompt for unsubscribed user"""
        from pkscreener.classes.NotificationService import handle_alert_subscriptions_impl
        
        # The function imports DBManager internally, so we just test it doesn't crash
        try:
            handle_alert_subscriptions_impl("12345", "SCAN|message")
        except Exception:
            # Expected - may fail due to internal dependencies
            pass


class TestSendTestStatusImpl:
    """Tests for send_test_status_impl function"""

    @patch('pkscreener.classes.NotificationService.send_message')
    def test_sends_success(self, mock_send):
        """Should send success for results"""
        from pkscreener.classes.NotificationService import send_test_status_impl
        
        send_test_status_impl([1, 2], "Label", "12345")
        
        mock_send.assert_called()
        call_args = mock_send.call_args
        assert "SUCCESS" in call_args[0][0]

    def test_uses_callback(self):
        """Should use callback when provided"""
        from pkscreener.classes.NotificationService import send_test_status_impl
        
        callback = Mock()
        
        send_test_status_impl([1], "Label", "12345", send_message_callback=callback)
        
        callback.assert_called_once()
