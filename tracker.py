import os
import re
import json
import base64
import requests

# --- CONFIGURATION ---
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()

MY_WHATSAPP_NUMBERS = ["+919619809009"]

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

def send_twilio_template_message(exchange, alert_type, title, description, target_number):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    
    variable1 = f"{exchange} {alert_type}"
    variable2 = f"{title} -> {description}"[:500]
    
    payload = {
        "From": "whatsapp:+14155238886",
        "To": f"whatsapp:{target_number}",
        "ContentSid": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
        "ContentVariables": json.dumps({"1": variable1, "2": variable2})
    }
    
    # Basic Auth encoding matching Utilities.base64Encode in Apps Script
    credentials = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    encoded_creds = base64.b64encode(credentials.encode("ascii")).decode("ascii")
    
    headers = {
        "Authorization": f"Basic {encoded_creds}"
    }
    
    response = requests.post(url, data=payload, headers=headers, timeout=10)
    print(f"Twilio response for {target_number}: Status {response.status_code} - Body: {response.text}")

def track_all_exchange_buybacks_and_takeovers():
    state = load_state()
    seen_cache = state.get("seen", {})
    
    alerts_sent = 0

    for feed_url in FEEDS:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.bseindia.com/"
            }
            response = requests.get(feed_url, headers=headers, timeout=15)
            status_code = response.status_code

            if status_code != 200:
                print(f"Failed to fetch BSE feed directly: Status {status_code}")
                continue

            raw_text = response.text
            if not raw_text:
                continue

            items = raw_text.split('<item>')
            if len(items) <= 1:
                continue

            max_items = min(len(items) - 1, 25)

            for i in range(1, max_items + 1):
                if alerts_sent >= 8:
                    break

                item_raw = items[i]
                
                title_match = re.search(r'<title>([\s\S]*?)</title>', item_raw)
                desc_match = re.search(r'<description>([\s\S]*?)</description>', item_raw)
                
                title = title_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if title_match else ''
                description = desc_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if desc_match else ''
                
                if not title:
                    continue

                # Clean up entity encodings
                title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                description = description.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

                # Fingerprint generation (exact match to Apps Script logic)
                text_to_hash = re.sub(r'\s+', '', title + description).lower()
                cache_key = base64.b64encode(text_to_hash.encode('utf-8')).decode('utf-8')[:45]
                
                if cache_key in seen_cache:
                    continue

                exchange = 'BSE'
                match_found = False
                alert_type = 'MONITOR'

                # 1. Corporate Buyback Routing
                if re.search(r'buyback|buy-back|buy back', title, re.IGNORECASE) or re.search(r'buyback|buy-back|buy back', description, re.IGNORECASE):
                    match_found = True
                    alert_type = 'BUYBACK'
                # 2. Targeted Takeover & SEBI SAST Open Offer Routing
                elif re.search(r'open offer|sast|public announcement|detailed public statement|letter of offer|manager to the offer', title, re.IGNORECASE) or \
                     re.search(r'open offer|sast|public announcement|detailed public statement|letter of offer|manager to the offer', description, re.IGNORECASE):
                    match_found = True
                    alert_type = 'OPEN OFFER / TAKEOVER'

                if match_found:
                    seen_cache[cache_key] = True

                    for number in MY_WHATSAPP_NUMBERS:
                        try:
                            send_twilio_template_message(exchange, alert_type, title, description, number)
                        except Exception as err:
                            print(f"Twilio Dispatch Failure for {number}: {str(err)}")
                    alerts_sent += 1
                else:
                    seen_cache[cache_key] = True

        except Exception as e:
            print('Processing Engine Failure Handler: ' + str(e))

    # Save updated state back
    state["seen"] = seen_cache
    save_state(state)

if __name__ == "__main__":
    track_all_exchange_buybacks_and_takeovers()