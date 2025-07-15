import requests
import logging
import re

logger = logging.getLogger(__name__)

BOT_TOKEN = '7884745275:AAGTNI72u1ry0sYxmzPt2W3dwe_4ZTT2bJk'
CHAT_ID = '-4886371299'

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2"""
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def clean_message_for_telegram(text: str) -> str:
    """Clean message text to avoid Markdown parsing issues"""
    # Remove or replace problematic characters
    text = text.replace('*', '•')  # Replace asterisks with bullets
    text = text.replace('_', '-')  # Replace underscores with hyphens
    text = text.replace('[', '(')  # Replace brackets
    text = text.replace(']', ')')
    text = text.replace('`', "'")  # Replace backticks
    text = text.replace('#', 'No.')  # Replace hashtags
    
    # Remove excessive emojis that might cause issues
    text = re.sub(r'[🚀🌐📍💰🎯📩🏀⚽]+', '', text)
    
    return text.strip()

def send_to_telegram(text: str, sender_info: dict = None):
    """
    Send message to Telegram with only essential information
    """
    try:
        # Clean the message text to avoid Markdown parsing issues
        clean_text = clean_message_for_telegram(text)
        
        # Build the message with only name, contact, and message
        message_parts = ["🚀 NEW OPPORTUNITY!\n"]
        
        if sender_info:
            # Add sender name (clean it too)
            if sender_info.get('name'):
                clean_name = clean_message_for_telegram(sender_info['name'])
                message_parts.append(f"👤 Contact: {clean_name}")
            
            # Add contact number
            contact_number = None
            if sender_info.get('number'):
                contact_number = sender_info['number'].replace('@s.whatsapp.net', '').replace('@g.us', '')
            elif sender_info.get('participant'):
                contact_number = sender_info['participant'].replace('@s.whatsapp.net', '')
            
            if contact_number:
                message_parts.append(f"📱 Number: +{contact_number}")
        
        # Add the message
        message_parts.append(f"\n💬 Message:\n{clean_text}")
        
        final_message = "\n".join(message_parts)
        
        # Use plain text instead of Markdown to avoid parsing issues
        payload = {
            'chat_id': CHAT_ID,
            'text': final_message
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