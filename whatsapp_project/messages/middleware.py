import psutil
import time
import tracemalloc
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging
from .memory_monitor import memory_monitor

logger = logging.getLogger(__name__)

class MemoryMonitoringMiddleware(MiddlewareMixin):
    """Django middleware to monitor memory usage per request"""
    
    def process_request(self, request):
        """Called before view processing"""
        request._memory_start_time = time.time()
        request._memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Start detailed memory tracking for webhook endpoints
        if 'webhook' in request.path:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            request._detailed_tracking = True
        else:
            request._detailed_tracking = False
    
    def process_response(self, request, response):
        """Called after view processing"""
        try:
            if hasattr(request, '_memory_start'):
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                duration = end_time - request._memory_start_time
                memory_diff = end_memory - request._memory_start
                
                # Log memory usage
                log_msg = (f"🌐 REQUEST [{request.method} {request.path}]: "
                          f"Duration: {duration:.2f}s, "
                          f"Memory: {request._memory_start:.1f}MB → {end_memory:.1f}MB "
                          f"({memory_diff:+.1f}MB)")
                
                if request._detailed_tracking and tracemalloc.is_tracing():
                    current, peak = tracemalloc.get_traced_memory()
                    log_msg += f", Peak: {peak/1024/1024:.1f}MB"
                
                if abs(memory_diff) > 5:  # Alert for >5MB changes
                    logger.warning(f"⚠️ {log_msg}")
                else:
                    logger.info(log_msg)
                
                # Add memory info to response headers in debug mode
                if getattr(settings, 'DEBUG', False):
                    response['X-Memory-Usage'] = f"{end_memory:.1f}MB"
                    response['X-Memory-Diff'] = f"{memory_diff:+.1f}MB"
                    response['X-Request-Duration'] = f"{duration:.2f}s"
                    
        except Exception as e:
            logger.error(f"Memory middleware error: {e}")
        
        return response



