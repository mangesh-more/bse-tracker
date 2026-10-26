import os
import requests
from bse import BSE

# Retrieve credentials from GitHub Secrets
TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
WHATSAPP_NUMBERS = ["+919619809009", "+919818555165"]

def send_whatsapp(title, description, alert_type):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    body_text = f"BSE {alert_type}\n\n{title} -> {description}"[:500]
    
    for num in WHATSAPP_NUMBERS:
        payload = {
            "From": "whatsapp:+14155238886",
            "To": f"whatsapp:{num}",
            "ContentSid": "HXb5b62575e6e4ff6129ad7c8efe1f983e",
            "ContentVariables": f'{{"1": "BSE {alert_type}", "2": "{body_text}"}}'
        }
        requests.post(url, data=payload, auth=(TWILIO_SID, TWILIO_TOKEN))

def main():
    with BSE() as bse:
        # Fetch latest announcements cleanly using the robust Python package
        res = bse.announcements(page_no=1)
        items = res.get("Table", [])
        
        for item in items[:25]:
            title = item.get("NEWSSUB", "")
            desc = item.get("HEADLINE", "")
            full_text = f"{title} {desc}"
            
            # Match filters
            if any(kw in full_text.lower() for kw in ["buyback", "buy-back", "buy back"]):
                send_whatsapp(title, desc, "BUYBACK")
            elif any(kw in full_text.lower() for kw in ["open offer", "sast", "manager to the offer", "letter of offer"]):
                send_whatsapp(title, desc, "OPEN OFFER / TAKEOVER")

if __name__ == "__main__":
    main()
