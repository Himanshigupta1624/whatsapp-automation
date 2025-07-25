import psutil
import tracemalloc
import gc
import sys
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json
from functools import wraps

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """
    Comprehensive memory monitoring for Django WhatsApp automation
    Tracks system memory, Python objects, and component-specific usage
    """
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.memory_snapshots = []
        self.peak_memory = 0
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Component-specific memory tracking
        self.component_memory = {
            'gemini_model': 0,
            'message_processing': 0,
            'database_operations': 0,
            'telegram_requests': 0,
            'pattern_matching': 0
        }
        
        # Start tracemalloc for detailed Python memory tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            
    def get_system_memory_info(self) -> Dict[str, Any]:
        """Get comprehensive system memory information"""
        try:
            # Process-specific memory
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # System-wide memory
            virtual_memory = psutil.virtual_memory()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'process_memory': {
                    'rss_mb': round(memory_info.rss / 1024 / 1024, 2),  # Resident Set Size
                    'vms_mb': round(memory_info.vms / 1024 / 1024, 2),  # Virtual Memory Size
                    'percent': round(memory_percent, 2),
                    'peak_mb': round(self.peak_memory / 1024 / 1024, 2)
                },
                'system_memory': {
                    'total_mb': round(virtual_memory.total / 1024 / 1024, 2),
                    'available_mb': round(virtual_memory.available / 1024 / 1024, 2),
                    'used_percent': virtual_memory.percent,
                    'free_mb': round(virtual_memory.free / 1024 / 1024, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {}
    
    def get_python_memory_info(self) -> Dict[str, Any]:
        """Get detailed Python memory allocation info"""
        try:
            # Get current memory usage
            current, peak = tracemalloc.get_traced_memory()
            
            # Get top memory consuming lines
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            # Object count by type
            object_counts = {}
            for obj_type in [dict, list, str, int, float]:
                count = len([obj for obj in gc.get_objects() if type(obj) is obj_type])
                object_counts[obj_type.__name__] = count
            
            # Top 5 memory consumers
            top_consumers = []
            for stat in top_stats[:5]:
                top_consumers.append({
                    'file': stat.traceback.format()[-1] if stat.traceback.format() else 'unknown',
                    'size_mb': round(stat.size / 1024 / 1024, 2),
                    'count': stat.count
                })
            
            return {
                'current_mb': round(current / 1024 / 1024, 2),
                'peak_mb': round(peak / 1024 / 1024, 2),
                'object_counts': object_counts,
                'top_consumers': top_consumers,
                'garbage_collections': {
                    'generation_0': gc.get_count()[0],
                    'generation_1': gc.get_count()[1],
                    'generation_2': gc.get_count()[2]
                }
            }
        except Exception as e:
            logger.error(f"Error getting Python memory info: {e}")
            return {}
    
    def track_component_memory(self, component: str, memory_delta: float):
        """Track memory usage for specific components"""
        if component in self.component_memory:
            self.component_memory[component] += memory_delta
    
    def get_component_memory_summary(self) -> Dict[str, float]:
        """Get memory usage summary by component"""
        total_tracked = sum(self.component_memory.values())
        
        summary = {}
        for component, memory in self.component_memory.items():
            summary[component] = {
                'mb': round(memory / 1024 / 1024, 2),
                'percent': round((memory / total_tracked * 100) if total_tracked > 0 else 0, 2)
            }
        
        return summary
    
    def memory_snapshot(self) -> Dict[str, Any]:
        """Take comprehensive memory snapshot"""
        current_memory = self.process.memory_info().rss
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': round(time.time() - self.start_time, 2),
            'system_memory': self.get_system_memory_info(),
            'python_memory': self.get_python_memory_info(),
            'component_memory': self.get_component_memory_summary()
        }
        
        self.memory_snapshots.append(snapshot)
        
        # Keep only last 100 snapshots to prevent memory buildup
        if len(self.memory_snapshots) > 100:
            self.memory_snapshots = self.memory_snapshots[-100:]
        
        return snapshot
    
    def start_continuous_monitoring(self, interval: int = 30):
        """Start continuous memory monitoring in background thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    snapshot = self.memory_snapshot()
                    
                    # Log critical memory situations
                    system_memory = snapshot.get('system_memory', {}).get('process_memory', {})
                    if system_memory.get('rss_mb', 0) > 500:  # Alert if over 500MB
                        logger.warning(f"High memory usage: {system_memory.get('rss_mb')}MB")
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Memory monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Memory monitoring stopped")
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        before_objects = len(gc.get_objects())
        collected = gc.collect()
        after_objects = len(gc.get_objects())
        
        return {
            'objects_before': before_objects,
            'objects_after': after_objects,
            'objects_collected': collected,
            'objects_freed': before_objects - after_objects
        }
    
    def get_memory_report(self) -> str:
        """Generate comprehensive memory report"""
        snapshot = self.memory_snapshot()
        
        report = f"""
🧠 MEMORY MONITORING REPORT
{'='*50}
Timestamp: {snapshot['timestamp']}
Uptime: {snapshot['uptime_seconds']} seconds

📊 PROCESS MEMORY:
- RSS: {snapshot['system_memory']['process_memory']['rss_mb']} MB
- VMS: {snapshot['system_memory']['process_memory']['vms_mb']} MB
- Peak: {snapshot['system_memory']['process_memory']['peak_mb']} MB
- CPU %: {snapshot['system_memory']['process_memory']['percent']}%

💻 SYSTEM MEMORY:
- Total: {snapshot['system_memory']['system_memory']['total_mb']} MB
- Available: {snapshot['system_memory']['system_memory']['available_mb']} MB
- Used: {snapshot['system_memory']['system_memory']['used_percent']}%

🐍 PYTHON MEMORY:
- Current: {snapshot['python_memory']['current_mb']} MB
- Peak: {snapshot['python_memory']['peak_mb']} MB

📦 COMPONENT MEMORY:
"""
        
        for component, stats in snapshot['component_memory'].items():
            report += f"- {component}: {stats['mb']} MB ({stats['percent']}%)\n"
        
        return report

# Global memory monitor instance
memory_monitor = MemoryMonitor()

def track_memory_usage(component: str):
    """Decorator to track memory usage of functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Take memory snapshot before
            before_memory = memory_monitor.process.memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Calculate memory delta
                after_memory = memory_monitor.process.memory_info().rss
                memory_delta = after_memory - before_memory
                
                # Track component memory usage
                memory_monitor.track_component_memory(component, memory_delta)
                
                # Log significant memory increases
                if memory_delta > 10 * 1024 * 1024:  # 10MB threshold
                    logger.warning(f"{component} used {memory_delta / 1024 / 1024:.2f}MB")
        
        return wrapper
    return decorator

def log_memory_usage(message: str = "Memory usage"):
    """Log current memory usage"""
    try:
        snapshot = memory_monitor.memory_snapshot()
        process_memory = snapshot['system_memory']['process_memory']
        logger.info(f"{message}: {process_memory['rss_mb']}MB RSS, {process_memory['percent']}% CPU")
    except Exception as e:
        logger.error(f"Failed to log memory usage: {e}")
