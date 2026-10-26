import os
import re
import requests

# Load and strip credentials
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
WHATSAPP_NUMBERS = ["+919619809009", "+919818555165"]

# --- DEBUG CHECK ---
print(f"DEBUG: SID Length = {len(TWILIO_SID)}")
print(f"DEBUG: SID Starts With = {TWILIO_SID[:4] if TWILIO_SID else 'EMPTY!'}")
print(f"DEBUG: Token Length = {len(TWILIO_TOKEN)}")
# ------------------

def send_whatsapp(title, description, alert_type):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    print(f"Target Twilio URL: {url}")
    
    body_text = f"BSE {alert_type}\n\n{title} -> {description}"[:500]
    
    for num in WHATSAPP_NUMBERS:
        payload = {
            "From": "whatsapp:+14155238886",
            "To": f"whatsapp:{num}",
            "ContentSid": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
            "ContentVariables": f'{{"1": "BSE {alert_type}", "2": "{body_text}"}}'
        }
        res = requests.post(url, data=payload, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=10)
        print(f"Twilio response for {num}: Status {res.status_code} - Body: {res.text}")

def main():
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
        
        # Test notification trigger for demonstration
        send_whatsapp("Test Stock Ltd", "Testing Python to Twilio integration.", "BUYBACK")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()