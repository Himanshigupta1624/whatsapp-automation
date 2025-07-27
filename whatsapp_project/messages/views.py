from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import MessageLog
from .filter import is_relevant_message
from .telegram import send_to_telegram
import logging
import datetime

logger = logging.getLogger(__name__)

@api_view(["POST", "GET"])
@csrf_exempt
def whatsapp_webhook(request):
    # Handle GET requests for testing
    if request.method == "GET":
        logger.info("GET request received on webhook endpoint")
        return Response({
            "status": "webhook_active", 
            "message": "WhatsApp webhook is running",
            "timestamp": str(datetime.datetime.now())
        })
    
    # Log ALL incoming requests for debugging
    logger.info("=" * 50)
    logger.info("WEBHOOK REQUEST RECEIVED")
    logger.info(f"Method: {request.method}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Raw Data: {request.body}")
    logger.info(f"Parsed Data: {request.data}")
    logger.info("=" * 50)
    
    try:
        
        webhook_data = request.data
        event_type = webhook_data.get('data', {}).get('event', '')


        if event_type == 'messages.upsert':
            messages = webhook_data.get('data', {}).get('data', {}).get('messages', [])

            for msg_data in messages:
                # Extract message text
                message_text = ""
                if 'message' in msg_data:
                    msg_obj = msg_data['message']

                    if 'conversation' in msg_obj:
                        message_text = msg_obj['conversation']
                    elif 'extendedTextMessage' in msg_obj:
                        message_text = msg_obj['extendedTextMessage'].get('text', '')
                    elif 'imageMessage' in msg_obj:
                        message_text = msg_obj['imageMessage'].get('caption', '')
                    elif 'videoMessage' in msg_obj:
                        message_text = msg_obj['videoMessage'].get('caption', '')

                # Extract only essential sender info (name and contact)
                sender_info = {}

                # Get sender name
                if 'pushName' in msg_data:
                    sender_info['name'] = msg_data['pushName']

                # Get contact number
                if 'key' in msg_data and 'remoteJid' in msg_data['key']:
                    remote_jid = msg_data['key']['remoteJid']
                    if '@g.us' in remote_jid:
                        # Group message - try to get participant
                        if 'participant' in msg_data.get('key', {}):
                            sender_info['participant'] = msg_data['key']['participant']
                    else:
                        # Direct message
                        sender_info['number'] = remote_jid

                # Process the message if we found text
                if message_text.strip():
                    is_relevant = is_relevant_message(message_text)

                    # Create simple log entry
                    message_log = MessageLog.objects.create(
                        raw_text=message_text,
                        is_relevant=is_relevant,
                        forwarded_to_telegram=False
                    )
            

                    # Send to Telegram if relevant
                    if is_relevant:
                        try:
                            success = send_to_telegram(message_text, sender_info)
                            message_log.forwarded_to_telegram = success
                            message_log.save()

                            if success:
                                logger.info(f"Opportunity forwarded: {message_text[:50]}...")
                        except Exception as e:
                            logger.error(f"Failed to send to Telegram: {e}")
        
        return Response({"status": "received"})

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return Response({"status": "error", "message": str(e)})