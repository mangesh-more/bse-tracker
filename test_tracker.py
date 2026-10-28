import os
import re
import time
import json
import base64
import requests

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Direct BSE XML announcements feed
FEEDS = [
    'https://www.bseindia.com/data/xml/announcements.aspx'
]

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"seen": {}}
    return {"seen": {}}

def save_state(state_data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_data, f)

def send_telegram_message(title, description):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Format message cleanly for Telegram
    message_text = f"🚨 *BSE BUYBACK ANNOUNCEMENT*\n\n*{title}*\n\n{description}"[:1000]
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram response: Status {response.status_code}")
    except Exception as err:
        print(f"Telegram Dispatch Failure: {str(err)}")

def track_bse_buybacks():
    state = load_state()
    seen_cache = state.get("seen", {})
    
    alerts_sent = 0
    total_buybacks_found = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.bseindia.com/"
    }

    for feed_url in FEEDS:
        response = None
        # Retry loop to handle BSE feed size delays
        for attempt in range(1, 4):
            try:
                print(f"Attempt {attempt}/3 fetching BSE feed...")
                response = requests.get(feed_url, headers=headers, timeout=40)
                if response.status_code == 200:
                    print("Successfully retrieved feed.")
                    break
            except Exception as err:
                print(f"Attempt {attempt} network error: {err}")
                if attempt < 3:
                    time.sleep(3)

        if not response or response.status_code != 200:
            print(f"Failed to fetch BSE feed after retries.")
            continue

        raw_text = response.text
        if not raw_text:
            continue

        items = raw_text.split('<item>')
        total_items = len(items) - 1
        print(f"Parsing full feed ({total_items} total items)...")

        # UNRESTRICTED SCAN: Iterates through ALL items in the entire feed
        for i in range(1, len(items)):
            item_raw = items[i]
            
            title_match = re.search(r'<title>([\s\S]*?)</title>', item_raw)
            desc_match = re.search(r'<description>([\s\S]*?)</description>', item_raw)
            
            title = title_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if title_match else ''
            description = desc_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if desc_match else ''
            
            if not title:
                continue

            # Clean XML entity encodings
            title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            description = description.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

            full_text = f"{title} {description}"

            # Fingerprint generation for state deduplication
            text_to_hash = re.sub(r'\s+', '', title + description).lower()
            cache_key = base64.b64encode(text_to_hash.encode('utf-8')).decode('utf-8')[:45]
            
            # STRICT FILTER: Focus solely on Buyback disclosures
            is_buyback = bool(re.search(r'buyback|buy-back|buy back', full_text, re.IGNORECASE))

            if is_buyback:
                total_buybacks_found += 1
                if cache_key not in seen_cache:
                    print(f"-> NEW BUYBACK DETECTED: {title}")
                    send_telegram_message(title, description)
                    seen_cache[cache_key] = True
                    alerts_sent += 1
            else:
                # Store non-buyback items in cache to prevent re-processing
                seen_cache[cache_key] = True

    print(f"\nScan complete. Total Buybacks in feed: {total_buybacks_found} | New alerts sent: {alerts_sent}")

    # Save updated state back
    state["seen"] = seen_cache
    save_state(state)

if __name__ == "__main__":
    track_bse_buybacks()