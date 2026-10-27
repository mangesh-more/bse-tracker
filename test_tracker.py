import os
import re
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def send_telegram_message(alert_type, title, description):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message_text = f"🚨 *BSE {alert_type} (FORCED TEST)*\n\n*{title}*\n\n{description}"[:1000]
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload, timeout=10)
    print(f"Telegram response: Status {response.status_code}")

def test_fetch_and_alert():
    print("Sending direct test ping to Telegram...")
    send_telegram_message(
        "SYSTEM PING", 
        "BSE Tracker Manual Test", 
        "Scan window expanded to 200 items. Bot is active!"
    )

    url = 'https://www.bseindia.com/data/xml/announcements.aspx'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.bseindia.com/"
    }
    
    print("\nFetching live BSE XML feed...")
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        print(f"Failed to fetch BSE feed: Status {response.status_code}")
        return

    items = response.text.split('<item>')
    total_items = len(items) - 1
    print(f"Successfully parsed {total_items} total items from feed.")

    matches_found = 0
    # FIX: Increased scan limit from 25 to 200 to capture recent announcements deeper in the feed
    max_items = min(total_items, 200)
    print(f"Scanning the latest {max_items} announcements for Buybacks and Open Offers...")

    for i in range(1, max_items + 1):
        item_raw = items[i]
        
        title_match = re.search(r'<title>([\s\S]*?)</title>', item_raw)
        desc_match = re.search(r'<description>([\s\S]*?)</description>', item_raw)
        
        title = title_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if title_match else ''
        description = desc_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if desc_match else ''
        
        if not title:
            continue

        title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        description = description.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

        full_text = f"{title} {description}"
        
        match_found = False
        alert_type = 'MONITOR'

        if re.search(r'buyback|buy-back|buy back', full_text, re.IGNORECASE):
            match_found = True
            alert_type = 'BUYBACK'
        elif re.search(r'open offer|sast|public announcement|detailed public statement|letter of offer|manager to the offer', full_text, re.IGNORECASE):
            match_found = True
            alert_type = 'OPEN OFFER / TAKEOVER'

        if match_found:
            print(f"-> MATCH FOUND [{i}/{max_items}]: [{alert_type}] {title}")
            send_telegram_message(alert_type, title, description)
            matches_found += 1

    print(f"\nScan complete. Scanned {max_items} items, sent {matches_found} matching alerts.")

if __name__ == "__main__":
    test_fetch_and_alert()