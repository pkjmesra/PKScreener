#!/usr/bin/env python3
"""
Fetch Ticks from PKTickBot

This script sends /ticks command to @pktickbot on Telegram and downloads
the ticks.json.zip file for use in PKScreener workflows.

Requires:
- TBTOKEN: Telegram bot token for the requester bot
- PKTICKBOT_CHAT_ID: Chat ID where pktickbot is accessible (or use @pktickbot directly)
"""

import os
import sys
import json
import time
import zipfile
import tempfile
from datetime import datetime

import pytz
import requests


def send_command_to_bot(bot_token: str, chat_id: str, command: str) -> dict:
    """Send a command to a Telegram bot and get the response."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": command
    }
    response = requests.post(url, json=payload, timeout=30)
    return response.json()


def get_updates(bot_token: str, offset: int = None, timeout: int = 30) -> list:
    """Get updates (messages) from Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params, timeout=timeout + 10)
    data = response.json()
    return data.get("result", [])


def download_file(bot_token: str, file_id: str, output_path: str) -> bool:
    """Download a file from Telegram by file_id."""
    # Get file path
    url = f"https://api.telegram.org/bot{bot_token}/getFile"
    response = requests.get(url, params={"file_id": file_id}, timeout=30)
    data = response.json()
    
    if not data.get("ok"):
        print(f"Failed to get file info: {data}")
        return False
    
    file_path = data["result"]["file_path"]
    
    # Download file
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    response = requests.get(download_url, timeout=120)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    return False


def wait_for_document(bot_token: str, chat_id: str, timeout_seconds: int = 120) -> str:
    """Wait for a document to be received from the bot."""
    start_time = time.time()
    last_update_id = None
    
    # Clear old updates first
    updates = get_updates(bot_token, timeout=1)
    if updates:
        last_update_id = updates[-1]["update_id"] + 1
    
    while time.time() - start_time < timeout_seconds:
        updates = get_updates(bot_token, offset=last_update_id, timeout=10)
        
        for update in updates:
            last_update_id = update["update_id"] + 1
            
            message = update.get("message", {})
            if message.get("document"):
                doc = message["document"]
                file_name = doc.get("file_name", "")
                if "ticks" in file_name.lower() or file_name.endswith(".zip"):
                    print(f"Received document: {file_name}")
                    return doc["file_id"]
        
        time.sleep(2)
    
    return None


def extract_zip(zip_path: str, output_dir: str) -> list:
    """Extract a zip file and return list of extracted files."""
    extracted = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            zf.extract(name, output_dir)
            extracted.append(os.path.join(output_dir, name))
    return extracted


def main():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    
    print(f"Fetching ticks from pktickbot at {now}")
    
    # Get credentials from environment
    bot_token = os.environ.get("TBTOKEN")  # Token for the requesting bot
    pktickbot_chat = os.environ.get("PKTICKBOT_CHAT_ID", "@pktickbot")
    
    if not bot_token:
        print("ERROR: TBTOKEN environment variable not set")
        print("This token is needed to interact with pktickbot via Telegram API")
        sys.exit(1)
    
    output_dir = os.environ.get("OUTPUT_DIR", "results/Data")
    os.makedirs(output_dir, exist_ok=True)
    
    # Method 1: Try to use the Telegram API directly
    try:
        print(f"Sending /ticks command to {pktickbot_chat}...")
        
        # Send the command
        result = send_command_to_bot(bot_token, pktickbot_chat, "/ticks")
        print(f"Command sent: {result.get('ok', False)}")
        
        if not result.get("ok"):
            print(f"Failed to send command: {result}")
            # Continue anyway - maybe the bot will respond
        
        # Wait for document response
        print("Waiting for ticks.json.zip from pktickbot...")
        file_id = wait_for_document(bot_token, pktickbot_chat, timeout_seconds=120)
        
        if file_id:
            # Download the file
            zip_path = os.path.join(output_dir, "ticks.json.zip")
            print(f"Downloading file to {zip_path}...")
            
            if download_file(bot_token, file_id, zip_path):
                print(f"Downloaded ticks.json.zip ({os.path.getsize(zip_path)} bytes)")
                
                # Extract
                extracted = extract_zip(zip_path, output_dir)
                print(f"Extracted: {extracted}")
                
                # Verify ticks.json exists and has data
                ticks_path = os.path.join(output_dir, "ticks.json")
                if os.path.exists(ticks_path):
                    with open(ticks_path, 'r') as f:
                        data = json.load(f)
                    print(f"SUCCESS: Loaded {len(data)} instruments from pktickbot")
                    
                    # Save metadata
                    metadata = {
                        "source": "pktickbot",
                        "fetched_at": now.isoformat(),
                        "instruments": len(data)
                    }
                    with open(os.path.join(output_dir, "ticks_metadata.json"), 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return 0
                else:
                    print("WARNING: ticks.json not found after extraction")
            else:
                print("Failed to download file")
        else:
            print("No document received from pktickbot within timeout")
    
    except Exception as e:
        print(f"Error fetching from pktickbot: {e}")
        import traceback
        traceback.print_exc()
    
    # Method 2: Try to fetch from GitHub raw URL (fallback)
    print("\nFalling back to GitHub raw data...")
    try:
        urls = [
            "https://raw.githubusercontent.com/pkjmesra/PKBrokers/actions-data-download/ticks.json",
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/ticks.json",
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        ticks_path = os.path.join(output_dir, "ticks.json")
                        with open(ticks_path, 'w') as f:
                            json.dump(data, f)
                        print(f"SUCCESS: Fetched {len(data)} instruments from {url}")
                        return 0
            except Exception as e:
                print(f"Failed to fetch from {url}: {e}")
    except Exception as e:
        print(f"GitHub fallback failed: {e}")
    
    print("FAILED: Could not fetch ticks from any source")
    return 1


if __name__ == "__main__":
    sys.exit(main())
