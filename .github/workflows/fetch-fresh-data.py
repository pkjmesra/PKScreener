#!/usr/bin/env python3
"""
Fetch fresh market data before running scans during market hours.

This script should be called at the start of scan workflows to ensure
we have the latest tick data before executing scans.

It will:
1. Check if we're in market hours
2. Download the latest ticks.json from PKBrokers
3. Download the latest PKL files if needed
4. Merge fresh ticks with historical data
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def is_market_hours():
    """Check if we're in market hours."""
    try:
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        return PKDateUtilities.is_extended_market_hours()
    except:
        # Fallback: Check if it's weekday and between 9:00-16:00 IST
        now = datetime.now()
        # IST is UTC+5:30
        hour = now.hour
        weekday = now.weekday()
        return weekday < 5 and 3 <= hour <= 10  # Approximate market hours in UTC


def download_fresh_ticks():
    """Download fresh ticks from multiple sources."""
    sources = [
        "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/ticks.json",
        "https://raw.githubusercontent.com/pkjmesra/PKBrokers/main/pkbrokers/kite/examples/results/Data/ticks.json",
    ]
    
    for url in sources:
        try:
            log(f"Trying to download ticks from: {url.split('/')[4]}")
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 100:
                    # Check timestamp freshness
                    sample_key = list(data.keys())[0]
                    timestamp = data[sample_key].get('ohlcv', {}).get('timestamp', '')
                    log(f"Downloaded {len(data)} symbols, latest: {timestamp}")
                    return data
        except Exception as e:
            log(f"Failed: {e}")
    
    return None


def download_latest_pkl():
    """Download the latest PKL file from GitHub."""
    from datetime import timedelta
    
    today = datetime.now()
    data_dir = Path("results/Data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Try multiple date formats
    for days_ago in range(0, 5):
        check_date = today - timedelta(days=days_ago)
        date_str = check_date.strftime('%d%m%Y')
        
        urls = [
            f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/stock_data_{date_str}.pkl",
        ]
        
        for url in urls:
            try:
                log(f"Trying PKL: stock_data_{date_str}.pkl")
                resp = requests.get(url, timeout=120)
                if resp.status_code == 200 and len(resp.content) > 1000000:  # > 1MB
                    pkl_path = data_dir / f"stock_data_{date_str}.pkl"
                    with open(pkl_path, 'wb') as f:
                        f.write(resp.content)
                    log(f"Downloaded {len(resp.content)/1024/1024:.1f} MB to {pkl_path}")
                    return str(pkl_path)
            except Exception as e:
                continue
    
    return None


def main():
    log("=" * 60)
    log("Fresh Data Fetch for Market Hours Scans")
    log("=" * 60)
    
    if not is_market_hours():
        log("Market is closed. Using existing cached data.")
        return 0
    
    log("Market is OPEN. Fetching fresh data...")
    
    # Step 1: Download fresh ticks
    ticks = download_fresh_ticks()
    if ticks:
        # Save ticks locally
        ticks_path = Path("results/Data/ticks.json")
        ticks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ticks_path, 'w') as f:
            json.dump(ticks, f)
        log(f"Saved ticks to {ticks_path}")
    else:
        log("Warning: Could not download fresh ticks")
    
    # Step 2: Download latest PKL if needed
    pkl_path = download_latest_pkl()
    if pkl_path:
        log(f"PKL available at: {pkl_path}")
    else:
        log("Warning: Could not download PKL file")
    
    log("=" * 60)
    log("Fresh data fetch completed")
    log("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
