from django.core.management.base import BaseCommand
from messages.memory_monitor import memory_monitor
import json
import time

class Command(BaseCommand):
    help = 'Generate memory usage report and test memory tracking'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='text',
            choices=['text', 'json'],
            help='Output format (text or json)'
        )
        
        parser.add_argument(
            '--force-gc',
            action='store_true',
            help='Force garbage collection before report'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run memory test with sample messages'
        )
    
    def handle(self, *args, **options):
        if options['force_gc']:
            gc_stats = memory_monitor.force_garbage_collection()
            self.stdout.write(f"Garbage collection: {gc_stats['objects_collected']} objects freed")
        
        if options['test']:
            self.run_memory_test()
        
        if options['format'] == 'json':
            snapshot = memory_monitor.memory_snapshot()
            self.stdout.write(json.dumps(snapshot, indent=2))
        else:
            report = memory_monitor.get_memory_report()
            self.stdout.write(report)
    
    def run_memory_test(self):
        """Run memory test with sample messages"""
        from messages.filter import is_job_requirement, quick_keyword_check
        from messages.models import MessageLog
        
        self.stdout.write("Starting Memory Test...")
        
        # Test messages that should trigger memory usage
        test_messages = [
            "Looking for a React developer for my startup project",
            "Need a graphic designer for logo design", 
            "Any freelance video editor available for YouTube videos?",
            "I'm offering web development services, contact me",
            "Urgent requirement Male & female Education : 10th"
        ]
        
        for i, message in enumerate(test_messages, 1):
            self.stdout.write(f"Processing message {i}: {message[:40]}...")
            
            # This should trigger pattern_matching memory tracking
            keyword_result = quick_keyword_check(message)
            
            # This should trigger message_processing and potentially gemini_model
            job_result = is_job_requirement(message)
            
            # This should trigger database_operations
            message_log = MessageLog.objects.create(
                raw_text=message,
                is_relevant=job_result,
                forwarded_to_telegram=False
            )
            
            self.stdout.write(f"   Result: Keywords={keyword_result}, Job={job_result}")
            time.sleep(0.5)  # Small delay to see memory changes
        
        self.stdout.write("Memory test completed!")