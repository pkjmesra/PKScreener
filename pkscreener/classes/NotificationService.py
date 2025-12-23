"""
NotificationService - Telegram and notification handling for PKScreener

This module handles:
- Sending messages to Telegram channels
- Sending photos and documents
- Media group handling
- Alert subscriptions
"""

import os
from time import sleep
from typing import Any, Dict, List, Optional

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
    send_photo,
    send_media_group
)


DEV_CHANNEL_ID = "-1001785195297"


class NotificationService:
    """
    Handles notifications and messaging for PKScreener.
    
    This class encapsulates the notification logic that was previously
    scattered in globals.py.
    """
    
    def __init__(self, user_passed_args=None):
        self.user_passed_args = user_passed_args
        self.test_messages_queue: List[str] = []
        self.media_group_dict: Dict[str, Any] = {}
        self.menu_choice_hierarchy = ""
    
    def set_menu_choice_hierarchy(self, hierarchy: str):
        """Set the menu choice hierarchy for messages"""
        self.menu_choice_hierarchy = hierarchy
    
    def send_message_to_telegram(
        self,
        message: Optional[str] = None,
        photo_file_path: Optional[str] = None,
        document_file_path: Optional[str] = None,
        caption: Optional[str] = None,
        user: Optional[str] = None,
        mediagroup: bool = False
    ):
        """
        Send message to Telegram channel or user.
        
        Args:
            message: Text message to send
            photo_file_path: Path to photo file
            document_file_path: Path to document file
            caption: Caption for photo/document
            user: User ID to send to
            mediagroup: Whether to send as media group
        """
        default_logger().debug(
            f"Received message:{message}, caption:{caption}, "
            f"for user: {user} with mediagroup:{mediagroup}"
        )
        
        # Check if we should send
        if not self._should_send_message():
            return
        
        if user is None and self.user_passed_args and self.user_passed_args.user:
            user = self.user_passed_args.user
        
        if not mediagroup:
            self._send_single_message(message, photo_file_path, document_file_path, caption, user)
        else:
            self._send_media_group(message, caption, user)
        
        # Notify dev channel
        if user is not None:
            self._notify_dev_channel(user, caption, message)
    
    def _should_send_message(self) -> bool:
        """Check if message should be sent"""
        if self.user_passed_args and self.user_passed_args.telegram:
            return False
        
        if "RUNNER" not in os.environ.keys():
            if self.user_passed_args and not self.user_passed_args.log:
                return False
        
        return True
    
    def _send_single_message(
        self,
        message: Optional[str],
        photo_file_path: Optional[str],
        document_file_path: Optional[str],
        caption: Optional[str],
        user: Optional[str]
    ):
        """Send a single message (not media group)"""
        # Track in test queue
        self.test_messages_queue.append(
            f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_file_path}"
        )
        if len(self.test_messages_queue) > 10:
            self.test_messages_queue.pop(0)
        
        # Clean caption
        if user is not None and caption is not None:
            caption = f"{caption.replace('&', 'n')}."
        
        # Send message
        if message is not None:
            try:
                cleaned_message = message.replace("&", "n").replace("<", "*")
                send_message(cleaned_message, userID=user)
            except Exception as e:
                default_logger().debug(e, exc_info=True)
        else:
            message = ""
        
        # Send photo
        if photo_file_path is not None:
            try:
                cleaned_caption = f"{caption.replace('&', 'n')}" if caption else ""
                send_photo(
                    photo_file_path, 
                    cleaned_caption[:1024] if cleaned_caption else "", 
                    userID=user
                )
                sleep(2)  # Rate limiting
            except Exception as e:
                default_logger().debug(e, exc_info=True)
        
        # Send document
        if document_file_path is not None:
            try:
                cleaned_caption = f"{caption.replace('&', 'n')}" if isinstance(caption, str) else ""
                send_document(
                    document_file_path,
                    cleaned_caption[:1024] if cleaned_caption else "",
                    userID=user
                )
                sleep(2)  # Rate limiting
            except Exception as e:
                default_logger().debug(e, exc_info=True)
    
    def _send_media_group(
        self,
        message: Optional[str],
        caption: Optional[str],
        user: Optional[str]
    ):
        """Send a media group"""
        file_paths = []
        file_captions = []
        
        if "ATTACHMENTS" in self.media_group_dict:
            attachments = self.media_group_dict["ATTACHMENTS"]
            num_files = len(attachments)
            
            if num_files >= 4:
                self.media_group_dict["ATTACHMENTS"] = []
            
            for attachment in attachments:
                file_paths.append(attachment["FILEPATH"])
                clean_caption = attachment["CAPTION"].replace('&', 'n')[:1024]
                if "<pre>" in clean_caption and "</pre>" not in clean_caption:
                    clean_caption = f"{clean_caption[:1018]}</pre>"
                file_captions.append(clean_caption)
            
            # Track in test queue
            if file_paths:
                self.test_messages_queue.append(
                    f"message:{file_captions[-1]}\ncaption:{file_captions[-1]}\n"
                    f"user:{user}\ndocument:{file_paths[-1]}"
                )
                if len(self.test_messages_queue) > 10:
                    self.test_messages_queue.pop(0)
            
            # Send media group
            if file_paths and self.user_passed_args and not self.user_passed_args.monitor:
                resp = send_media_group(
                    user=self.user_passed_args.user,
                    png_paths=[],
                    png_album_caption=None,
                    file_paths=file_paths,
                    file_captions=file_captions
                )
                if resp is not None:
                    default_logger().debug(resp.text, exc_info=True)
            
            caption = f"{len(file_captions)} files sent!"
            message = self.media_group_dict.get("CAPTION", "-").replace('&', 'n').replace("<", "*")[:1024]
            
            default_logger().debug(
                f"Received updated message:{message}, caption:{caption}, "
                f"for user: {user} with mediagroup:True"
            )
        else:
            default_logger().debug(
                f"No ATTACHMENTS in media_group_dict: {self.media_group_dict.keys()}"
            )
        
        # Cleanup files
        for f in file_paths:
            try:
                if "RUNNER" in os.environ.keys():
                    os.remove(f)
                elif not f.endswith("xlsx"):
                    os.remove(f)
            except Exception:
                pass
        
        # Handle subscriptions
        self.handle_alert_subscriptions(user, message)
    
    def _notify_dev_channel(
        self,
        user: str,
        caption: Optional[str],
        message: Optional[str]
    ):
        """Notify dev channel about user interaction"""
        if str(user) != str(DEV_CHANNEL_ID):
            if self.user_passed_args and not self.user_passed_args.monitor:
                options = self.user_passed_args.options.replace(':D', '') if self.user_passed_args.options else ""
                send_message(
                    f"Responded back to userId:{user} with {caption}.{message} [{options}]",
                    userID=DEV_CHANNEL_ID,
                )
    
    def handle_alert_subscriptions(self, user: Optional[str], message: Optional[str]):
        """
        Handle user subscriptions to automated alerts.
        
        Case 1: If user is not subscribed, prompt to subscribe
        Case 2: If user is already subscribed, inform them
        """
        if user is None or message is None or "|" not in str(message):
            return
        
        try:
            user_id = int(user)
            if user_id <= 0:
                return
            
            scan_id = message.split("|")[0].replace("*b>", "").strip()
            
            from PKDevTools.classes.DBManager import DBManager
            db_manager = DBManager()
            
            if db_manager.url is None or db_manager.token is None:
                return
            
            alert_user = db_manager.alertsForUser(user_id)
            
            # Case 1: Not subscribed
            if (alert_user is None or 
                len(alert_user.scannerJobs) == 0 or 
                str(scan_id) not in alert_user.scannerJobs):
                
                price = '40' if str(scan_id).upper().startswith('P') else '31'
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": "Yes! Subscribe", "callback_data": f"SUB_{scan_id}"}]
                    ],
                }
                send_message(
                    message=(
                        f"🔴 <b>Please check your current alerts, balance and subscriptions "
                        f"using /OTP before subscribing for alerts</b>.🔴 "
                        f"If you are not already subscribed to this alert, would you like to "
                        f"subscribe to this ({scan_id}) automated scan alert for a day during "
                        f"market hours (NSE - IST timezone)? You will need to pay ₹ {price} "
                        f"(One time) for automated alerts to {scan_id} all day on the day of "
                        f"subscription. 🔴 If you say <b>Yes</b>, the corresponding charges "
                        f"will be deducted from your alerts balance!🔴"
                    ),
                    userID=user_id,
                    reply_markup=reply_markup
                )
            
            # Case 2: Already subscribed
            elif (alert_user is not None and 
                  len(alert_user.scannerJobs) > 0 and 
                  str(scan_id) in alert_user.scannerJobs):
                
                send_message(
                    message=(
                        f"Thank you for subscribing to (<b>{scan_id}</b>) automated scan alert! "
                        f"We truly hope you are enjoying the alerts! You will continue to receive "
                        f"alerts for the duration of NSE Market hours for today. "
                        f"For any feedback, drop a note to @ItsOnlyPK."
                    ),
                    userID=user_id,
                )
                
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    def send_test_status(
        self,
        screen_results,
        label: str,
        user: Optional[str] = None
    ):
        """Send test status message"""
        result_count = len(screen_results) if screen_results is not None else 0
        status = "<b>SUCCESS</b>" if result_count >= 1 else "<b>FAIL</b>"
        
        self.send_message_to_telegram(
            message=f"{status}: Found {result_count} Stocks for {label}",
            user=user
        )
    
    def add_to_media_group(
        self,
        file_path: str,
        caption: str,
        group_caption: Optional[str] = None
    ):
        """Add file to media group for batch sending"""
        if "ATTACHMENTS" not in self.media_group_dict:
            self.media_group_dict["ATTACHMENTS"] = []
        
        self.media_group_dict["ATTACHMENTS"].append({
            "FILEPATH": file_path,
            "CAPTION": caption
        })
        
        if group_caption:
            self.media_group_dict["CAPTION"] = group_caption
    
    def clear_media_group(self):
        """Clear media group"""
        self.media_group_dict = {}


def send_global_market_barometer(user_args=None):
    """Send global market barometer information"""
    from pkscreener.classes.Barometer import Barometer
    
    try:
        barometer = Barometer()
        message = barometer.getGlobalMarketBarometer()
        
        if message:
            notification_service = NotificationService(user_args)
            notification_service.send_message_to_telegram(message=message)
            
    except Exception as e:
        default_logger().debug(e, exc_info=True)


def send_message_to_telegram_channel_impl(
    message=None,
    photo_file_path=None,
    document_file_path=None,
    caption=None,
    user=None,
    mediagroup=False,
    user_passed_args=None,
    test_messages_queue=None,
    media_group_dict=None,
    menu_choice_hierarchy=""
):
    """
    Implementation of sendMessageToTelegramChannel for delegation from globals.py.
    
    This function provides a procedural interface to the NotificationService class,
    allowing globals.py to delegate to it while passing global state as arguments.
    
    Returns:
        tuple: Updated (test_messages_queue, media_group_dict) for globals to update
    """
    if test_messages_queue is None:
        test_messages_queue = []
    if media_group_dict is None:
        media_group_dict = {}
    
    default_logger().debug(
        f"Received message:{message}, caption:{caption}, "
        f"for user: {user} with mediagroup:{mediagroup}"
    )
    
    # Check if we should send
    should_send = True
    if ("RUNNER" not in os.environ.keys() and 
        (user_passed_args is not None and not user_passed_args.log)) or \
       (user_passed_args is not None and user_passed_args.telegram):
        return test_messages_queue, media_group_dict
    
    if user is None and user_passed_args is not None and user_passed_args.user is not None:
        user = user_passed_args.user
    
    if not mediagroup:
        # Track in test queue
        if test_messages_queue is not None:
            test_messages_queue.append(
                f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_file_path}"
            )
            if len(test_messages_queue) > 10:
                test_messages_queue.pop(0)
        
        # Clean caption
        if user is not None and caption is not None:
            caption = f"{caption.replace('&', 'n')}."
        
        # Send message
        if message is not None:
            try:
                cleaned_message = message.replace("&", "n").replace("<", "*")
                send_message(cleaned_message, userID=user)
            except Exception as e:
                default_logger().debug(e, exc_info=True)
        else:
            message = ""
        
        # Send photo
        if photo_file_path is not None:
            try:
                cleaned_caption = f"{caption.replace('&', 'n')}" if caption else ""
                send_photo(
                    photo_file_path, 
                    cleaned_caption[:1024] if cleaned_caption else "", 
                    userID=user
                )
                sleep(2)  # Rate limiting
            except Exception as e:
                default_logger().debug(e, exc_info=True)
        
        # Send document
        if document_file_path is not None:
            try:
                cleaned_caption = f"{caption.replace('&', 'n')}" if isinstance(caption, str) else ""
                send_document(
                    document_file_path,
                    cleaned_caption[:1024] if cleaned_caption else "",
                    userID=user
                )
                sleep(2)  # Rate limiting
            except Exception as e:
                default_logger().debug(e, exc_info=True)
    
    else:  # Media group message
        file_paths = []
        file_captions = []
        
        if "ATTACHMENTS" in media_group_dict.keys():
            attachments = media_group_dict["ATTACHMENTS"]
            num_files = len(attachments)
            
            if num_files >= 4:
                media_group_dict["ATTACHMENTS"] = []
            
            for attachment in attachments:
                file_paths.append(attachment["FILEPATH"])
                clean_caption = attachment["CAPTION"].replace('&', 'n')[:1024]
                if "<pre>" in clean_caption and "</pre>" not in clean_caption:
                    clean_caption = f"{clean_caption[:1018]}</pre>"
                file_captions.append(clean_caption)
            
            # Track in test queue
            if test_messages_queue is not None and len(file_paths) > 0:
                test_messages_queue.append(
                    f"message:{file_captions[-1]}\ncaption:{file_captions[-1]}\n"
                    f"user:{user}\ndocument:{file_paths[-1]}"
                )
                if len(test_messages_queue) > 10:
                    test_messages_queue.pop(0)
            
            # Send media group
            if len(file_paths) > 0 and user_passed_args is not None and not user_passed_args.monitor:
                resp = send_media_group(
                    user=user_passed_args.user,
                    png_paths=[],
                    png_album_caption=None,
                    file_paths=file_paths,
                    file_captions=file_captions
                )
                if resp is not None:
                    default_logger().debug(resp.text, exc_info=True)
            
            caption = f"{len(file_captions)} files sent!"
            message = media_group_dict.get("CAPTION", "-").replace('&', 'n').replace("<", "*")[:1024]
            
            default_logger().debug(
                f"Received updated message:{message}, caption:{caption}, "
                f"for user: {user} with mediagroup:True"
            )
        else:
            default_logger().debug(
                f"No ATTACHMENTS in media_group_dict: {media_group_dict.keys()}\n"
                f"Received updated message:{message}, caption:{caption}, "
                f"for user: {user} with mediagroup:{mediagroup}"
            )
        
        # Cleanup files
        for f in file_paths:
            try:
                if "RUNNER" in os.environ.keys():
                    os.remove(f)
                elif not f.endswith("xlsx"):
                    os.remove(f)
            except Exception:
                pass
        
        # Handle subscriptions
        handle_alert_subscriptions_impl(user, message)
    
    # Notify dev channel
    if user is not None:
        if str(user) != str(DEV_CHANNEL_ID) and user_passed_args is not None and not user_passed_args.monitor:
            options = user_passed_args.options.replace(':D', '') if user_passed_args.options else ""
            send_message(
                f"Responded back to userId:{user} with {caption}.{message} [{options}]",
                userID=DEV_CHANNEL_ID,
            )
    
    return test_messages_queue, media_group_dict


def handle_alert_subscriptions_impl(user, message):
    """
    Implementation of handleAlertSubscriptions for delegation from globals.py.
    
    Handles user subscriptions to automated alerts for a given scan type/category.
    Case 1: If user is not subscribed, prompt to subscribe
    Case 2: If user is already subscribed, inform them
    """
    if user is None or message is None or "|" not in str(message):
        return
    
    try:
        user_id = int(user)
        if user_id <= 0:
            return
        
        scan_id = message.split("|")[0].replace("*b>", "").strip()
        
        from PKDevTools.classes.DBManager import DBManager
        db_manager = DBManager()
        
        if db_manager.url is None or db_manager.token is None:
            return
        
        alert_user = db_manager.alertsForUser(user_id)
        
        # Case 1: Not subscribed
        if (alert_user is None or 
            len(alert_user.scannerJobs) == 0 or 
            str(scan_id) not in alert_user.scannerJobs):
            
            price = '40' if str(scan_id).upper().startswith('P') else '31'
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "Yes! Subscribe", "callback_data": f"SUB_{scan_id}"}]
                ],
            }
            send_message(
                message=(
                    f"🔴 <b>Please check your current alerts, balance and subscriptions "
                    f"using /OTP before subscribing for alerts</b>.🔴 "
                    f"If you are not already subscribed to this alert, would you like to "
                    f"subscribe to this ({scan_id}) automated scan alert for a day during "
                    f"market hours (NSE - IST timezone)? You will need to pay ₹ {price} "
                    f"(One time) for automated alerts to {scan_id} all day on the day of "
                    f"subscription. 🔴 If you say <b>Yes</b>, the corresponding charges "
                    f"will be deducted from your alerts balance!🔴"
                ),
                userID=user_id,
                reply_markup=reply_markup
            )
        
        # Case 2: Already subscribed
        elif (alert_user is not None and 
              len(alert_user.scannerJobs) > 0 and 
              str(scan_id) in alert_user.scannerJobs):
            
            send_message(
                message=(
                    f"Thank you for subscribing to (<b>{scan_id}</b>) automated scan alert! "
                    f"We truly hope you are enjoying the alerts! You will continue to receive "
                    f"alerts for the duration of NSE Market hours for today. "
                    f"For any feedback, drop a note to @ItsOnlyPK."
                ),
                userID=user_id,
            )
            
    except Exception as e:
        default_logger().debug(e, exc_info=True)


def send_test_status_impl(screen_results, label, user=None, send_message_callback=None):
    """Send test status message - implementation for globals.py delegation"""
    result_count = len(screen_results) if screen_results is not None else 0
    status = "<b>SUCCESS</b>" if result_count >= 1 else "<b>FAIL</b>"
    
    message = f"{status}: Found {result_count} Stocks for {label}"
    
    if send_message_callback:
        send_message_callback(message=message, user=user)
    else:
        send_message(message, userID=user)

