from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import MessageLog
from .filter import is_relevant_message
from .telegram import send_to_telegram
from .memory_monitor import memory_monitor, track_memory_usage, log_memory_usage
import logging
import datetime

logger = logging.getLogger(__name__)

@api_view(["POST"])
@track_memory_usage('message_processing')
def whatsapp_webhook(request):
    try:
        log_memory_usage("Webhook processing start")
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
                    log_memory_usage(f"Before filtering message: {message_text[:30]}...")
                    is_relevant = is_relevant_message(message_text)
                    
                    # Create simple log entry
                    before_db = memory_monitor.process.memory_info().rss
                    message_log = MessageLog.objects.create(
                            raw_text=message_text,
                            is_relevant=is_relevant,
                            forwarded_to_telegram=False
                        )
                    after_db = memory_monitor.process.memory_info().rss
                    memory_monitor.track_component_memory('database_operations', after_db - before_db)
                    
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
        log_memory_usage("Webhook processing end")
        return Response({"status": "received"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        log_memory_usage("Webhook processing error")
        return Response({"status": "error", "message": str(e)})

@api_view(["GET"])
def memory_stats(request):
    """Endpoint to get current memory statistics"""
    try:
        import psutil
        import gc
        
        process = psutil.Process()
        system_memory = psutil.virtual_memory()
        
        stats = {
            "system": {
                "total_gb": round(system_memory.total / 1024**3, 2),
                "used_gb": round(system_memory.used / 1024**3, 2),
                "available_gb": round(system_memory.available / 1024**3, 2),
                "percentage": system_memory.percent
            },
            "process": {
                "rss_mb": round(process.memory_info().rss / 1024**2, 2),
                "vms_mb": round(process.memory_info().vms / 1024**2, 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "python": {
                "objects_count": len(gc.get_objects()),
                "garbage_count": len(gc.garbage)
            },
            "component_memory": memory_monitor.get_component_memory_summary()
        }
        
        # Get monitoring history if available
        monitor_stats = memory_monitor.get_component_memory_summary()
        if monitor_stats:
            stats["component_tracking"] = monitor_stats
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(["POST"]) 
def test_memory_usage(request):
    """Test endpoint to trigger memory usage for testing"""
    try:
        from .filter import is_job_requirement, quick_keyword_check
        
        # Get test message from request
        test_message = request.data.get('message', 'Looking for a React developer for my project')
        
        log_memory_usage("Test message processing start")
        
        # Test pattern matching
        keyword_result = quick_keyword_check(test_message)
        
        # Test full processing  
        job_result = is_job_requirement(test_message)
        
        # Test database operation
        message_log = MessageLog.objects.create(
            raw_text=test_message,
            is_relevant=job_result,
            forwarded_to_telegram=False
        )
        
        log_memory_usage("Test message processing end")
        
        return Response({
            "message": test_message,
            "keyword_check": keyword_result,
            "job_requirement": job_result,
            "memory_report": memory_monitor.get_memory_report(),
            "component_memory": memory_monitor.get_component_memory_summary()
        })
        
    except Exception as e:
        logger.error(f"Error in memory test: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def memory_stats(request):
    """Endpoint to get current memory statistics"""
    try:
        import psutil
        import gc
        process = psutil.Process()
        system_memory = psutil.virtual_memory()
        
        stats = {
            "system": {
                "total_gb": round(system_memory.total / 1024**3, 2),
                "used_gb": round(system_memory.used / 1024**3, 2),
                "available_gb": round(system_memory.available / 1024**3, 2),
                "percentage": system_memory.percent
            },
            "process": {
                "rss_mb": round(process.memory_info().rss / 1024**2, 2),
                "vms_mb": round(process.memory_info().vms / 1024**2, 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "python": {
                "objects_count": len(gc.get_objects()),
                "garbage_count": len(gc.garbage)
            }
        }
        
        # Get monitoring history if available
        monitor_stats = memory_monitor.get_component_memory_summary()
        if monitor_stats:
            stats["components"] = monitor_stats
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def test_memory_components(request):
    """Test endpoint to trigger memory usage in different components"""
    try:
        from .filter import is_relevant_message
        from .telegram import send_simple_message
        import time
        
        log_memory_usage("Starting memory component test")
        
        # Test message processing
        test_message = "Looking for a web developer for my project. Need someone experienced with React and Node.js"
        
        # Simulate processing
        for i in range(5):
            log_memory_usage(f"Test iteration {i+1}")
            
            # Test pattern matching
            with track_memory_usage('pattern_matching'):
                result = is_relevant_message(test_message)
            
            # Test database operations
            with track_memory_usage('database_operations'):
                message_log = MessageLog.objects.create(
                    raw_text=f"Test message {i+1}: {test_message}",
                    is_relevant=result,
                    forwarded_to_telegram=False
                )
            
            # Small delay to see memory changes
            time.sleep(0.1)
        
        log_memory_usage("Memory component test completed")
        
        # Get updated component summary
        component_summary = memory_monitor.get_component_memory_summary()
        
        return Response({
            "status": "test_completed",
            "component_memory": component_summary,
            "message": "Memory component test completed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in memory component test: {e}")
        return Response({"status": "error", "message": str(e)}, status=500)