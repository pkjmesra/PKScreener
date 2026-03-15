#!/usr/bin/python3
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

"""
BotHandlers - Refactored bot handlers for PKScreener Telegram Bot

This module contains refactored handler classes for better maintainability:
- UserHandler: User registration and authentication
- MenuHandler: Menu navigation and rendering  
- ScanHandler: Scan execution and result handling
- SubscriptionHandler: User subscription management
"""

import logging
import re
import threading
from time import sleep

from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.MarketHours import MarketHours

logger = logging.getLogger(__name__)


class PKBotLocalCache(SingletonMixin, metaclass=SingletonType):
    """Singleton cache for bot-related data."""
    
    def __init__(self):
        super(PKBotLocalCache, self).__init__()
        self.registered_ids = []
        self.user_states = {}


class BotConstants:
    """Constants used across bot handlers."""
    
    MAX_MSG_LENGTH = 4096
    OWNER_USER = "Itsonlypk"
    APOLOGY_TEXT = ("Apologies! The @nse_pkscreener_bot is NOT available for the time being! "
                   "We are working with our host GitHub and other data source providers to sort out "
                   "pending invoices and restore the services soon! Thanks for your patience and support! 🙏")
    
    # Menu skip configurations
    TOP_LEVEL_SCANNER_MENUS = ["X", "B", "MI", "DV", "P"]
    TOP_LEVEL_SCANNER_SKIP_MENUS = ["M", "S", "F", "G", "C", "T", "D", "I", "E", "U", "L", "Z", "P"]
    
    INDEX_COMMANDS_SKIP_MENUS_SCANNER = ["W", "E", "M", "Z", "S"]
    INDEX_COMMANDS_SKIP_MENUS_BACKTEST = ["W", "E", "M", "Z", "S", "N", "0", "15"]
    
    SCANNER_MENUS_WITH_NO_SUBMENUS = [
        "1", "2", "3", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35",
        "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"
    ]
    SCANNER_MENUS_WITH_SUBMENU_SUPPORT = ["6", "7", "21", "22", "30", "32", "33", "40"]
    SCANNER_SUBMENUS_CHILDLEVEL_SUPPORT = {
        "6": ["7", "10"],
        "7": ["3", "6", "7", "9"]
    }


class UserHandler:
    """Handles user registration, authentication, and OTP."""
    
    def __init__(self, config_manager):
        """
        Initialize UserHandler.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.cache = PKBotLocalCache()
    
    def register_user(self, user, force_fetch=False):
        """
        Register a user and get OTP.
        
        Args:
            user: Telegram user object
            force_fetch: Force fetch from database
            
        Returns:
            tuple: (otp_value, subscription_model, subscription_validity, alert_user)
        """
        otp_value, subs_model, subs_validity, alert_user = 0, 0, None, None
        
        if user is not None and (user.id not in self.cache.registered_ids or force_fetch):
            try:
                from PKDevTools.classes.DBManager import DBManager
                db_manager = DBManager()
                otp_value, subs_model, subs_validity, alert_user = db_manager.getOTP(
                    user.id, user.username,
                    f"{user.first_name} {user.last_name}",
                    validityIntervalInSeconds=self.config_manager.otpInterval
                )
                
                if str(otp_value).strip() != '0' and user.id not in self.cache.registered_ids:
                    self.cache.registered_ids.append(user.id)
            except Exception as e:
                logger.error(f"Error registering user: {e}")
        
        return otp_value, subs_model, subs_validity, alert_user
    
    def load_registered_users(self):
        """Load all registered users from database."""
        try:
            from PKDevTools.classes.DBManager import DBManager
            db_manager = DBManager()
            users = db_manager.getUsers(fieldName="userid")
            user_ids = [user.userid for user in users]
            self.cache.registered_ids.extend(user_ids)
        except Exception as e:
            logger.error(f"Error loading registered users: {e}")


class MenuHandler:
    """Handles menu navigation and rendering for the bot."""
    
    def __init__(self):
        """Initialize MenuHandler."""
        from pkscreener.classes.MenuOptions import menus
        self.m0 = menus()
        self.m1 = menus()
        self.m2 = menus()
        self.m3 = menus()
        self.m4 = menus()
    
    def get_menu_for_level(self, level, parent_menu=None, skip_menus=None):
        """
        Get menu items for a specific level.
        
        Args:
            level: Menu level (0-4)
            parent_menu: Parent menu for rendering
            skip_menus: List of menu keys to skip
            
        Returns:
            list: Menu items for the level
        """
        if skip_menus is None:
            skip_menus = []
        
        menu = getattr(self, f'm{level}')
        menu.renderForMenu(selectedMenu=parent_menu, skip=skip_menus, asList=True)
        
        return [m for m in menu.menuDict.values() if m.menuKey not in skip_menus]
    
    def create_inline_keyboard(self, menu_items, callback_prefix=""):
        """
        Create inline keyboard markup from menu items.
        
        Args:
            menu_items: List of menu items
            callback_prefix: Prefix for callback data
            
        Returns:
            InlineKeyboardMarkup: Telegram inline keyboard
        """
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = []
        row = []
        
        for item in menu_items:
            button = InlineKeyboardButton(
                text=item.menuText[:30],  # Limit button text length
                callback_data=f"{callback_prefix}{item.menuKey}"
            )
            row.append(button)
            
            if len(row) >= 2:  # 2 buttons per row
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)


class SubscriptionHandler:
    """Handles user subscription management."""
    
    def __init__(self):
        """Initialize SubscriptionHandler."""
        pass
    
    def update_subscription(self, user_id, sub_value, sub_type="add"):
        """
        Update user subscription.
        
        Args:
            user_id: Telegram user ID
            sub_value: Subscription value
            sub_type: Type of update ("add" or "remove")
            
        Returns:
            str: Result message or None on success
        """
        from pkscreener.classes.WorkflowManager import run_workflow
        from PKDevTools.classes.Environment import PKEnvironment
        
        workflow_name = "w18-workflow-sub-data.yml"
        branch = "main"
        updated_results = None
        
        try:
            workflow_post_data = (
                '{"ref":"'
                + branch
                + '","inputs":{"userid":"'
                + f"{user_id}"
                + '","subtype":"'
                + f"{sub_type}"
                + '","subvalue":"'
                + f"{sub_value}"
                + '"}}'
            )
            
            ghp_token = PKEnvironment().allSecrets["PKG"]
            resp = run_workflow(
                workflowType="O",
                repo="PKScreener",
                owner="pkjmesra",
                branch=branch,
                ghp_token=ghp_token,
                workflow_name=workflow_name,
                workflow_postData=workflow_post_data
            )
            
            if resp is not None and resp.status_code != 204:
                updated_results = ("Uh oh! We ran into a problem enabling your subscription.\n"
                                 "Please reach out to @ItsOnlyPK to resolve.")
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            updated_results = ("Uh oh! We ran into a problem enabling your subscription.\n"
                             "Please reach out to @ItsOnlyPK to resolve.")
        
        return updated_results
    
    def match_utr(self, utr):
        """
        Match UTR to transaction.
        
        Args:
            utr: UTR number to match
            
        Returns:
            dict: Matched transaction or None
        """
        try:
            from PKDevTools.classes.GmailReader import PKGmailReader
            return PKGmailReader.matchUTR(utr=utr)
        except Exception as e:
            logger.error(f"Error matching UTR: {e}")
            return None


class MarketTimeHandler:
    """Handles market time-related operations."""
    
    @staticmethod
    def is_in_market_hours():
        """
        Check if current time is within market hours.
        
        Returns:
            bool: True if in market hours
        """
        now = PKDateUtilities.currentDateTime()
        market_start_time = PKDateUtilities.currentDateTime(
            simulate=True,
            hour=MarketHours().openHour,
            minute=MarketHours().openMinute
        )
        market_close_time = PKDateUtilities.currentDateTime(
            simulate=True,
            hour=MarketHours().closeHour,
            minute=MarketHours().closeMinute
        )
        
        return (not PKDateUtilities.isTodayHoliday()[0] and 
                now >= market_start_time and 
                now <= market_close_time)
    
    @staticmethod
    def initialize_intraday_timer(callback_func):
        """
        Initialize timer for intraday monitoring.
        
        Args:
            callback_func: Function to call when timer fires
            
        Returns:
            threading.Timer: Timer object or None
        """
        try:
            if PKDateUtilities.isTodayHoliday()[0]:
                return None
            
            now = PKDateUtilities.currentDateTime()
            market_start_time = PKDateUtilities.currentDateTime(
                simulate=True,
                hour=MarketHours().openHour,
                minute=MarketHours().openMinute - 1
            )
            market_close_time = PKDateUtilities.currentDateTime(
                simulate=True,
                hour=MarketHours().closeHour,
                minute=MarketHours().closeMinute
            )
            market_open_prior = PKDateUtilities.currentDateTime(
                simulate=True,
                hour=MarketHours().openHour - 2,
                minute=MarketHours().openMinute + 30
            )
            
            if now < market_start_time and now >= market_open_prior:
                difference = (market_start_time - now).total_seconds() + 1
                timer = threading.Timer(difference, callback_func, args=[])
                timer.start()
                return timer
            elif now >= market_start_time and now <= market_close_time:
                callback_func()
                return None
        except Exception as e:
            logger.error(f"Error initializing intraday timer: {e}")
            callback_func()
        
        return None


class TextSanitizer:
    """Utility class for text sanitization."""
    
    @staticmethod
    def sanitize(text, max_length=4096):
        """
        Sanitize text for Telegram message.
        
        Args:
            text: Text to sanitize
            max_length: Maximum message length
            
        Returns:
            str: Sanitized text
        """
        if text is None:
            return ""
        
        elif len(text) > max_length:
            return text[:max_length]
        
        return text
    
    @staticmethod
    def escape_html(text):
        """
        Escape HTML characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            str: Escaped text
        """
        import html
        return html.escape(str(text))






