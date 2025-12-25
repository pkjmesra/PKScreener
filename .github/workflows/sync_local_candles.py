#!/usr/bin/env python3
"""
Sync Local Candle Database

This script syncs candle data from Turso (or existing pickle files) to local SQLite
databases and exports them in PKScreener-compatible format.
"""

import os
import sys
import glob
import pickle
from datetime import datetime
from pathlib import Path

import pytz

# Ensure results/Data directory exists
os.makedirs('results/Data', exist_ok=True)

def main():
    tz = pytz.timezone('Asia/Kolkata')
    date_suffix = datetime.now(tz).strftime('%y%m%d')
    force_fallback = os.environ.get('FORCE_TICK_FALLBACK', 'N') == 'Y'
    
    print(f"Starting candle sync for {date_suffix}")
    print(f"Force tick fallback: {force_fallback}")
    
    try:
        from pkbrokers.kite.localCandleDatabase import LocalCandleDatabase
        
        # Create local database in results/Data
        db = LocalCandleDatabase(base_path='results/Data')
        
        success = False
        if not force_fallback:
            # Try Turso sync first
            print("Attempting Turso sync...")
            success = db.sync_from_turso()
        
        if not success:
            print("Turso sync failed or skipped, using existing pickle data...")
            # Find and load existing pickle files
            pkl_files = sorted(glob.glob('results/Data/stock_data_*.pkl'))
            if pkl_files:
                latest_pkl = pkl_files[-1]
                print(f"Loading from: {latest_pkl}")
                try:
                    with open(latest_pkl, 'rb') as f:
                        data = pickle.load(f)
                    print(f"Loaded {len(data)} symbols")
                    
                    # Import into local database
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
                    
                except Exception as e:
                    print(f"Error loading pickle: {e}")
        
        # Export to pickle format
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
