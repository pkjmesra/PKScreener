#!/usr/bin/env python3
"""
Convert ticks.json to pickle format for PKScreener.
This script is used as a fallback when the main data download fails.
"""
import json
import pickle
import sys
from datetime import datetime

try:
    import pandas as pd
    import pytz
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "pytz"])
    import pandas as pd
    import pytz


def convert_ticks_to_pickle(ticks_path, output_dir):
    try:
        with open(ticks_path, 'r') as f:
            ticks_data = json.load(f)
        
        print(f"Loaded {len(ticks_data)} instruments from {ticks_path}")
        
        stock_data = {}
        timezone = pytz.timezone('Asia/Kolkata')
        today = datetime.now(timezone).strftime('%y%m%d')
        
        for instrument_token, instrument_data in ticks_data.items():
            try:
                tradingsymbol = instrument_data.get('trading_symbol', '')
                if not tradingsymbol:
                    continue
                
                ohlcv = instrument_data.get('ohlcv', {})
                if not ohlcv:
                    continue
                
                timestamp = ohlcv.get('timestamp', datetime.now(timezone).isoformat())
                
                df = pd.DataFrame([{
                    'Date': pd.to_datetime(timestamp),
                    'Open': ohlcv.get('open', 0),
                    'High': ohlcv.get('high', 0),
                    'Low': ohlcv.get('low', 0),
                    'Close': ohlcv.get('close', 0),
                    'Volume': ohlcv.get('volume', 0),
                }])
                
                if not df.empty:
                    df.set_index('Date', inplace=True)
                    stock_data[tradingsymbol] = df
                    
            except Exception as e:
                continue
        
        if stock_data:
            output_path = f"{output_dir}/stock_data_{today}.pkl"
            with open(output_path, 'wb') as f:
                pickle.dump(stock_data, f)
            print(f"Saved {len(stock_data)} symbols to {output_path}")
            
            intraday_path = f"{output_dir}/intraday_stock_data_{today}.pkl"
            with open(intraday_path, 'wb') as f:
                pickle.dump(stock_data, f)
            print(f"Saved {len(stock_data)} symbols to {intraday_path}")
            
            return True
        else:
            print("No valid data to save")
            return False
            
    except Exception as e:
        print(f"Error converting ticks to pickle: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert ticks.json to pickle format")
    parser.add_argument("--ticks", default="/tmp/ticks.json", help="Path to ticks.json")
    parser.add_argument("--output", default="actions-data-download", help="Output directory")
    
    args = parser.parse_args()
    
    success = convert_ticks_to_pickle(args.ticks, args.output)
    sys.exit(0 if success else 1)
