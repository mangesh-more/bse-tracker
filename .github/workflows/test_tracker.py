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
    print(f"Telegram response: Status {response.status_code} - Body: {response.text}")

def test_fetch_and_alert():
    print("Sending direct test ping to Telegram...")
    send_telegram_message(
        "SYSTEM PING", 
        "BSE Tracker Manual Test", 
        "If you see this message, your Telegram Bot token and Chat ID are working perfectly on GitHub!"
    )

    url = 'https://www.bseindia.com/data/xml/announcements.aspx'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.bseindia.com/"
    }
    
    print("\nFetching live BSE XML feed (ignoring cache)...")
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        print(f"Failed to fetch BSE feed: Status {response.status_code}")
        return

    items = response.text.split('<item>')
    print(f"Successfully parsed {len(items)-1} total items from feed.")

    matches_found = 0
    max_items = min(len(items) - 1, 25)

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
            print(f"-> MATCH FOUND: [{alert_type}] {title}")
            send_telegram_message(alert_type, title, description)
            matches_found += 1

    print(f"\nScan complete. Sent {matches_found} matching alerts to Telegram.")

if __name__ == "__main__":
    test_fetch_and_alert()