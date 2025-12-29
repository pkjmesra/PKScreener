#!/usr/bin/env python
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
import os
from time import sleep

from PKDevTools.classes.log import default_logger
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
    send_photo,
    send_media_group
)

from pkscreener.classes import ImageUtility


class TelegramNotifier:
    """
    Handles all Telegram notification functionality for the PKScreener application.
    Supports sending messages, photos, documents, and media groups to Telegram channels.
    """
    
    DEV_CHANNEL_ID = "-1001785195297"
    
    def __init__(self, user_passed_args=None, test_messages_queue=None, media_group_dict=None):
        """
        Initialize TelegramNotifier.
        
        Args:
            user_passed_args: User passed arguments
            test_messages_queue: Queue for test messages
            media_group_dict: Dictionary for media group attachments
        """
        self.user_passed_args = user_passed_args
        self.test_messages_queue = test_messages_queue if test_messages_queue is not None else []
        self.media_group_dict = media_group_dict if media_group_dict is not None else {}
        
    def send_quick_scan_result(self, menu_choice_hierarchy, user, tabulated_results,
                               markdown_results, caption, png_name, png_extension,
                               addendum=None, addendum_label=None, backtest_summary="",
                               backtest_detail="", summary_label=None, detail_label=None,
                               legend_prefix_text="", force_send=False):
        """
        Send quick scan results to Telegram.
        
        Args:
            menu_choice_hierarchy: Menu choice hierarchy string
            user: User ID
            tabulated_results: Tabulated results string
            markdown_results: Markdown formatted results
            caption: Caption for the message
            png_name: PNG file name
            png_extension: PNG file extension
            addendum: Additional text
            addendum_label: Label for addendum
            backtest_summary: Backtest summary text
            backtest_detail: Backtest detail text
            summary_label: Label for summary
            detail_label: Label for detail
            legend_prefix_text: Legend prefix
            force_send: Whether to force send
        """
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if (("RUNNER" not in os.environ.keys()) or 
                ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
                return
                
        try:
            if not is_token_telegram_configured():
                return
                
            ImageUtility.PKImageTools.tableToImage(
                markdown_results,
                tabulated_results,
                png_name + png_extension,
                menu_choice_hierarchy,
                backtestSummary=backtest_summary,
                backtestDetail=backtest_detail,
                addendum=addendum,
                addendumLabel=addendum_label,
                summaryLabel=summary_label,
                detailLabel=detail_label,
                legendPrefixText=legend_prefix_text
            )
            
            if force_send:
                self.send_message_to_telegram(
                    message=None,
                    document_file_path=png_name + png_extension,
                    caption=caption,
                    user=user,
                )
                os.remove(png_name + png_extension)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
    def send_message_to_telegram(self, message=None, photo_file_path=None,
                                  document_file_path=None, caption=None, user=None,
                                  mediagroup=False):
        """
        Send a message to Telegram channel.
        
        Args:
            message: Message text
            photo_file_path: Path to photo file
            document_file_path: Path to document file
            caption: Caption text
            user: User ID
            mediagroup: Whether to send as media group
        """
        default_logger().debug(
            f"Received message:{message}, caption:{caption}, "
            f"for user: {user} with mediagroup:{mediagroup}"
        )
        
        # Check if we should send
        if (("RUNNER" not in os.environ.keys() and 
             (self.user_passed_args is not None and not self.user_passed_args.log)) or 
            (self.user_passed_args is not None and self.user_passed_args.telegram)):
            return
            
        if user is None and self.user_passed_args is not None and self.user_passed_args.user is not None:
            user = self.user_passed_args.user
            
        if not mediagroup:
            self._send_single_message(message, photo_file_path, document_file_path, caption, user)
        else:
            self._send_media_group_message(user, message, caption)
            
        if user is not None:
            if str(user) != str(self.DEV_CHANNEL_ID) and self.user_passed_args is not None and not self.user_passed_args.monitor:
                # Send an update to dev channel
                send_message(
                    f"Responded back to userId:{user} with {caption}.{message} "
                    f"[{self.user_passed_args.options.replace(':D', '')}]",
                    userID=self.DEV_CHANNEL_ID,
                )
                
    def _send_single_message(self, message, photo_file_path, document_file_path, caption, user):
        """Send a single message (text, photo, or document)."""
        if self.test_messages_queue is not None:
            self.test_messages_queue.append(
                f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_file_path}"
            )
            if len(self.test_messages_queue) > 10:
                self.test_messages_queue.pop(0)
                
        if user is not None and caption is not None:
            caption = f"{caption.replace('&', 'n')}."
            
        if message is not None:
            try:
                message = message.replace("&", "n").replace("<", "*")
                send_message(message, userID=user)
            except Exception as e:
                default_logger().debug(e, exc_info=True)
        else:
            message = ""
            
        if photo_file_path is not None:
            try:
                if caption is not None:
                    caption = f"{caption.replace('&', 'n')}"
                send_photo(photo_file_path, (caption if len(caption) <= 1024 else ""), userID=user)
                sleep(2)  # Breather for telegram API
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                
        if document_file_path is not None:
            try:
                if caption is not None and isinstance(caption, str):
                    caption = f"{caption.replace('&', 'n')}"
                send_document(document_file_path, (caption if len(caption) <= 1024 else ""), userID=user)
                sleep(2)  # Breather for telegram API
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                
    def _send_media_group_message(self, user, message, caption):
        """Send a media group message with multiple attachments."""
        file_paths = []
        file_captions = []
        
        if "ATTACHMENTS" in self.media_group_dict.keys():
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
                
            if self.test_messages_queue is not None:
                self.test_messages_queue.append(
                    f"message:{file_captions[-1]}\ncaption:{file_captions[-1]}\n"
                    f"user:{user}\ndocument:{file_paths[-1]}"
                )
                if len(self.test_messages_queue) > 10:
                    self.test_messages_queue.pop(0)
                    
            if len(file_paths) > 0 and not self.user_passed_args.monitor:
                resp = send_media_group(
                    user=self.user_passed_args.user,
                    png_paths=[],
                    png_album_caption=None,
                    file_paths=file_paths,
                    file_captions=file_captions
                )
                if resp is not None:
                    default_logger().debug(resp.text, exc_info=True)
                    
            caption = f"{str(len(file_captions))} files sent!"
            message = (self.media_group_dict["CAPTION"].replace('&', 'n').replace("<", "*")[:1024] 
                      if "CAPTION" in self.media_group_dict.keys() else "-")
            default_logger().debug(
                f"Received updated message:{message}, caption:{caption}, "
                f"for user: {user} with mediagroup:True"
            )
        else:
            default_logger().debug(
                f"No ATTACHMENTS in media_group_dict: {self.media_group_dict.keys()}"
            )
            
        # Clean up files
        for f in file_paths:
            try:
                if "RUNNER" in os.environ.keys():
                    os.remove(f)
                elif not f.endswith("xlsx"):
                    os.remove(f)
            except:
                pass
                
        # Handle alert subscriptions
        self._handle_alert_subscriptions(user, message)
        
    def _handle_alert_subscriptions(self, user, message):
        """
        Handle user subscriptions to automated alerts.
        
        Args:
            user: User ID
            message: Message text
        """
        if user is not None and message is not None and "|" in str(message):
            if int(user) > 0:
                # Individual user
                scan_id = message.split("|")[0].replace("*b>", "").strip()
                
                from PKDevTools.classes.DBManager import DBManager
                db_manager = DBManager()
                
                if db_manager.url is not None and db_manager.token is not None:
                    alert_user = db_manager.alertsForUser(int(user))
                    
                    # Case 1: User not subscribed
                    if (alert_user is None or 
                        len(alert_user.scannerJobs) == 0 or 
                        str(scan_id) not in alert_user.scannerJobs):
                        reply_markup = {
                            "inline_keyboard": [
                                [{"text": "Yes! Subscribe", "callback_data": f"SUB_{scan_id}"}]
                            ],
                        }
                        send_message(
                            message=(
                                f"🔴 <b>Please check your current alerts, balance and subscriptions "
                                f"using /OTP before subscribing for alerts</b>.🔴 If you are not "
                                f"already subscribed to this alert, would you like to subscribe to "
                                f"this ({scan_id}) automated scan alert for a day during market hours "
                                f"(NSE - IST timezone)? You will need to pay ₹ "
                                f"{'40' if str(scan_id).upper().startswith('P') else '31'} (One time) "
                                f"for automated alerts to {scan_id} all day on the day of subscription. "
                                f"🔴 If you say <b>Yes</b>, the corresponding charges will be deducted "
                                f"from your alerts balance!🔴"
                            ),
                            userID=int(user),
                            reply_markup=reply_markup
                        )
                    # Case 2: User already subscribed
                    elif (alert_user is not None and 
                          len(alert_user.scannerJobs) > 0 and 
                          str(scan_id) in alert_user.scannerJobs):
                        send_message(
                            message=(
                                f"Thank you for subscribing to (<b>{scan_id}</b>) automated scan alert! "
                                f"We truly hope you are enjoying the alerts! You will continue to "
                                f"receive alerts for the duration of NSE Market hours for today. "
                                f"For any feedback, drop a note to @ItsOnlyPK."
                            ),
                            userID=int(user),
                        )
                        
    def send_test_status(self, screen_results, label, user=None):
        """
        Send test status message to Telegram.
        
        Args:
            screen_results: Screen results dataframe
            label: Label for the test
            user: User ID
        """
        msg = "<b>SUCCESS</b>" if (screen_results is not None and len(screen_results) >= 1) else "<b>FAIL</b>"
        self.send_message_to_telegram(
            message=f"{msg}: Found {len(screen_results) if screen_results is not None else 0} Stocks for {label}",
            user=user
        )
        
    def send_global_market_barometer(self):
        """Send global market barometer information to Telegram."""
        from pkscreener.classes import Barometer
        from PKDevTools.classes.Environment import PKEnvironment
        
        suggestion_text = (
            "Feel free to share on social media.Try @nse_pkscreener_bot for more scans! "
            "<i><b><u>You agree that you have read</u></b>:"
            "https://pkjmesra.github.io/PKScreener/Disclaimer.txt</i> "
            "<b>and accept TOS</b>: https://pkjmesra.github.io/PKScreener/tos.txt "
            "<b>STOP using and exit from channel/group, if you do not.</b>"
        )
        caption = f"Global Market Barometer with India market Performance (top) and Valuation (bottom).{suggestion_text}"
        gmb_path = Barometer.getGlobalMarketBarometerValuation()
        
        try:
            if gmb_path is not None:
                channel_id, _, _, _ = PKEnvironment().secrets
                user = (self.user_passed_args.user if self.user_passed_args is not None 
                       else (int(f"-{channel_id}") if channel_id is not None and len(str(channel_id)) > 0 else None))
                       
                gmb_file_size = os.stat(gmb_path).st_size if os.path.exists(gmb_path) else 0
                from PKDevTools.classes.OutputControls import OutputControls
                OutputControls().printOutput(f"Barometer report created with size {gmb_file_size} @ {gmb_path}")
                
                self.send_message_to_telegram(
                    message=None,
                    photo_file_path=gmb_path,
                    caption=caption,
                    user=user,
                )
                os.remove(gmb_path)
            else:
                from pkscreener.classes.PKAnalytics import PKAnalyticsService
                import sys
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
    def add_attachment(self, file_path, caption):
        """
        Add an attachment to the media group dictionary.
        
        Args:
            file_path: Path to the file
            caption: Caption for the attachment
        """
        if "ATTACHMENTS" not in self.media_group_dict:
            self.media_group_dict["ATTACHMENTS"] = []
            
        self.media_group_dict["ATTACHMENTS"].append({
            "FILEPATH": file_path,
            "CAPTION": caption.replace('&', 'n')
        })
        
    def set_caption(self, caption):
        """
        Set the main caption for media group.
        
        Args:
            caption: Caption text
        """
        self.media_group_dict["CAPTION"] = caption




