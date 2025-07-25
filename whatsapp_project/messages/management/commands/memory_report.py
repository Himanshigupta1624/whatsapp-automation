from django.core.management.base import BaseCommand
from messages.memory_monitor import memory_monitor
import json

class Command(BaseCommand):
    help = 'Generate memory usage report'
    
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
    
    def handle(self, *args, **options):
        if options['force_gc']:
            gc_stats = memory_monitor.force_garbage_collection()
            self.stdout.write(f"Garbage collection: {gc_stats['objects_collected']} objects freed")
        
        if options['format'] == 'json':
            snapshot = memory_monitor.memory_snapshot()
            self.stdout.write(json.dumps(snapshot, indent=2))
        else:
            report = memory_monitor.get_memory_report()
            self.stdout.write(report)