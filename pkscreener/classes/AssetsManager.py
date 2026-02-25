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
            max_stale_trading_days: Maximum acceptable age in TRADING days (not calendar days)
            
        Returns:
            tuple: (is_fresh: bool, data_date: date or None, trading_days_old: int)
        """
        try:
            from datetime import datetime
            from PKDevTools.classes.PKDateUtilities import PKDateUtilities
            
            # Get the last trading date (accounts for weekends and holidays)
            last_trading_date = PKDateUtilities.tradingDate()
            if isinstance(last_trading_date, datetime):
                last_trading_date = last_trading_date.date()
            
            last_date = None
            
            # Handle DataFrame
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
        Validate freshness of stock data and log warnings for stale data.
        
        Args:
            stockDict: Dictionary of stock data
            isTrading: Whether market is currently trading
            
        Returns:
            tuple: (fresh_count, stale_count, oldest_date)
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
    def _apply_fresh_ticks_to_data(stockDict):
        """
        Apply fresh tick data from PKBrokers to update stale stock data.
        
        This method downloads the latest ticks.json from PKBrokers/PKScreener
        and merges today's OHLCV data into the existing stockDict.
        
        Args:
            stockDict: Dictionary of stock data (symbol -> dict with 'data', 'columns', 'index')
            
        Returns:
            dict: Updated stockDict with fresh tick data merged
        """
        # #region agent log
        import json
        log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:_apply_fresh_ticks_to_data:181","message":"Function entry","data":{"stockDict_keys":list(stockDict.keys())[:5] if stockDict else [],"stockDict_len":len(stockDict) if stockDict else 0},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except Exception as e:
            try:
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:_apply_fresh_ticks_to_data:181","message":"Error in function entry log","data":{"error":str(e)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
        # #endregion
        import requests
        from datetime import datetime
        
        try:
            # Try to download fresh ticks from multiple sources
            ticks_sources = [
                "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/ticks.json",
                "https://raw.githubusercontent.com/pkjmesra/PKBrokers/main/pkbrokers/kite/examples/results/Data/ticks.json",
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
                # #region agent log
                import json
                log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
                try:
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"AssetsManager.py:_apply_fresh_ticks_to_data:229","message":"No ticks data available, will update timestamps to market close","data":{},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                except: pass
                # #endregion
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
                
                for symbol, stock_data in stockDict.items():
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
            
            # Apply ticks to stockDict
            for instrument_token, tick_info in ticks_data.items():
                if not isinstance(tick_info, dict):
                    continue
                
                symbol = tick_info.get('trading_symbol', '')
                ohlcv = tick_info.get('ohlcv', {})
                
                if not symbol or not ohlcv or ohlcv.get('close', 0) <= 0:
                    continue
                
                # Check if ohlcv has a timestamp field (alternative to last_update)
                ohlcv_timestamp = ohlcv.get('timestamp')
                
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
                    # #region agent log
                    import json
                    log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
                    try:
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:327","message":"Determining timestamp for symbol","data":{"symbol":symbol,"is_trading_hours":is_trading_hours,"tick_info_keys":list(tick_info.keys())[:5] if isinstance(tick_info, dict) else None,"has_last_update":"last_update" in tick_info if isinstance(tick_info, dict) else False},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    if is_trading_hours:
                        # Use timestamp from ticks.json (when the data was actually captured)
                        # This shows the actual time when the tick data was saved for each stock
                        # Try multiple sources: last_update, last_updated (top level), ohlcv.timestamp, or current time
                        last_update = tick_info.get('last_update') or tick_info.get('last_updated') or ohlcv_timestamp
                        # #region agent log
                        try:
                            with open(log_path, 'a') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:333","message":"Checking last_update","data":{"symbol":symbol,"last_update":str(last_update) if last_update else None,"last_update_type":type(last_update).__name__ if last_update else None,"ohlcv_timestamp":str(ohlcv_timestamp) if ohlcv_timestamp else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                        except: pass
                        # #endregion
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
                                timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
                                # #region agent log
                                try:
                                    with open(log_path, 'a') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:344","message":"Using last_update timestamp","data":{"symbol":symbol,"timestamp_str":timestamp_str},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                            except Exception as e:
                                # Fallback to current time if last_update parsing fails
                                timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')
                                # #region agent log
                                try:
                                    with open(log_path, 'a') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:347","message":"last_update parsing failed, using current time","data":{"symbol":symbol,"error":str(e),"timestamp_str":timestamp_str},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                        else:
                            # Fallback to current time if last_update not available
                            timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')
                            # #region agent log
                            try:
                                with open(log_path, 'a') as f:
                                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:350","message":"last_update not available, using current time","data":{"symbol":symbol,"timestamp_str":timestamp_str},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                            except: pass
                            # #endregion
                    else:
                        # After market hours, try to use the actual timestamp when data was captured
                        # This shows when each stock's data was actually updated, not just market close time
                        last_update = tick_info.get('last_update') or tick_info.get('last_updated') or ohlcv_timestamp
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
                                timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
                                # #region agent log
                                try:
                                    with open(log_path, 'a') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:354","message":"Market closed, using data capture timestamp","data":{"symbol":symbol,"timestamp_str":timestamp_str,"last_update":str(last_update)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                            except Exception as e:
                                # Fallback to market close time if parsing fails
                                timestamp_str = f"{today_str} 15:30:00"
                                # #region agent log
                                try:
                                    with open(log_path, 'a') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:375","message":"Market closed, timestamp parsing failed, using market close time","data":{"symbol":symbol,"timestamp_str":timestamp_str,"error":str(e)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                        else:
                            # No timestamp available, use market close time
                            timestamp_str = f"{today_str} 15:30:00"
                            # #region agent log
                            try:
                                with open(log_path, 'a') as f:
                                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"AssetsManager.py:_apply_fresh_ticks_to_data:382","message":"Market closed, no timestamp available, using market close time","data":{"symbol":symbol,"timestamp_str":timestamp_str},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                            except: pass
                            # #endregion
                    
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
                    
                    # Append today's fresh data with proper timestamp
                    new_rows.append(today_row)
                    new_index.append(timestamp_str)
                    
                    # #region agent log
                    import json
                    log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
                    try:
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"AssetsManager.py:_apply_fresh_ticks_to_data:320","message":"Setting timestamp for symbol","data":{"symbol":symbol,"timestamp_str":timestamp_str,"is_trading_hours":is_trading_hours,"new_index_last":new_index[-1] if new_index else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
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
                    + f"  [+] Applied fresh tick data to {updated_count} stocks."
                    + colorText.END
                )
            
        except Exception as e:
            # #region agent log
            import json
            log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
            try:
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"AssetsManager.py:_apply_fresh_ticks_to_data:343","message":"Exception in _apply_fresh_ticks_to_data","data":{"error":str(e)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            default_logger().debug(f"Error applying fresh ticks: {e}")
        
        # #region agent log
        import json
        log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
        try:
            sample_symbol = list(stockDict.keys())[0] if stockDict else None
            sample_index = stockDict[sample_symbol]['index'][-1] if sample_symbol and stockDict.get(sample_symbol, {}).get('index') else None
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:_apply_fresh_ticks_to_data:357","message":"Function exit","data":{"updated_count":updated_count,"sample_symbol":sample_symbol,"sample_index_last":str(sample_index) if sample_index else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        return stockDict

    @staticmethod
    def download_fresh_pkl_from_github() -> tuple:
        """
        Download the latest pkl file from GitHub actions-data-download branch.
        
        This method tries multiple URLs and date formats to find the most recent
        stock_data_DDMMYYYY.pkl file.
        
        Returns:
            tuple: (success, file_path, num_instruments)
        """
        import requests
        import pickle
        from datetime import datetime, timedelta
        
        try:
            today = datetime.now()
            data_dir = Archiver.get_user_data_dir()
            
            # URLs and date formats to try
            urls_to_try = []
            
            for days_ago in range(0, 10):
                check_date = today - timedelta(days=days_ago)
                date_str_full = check_date.strftime('%d%m%Y')
                date_str_short = check_date.strftime('%-d%m%y') if hasattr(check_date, 'strftime') else check_date.strftime('%d%m%y').lstrip('0')
                
                for date_str in [date_str_full, date_str_short]:
                    urls_to_try.extend([
                        f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/stock_data_{date_str}.pkl",
                        f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/stock_data_{date_str}.pkl",
                    ])
            
            # Also try generic names
            urls_to_try.extend([
                "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/daily_candles.pkl",
                "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/daily_candles.pkl",
            ])
            
            output_path = os.path.join(data_dir, "stock_data_github.pkl")
            
            # Track best file (most rows per stock)
            best_file = None
            best_url = None
            best_rows_per_stock = 0
            best_num_instruments = 0
            
            for url in urls_to_try:
                try:
                    default_logger().debug(f"Trying to download pkl from: {url}")
                    response = requests.get(url, timeout=60)
                    
                    if response.status_code == 200 and len(response.content) > 10000:
                        # Check data quality before accepting
                        temp_path = output_path + ".tmp"
                        with open(temp_path, 'wb') as f:
                            f.write(response.content)
                        
                        # Verify it's a valid pkl and check quality
                        with open(temp_path, 'rb') as f:
                            data = pickle.load(f)
                        
                        if data and len(data) > 0:
                            # Check average rows per stock (quality indicator)
                            sample_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'SBIN']
                            rows_count = []
                            for sym in sample_symbols:
                                if sym in data:
                                    item = data[sym]
                                    if isinstance(item, pd.DataFrame):
                                        rows_count.append(len(item))
                                    elif isinstance(item, dict) and 'data' in item:
                                        rows_count.append(len(item['data']))
                            
                            avg_rows = sum(rows_count) / len(rows_count) if rows_count else 0
                            
                            # Prefer files with more rows (full history = ~251 rows, incomplete = 1-10 rows)
                            if avg_rows > best_rows_per_stock:
                                best_file = temp_path
                                best_url = url
                                best_rows_per_stock = avg_rows
                                best_num_instruments = len(data)
                                default_logger().debug(f"Found better file: {url} ({len(data)} instruments, avg {avg_rows:.1f} rows/stock)")
                            
                except Exception as e:
                    default_logger().debug(f"Failed to download from {url}: {e}")
                    continue
            
            # Use the best file found
            if best_file and best_rows_per_stock >= 100:  # Require at least 100 rows per stock (full history)
                import shutil
                shutil.move(best_file, output_path)
                default_logger().info(f"Downloaded best pkl from GitHub: {best_url} ({best_num_instruments} instruments, avg {best_rows_per_stock:.1f} rows/stock)")
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Downloaded fresh data from GitHub ({best_num_instruments} instruments, {best_rows_per_stock:.0f} rows/stock)"
                    + colorText.END
                )
                return True, output_path, best_num_instruments
            elif best_file:
                # Even if not ideal, use it if it's the best we found
                import shutil
                shutil.move(best_file, output_path)
                default_logger().warning(f"Downloaded pkl with limited history: {best_url} ({best_num_instruments} instruments, avg {best_rows_per_stock:.1f} rows/stock)")
                return True, output_path, best_num_instruments
            
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
            True if workflow was triggered successfully
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

    def make_hyperlink(value):
        url = "https://in.tradingview.com/chart?symbol=NSE:{}"
        return '=HYPERLINK("%s", "%s")' % (url.format(ImageUtility.PKImageTools.stockNameFromDecoratedName(value)), value)

    # Save screened results to excel
    def promptSaveResults(sheetName,df_save, defaultAnswer=None,pastDate=None,screenResults=None):
        """
        Tries to save the dataframe output into an excel file.

        It will first try to save to the current-working-directory/results/

        If it fails to save, it will then try to save to Desktop and then eventually into
        a temporary directory.
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
                            + f"[>] Do you want to review legends used in the report above? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): ",defaultInput="N"
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
        if response is not None and response.upper() != "N":
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

    def afterMarketStockDataExists(intraday=False, forceLoad=False):
        exists, cache_file = Archiver.afterMarketStockDataExists(intraday=intraday,
                                                                 forceLoad=forceLoad,
                                                                 date_suffix=True)
        return exists, cache_file

    @Halo(text='', spinner='dots')
    def saveStockData(stockDict, configManager, loadCount, intraday=False, downloadOnly=False, forceSave=False):
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

    def had_rate_limit_errors():
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
        default_logger().debug(f"Attempted fresh download of {len(stockCodes)} stocks and downloaded {len(processedStocks)} stocks. {len(leftOutStocks)} stocks remaining.")
        return stockDict, leftOutStocks

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
        # #region agent log
        import json
        log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadStockData:842","message":"loadStockData entry","data":{"stockCodes_len":len(stockCodes) if stockCodes else 0,"downloadOnly":downloadOnly,"isTrading":PKDateUtilities.isTradingTime()},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        isIntraday = isIntraday or configManager.isIntradayConfig()
        exists, cache_file = PKAssetsManager.afterMarketStockDataExists(
            isIntraday, forceLoad=forceLoad
        )
        initialLoadCount = len(stockDict)
        leftOutStocks = None
        recentDownloadFromOriginAttempted = False
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        isTrading = PKDateUtilities.isTradingTime() and (PKDateUtilities.wasTradedOn() or not PKDateUtilities.isTodayHoliday()[0])
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadStockData:870","message":"isTrading check","data":{"isTrading":isTrading,"cache_file":cache_file,"exists":exists},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
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
                stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(stockDict,configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading)
            else:
                # Try to download fresh data from GitHub first
                success, github_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
                if success and github_path:
                    # Replace local cache with fresh GitHub data
                    import shutil
                    shutil.copy(github_path, srcFilePath)
                    default_logger().info(f"Replaced stale/insufficient local cache with fresh data from GitHub ({num_instruments} instruments)")
                    OutputControls().printOutput(
                        colorText.GREEN
                        + f"  [+] Downloaded and replaced cache with fresh data ({num_instruments} instruments)"
                        + colorText.END
                    )
                    # Now load from the updated local cache
                    stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(stockDict,configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading)
                else:
                    # If GitHub download failed, still try to load from local (might be better than nothing)
                    default_logger().warning("Failed to download fresh data from GitHub, using stale/insufficient local cache")
                    stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(stockDict,configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading)
        if (
            not stockDataLoaded
            and ("1d" if isIntraday else ConfigManager.default_period)
            == configManager.period
            and ("1m" if isIntraday else ConfigManager.default_duration)
            == configManager.duration
        ) or forceRedownload:
            stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(stockDict,configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading)
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
        # start_backup()
        return stockDict

    @Halo(text='  [+] Loading data from local cache...', spinner='dots')
    def loadDataFromLocalPickle(stockDict, configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading):
        # #region agent log
        import json
        log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadDataFromLocalPickle:930","message":"loadDataFromLocalPickle entry","data":{"isTrading":isTrading,"stockDict_len":len(stockDict) if stockDict else 0,"cache_file":cache_file},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
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
            # #region agent log
            import json
            log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
            try:
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadDataFromLocalPickle:1030","message":"Checking if should apply fresh ticks","data":{"isTrading":isTrading,"stockDict_len":len(stockDict) if stockDict else 0,"stockDict_keys_sample":list(stockDict.keys())[:3] if stockDict else []},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except Exception as e:
                try:
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadDataFromLocalPickle:1030","message":"Error logging","data":{"error":str(e)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                except: pass
            # #endregion
            if stockDict:
                # #region agent log
                try:
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadDataFromLocalPickle:1032","message":"About to call _apply_fresh_ticks_to_data","data":{"isTrading":isTrading,"stockDict_len":len(stockDict) if stockDict else 0},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                except: pass
                # #endregion
                # Always apply fresh ticks to update timestamps (during trading: current time, after hours: market close time)
                stockDict = PKAssetsManager._apply_fresh_ticks_to_data(stockDict)
                # #region agent log
                try:
                    sample_stock = list(stockDict.keys())[0] if stockDict else None
                    sample_index = stockDict[sample_stock]['index'][-1] if sample_stock and stockDict.get(sample_stock, {}).get('index') else None
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadDataFromLocalPickle:1033","message":"After _apply_fresh_ticks_to_data","data":{"stockDict_len":len(stockDict) if stockDict else 0,"sample_stock":sample_stock,"sample_index_last":str(sample_index) if sample_index else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                except: pass
                # #endregion
                
                # Save updated stockDict back to PKL file if we're in downloadOnly mode or GitHub Actions
                # This ensures PKL files committed to actions-data-download branch contain the latest tick data
                if downloadOnly or ("RUNNER" in os.environ.keys()):
                    # #region agent log
                    try:
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadDataFromLocalPickle:1040","message":"Saving updated stockDict with fresh ticks to PKL","data":{"downloadOnly":downloadOnly,"hasRUNNER":"RUNNER" in os.environ.keys(),"stockDict_len":len(stockDict) if stockDict else 0},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
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

    def downloadSavedDataFromServer(stockDict, configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading):
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
                        if stockDict and isTrading:
                            fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
                                stockDict, isTrading=isTrading
                            )
                            if stale_count > 0:
                                default_logger().warning(
                                    f"[DATA-FRESHNESS] Server data has {stale_count} stale stocks. "
                                    f"Oldest: {oldest_date}. Fresh ticks recommended."
                                )
                                # Trigger history download workflow if data is stale
                                is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
                                    stockDict, trigger_download=True
                                )
                                if not is_fresh and missing_days > 0:
                                    # Try to apply fresh tick data while history download is in progress
                                    stockDict = PKAssetsManager._apply_fresh_ticks_to_data(stockDict)
                        # copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
                        # srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
                        # if os.path.exists(copyFilePath) and os.path.exists(srcFilePath):
                        #     shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
                        # if not os.path.exists(copyFilePath) and os.path.exists(srcFilePath): # Let's make a copy of the original one
                        #     shutil.copy(srcFilePath,copyFilePath)
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
                
        # #region agent log
        import json
        log_path = '/Users/praveen.jha1/Downloads/codes/PKScreener-main/.cursor/debug.log'
        try:
            sample_stock = list(stockDict.keys())[0] if stockDict else None
            sample_index = stockDict[sample_stock]['index'][-1] if sample_stock and stockDict.get(sample_stock, {}).get('index') else None
            with open(log_path, 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"AssetsManager.py:loadStockData:1280","message":"loadStockData return","data":{"stockDict_len":len(stockDict) if stockDict else 0,"stockDataLoaded":stockDataLoaded,"sample_stock":sample_stock,"sample_index_last":str(sample_index) if sample_index else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        return stockDict,stockDataLoaded

    # Save screened results to excel
    def promptFileExists(cache_file="stock_data_*.pkl", defaultAnswer=None):
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
