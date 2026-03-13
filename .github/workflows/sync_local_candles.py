#!/usr/bin/env python3
"""
Sync Local Candle Database

This script syncs candle data from multiple sources:
1. Turso database (primary)
2. PKBrokers tick data from GitHub (fallback)
3. Existing pickle files (last resort)

It exports data in PKScreener-compatible format.
"""

import os
import sys
import glob
import json
import pickle
import requests
from datetime import datetime
from pathlib import Path

import pytz
import pandas as pd

# Ensure results/Data directory exists
os.makedirs('results/Data', exist_ok=True)


def fetch_ticks_from_github():
    """Fetch tick data from PKBrokers main branch."""
    # Ticks are committed to PKBrokers main branch by the orchestrator
    ticks_url = "https://raw.githubusercontent.com/pkjmesra/PKBrokers/main/pkbrokers/kite/examples/results/Data/ticks.json"
    print(f"Fetching ticks from: {ticks_url}")
    
    try:
        response = requests.get(ticks_url, timeout=30)
        if response.status_code == 200:
            ticks_data = response.json()
            print(f"Fetched ticks for {len(ticks_data)} instruments")
            return ticks_data
        else:
            print(f"Failed to fetch ticks: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching ticks: {e}")
        return None


def aggregate_ticks_to_daily(ticks_data):
    """
    Convert tick data to daily OHLCV format.
    
    Expected ticks_data format (from PKBrokers InMemoryCandleStore.export_to_ticks_json):
    {
        "instrument_token": {
            "instrument_token": 12345,
            "trading_symbol": "RELIANCE",
            "tick_count": 100,
            "ohlcv": {
                "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 1000000
            },
            "last_update": 1234567890.123
        }
    }
    """
    daily_data = {}
    
    if not ticks_data:
        return daily_data
    
    tz = pytz.timezone('Asia/Kolkata')
    today = datetime.now(tz).strftime('%Y-%m-%d')
    
    for instrument_token, data in ticks_data.items():
        try:
            # New format: data contains trading_symbol and ohlcv
            if isinstance(data, dict) and 'ohlcv' in data:
                symbol = data.get('trading_symbol', str(instrument_token))
                ohlcv = data.get('ohlcv', {})
                
                if ohlcv and ohlcv.get('close', 0) > 0:
                    daily_data[symbol] = {
                        'date': today,
                        'open': float(ohlcv.get('open', 0)),
                        'high': float(ohlcv.get('high', 0)),
                        'low': float(ohlcv.get('low', 0)),
                        'close': float(ohlcv.get('close', 0)),
                        'volume': int(ohlcv.get('volume', 0))
                    }
                    continue
            
            # Legacy format: data is a list of ticks
            if isinstance(data, list) and len(data) > 0:
                prices = []
                volumes = []
                
                for tick in data:
                    if isinstance(tick, dict):
                        ltp = tick.get('last_price', tick.get('ltp', tick.get('close')))
                        vol = tick.get('volume', tick.get('traded_volume', 0))
                        if ltp:
                            prices.append(float(ltp))
                        if vol:
                            volumes.append(int(vol))
                
                if prices:
                    daily_data[instrument_token] = {
                        'date': today,
                        'open': prices[0],
                        'high': max(prices),
                        'low': min(prices),
                        'close': prices[-1],
                        'volume': max(volumes) if volumes else 0
                    }
        except Exception as e:
            print(f"Error aggregating {instrument_token}: {e}")
            continue
    
    print(f"Aggregated {len(daily_data)} symbols from ticks")
    return daily_data


def main():
    tz = pytz.timezone('Asia/Kolkata')
    date_suffix = datetime.now(tz).strftime('%y%m%d')
    force_fallback = os.environ.get('FORCE_TICK_FALLBACK', 'N') == 'Y'
    
    # Check DB_TYPE from environment - determines if we use Turso or local SQLite
    db_type = os.environ.get('DB_TYPE', 'local').lower()
    use_turso = (db_type == 'turso')
    
    print(f"Starting candle sync for {date_suffix}")
    print(f"DB_TYPE: {db_type} (use_turso: {use_turso})")
    print(f"Force tick fallback: {force_fallback}")
    
    try:
        # Try to import LocalCandleDatabase (requires libsql for Turso, but optional for local SQLite)
        try:
            from pkbrokers.kite.localCandleDatabase import LocalCandleDatabase
            _LOCAL_DB_AVAILABLE = True
        except ImportError as e:
            print(f"LocalCandleDatabase not available (libsql may be missing): {e}")
            print("Will use fallback methods only...")
            _LOCAL_DB_AVAILABLE = False
        
        success = False
        if _LOCAL_DB_AVAILABLE:
            # Create local database in results/Data
            db = LocalCandleDatabase(base_path='results/Data')
            
            # Only try Turso sync if DB_TYPE=turso and not forcing fallback
            if use_turso and not force_fallback:
                # Try Turso sync (requires libsql)
                try:
                    print("Attempting Turso sync (DB_TYPE=turso)...")
                    success = db.sync_from_turso()
                    if success:
                        print("Turso sync successful")
                except Exception as e:
                    print(f"Turso sync failed (libsql may not be available): {e}")
                    success = False
            elif not use_turso:
                print(f"DB_TYPE={db_type}, skipping Turso sync (using local SQLite only)")
                # For local mode, we'll use fallback methods (ticks or pickle files)
                success = False
            else:
                print("Force fallback enabled, skipping Turso sync")
                success = False
        
        if not success:
            print("Turso sync failed or skipped...")
            
            # Fallback 1: Try fetching ticks from PKBrokers GitHub
            print("Trying PKBrokers tick data from GitHub...")
            ticks_data = fetch_ticks_from_github()
            daily_from_ticks = aggregate_ticks_to_daily(ticks_data)
            
            if daily_from_ticks and _LOCAL_DB_AVAILABLE:
                print(f"Importing {len(daily_from_ticks)} symbols from ticks...")
                now = datetime.now(tz).isoformat()
                
                daily_conn = db._get_daily_connection()
                cursor = daily_conn.cursor()
                
                for symbol, ohlcv in daily_from_ticks.items():
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO daily_candles 
                            (symbol, date, open, high, low, close, volume, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            symbol.replace('.NS', ''),
                            ohlcv['date'],
                            ohlcv['open'],
                            ohlcv['high'],
                            ohlcv['low'],
                            ohlcv['close'],
                            ohlcv['volume'],
                            now
                        ))
                    except Exception as e:
                        print(f"Error importing {symbol}: {e}")
                        continue
                
                daily_conn.commit()
                print(f"Imported tick data into local database")
                success = True
        
        if not success:
            # Fallback 2: Use existing pickle files
            print("Using existing pickle data as last resort...")
            pkl_files = sorted(glob.glob('results/Data/stock_data_*.pkl'))
            if pkl_files:
                latest_pkl = pkl_files[-1]
                print(f"Loading from: {latest_pkl}")
                try:
                    with open(latest_pkl, 'rb') as f:
                        data = pickle.load(f)
                    print(f"Loaded {len(data)} symbols")
                    
                    # Import into local database (only if available)
                    if _LOCAL_DB_AVAILABLE:
                        now = datetime.now(tz).isoformat()
                        today = datetime.now(tz).strftime('%Y-%m-%d')
                        
                        daily_conn = db._get_daily_connection()
                        cursor = daily_conn.cursor()
                        
                        import pandas as pd
                        for symbol, sym_data in data.items():
                            try:
                                if isinstance(sym_data, pd.DataFrame):
                                    df = sym_data
                                elif isinstance(sym_data, dict) and 'data' in sym_data:
                                    df = pd.DataFrame(
                                        data=sym_data['data'],
                                        columns=sym_data.get('columns', ['open', 'high', 'low', 'close', 'volume']),
                                        index=sym_data.get('index', [])
                                    )
                                else:
                                    continue
                                
                                for idx, row in df.iterrows():
                                    date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
                                    cursor.execute('''
                                        INSERT OR REPLACE INTO daily_candles 
                                        (symbol, date, open, high, low, close, volume, updated_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        symbol.replace('.NS', ''),
                                        date_str,
                                        float(row.get('open', row.iloc[0]) if hasattr(row, 'get') else row.iloc[0]),
                                        float(row.get('high', row.iloc[1]) if hasattr(row, 'get') else row.iloc[1]),
                                        float(row.get('low', row.iloc[2]) if hasattr(row, 'get') else row.iloc[2]),
                                        float(row.get('close', row.iloc[3]) if hasattr(row, 'get') else row.iloc[3]),
                                        int(row.get('volume', row.iloc[4]) if hasattr(row, 'get') else row.iloc[4]),
                                        now
                                    ))
                            except Exception as e:
                                print(f"Error importing {symbol}: {e}")
                                continue
                        
                        daily_conn.commit()
                        print(f"Imported data into local database")
                    else:
                        print("Local database not available, skipping import")
                    
                except Exception as e:
                    print(f"Error loading pickle: {e}")
        
        # Export to pickle format (only if database is available)
        if _LOCAL_DB_AVAILABLE:
            print("Exporting to pickle format...")
            daily_path, intraday_path = db.export_to_pickle(output_dir='results/Data')
            
            # Print stats
            stats = db.get_stats()
            print(f"\nSync Complete:")
            print(f"  Daily: {stats['daily']['symbols']} symbols, {stats['daily']['records']} records")
            print(f"  Intraday: {stats['intraday']['symbols']} symbols, {stats['intraday']['records']} records")
            print(f"  Daily DB: {stats['daily']['db_size_mb']:.2f} MB")
            print(f"  Intraday DB: {stats['intraday']['db_size_mb']:.2f} MB")
            print(f"\nExported to:")
            print(f"  Daily: {daily_path}")
            print(f"  Intraday: {intraday_path}")
            
            db.close()
        else:
            print("\nSync Complete (using pickle files only, no database)")
        
    except ImportError as e:
        print(f"PKBrokers not available: {e}")
        print("Using existing pickle files only...")
        
        # Just ensure we have valid pickle files
        pkl_files = sorted(glob.glob('results/Data/stock_data_*.pkl'))
        if pkl_files:
            print(f"Found {len(pkl_files)} existing pickle files")
            print(f"Latest: {pkl_files[-1]}")
        else:
            print("No pickle files found")
            sys.exit(1)
    
    print("\nSync completed successfully!")


if __name__ == "__main__":
    main()
