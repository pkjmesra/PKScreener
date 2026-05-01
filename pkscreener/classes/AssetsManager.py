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
import glob
import os
import pickle
import shutil
import tempfile
import pandas as pd
import numpy as np
from halo import Halo
from alive_progress import alive_bar
# from yfinance import shared

from PKDevTools.classes.log import default_logger
from PKDevTools.classes import Archiver
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.MarketHours import MarketHours
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.PKBackupRestore import start_backup

import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes import Utility, ImageUtility
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.PKScheduler import PKScheduler


class PKAssetsManager:
    """
    PKAssetsManager - Centralized Asset and Data Management for PK Screener

    This class serves as the primary data management hub for the PK Screener application.
    It handles all aspects of financial data acquisition, caching, validation, and persistence.
    
    Key Responsibilities:
    ---------------------
    1. **Data Acquisition**: Downloads stock data from various sources (GitHub, PKBrokers, local cache)
    2. **Data Caching**: Manages local pickle file caching for performance optimization
    3. **Data Freshness Validation**: Ensures data is current and not stale using trading day calculations
    4. **Selective Data Loading**: Supports loading data for specific stocks or entire market
    5. **Real-time Tick Updates**: Integrates with PKBrokers for intraday tick data
    6. **Data Persistence**: Saves screened results to Excel and other formats
    7. **GitHub Actions Integration**: Downloads from actions-data-download branch for CI/CD pipelines
    
    Architecture:
    -------------
    - Uses singleton pattern for fetcher and configManager instances
    - Implements multi-source fallback (local cache → GitHub → PKBrokers → Origin)
    - Supports both daily and intraday data timeframes
    - Maintains data integrity with timestamp format preservation
    
    Data Flow:
    ----------
    1. `loadStockData()` - Primary entry point for loading stock data
    2. Checks local cache freshness → validates data quality
    3. Falls back to GitHub Actions data if local is stale
    4. Applies real-time ticks from PKBrokers during market hours
    5. Filters data based on requested stockCodes (selective loading)
    6. Returns filtered dictionary of stock data
    
    Attributes:
    -----------
    fetcher : StockDataFetcher
        Singleton fetcher instance for downloading raw stock data
    configManager : ConfigManager
        Singleton configuration manager for application settings
    """
    
    fetcher = Fetcher.screenerStockDataFetcher()
    configManager = ConfigManager.tools()
    configManager.getConfig(ConfigManager.parser)

    @staticmethod
    def is_data_fresh(stock_data, max_stale_trading_days=1):
        """
        Check if stock data is fresh (within max_stale_trading_days).
        
        Uses PKDateUtilities to account for weekends and market holidays.
        Data is considered fresh if its date >= the last trading day.
        
        Args:
            stock_data: DataFrame or dict with stock data
                       Can be either:
                       - pd.DataFrame with DateTimeIndex
                       - dict with 'index' key (from to_dict("split"))
                       - dict with 'data' key for OHLCV values
            max_stale_trading_days: Maximum acceptable age in TRADING days (not calendar days)
                                    Default 1 means data from last trading day is acceptable
        
        Returns:
            tuple: (is_fresh: bool, data_date: date or None, trading_days_old: int)
                   - is_fresh: True if data is not stale
                   - data_date: The latest date in the data
                   - trading_days_old: Number of trading days since data_date
        
        Examples:
            >>> is_fresh, date, age = PKAssetsManager.is_data_fresh(df)
            >>> if not is_fresh:
            ...     print(f"Data is {age} trading days old from {date}")
        """
        try:
            from datetime import datetime
            from PKDevTools.classes.PKDateUtilities import PKDateUtilities
            
            # Get the last trading date (accounts for weekends and holidays)
            last_trading_date = PKDateUtilities.tradingDate()
            if isinstance(last_trading_date, datetime):
                last_trading_date = last_trading_date.date()
            
            last_date = None
            
            # Handle DataFrame input
            if isinstance(stock_data, pd.DataFrame) and not stock_data.empty:
                last_date = stock_data.index[-1]
                if hasattr(last_date, 'date'):
                    last_date = last_date.date()
                elif isinstance(last_date, str):
                    last_date = datetime.strptime(last_date[:10], '%Y-%m-%d').date()
            
            # Handle dict with 'index' key (from to_dict("split"))
            elif isinstance(stock_data, dict) and 'index' in stock_data:
                index = stock_data['index']
                if index:
                    last_date = index[-1]
                    if hasattr(last_date, 'date'):
                        last_date = last_date.date()
                    elif isinstance(last_date, str):
                        # Try multiple date formats
                        date_str = str(last_date)
                        # Remove timezone info if present
                        if 'T' in date_str:
                            date_str = date_str.split('T')[0]
                        elif '+' in date_str:
                            date_str = date_str.split('+')[0]
                        elif ' ' in date_str:
                            date_str = date_str.split(' ')[0]
                        # Try parsing
                        try:
                            last_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                        except:
                            # Try other formats
                            try:
                                last_date = pd.to_datetime(date_str).date()
                            except:
                                last_date = None
            
            if last_date is None:
                return True, None, 0  # Can't determine, assume fresh
            
            # Calculate trading days between data date and last trading date
            # Data is fresh if it's from the last trading day or more recent
            if last_date >= last_trading_date:
                return True, last_date, 0
            
            # Count trading days between last_date and last_trading_date
            trading_days_old = PKDateUtilities.trading_days_between(last_date, last_trading_date)
            is_fresh = trading_days_old <= max_stale_trading_days
            
            return is_fresh, last_date, trading_days_old
            
        except Exception as e:
            default_logger().debug(f"Error checking data freshness: {e}")
            return True, None, 0  # On error, assume fresh to not block

    @staticmethod
    def validate_data_freshness(stockDict, isTrading=False):
        """
        Validate freshness of stock data across all stocks and log warnings for stale data.
        
        This method iterates through all stocks in the dictionary, checks their data
        freshness using is_data_fresh(), and provides comprehensive statistics about
        data quality.
        
        Args:
            stockDict: Dictionary of stock data where keys are stock symbols and values
                      are either DataFrames or dicts with OHLCV data
            isTrading: Boolean indicating whether market is currently trading.
                      When True, stale data warnings are more prominent.
        
        Returns:
            tuple: (fresh_count, stale_count, oldest_date)
                   - fresh_count: Number of stocks with fresh data
                   - stale_count: Number of stocks with stale data
                   - oldest_date: The oldest data date found across all stocks
        
        Notes:
            - Logs warnings at WARNING level for stale data during trading hours
            - For small stale counts (<=5), logs individual stock details for debugging
            - Used primarily for monitoring data quality in production
        
        Examples:
            >>> fresh, stale, oldest = PKAssetsManager.validate_data_freshness(stockDict, isTrading=True)
            >>> if stale > 0:
            ...     print(f"Warning: {stale} stocks have stale data as of {oldest}")
        """
        from datetime import datetime
        
        fresh_count = 0
        stale_count = 0
        oldest_date = None
        stale_stocks = []
        
        for stock, data in stockDict.items():
            is_fresh, data_date, age_days = PKAssetsManager.is_data_fresh(data)
            
            if is_fresh:
                fresh_count += 1
            else:
                stale_count += 1
                stale_stocks.append((stock, data_date, age_days))
                
            if data_date and (oldest_date is None or data_date < oldest_date):
                oldest_date = data_date
        
        # Log warning for stale data during trading hours
        if isTrading and stale_count > 0:
            default_logger().warning(
                f"[DATA-FRESHNESS] {stale_count} stocks have stale data (older than last trading day). "
                f"Oldest data from: {oldest_date}. Consider fetching fresh tick data."
            )
            if stale_count <= 5:
                for stock, date, age in stale_stocks:
                    default_logger().warning(f"[DATA-FRESHNESS] {stock}: data from {date} ({age} trading days old)")
        
        return fresh_count, stale_count, oldest_date

    @staticmethod
    def _apply_fresh_ticks_to_data(stockDict, stockCodes=None):
        """
        Apply fresh tick data from PKBrokers to update stale stock data.
        
        This method downloads the latest ticks.json from PKBrokers/PKScreener
        and merges today's OHLCV data into the existing stockDict while
        preserving the original timestamp format.
        
        IMPORTANT: This method now supports selective filtering based on stockCodes.
        If stockCodes is provided (non-empty list), only those stocks will be updated.
        If stockCodes is None or empty, all stocks will be updated.
        
        Args:
            stockDict: Dictionary of stock data (symbol -> dict with 'data', 'columns', 'index')
                       Dictionary with 'index' in ascending order (oldest first, newest last)
            stockCodes: Optional list of stock symbols to update.
                       - If None or empty: Update ALL stocks in stockDict
                       - If provided: Only update stocks in this list
        
        Returns:
            dict: Updated stockDict with fresh tick data merged
            
        Notes:
            - Preserves original timestamp format (ISO, datetime string, Unix timestamp, etc.)
            - During market hours: Uses actual tick timestamps from PKBrokers
            - After market hours: Updates timestamps to market close time (15:30)
            - Handles missing ticks gracefully (updates timestamps only when needed)
        
        Examples:
            >>> # Update all stocks
            >>> updated = PKAssetsManager._apply_fresh_ticks_to_data(stockDict)
            >>> 
            >>> # Update only specific stocks
            >>> updated = PKAssetsManager._apply_fresh_ticks_to_data(stockDict, stockCodes=['RELIANCE', 'TCS'])
        """
        import requests
        from datetime import datetime
        
        try:
            # Try to download fresh ticks from multiple sources
            ticks_sources = [
                "https://raw.githubusercontent.com/pkjmesra/PKBrokers/main/pkbrokers/kite/examples/results/Data/ticks.json",
                "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/ticks.json",
            ]
            
            ticks_data = None
            for url in ticks_sources:
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        ticks_data = response.json()
                        if ticks_data and len(ticks_data) > 0:
                            default_logger().info(f"Downloaded {len(ticks_data)} ticks from {url}")
                            break
                except Exception as e:
                    default_logger().debug(f"Failed to fetch ticks from {url}: {e}")
                    continue
            
            if not ticks_data:
                default_logger().debug("No tick data available, updating today's timestamps to market close time")
                # Even without ticks.json, we should update today's timestamps to market close time (15:30)
                # if they have early morning timestamps
                import pytz
                from PKDevTools.classes.PKDateUtilities import PKDateUtilities
                timezone = pytz.timezone("Asia/Kolkata")
                now = datetime.now(timezone)
                today_str = now.strftime('%Y-%m-%d')
                is_trading_hours = PKDateUtilities.isTradingTime()
                market_close_time = f"{today_str} 15:30:00"
                updated_count = 0
                
                # Determine which stocks to update
                stocks_to_update = stockDict.keys()
                if stockCodes and len(stockCodes) > 0:
                    stocks_to_update = [s for s in stockCodes if s in stockDict]
                
                for symbol in stocks_to_update:
                    stock_data = stockDict.get(symbol)
                    if not isinstance(stock_data, dict) or 'index' not in stock_data:
                        continue
                    
                    index_list = stock_data.get('index', [])
                    if not index_list:
                        continue
                    
                    # Check if the last index is from today but has early morning time (< 15:00)
                    last_index = str(index_list[-1])
                    if len(last_index) >= 10 and last_index[:10] == today_str:
                        # Parse the time component
                        try:
                            if ' ' in last_index:
                                time_part = last_index.split(' ')[1] if len(last_index.split(' ')) > 1 else ""
                                if time_part:
                                    hour = int(time_part.split(':')[0]) if ':' in time_part else 0
                                    # If time is before 15:00 (3 PM), update to market close
                                    if hour < 15:
                                        # Update the last index to market close time
                                        new_index = list(index_list)
                                        new_index[-1] = market_close_time
                                        stock_data['index'] = new_index
                                        stockDict[symbol] = stock_data
                                        updated_count += 1
                        except:
                            pass
                
                if updated_count > 0:
                    default_logger().info(f"Updated {updated_count} symbols' timestamps to market close time")
                
                return stockDict
            
            # Get today's date for the merge
            import pytz
            from PKDevTools.classes.PKDateUtilities import PKDateUtilities
            
            timezone = pytz.timezone("Asia/Kolkata")
            now = datetime.now(timezone)
            today_str = now.strftime('%Y-%m-%d')
            is_trading_hours = PKDateUtilities.isTradingTime()
            updated_count = 0
            
            # Determine which stocks to update
            stocks_to_update = stockDict.keys()
            if stockCodes and len(stockCodes) > 0:
                stocks_to_update = [s for s in stockCodes if s in stockDict]
                default_logger().debug(f"Applying fresh ticks to {len(stocks_to_update)} selective stocks")
            
            # IMPORTANT: First, detect the timestamp format from existing data
            # Get a sample symbol to detect the format
            sample_symbol = next(iter(stocks_to_update)) if stocks_to_update else next(iter(stockDict.keys())) if stockDict else None
            original_timestamp_format = None
            original_timestamp_sample = None
            
            if sample_symbol and sample_symbol in stockDict:
                sample_data = stockDict[sample_symbol]
                if isinstance(sample_data, dict) and 'index' in sample_data and sample_data['index']:
                    original_timestamp_sample = sample_data['index'][-1]
                    # Detect if it's a string, datetime object, or timestamp
                    if isinstance(original_timestamp_sample, str):
                        if '.' in original_timestamp_sample and 'T' in original_timestamp_sample:
                            original_timestamp_format = 'iso_with_microseconds'
                        elif 'T' in original_timestamp_sample:
                            original_timestamp_format = 'iso'
                        elif ' ' in original_timestamp_sample:
                            original_timestamp_format = 'datetime_string'
                        else:
                            original_timestamp_format = 'string'
                    elif isinstance(original_timestamp_sample, (int, float)):
                        original_timestamp_format = 'unix_timestamp'
                    elif hasattr(original_timestamp_sample, 'strftime'):
                        original_timestamp_format = 'datetime_object'
            
            default_logger().debug(f"Detected original timestamp format: {original_timestamp_format}")
            
            # Helper function to format timestamp to match original format
            def format_timestamp_to_match_original(dt: datetime, original_format: str, original_sample=None) -> str:
                """Format a datetime to match the original timestamp format."""
                if original_format == 'iso_with_microseconds':
                    return dt.isoformat()
                elif original_format == 'iso':
                    return dt.isoformat().split('.')[0]
                elif original_format == 'datetime_string':
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                elif original_format == 'unix_timestamp':
                    return int(dt.timestamp())
                elif original_format == 'datetime_object':
                    return dt
                else:
                    # Default to datetime string format
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Apply ticks to stockDict - only for selected stocks
            for instrument_token, tick_info in ticks_data.items():
                if not isinstance(tick_info, dict):
                    continue
                
                symbol = tick_info.get('trading_symbol', '')
                ohlcv = tick_info.get('ohlcv', {})
                
                if not symbol or not ohlcv or ohlcv.get('close', 0) <= 0:
                    continue
                
                # Skip if we're filtering by stockCodes and this symbol is not in the list
                if stockCodes and len(stockCodes) > 0 and symbol not in stockCodes:
                    continue
                
                # Find matching symbol in stockDict
                if symbol not in stockDict:
                    continue
                
                stock_data = stockDict[symbol]
                if not isinstance(stock_data, dict) or 'data' not in stock_data:
                    continue
                
                try:
                    # Create today's candle row
                    today_row = [
                        float(ohlcv.get('open', 0)),
                        float(ohlcv.get('high', 0)),
                        float(ohlcv.get('low', 0)),
                        float(ohlcv.get('close', 0)),
                        int(ohlcv.get('volume', 0))
                    ]
                    
                    # Check if we have 6 columns (with Adj Close)
                    columns = stock_data.get('columns', [])
                    if len(columns) == 6:
                        today_row.append(float(ohlcv.get('close', 0)))  # Adj Close = Close
                    
                    # Determine the timestamp for the index
                    # During market hours: use last_update from ticks (when data was captured)
                    # After market hours: always use market close time (15:30)
                    if is_trading_hours:
                        # Use timestamp from ticks.json (when the data was actually captured)
                        # This shows the actual time when the tick data was saved for each stock
                        last_update = ohlcv.get('timestamp')
                        if last_update:
                            try:
                                # last_update might be a timestamp (float) or ISO string
                                if isinstance(last_update, (int, float)):
                                    timestamp_dt = datetime.fromtimestamp(last_update, tz=timezone)
                                else:
                                    timestamp_dt = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
                                    if timestamp_dt.tzinfo is None:
                                        timestamp_dt = timezone.localize(timestamp_dt)
                                    timestamp_dt = timestamp_dt.astimezone(timezone)
                            except Exception:
                                timestamp_dt = now
                        else:
                            timestamp_dt = now
                    else:
                        # After market hours, use market close time
                        last_update = ohlcv.get('timestamp')
                        if last_update:
                            try:
                                # Parse the timestamp (could be ISO string or float)
                                if isinstance(last_update, (int, float)):
                                    timestamp_dt = datetime.fromtimestamp(last_update, tz=timezone)
                                else:
                                    # Handle ISO format strings like "2026-01-07T10:29:13.827168" or "2026-01-07T10:29:09"
                                    timestamp_str_clean = str(last_update).replace('Z', '+00:00')
                                    if 'T' in timestamp_str_clean:
                                        # ISO format with T separator
                                        timestamp_dt = datetime.fromisoformat(timestamp_str_clean)
                                    else:
                                        # Try parsing as regular datetime string
                                        timestamp_dt = datetime.strptime(timestamp_str_clean, '%Y-%m-%d %H:%M:%S')
                                    if timestamp_dt.tzinfo is None:
                                        timestamp_dt = timezone.localize(timestamp_dt)
                                    timestamp_dt = timestamp_dt.astimezone(timezone)
                            except Exception:
                                # Use market close time
                                timestamp_dt = timezone.localize(datetime.strptime(f"{today_str} 15:30:00", '%Y-%m-%d %H:%M:%S'))
                        else:
                            timestamp_dt = timezone.localize(datetime.strptime(f"{today_str} 15:30:00", '%Y-%m-%d %H:%M:%S'))
                    
                    # CRITICAL FIX: Format timestamp to match original data format
                    timestamp_str = format_timestamp_to_match_original(
                        timestamp_dt, 
                        original_timestamp_format,
                        original_timestamp_sample
                    )
                    
                    # Check if today's data already exists and update/append
                    data_rows = stock_data.get('data', [])
                    index_list = stock_data.get('index', [])
                    
                    # Find and remove today's existing data (by date, not full timestamp)
                    new_rows = []
                    new_index = []
                    for idx, row in zip(index_list, data_rows):
                        idx_str = str(idx)
                        idx_date = idx_str[:10] if len(idx_str) >= 10 else idx_str
                        # Remove all entries from today - we'll replace with fresh data
                        if idx_date != today_str:
                            new_rows.append(row)
                            new_index.append(idx)
                    
                    # Append today's fresh data with properly formatted timestamp
                    new_rows.append(today_row)
                    new_index.append(timestamp_str)
                    
                    stock_data['data'] = new_rows
                    stock_data['index'] = new_index
                    stockDict[symbol] = stock_data
                    updated_count += 1
                    
                except Exception as e:
                    default_logger().debug(f"Error applying tick for {symbol}: {e}", exc_info=True)
                    continue
            
            if updated_count > 0:
                default_logger().info(f"Applied fresh tick data to {updated_count} symbols")
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"\n  [+] Applied fresh tick data to {updated_count} stocks."
                    + colorText.END
                )
            elif stockCodes and len(stockCodes) > 0:
                default_logger().debug(f"No fresh ticks available for the requested {len(stockCodes)} stocks")
            
        except Exception as e:
            default_logger().debug(f"Error applying fresh ticks: {e}")
        
        return stockDict

    @staticmethod
    def _download_and_validate_pkl(url: str, output_path: str, min_rows_required: int = 100) -> tuple:
        """
        Download and validate a pickle file from a given URL.
        
        This helper method downloads a pickle file, validates its contents,
        and checks that it has sufficient data quality (minimum rows per stock).
        
        Args:
            url: The URL to download the pickle file from
            output_path: Local file path to save the downloaded pickle
            min_rows_required: Minimum average rows per stock required for validity
        
        Returns:
            tuple: (success, file_path, num_instruments, avg_rows)
                   - success: Boolean indicating if download and validation succeeded
                   - file_path: Path to the downloaded file (if successful)
                   - num_instruments: Number of stocks/instruments in the pickle
                   - avg_rows: Average number of rows per stock (data completeness metric)
        
        Notes:
            - Downloads to a temporary file first, then moves to final location
            - Validates using sample symbols (RELIANCE, TCS, INFY, HDFCBANK, SBIN)
            - Discards file if average rows < min_rows_required
        """
        import requests
        import pickle
        import pandas as pd
        
        try:
            default_logger().debug(f"Attempting to download from: {url}")
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200 and len(response.content) > 10000:
                temp_path = output_path + ".tmp"
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                with open(temp_path, 'rb') as f:
                    data = pickle.load(f)
                
                default_logger().debug(f"Loaded PKL file. Total items: {len(data) if data else 0}")
                if data:
                    default_logger().debug(f"Sample keys from PKL: {list(data.keys())[:5]}")

                if data and len(data) > 0:
                    rows_count = []
                    sample_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'SBIN']
                    for sym in sample_symbols:
                        if sym in data:
                            item = data[sym]
                            current_rows = 0
                            if isinstance(item, pd.DataFrame):
                                current_rows = len(item)
                            elif isinstance(item, dict) and 'data' in item:
                                current_rows = len(item['data'])
                            
                            rows_count.append(current_rows)
                            default_logger().debug(f"Symbol {sym}: Found {current_rows} rows.")
                    
                    avg_rows = sum(rows_count) / len(rows_count) if rows_count else 0
                    
                    if avg_rows >= min_rows_required:
                        try:
                            shutil.move(temp_path, output_path)
                            return True, output_path, len(data), avg_rows
                        except Exception as e:
                            default_logger().error(f"Error moving file: {e}")
                    else:
                        default_logger().debug(f"Downloaded PKL has insufficient rows (avg {avg_rows:.1f} < {min_rows_required}). Discarding. Sampled symbols rows: {rows_count}")
                        os.remove(temp_path)
            
            return False, None, 0, 0
        except Exception as e:
            default_logger().debug(f"Failed to download or validate {url}: {e}")
            return False, None, 0, 0

    @staticmethod
    def download_fresh_pkl_from_github(intraday=False) -> tuple:
        """
        Download the latest pkl file from GitHub actions-data-download branch.
        
        This method tries multiple URLs and date formats to find the most recent
        stock_data_DDMMYYYY.pkl file. It prioritizes the exact filename
        returned by Archiver.afterMarketStockDataExists().
        
        Args:
            intraday (bool): Whether to look for intraday data (True) or daily data (False)
        
        Returns:
            tuple: (success, file_path, num_instruments)
                   - success: Boolean indicating if download succeeded
                   - file_path: Path to the downloaded file
                   - num_instruments: Number of stocks/instruments in the downloaded data
        
        Notes:
            - Searches for files up to 10 days back
            - Tests multiple date formats (DDMMYYYY and DMMYY)
            - Prioritizes files with highest average rows per stock
            - Falls back to generic names (daily_candles.pkl) if dated files unavailable
        """
        from datetime import datetime, timedelta
        
        try:
            data_dir = Archiver.get_user_data_dir()
            MIN_ROWS_REQUIRED = 100 # Consistent with the existing logic
            
            # 1. First, try to download the exact file name expected by Archiver.afterMarketStockDataExists()
            _, expected_cache_file_name = Archiver.afterMarketStockDataExists(intraday=intraday)
            output_path = os.path.join(data_dir, expected_cache_file_name)
            expected_url_primary = f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/{expected_cache_file_name}"
            expected_url_fallback = f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/{expected_cache_file_name}"

            # Try primary URL first
            success, downloaded_path, num_instruments, avg_rows = PKAssetsManager._download_and_validate_pkl(
                expected_url_primary, output_path, MIN_ROWS_REQUIRED
            )
            if success:
                default_logger().info(f"Downloaded expected pkl from GitHub (primary URL): {expected_url_primary} ({num_instruments} instruments, avg {avg_rows:.1f} rows/stock)")
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Downloaded fresh data from GitHub ({num_instruments} instruments, {avg_rows:.0f} rows/stock)"
                    + colorText.END
                )
                return True, downloaded_path, num_instruments
            
            # If primary failed, try fallback URL
            success, downloaded_path, num_instruments, avg_rows = PKAssetsManager._download_and_validate_pkl(
                expected_url_fallback, output_path, MIN_ROWS_REQUIRED
            )
            if success:
                default_logger().info(f"Downloaded expected pkl from GitHub (fallback URL): {expected_url_fallback} ({num_instruments} instruments, avg {avg_rows:.1f} rows/stock)")
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Downloaded fresh data from GitHub ({num_instruments} instruments, {avg_rows:.0f} rows/stock)"
                    + colorText.END
                )
                return True, downloaded_path, num_instruments

            # 2. If the exact file is not found or valid, fall back to existing logic (trying multiple dated files and generic names)
            default_logger().info("Expected pkl not found or valid. Falling back to broader search.")

            today = datetime.now()
            urls_to_try = []
            
            for days_ago in range(0, 10):
                check_date = today - timedelta(days=days_ago)
                date_str_full = check_date.strftime('%d%m%Y')
                date_str_short = check_date.strftime('%-d%m%y') if hasattr(check_date, 'strftime') else check_date.strftime('%d%m%y').lstrip('0')
                
                for date_str in [date_str_full, date_str_short]:
                    # Ensure we don't try the expected file again, if it was included in the date_str loop
                    current_file_name_full = f"stock_data_{date_str}.pkl"
                    current_file_name_intraday = f"stock_data_{date_str}_intraday.pkl"
                    
                    if intraday:
                        if current_file_name_intraday != expected_cache_file_name:
                            urls_to_try.extend([
                                f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/{current_file_name_intraday}",
                                f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/{current_file_name_intraday}",
                            ])
                    else:
                        if current_file_name_full != expected_cache_file_name:
                            urls_to_try.extend([
                                f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/{current_file_name_full}",
                                f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/{current_file_name_full}",
                            ])
            
            # Also try generic names
            urls_to_try.extend([
                "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/daily_candles.pkl",
                "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/daily_candles.pkl",
            ])
            
            best_file = None
            best_url = None
            best_rows_per_stock = 0
            best_num_instruments = 0
            
            for url in urls_to_try:
                success, downloaded_path, num_instruments, avg_rows = PKAssetsManager._download_and_validate_pkl(
                    url, output_path, MIN_ROWS_REQUIRED
                )
                
                if success:
                    if avg_rows > best_rows_per_stock:
                        best_file = downloaded_path
                        best_url = url
                        best_rows_per_stock = avg_rows
                        best_num_instruments = num_instruments
                        default_logger().debug(f"Found better file: {url} ({num_instruments} instruments, avg {avg_rows:.1f} rows/stock)")
                    else: # Clean up less optimal download
                        os.remove(downloaded_path) # _download_and_validate_pkl already moves temp_path to output_path if successful
                
            # Use the best file found
            if best_file:
                default_logger().info(f"Downloaded best pkl from GitHub: {best_url} ({best_num_instruments} instruments, avg {best_rows_per_stock:.1f} rows/stock)")
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Downloaded fresh data from GitHub ({best_num_instruments} instruments, {best_rows_per_stock:.0f} rows/stock)"
                    + colorText.END
                )
                return True, best_file, best_num_instruments
            
            default_logger().warning("Could not download pkl from GitHub")
            return False, None, 0
            
        except Exception as e:
            default_logger().debug(f"Error downloading pkl from GitHub: {e}")
            return False, None, 0

    @staticmethod
    def trigger_history_download_workflow(missing_days: int = 1) -> bool:
        """
        Trigger the PKBrokers w1-workflow-history-data-child.yml workflow to download missing OHLCV data.
        
        When pkl data from actions-data-download is stale (latest date < last trading date),
        this method triggers a GitHub Actions workflow to download the missing history.
        
        Args:
            missing_days: Number of trading days of historical data to fetch
            
        Returns:
            True if workflow was triggered successfully, False otherwise
        
        Notes:
            - Requires GITHUB_TOKEN or CI_PAT environment variable
            - Triggers workflow on PKBrokers repository
            - Non-blocking: Workflow runs asynchronously
        """
        import requests
        import os
        
        try:
            github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('CI_PAT')
            if not github_token:
                default_logger().warning("GITHUB_TOKEN or CI_PAT not found. Cannot trigger history download workflow.")
                return False
            
            # Trigger PKBrokers history workflow
            url = "https://api.github.com/repos/pkjmesra/PKBrokers/actions/workflows/w1-workflow-history-data-child.yml/dispatches"
            
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            payload = {
                "ref": "main",
                "inputs": {
                    "period": "day",
                    "pastoffset": str(missing_days),
                    "logLevel": "20"
                }
            }
            
            default_logger().info(f"Triggering history download workflow with past_offset={missing_days}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 204:
                default_logger().info("Successfully triggered history download workflow")
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Triggered history download for {missing_days} missing trading days."
                    + colorText.END
                )
                return True
            else:
                default_logger().warning(f"Failed to trigger history workflow: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            default_logger().debug(f"Error triggering history download workflow: {e}")
            return False

    @staticmethod
    def ensure_data_freshness(stockDict, trigger_download: bool = True) -> tuple:
        """
        Ensure downloaded pkl data is fresh. If stale, optionally trigger history download.
        
        This should be called after downloading data from actions-data-download to ensure
        the data is up-to-date before using it for scans.
        
        Args:
            stockDict: Dictionary of stock data
            trigger_download: If True, trigger history download workflow when data is stale
            
        Returns:
            tuple: (is_fresh, missing_trading_days)
                   - is_fresh: Boolean indicating if data is fresh
                   - missing_trading_days: Number of missing trading days (0 if fresh)
        """
        try:
            from PKDevTools.classes.PKDateUtilities import PKDateUtilities
            from datetime import datetime
            
            if not stockDict:
                return True, 0
            
            # Get the last trading date
            last_trading_date = PKDateUtilities.tradingDate()
            if hasattr(last_trading_date, 'date'):
                last_trading_date = last_trading_date.date()
            
            # Find the latest date across all stocks
            latest_data_date = None
            for stock, data in stockDict.items():
                is_fresh, data_date, _ = PKAssetsManager.is_data_fresh(data)
                if data_date and (latest_data_date is None or data_date > latest_data_date):
                    latest_data_date = data_date
            
            if latest_data_date is None:
                return True, 0
            
            # Check if data is fresh
            if latest_data_date >= last_trading_date:
                return True, 0
            
            # Calculate missing trading days
            missing_days = PKDateUtilities.trading_days_between(latest_data_date, last_trading_date)
            
            if missing_days > 0:
                default_logger().warning(
                    f"Data is stale by {missing_days} trading days. "
                    f"Latest data: {latest_data_date}, Last trading date: {last_trading_date}"
                )
                
                if trigger_download:
                    # Trigger history download workflow
                    PKAssetsManager.trigger_history_download_workflow(missing_days)
            
            return missing_days <= 0, missing_days
            
        except Exception as e:
            default_logger().debug(f"Error ensuring data freshness: {e}")
            return True, 0

    @staticmethod
    def make_hyperlink(value):
        """Create an Excel hyperlink to TradingView chart for a stock symbol."""
        url = "https://in.tradingview.com/chart?symbol=NSE:{}"
        return '=HYPERLINK("%s", "%s")' % (url.format(ImageUtility.PKImageTools.stockNameFromDecoratedName(value)), value)

    @staticmethod
    def promptSaveResults(sheetName, df_save, defaultAnswer=None, pastDate=None, screenResults=None):
        """
        Save screened results to an Excel file with multiple fallback locations.
        
        This method attempts to save a DataFrame to Excel, trying multiple locations
        in order of preference:
        1. Current working directory / results folder
        2. User's Desktop folder
        3. System temporary directory (last resort)
        
        Also creates a CSV version alongside the Excel file.
        
        Args:
            sheetName: Name of the Excel sheet (truncated to 31 chars)
            df_save: DataFrame to save (will be cleaned of color styles)
            defaultAnswer: Optional default user response for saving (Y/N)
            pastDate: Optional date string for filename (for date-range reports)
            screenResults: Optional additional results (currently unused)
            
        Returns:
            str or None: Path to saved file if successful, None otherwise
        
        Notes:
            - Creates hyperlinks for stock symbols
            - Removes color formatting before saving
            - Filename format: PKS_{sheetName}_{date_range?}_{timestamp}.xlsx
        """
        data = df_save.copy()
        try:
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            data = ImageUtility.PKImageTools.removeAllColorStyles(data)
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            default_logger().debug(e,exc_info=True)
            pass
        try:
            data.reset_index(inplace=True)
            with pd.option_context('mode.chained_assignment', None):
                data["Stock"] = data['Stock'].apply(PKAssetsManager.make_hyperlink)
            data.set_index("Stock", inplace=True)
        except: # pragma: no cover
            pass
        df = data
        isSaved = False
        try:
            if defaultAnswer is None:
                responseLegends = str(
                        OutputControls().takeUserInput(
                            colorText.WARN
                            + f"[>] Do you want to review legends used in the report above? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): ", defaultInput="N"
                        ) or "N"
                    ).upper()
                if "Y" in responseLegends:
                    OutputControls().printOutput(ImageUtility.PKImageTools.getLegendHelpText(table=None).replace("***:",colorText.END+":").replace("***"," " +colorText.FAIL))
                if not PKAssetsManager.configManager.alwaysExportToExcel:
                    response = str(
                        input(
                            colorText.WARN
                            + f"[>] Do you want to save the results in excel file? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): "
                        ) or "N"
                    ).upper()
                else:
                    response = "Y"
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            response = "Y"
        if response is not None and str(response).upper() != "N":
            pastDateString = f"{pastDate}_to_" if pastDate is not None else ""
            filename = (
                f"PKS_{sheetName.strip()}_"
                + pastDateString
                + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
                + ".xlsx"
            )
            desktop = os.path.expanduser("~/Desktop")
            # # the above is valid on Windows (after 7) but if you want it in os normalized form:
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            filePath = ""
            try:
                filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                # Convert the dataframe to an XlsxWriter Excel object.
                df.to_excel(writer, sheet_name=sheetName[-31:]) # sheetname cannot be beyond 31 character
                # Close the Pandas Excel writer and output the Excel file.
                writer.close()
                df.to_csv(filePath.replace(".xlsx",".csv"))
                isSaved = True
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + (
                        "  [+] Error saving file at %s"
                        % filePath
                    )
                    + colorText.END
                )
                try:
                    filePath = os.path.join(desktop, filename)
                    # Create a Pandas Excel writer using XlsxWriter as the engine.
                    writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                    # Convert the dataframe to an XlsxWriter Excel object.
                    df.to_excel(writer, sheet_name=sheetName)
                    # Close the Pandas Excel writer and output the Excel file.
                    writer.close()
                    isSaved = True
                except KeyboardInterrupt: # pragma: no cover
                    raise KeyboardInterrupt
                except Exception as ex:  # pragma: no cover
                    default_logger().debug(ex, exc_info=True)
                    OutputControls().printOutput(
                        colorText.FAIL
                        + (
                            "  [+] Error saving file at %s"
                            % filePath
                        )
                        + colorText.END
                    )
                    try:
                        filePath = os.path.join(tempfile.gettempdir(), filename)
                        # Create a Pandas Excel writer using XlsxWriter as the engine.
                        writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                        # Convert the dataframe to an XlsxWriter Excel object.
                        df.to_excel(writer, sheet_name=sheetName)
                        # Close the Pandas Excel writer and output the Excel file.
                        writer.close()
                        isSaved = True
                    except Exception as ex:  # pragma: no cover
                        pass
            OutputControls().printOutput(
                (colorText.GREEN if isSaved else colorText.FAIL)
                + (("  [+] Results saved to %s" % filePath) if isSaved else "  [+] Failed saving results into Excel file!")
                + colorText.END
            )
            return filePath
        return None

    @staticmethod
    def afterMarketStockDataExists(intraday=False, forceLoad=False):
        """
        Check if after-market stock data cache file exists.
        
        This is a wrapper around Archiver.afterMarketStockDataExists().
        
        Args:
            intraday: Whether to check for intraday data file
            forceLoad: Force check even if cache might be stale
        
        Returns:
            tuple: (exists, cache_file_name)
                   - exists: Boolean indicating if file exists
                   - cache_file_name: Name of the cache file
        """
        exists, cache_file = Archiver.afterMarketStockDataExists(intraday=intraday,
                                                                 forceLoad=forceLoad,
                                                                 date_suffix=True)
        return exists, cache_file

    @Halo(text='', spinner='dots')
    def saveStockData(stockDict, configManager, loadCount, intraday=False, downloadOnly=False, forceSave=False):
        """
        Save stock data to a pickle cache file.
        
        This method persists the stock dictionary to disk for future fast loading.
        
        Args:
            stockDict: Dictionary of stock data to save
            configManager: Configuration manager instance
            loadCount: Previous load count (used to determine if new data exists)
            intraday: Whether this is intraday data
            downloadOnly: If True, saves to actions-data-download directory
            forceSave: Force save even if cache already exists
        
        Returns:
            str: Path to the saved cache file
        
        Notes:
            - Uses highest pickle protocol for efficiency
            - In downloadOnly mode, clears existing patterns and commits to git
        """
        exists, fileName = PKAssetsManager.afterMarketStockDataExists(
            configManager.isIntradayConfig() or intraday
        )
        outputFolder = Archiver.get_user_data_dir()
        if downloadOnly:
            outputFolder = outputFolder.replace(f"results{os.sep}Data","actions-data-download")
            if not os.path.isdir(outputFolder):
                try:
                    os.makedirs(os.path.dirname(f"{outputFolder}{os.sep}"), exist_ok=True)
                except: # pragma: no cover
                    pass
            configManager.deleteFileWithPattern(rootDir=outputFolder)
        cache_file = os.path.join(outputFolder, fileName)
        if not os.path.exists(cache_file) or forceSave or (loadCount >= 0 and len(stockDict) > (loadCount + 1)):
            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(stockDict.copy(), f, protocol=pickle.HIGHEST_PROTOCOL)
                    OutputControls().printOutput(colorText.GREEN + "=> Done." + colorText.END)
                if downloadOnly:
                    # if "RUNNER" not in os.environ.keys():
                        # copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{fileName}")
                        # cacheFileSize = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
                        # if os.path.exists(cache_file) and cacheFileSize >= 1024*1024*40:
                        #     shutil.copy(cache_file,copyFilePath) # copy is the saved source of truth

                    rootDirs = [Archiver.get_user_data_dir(),Archiver.get_user_indices_dir(),outputFolder]
                    patterns = ["*.csv","*.pkl"]
                    for dir in rootDirs:
                        for pattern in patterns:
                            for f in glob.glob(pattern, root_dir=dir, recursive=True):
                                OutputControls().printOutput(colorText.GREEN + f"=> {f}" + colorText.END)
                                if "RUNNER" in os.environ.keys():
                                    Committer.execOSCommand(f"git add {f} -f >/dev/null 2>&1")

            except pickle.PicklingError as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + "=> Error while Caching Stock Data."
                    + colorText.END
                )
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
        else:
            OutputControls().printOutput(
                colorText.GREEN + "=> Already Cached." + colorText.END
            )
            if downloadOnly:
                OutputControls().printOutput(colorText.GREEN + f"=> {cache_file}" + colorText.END)
        return cache_file

    @staticmethod
    def had_rate_limit_errors():
        """
        Check if there have been rate limit errors in previous requests.
        
        Currently returns False as this functionality is disabled.
        Previously used to detect Yahoo Finance rate limiting.
        
        Returns:
            bool: Always returns False
        """
        return False
        """Checks if any stored errors are YFRateLimitError."""
        err = "" #",".join(list(shared._ERRORS.values()))
        hitRateLimit = "YFRateLimitError" in err or "Too Many Requests" in err or "429" in err
        if hitRateLimit:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] We hit a rate limit error in the previous request(s)!"
                + colorText.END
            )
        return hitRateLimit
    
    @Halo(text='  [+] Downloading fresh data from Data Providers...', spinner='dots')
    def downloadLatestData(stockDict,configManager,stockCodes=[],exchangeSuffix=".NS",downloadOnly=False,numStocksPerIteration=0):
        """
        Download latest data directly from data providers (origin source).
        
        This method bypasses caches and fetches fresh data from the primary source.
        Currently a placeholder - actual implementation would use multiprocessing.
        
        Args:
            stockDict: Dictionary to populate with downloaded data
            configManager: Configuration manager
            stockCodes: List of stock symbols to download
            exchangeSuffix: Exchange suffix (e.g., ".NS" for NSE)
            downloadOnly: If True, only downloads without processing
            numStocksPerIteration: Number of stocks per batch (0 = auto)
        
        Returns:
            tuple: (updated_stockDict, leftOutStocks)
        """
        """
        shared._ERRORS.clear()  # Clear previous errors
        # if numStocksPerIteration == 0:
        # maxParallelProcesses = 17
        numStocksPerIteration = 100 #(int(len(stockCodes)/int(len(stockCodes)/maxParallelProcesses)) if len(stockCodes) >= maxParallelProcesses else len(stockCodes)) + 1
        queueCounter = 0
        iterations = int(len(stockCodes)/numStocksPerIteration) + 1
        tasksList = []
        while queueCounter < iterations:
            stocks = []
            if queueCounter < iterations:
                stocks = stockCodes[numStocksPerIteration* queueCounter : numStocksPerIteration* (queueCounter + 1)]
            else:
                stocks = ["DUMMYStock"]#stockCodes[numStocksPerIteration* queueCounter :]
            fn_args = (stocks, configManager.period, configManager.duration,exchangeSuffix)
            task = PKTask(f"DataDownload-{queueCounter}",long_running_fn=PKAssetsManager.fetcher.fetchStockDataWithArgs,long_running_fn_args=fn_args)
            task.userData = stocks
            if len(stocks) > 0:
                tasksList.append(task)
            queueCounter += 1
        """
        processedStocks = []
        """
        if len(tasksList) > 0:
            # Suppress any multiprocessing errors/warnings
            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                PKScheduler.scheduleTasks(tasksList=tasksList, 
                                        label=f"Downloading latest data [{configManager.period},{configManager.duration}] (Total={len(stockCodes)} records in {len(tasksList)} batches){'Be Patient!' if len(stockCodes)> 2000 else ''}",
                                        timeout=(5+2.5*configManager.longTimeout*(4 if downloadOnly else 1)), # 5 sec additional time for multiprocessing setup
                                        minAcceptableCompletionPercentage=(100 if downloadOnly else 100),
                                        showProgressBars=configManager.logsEnabled)
            for task in tasksList:
                if task.result is not None and isinstance(task.result,pd.DataFrame) and not task.result.empty:
                    for stock in task.userData:
                        taskResult = task.result.get(f"{stock}{exchangeSuffix}")
                        if taskResult is not None and isinstance(taskResult,pd.DataFrame) and not taskResult.empty:
                            stockDict[stock] = taskResult.to_dict("split")
                            processedStocks.append(stock)
        """
        leftOutStocks = list(set(stockCodes)-set(processedStocks))
        default_logger().debug(f"Attempted fresh download of {len(stockCodes)} stocks and downloaded {len(processedStocks)} stocks. {len(leftOutStocks)} stocks remaining/ignored.")
        return stockDict, 0

    @Halo(text='  [+] Downloading fresh instruments and their data from Data Providers...', spinner='dots')
    def loadStockData(
        stockDict,
        configManager,
        downloadOnly=False,
        defaultAnswer=None,
        retrial=False,
        forceLoad=False,
        stockCodes=[],
        exchangeSuffix=".NS",
        isIntraday = False,
        forceRedownload=False,
        userDownloadOption=None
    ):
        """
        Primary method for loading stock data from various sources with intelligent fallback.
        
        This is the main entry point for data loading. It implements a sophisticated
        multi-tier caching strategy with selective stock filtering.
        
        Data Source Priority:
        1. Local pickle cache (if fresh and has sufficient data)
        2. GitHub Actions data (actions-data-download branch)
        3. PKBrokers real-time ticks (during market hours)
        4. Origin data providers (fallback)
        
        NEW FEATURE: Selective Loading
        ---------------------------------
        If stockCodes is provided (non-empty list), this method will:
        - Only load data for the specified stocks from cache/sources
        - Only apply fresh ticks to the specified stocks
        - Return a filtered dictionary containing only requested stocks
        
        If stockCodes is empty or None, loads all available stocks.
        
        Args:
            stockDict: Dictionary to populate with loaded data (modified in-place)
            configManager: Configuration manager instance
            downloadOnly: If True, only downloads without processing
            defaultAnswer: Default user response for prompts
            retrial: Whether this is a retry attempt (prevents infinite recursion)
            forceLoad: Force load even if cache exists
            stockCodes: List of specific stock symbols to load (EMPTY = load all)
            exchangeSuffix: Exchange suffix for symbol matching (e.g., ".NS")
            isIntraday: Whether to load intraday data
            forceRedownload: Force redownload even if cache exists
            userDownloadOption: User preference for download source
        
        Returns:
            dict: Updated stockDict containing only requested stocks (filtered by stockCodes)
        
        Examples:
            >>> # Load all stocks
            >>> all_stocks = PKAssetsManager.loadStockData({}, configManager)
            >>> 
            >>> # Load only specific stocks
            >>> selected = PKAssetsManager.loadStockData({}, configManager, stockCodes=['RELIANCE', 'TCS'])
            >>> 
            >>> # During market hours with selective updates
            >>> intraday = PKAssetsManager.loadStockData({}, configManager, isIntraday=True, stockCodes=['INFY', 'HDFC'])
        """
        isIntraday = isIntraday or configManager.isIntradayConfig()
        exists, cache_file = PKAssetsManager.afterMarketStockDataExists(
            isIntraday, forceLoad=forceLoad
        )
        initialLoadCount = len(stockDict)
        leftOutStocks = None
        recentDownloadFromOriginAttempted = False
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        isTrading = PKDateUtilities.isTradingTime() and (PKDateUtilities.wasTradedOn() or not PKDateUtilities.isTodayHoliday()[0])
        if isTrading or not os.path.exists(srcFilePath):
            try:
                from pkbrokers.kite.examples.externals import kite_fetch_save_pickle
                if kite_fetch_save_pickle():
                    default_logger().info("pkl file update succeeded!")
            except Exception as e:
                default_logger().error(f"Error downloading latest file:{e}")
            isTrading = False
        if userDownloadOption is not None and "B" in userDownloadOption: # Backtests
            isTrading = False
        # Check if NSEI data is requested
        if configManager.baseIndex not in stockCodes:
            stockCodes.insert(0,configManager.baseIndex)
        # stockCodes is not None mandates that we start our work based on the downloaded data from yesterday
        if (stockCodes is not None and len(stockCodes) > 0) and (isTrading or downloadOnly):
            recentDownloadFromOriginAttempted = True
            stockDict, leftOutStocks = PKAssetsManager.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(stockCodes) if stockCodes is not None else 0)
            if len(leftOutStocks) > int(len(stockCodes)*0.05) and not PKAssetsManager.had_rate_limit_errors():
                # During live market hours, we may not really get additional data if we didn't
                # get it the first time
                # More than 5 % of stocks are still remaining
                stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,leftOutStocks,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(leftOutStocks) if leftOutStocks is not None else 0)
            # return stockDict
        
        # Filter stockDict to only include requested stocks after download
        if stockCodes and len(stockCodes) > 0:
            # Create a filtered dictionary with only requested stocks
            filtered_stockDict = {}
            for code in stockCodes:
                if code in stockDict:
                    filtered_stockDict[code] = stockDict[code]
            stockDict = filtered_stockDict
            default_logger().debug(f"Filtered to {len(stockDict)} requested stocks")
        
        if downloadOnly or isTrading:
            # We don't want to download from local stale pkl file or stale file at server
            # start_backup()
            return stockDict
        
        default_logger().debug(
            f"Stock data cache file:{cache_file} exists ->{str(exists)}"
        )
        stockDataLoaded = False
        # copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
        # if os.path.exists(copyFilePath):
        #     shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
        if os.path.exists(srcFilePath) and not forceRedownload:
            # Check if local cache is stale OR has insufficient data before loading
            is_local_stale = False
            has_insufficient_data = False
            MIN_ROWS_REQUIRED = 20  # Minimum rows needed for technical indicators (SMA20)
            try:
                with open(srcFilePath, "rb") as f:
                    sample_data = pickle.load(f)
                    if sample_data and len(sample_data) > 0:
                        # Check freshness of first available stock
                        # If filtering by stockCodes, prioritize checking requested stocks
                        sample_stock = None
                        if stockCodes and len(stockCodes) > 0:
                            # Find first requested stock that exists in sample
                            for code in stockCodes:
                                if code in sample_data:
                                    sample_stock = code
                                    break
                        if not sample_stock:
                            sample_stock = list(sample_data.keys())[0]
                        
                        sample_stock_data = sample_data[sample_stock]
                        is_fresh, data_date, trading_days_old = PKAssetsManager.is_data_fresh(sample_stock_data, max_stale_trading_days=1)
                        if not is_fresh:
                            is_local_stale = True
                            default_logger().info(f"Local cache is stale (data_date={data_date}, trading_days_old={trading_days_old}), will download fresh data")
                            OutputControls().printOutput(
                                colorText.WARN
                                + f"  [!] Local cache is stale (data from {data_date}), downloading fresh data..."
                                + colorText.END
                            )
                        
                        # Check data quality (minimum rows per stock)
                        row_count = 0
                        if isinstance(sample_stock_data, pd.DataFrame):
                            row_count = len(sample_stock_data)
                        elif isinstance(sample_stock_data, dict) and 'data' in sample_stock_data:
                            row_count = len(sample_stock_data.get('data', []))
                        elif isinstance(sample_stock_data, dict) and 'index' in sample_stock_data:
                            row_count = len(sample_stock_data.get('index', []))
                        
                        if row_count < MIN_ROWS_REQUIRED:
                            has_insufficient_data = True
                            default_logger().info(f"Local cache has insufficient data ({row_count} rows < {MIN_ROWS_REQUIRED} required), will download fresh data")
                            OutputControls().printOutput(
                                colorText.WARN
                                + f"  [!] Local cache has insufficient data ({row_count} rows), downloading fresh data..."
                                + colorText.END
                            )
            except Exception as e:
                default_logger().debug(f"Error checking local cache freshness: {e}")
                # If we can't check, assume it's OK and try loading
            
            # Only load from local cache if it's fresh AND has sufficient data
            if not is_local_stale and not has_insufficient_data:
                stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(
                    stockDict, configManager, downloadOnly, defaultAnswer, 
                    exchangeSuffix, cache_file, isTrading, stockCodes
                )
            else:
                # Try to download fresh data from GitHub first
                success, github_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github(intraday=isIntraday)
                if success and github_path:
                    # Replace local cache with fresh GitHub data
                    try:
                        shutil.copy(github_path, srcFilePath)
                    except Exception as e:
                        default_logger().error(f"Error copying GitHub data to local cache: {e}")
                    default_logger().info(f"Replaced stale/insufficient local cache with fresh data from GitHub ({num_instruments} instruments)")
                    OutputControls().printOutput(
                        colorText.GREEN
                        + f"  [+] Downloaded and replaced cache with fresh data ({num_instruments} instruments)"
                        + colorText.END
                    )
                    # Now load from the updated local cache
                    stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(
                        stockDict, configManager, downloadOnly, defaultAnswer, 
                        exchangeSuffix, cache_file, isTrading, stockCodes
                    )
                else:
                    # If GitHub download failed, still try to load from local (might be better than nothing)
                    default_logger().warning("Failed to download fresh data from GitHub, using stale/insufficient local cache")
                    stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(
                        stockDict, configManager, downloadOnly, defaultAnswer, 
                        exchangeSuffix, cache_file, isTrading, stockCodes
                    )
        if (
            not stockDataLoaded
            and ("1d" if isIntraday else ConfigManager.default_period)
            == configManager.period
            and ("1m" if isIntraday else ConfigManager.default_duration)
            == configManager.duration
        ) or forceRedownload:
            stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(
                stockDict, configManager, downloadOnly, defaultAnswer, retrial, 
                forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, 
                cache_file, isTrading
            )
        if not stockDataLoaded:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] Cache unavailable on pkscreener server, Continuing.."
                + colorText.END
            )
        if not stockDataLoaded and not recentDownloadFromOriginAttempted and not PKAssetsManager.had_rate_limit_errors():
            stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(stockCodes) if stockCodes is not None else 0)
        # See if we need to save stock data
        stockDataLoaded = stockDataLoaded or (len(stockDict) > 0 and (len(stockDict) != initialLoadCount))
        leftOutStocks = list(set(stockCodes)-set(list(stockDict.keys())))
        if len(leftOutStocks) > int(len(stockCodes)*0.05) and not PKAssetsManager.had_rate_limit_errors():
            # More than 5 % of stocks are still remaining
            stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,leftOutStocks,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(leftOutStocks) if leftOutStocks is not None else 0)
        if stockDataLoaded and downloadOnly:
            PKAssetsManager.saveStockData(stockDict,configManager,initialLoadCount,isIntraday,downloadOnly, forceSave=stockDataLoaded)
        
        # Final filter to ensure only requested stocks are returned
        if stockCodes and len(stockCodes) > 0:
            filtered_final = {}
            for code in stockCodes:
                if code in stockDict:
                    filtered_final[code] = stockDict[code]
            stockDict = filtered_final
            default_logger().debug(f"Final filter: returning {len(stockDict)} of {len(stockCodes)} requested stocks")
        
        # start_backup()
        return stockDict

    @Halo(text='  [+] Loading data from local cache...', spinner='dots')
    def loadDataFromLocalPickle(stockDict, configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading, stockCodes=None):
        """
        Load stock data from local pickle cache file.
        
        This method loads cached data and optionally filters to requested stocks.
        
        Args:
            stockDict: Dictionary to populate with loaded data
            configManager: Configuration manager instance
            downloadOnly: If True, only downloads without processing
            defaultAnswer: Default user response for prompts
            exchangeSuffix: Exchange suffix for symbol matching
            cache_file: Name of the cache file
            isTrading: Whether market is currently trading
            stockCodes: Optional list of stock symbols to load (None = load all)
        
        Returns:
            tuple: (updated_stockDict, stockDataLoaded)
                   - updated_stockDict: Dictionary with loaded data (filtered if stockCodes provided)
                   - stockDataLoaded: Boolean indicating successful load
        
        Notes:
            - Applies fresh ticks after loading if requested
            - Preserves existing MF/FII/FairValue data during trading hours
            - Handles DataFrame column duplication (lowercase/uppercase)
        """
        stockDataLoaded = False
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)

        try:
            with open(srcFilePath, "rb") as f:
                stockData = pickle.load(f)
            if not stockData:
                return stockDict, stockDataLoaded
            if not downloadOnly:
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"\n  [+] Automatically Using [{len(stockData)}] Tickers' Cached Stock Data"
                    + (" due to After-Market hours" if not PKDateUtilities.isTradingTime() else "")
                    + colorText.END
                )
            multiIndex = stockData.keys()
            if isinstance(multiIndex, pd.MultiIndex):
                listStockCodes = sorted(set(multiIndex.get_level_values(0)))
            else:
                listStockCodes = list(stockData.keys())
            if exchangeSuffix and any(exchangeSuffix in code for code in listStockCodes):
                listStockCodes = [x.replace(exchangeSuffix, "") for x in listStockCodes]
            # Filter out numeric keys (instrument tokens) - they have stale data
            # and the same stocks exist with proper symbol keys with fresh data
            listStockCodes = [code for code in listStockCodes if not str(code).isdigit()]
            
            # Apply stockCodes filter if provided
            if stockCodes and len(stockCodes) > 0:
                listStockCodes = [code for code in listStockCodes if code in stockCodes]
                default_logger().debug(f"Filtered local pickle to {len(listStockCodes)} requested stocks")
            
            for stock in listStockCodes:
                df_or_dict = stockData.get(stock)
                # Handle DataFrame with duplicate lowercase/uppercase columns
                if isinstance(df_or_dict, pd.DataFrame):
                    # Merge lowercase and uppercase OHLCV columns
                    ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
                    clean_df = pd.DataFrame(index=df_or_dict.index)
                    for col in ohlcv_cols:
                        lower_col = col
                        upper_col = col.capitalize()
                        has_lower = lower_col in df_or_dict.columns
                        has_upper = upper_col in df_or_dict.columns
                        if has_lower and has_upper:
                            # Both exist - merge (fillna from lowercase with uppercase)
                            lower_data = df_or_dict[lower_col].iloc[:, 0] if isinstance(df_or_dict[lower_col], pd.DataFrame) else df_or_dict[lower_col]
                            upper_data = df_or_dict[upper_col].iloc[:, 0] if isinstance(df_or_dict[upper_col], pd.DataFrame) else df_or_dict[upper_col]
                            clean_df[col] = lower_data.fillna(upper_data)
                        elif has_lower:
                            clean_df[col] = df_or_dict[lower_col].iloc[:, 0] if isinstance(df_or_dict[lower_col], pd.DataFrame) else df_or_dict[lower_col]
                        elif has_upper:
                            clean_df[col] = df_or_dict[upper_col].iloc[:, 0] if isinstance(df_or_dict[upper_col], pd.DataFrame) else df_or_dict[upper_col]
                    # Copy other non-OHLCV columns
                    for col in df_or_dict.columns:
                        if col.lower() not in ohlcv_cols and col not in clean_df.columns:
                            clean_df[col] = df_or_dict[col]
                    df_or_dict = clean_df.to_dict("split")
                existingPreLoadedData = stockDict.get(stock)
                if existingPreLoadedData:
                    if isTrading:
                        for col in ["MF", "FII", "MF_Date", "FII_Date", "FairValue"]:
                            existingPreLoadedData[col] = df_or_dict.get(col)
                        stockDict[stock] = existingPreLoadedData
                    else:
                        stockDict[stock] = {**existingPreLoadedData, **df_or_dict}
                elif not isTrading:
                    stockDict[stock] = df_or_dict
            stockDataLoaded = True
            
            # Always try to apply fresh real-time data or update timestamps
            # During trading hours: use current time for latest timestamps
            # After market hours: update today's data to market close time (15:30) if it has early morning timestamps
            if stockDict and len(stockDict) > 0:
                # Pass stockCodes to _apply_fresh_ticks_to_data for selective updates
                stockDict = PKAssetsManager._apply_fresh_ticks_to_data(stockDict, stockCodes=stockCodes)
            if stockDict and isTrading:                
                # Save updated stockDict back to PKL file if we're in downloadOnly mode or GitHub Actions
                # This ensures PKL files committed to actions-data-download branch contain the latest tick data
                if downloadOnly or ("RUNNER" in os.environ.keys()):
                    # Force save the updated data with fresh ticks
                    isIntraday = configManager.isIntradayConfig()
                    PKAssetsManager.saveStockData(stockDict, configManager, len(stockDict) if stockDict else 0, isIntraday, downloadOnly, forceSave=True)
                
                # Also validate and warn if still stale
                fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
                    stockDict, isTrading=isTrading
                )
                if stale_count > 0:
                    default_logger().debug(
                        f"Warning: {stale_count} stocks still have stale data after applying fresh ticks (oldest: {oldest_date})"
                    )
        except (pickle.UnpicklingError, EOFError) as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL + "  [+] Error while Reading Stock Cache." + colorText.END
            )
            if PKAssetsManager.promptFileExists(defaultAnswer=defaultAnswer) == "Y":
                configManager.deleteFileWithPattern()
        except KeyboardInterrupt:
            raise
        return stockDict, stockDataLoaded

    @Halo(text='', spinner='dots')
    def downloadSavedDefaultsFromServer(cache_file):
        """
        Download default saved data from server (legacy method).
        
        This method is a simpler version of downloadSavedDataFromServer
        that only downloads without processing.
        
        Args:
            cache_file: Name of the cache file to download
        
        Returns:
            bool: True if download succeeded, False otherwise
        """
        fileDownloaded = False
        resp = Utility.tools.tryFetchFromServer(cache_file)
        if resp is not None:
            default_logger().debug(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            serverBytes = int(contentLength) if contentLength is not None else 0
            KB = 1024
            MB = KB * 1024
            chunksize = MB if serverBytes >= MB else (KB if serverBytes >= KB else 1)
            filesize = int( serverBytes / chunksize)
            if filesize > 40: #Something definitely went wrong. It should be upward of 40bytes
                try:
                    with open(os.path.join(Archiver.get_user_data_dir(), cache_file),"w+",) as f: # .split(os.sep)[-1]
                        f.write(resp.text)
                    fileDownloaded = True
                except: # pragma: no cover
                    pass
        return fileDownloaded

    @staticmethod
    def downloadSavedDataFromServer(stockDict, configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading):
        """
        Download saved data from PK Screener server as fallback.
        
        This method attempts to download pre-saved pickle files from the project server
        when local cache is unavailable or stale.
        
        Args:
            stockDict: Dictionary to populate with downloaded data
            configManager: Configuration manager instance
            downloadOnly: If True, only downloads without processing
            defaultAnswer: Default user response for prompts
            retrial: Whether this is a retry attempt
            forceLoad: Force load even if cache exists
            stockCodes: List of stock symbols to load
            exchangeSuffix: Exchange suffix for symbol matching
            isIntraday: Whether this is intraday data
            forceRedownload: Force redownload from server
            cache_file: Name of the cache file
            isTrading: Whether market is currently trading
        
        Returns:
            tuple: (updated_stockDict, stockDataLoaded)
        """
        stockDataLoaded = False
        resp = Utility.tools.tryFetchFromServer(cache_file)
        if resp is not None:
            default_logger().debug(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            serverBytes = int(contentLength) if contentLength is not None else 0
            KB = 1024
            MB = KB * 1024
            chunksize = MB if serverBytes >= MB else (KB if serverBytes >= KB else 1)
            filesize = int( serverBytes / chunksize)
            if filesize > 20 and chunksize == MB: # Saved data can't be in KBs. Something definitely went wrong. It should be upward of 40MB
                bar, spinner = Utility.tools.getProgressbarStyle()
                try:
                    f = open(
                            os.path.join(Archiver.get_user_data_dir(), cache_file),
                            "w+b",
                        )  # .split(os.sep)[-1]
                    dl = 0
                    with alive_bar(
                            filesize, bar=bar, spinner=spinner, manual=True
                        ) as progressbar:
                        for data in resp.iter_content(chunk_size=chunksize):
                            dl += 1
                            f.write(data)
                            progressbar(dl / filesize)
                            if dl >= filesize:
                                progressbar(1.0)
                    f.close()
                    with open(
                            os.path.join(Archiver.get_user_data_dir(), cache_file),
                            "rb",
                        ) as f:
                        stockData = pickle.load(f)
                    if len(stockData) > 0:
                        multiIndex = stockData.keys()
                        if isinstance(multiIndex, pd.MultiIndex):
                                # If we requested for multiple stocks from yfinance
                                # we'd have received a multiindex dataframe
                            listStockCodes = multiIndex.get_level_values(0)
                            listStockCodes = sorted(list(filter(None,list(set(listStockCodes)))))
                            if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                                listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                        else:
                            listStockCodes = list(stockData.keys())
                            if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                                listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                        
                        # Apply stockCodes filter if provided
                        if stockCodes and len(stockCodes) > 0:
                            listStockCodes = [code for code in listStockCodes if code in stockCodes]
                            default_logger().debug(f"Filtered server data to {len(listStockCodes)} requested stocks")
                        
                        for stock in listStockCodes:
                            df_or_dict = stockData.get(stock)
                            df_or_dict = df_or_dict.to_dict("split") if isinstance(df_or_dict,pd.DataFrame) else df_or_dict
                                # This will keep all the latest security data we downloaded
                                # just now and also copy the additional data like, MF/FII,FairValue
                                # etc. data, from yesterday's saved data.
                            try:
                                existingPreLoadedData = stockDict.get(stock)
                                if existingPreLoadedData is not None:
                                    if isTrading:
                                            # Only copy the MF/FII/FairValue data and leave the stock prices as is.
                                        cols = ["MF", "FII","MF_Date","FII_Date","FairValue"]
                                        for col in cols:
                                            existingPreLoadedData[col] = df_or_dict.get(col)
                                        stockDict[stock] = existingPreLoadedData
                                    else:
                                        stockDict[stock] = df_or_dict | existingPreLoadedData
                                else:
                                    if not isTrading:
                                        stockDict[stock] = df_or_dict
                            except: # pragma: no cover
                                    # Probably, the "stock" got removed from the latest download
                                    # and so, was not found in stockDict
                                continue
                        stockDataLoaded = True
                        
                        # Validate data freshness after server download
                        if stockDict and len(stockDict) > 0:
                            # Pass stockCodes for selective tick updates
                            stockDict = PKAssetsManager._apply_fresh_ticks_to_data(stockDict, stockCodes=stockCodes)
                        # if isTrading:
                        #     fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
                        #         stockDict, isTrading=isTrading
                        #     )
                        #     if stale_count > 0:
                        #         default_logger().warning(
                        #             f"[DATA-FRESHNESS] Server data has {stale_count} stale stocks. "
                        #             f"Oldest: {oldest_date}. Fresh ticks recommended."
                        #         )
                        #         # Trigger history download workflow if data is stale
                        #         is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
                        #             stockDict, trigger_download=True
                        #         )
                        #         if not is_fresh and missing_days > 0:
                        #             # Try to apply fresh tick data while history download is in progress
                        #             stockDict = PKAssetsManager._apply_fresh_ticks_to_data(stockDict, stockCodes=stockCodes)
                        # Remove the progress bar now!
                        OutputControls().moveCursorUpLines(1)
                except KeyboardInterrupt: # pragma: no cover
                    raise KeyboardInterrupt
                except Exception as e:  # pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    OutputControls().printOutput("[!] Download Error - " + str(e))
            else:
                default_logger().debug(
                        f"Stock data cache file:{cache_file} on server has length ->{filesize} {'Mb' if chunksize >= MB else ('Kb' if chunksize >= KB else 'bytes')}"
                    )
            if not retrial and not stockDataLoaded:
                # Don't try for more than once.
                stockDict = PKAssetsManager.loadStockData(
                        stockDict,
                        configManager,
                        downloadOnly,
                        defaultAnswer,
                        retrial=True,
                        forceLoad=forceLoad,
                        stockCodes=stockCodes,
                        exchangeSuffix=exchangeSuffix,
                        isIntraday = isIntraday,
                        forceRedownload=forceRedownload
                    )
                
        return stockDict,stockDataLoaded

    @staticmethod
    def promptFileExists(cache_file="stock_data_*.pkl", defaultAnswer=None):
        """
        Prompt user for permission to overwrite existing file.
        
        Args:
            cache_file: Name or pattern of the cache file
            defaultAnswer: Optional default answer (Y/N)
        
        Returns:
            str: "Y" if user agrees to overwrite, "N" otherwise
        """
        try:
            if defaultAnswer is None:
                response = str(
                    input(
                        colorText.WARN
                        + "[>] "
                        + cache_file
                        + " already exists. Do you want to replace this? [Y/N] (Default: Y): "
                ) or "Y").upper()
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        return "Y" if response != "N" else "N"