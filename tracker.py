import os
import re
import requests

# Load and strip credentials
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
WHATSAPP_NUMBERS = ["+919619809009", "+919818555165"]

def send_whatsapp(title, description, alert_type):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    
    # Format a clean, readable text message body using standard Body parameter
    message_body = f"📢 BSE {alert_type}\n\n*{title}*\n\n{description}"[:1500]
    
    for num in WHATSAPP_NUMBERS:
        payload = {
            "From": "whatsapp:+14155238886",
            "To": f"whatsapp:{num}",
            "Body": message_body
        }
        res = requests.post(url, data=payload, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=10)
        print(f"Twilio response for {num}: Status {res.status_code} - Body: {res.text}")

def main():
    # --- TEST NOTIFICATION DELIVERY ---
    print("Sending test notification...")
    send_whatsapp("Test Stock Ltd (500000)", "Testing Python to Twilio WhatsApp integration.", "BUYBACK")
    # -----------------------------------

    url = "https://www.bseindia.com/data/xml/announcements.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    print("Fetching BSE XML feed...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"BSE Response Status: {response.status_code}")
        
        if response.status_code != 200:
            return

        raw_text = response.text
        items = raw_text.split('<item>')
        print(f"Successfully parsed {len(items)-1} total items from feed.")
        
        for item_raw in items[1:25]:
            title_match = re.search(r'<title>([\s\S]*?)</title>', item_raw)
            desc_match = re.search(r'<description>([\s\S]*?)</description>', item_raw)
            
            title = title_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if title_match else ''
            desc = desc_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if desc_match else ''
            
            if not title:
                continue
                
            full_text = f"{title} {desc}".lower()
            
            # Match Buybacks
            if any(kw in full_text for kw in ["buyback", "buy-back", "buy back"]):
                print(f"Match found: BUYBACK -> {title}")
                send_whatsapp(title, desc, "BUYBACK")
            # Match Takeovers / Open Offers
            elif any(kw in full_text for kw in ["open offer", "sast", "manager to the offer", "letter of offer"]):
                print(f"Match found: TAKEOVER -> {title}")
                send_whatsapp(title, desc, "OPEN OFFER / TAKEOVER")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()