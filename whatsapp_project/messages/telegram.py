import requests
import logging

logger = logging.getLogger(__name__)

BOT_TOKEN = '7884745275:AAGTNI72u1ry0sYxmzPt2W3dwe_4ZTT2bJk'
CHAT_ID = '-4886371299'

def send_to_telegram(text: str, sender_info: dict = None):
    """
    Send message to Telegram with only essential information
    """
    try:
        # Build the message with only name, contact, and message
        message_parts = ["🚀 *New Web Development Opportunity!*\n"]
        
        if sender_info:
            # Add sender name
            if sender_info.get('name'):
                message_parts.append(f"👤 *Contact:* {sender_info['name']}")
            
            # Add contact number
            contact_number = None
            if sender_info.get('number'):
                contact_number = sender_info['number'].replace('@s.whatsapp.net', '').replace('@g.us', '')
            elif sender_info.get('participant'):
                contact_number = sender_info['participant'].replace('@s.whatsapp.net', '')
            
            if contact_number:
                message_parts.append(f"📱 *Number:* +{contact_number}")
        
        # Add the message
        message_parts.append(f"\n💬 *Message:*\n{text}")
        
        final_message = "\n".join(message_parts)
        
        payload = {
            'chat_id': CHAT_ID,
            'text': final_message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
            data=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Message sent to Telegram successfully")
            return True
        else:
            logger.error(f"Failed to send to Telegram: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")
        return False

def send_simple_message(text: str):
    """Fallback function for simple messages without details"""
    return send_to_telegram(text)