from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messages'
    label = 'whatsapp_messages'
    
    def ready(self):
        """Initialize memory monitoring when Django starts"""
        try:
            from django.conf import settings
            from .memory_monitor import memory_monitor
            
            # Start memory monitoring if enabled
            if getattr(settings, 'MEMORY_MONITORING', {}).get('ENABLE_CONTINUOUS_MONITORING', False):
                interval = getattr(settings, 'MEMORY_MONITORING', {}).get('MONITORING_INTERVAL', 30)
                memory_monitor.start_continuous_monitoring(interval)
                print(f"🧠 Memory monitoring started (interval: {interval}s)")
            
        except Exception as e:
            print(f"Failed to start memory monitoring: {e}")
    
    def ready(self):
        # Start memory monitoring when Django starts
        from .memory_monitor import memory_monitor
        from django.conf import settings
        
        if getattr(settings, 'MEMORY_MONITORING', {}).get('ENABLE_CONTINUOUS_MONITORING', False):
            interval = getattr(settings, 'MEMORY_MONITORING', {}).get('MONITORING_INTERVAL', 30)
            memory_monitor.start_continuous_monitoring(interval)
