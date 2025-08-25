"""Cache management command handlers"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from .base import BaseCommand


class CacheCommand(BaseCommand):
    """Handle cache-related commands"""

    def add_arguments(self, subparsers):
        """Add cache-specific arguments to parser"""
        # Create the cache parser first
        parser = subparsers.add_parser(
            "cache",
            help="Cache management",
            description="Manage the local cache for pipelines"
        )
        
        # Now add subparsers to the cache parser
        cache_subparsers = parser.add_subparsers(
            dest="cache_action",
            help="Cache management actions"
        )
        
        # Stats subcommand
        stats_parser = cache_subparsers.add_parser(
            "stats",
            help="Show cache statistics"
        )
        stats_parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed statistics"
        )
        
        # Clear subcommand
        clear_parser = cache_subparsers.add_parser(
            "clear",
            help="Clear cache"
        )
        clear_parser.add_argument(
            "--all",
            action="store_true",
            help="Clear all cache (requires confirmation)"
        )
        clear_parser.add_argument(
            "--pipeline",
            type=int,
            help="Clear specific pipeline from cache"
        )
        clear_parser.add_argument(
            "--older-than",
            type=int,
            help="Clear pipelines older than N days"
        )
        clear_parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompts"
        )
        
        # List subcommand
        list_parser = cache_subparsers.add_parser(
            "list",
            help="List cached items"
        )
        list_parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Limit number of items shown (default: 20)"
        )
        list_parser.add_argument(
            "--sort",
            choices=["id", "date", "size"],
            default="date",
            help="Sort order (default: date)"
        )
        
        # Info subcommand
        info_parser = cache_subparsers.add_parser(
            "info",
            help="Show cache configuration and location"
        )

    def handle(self, config, args):
        """Handle cache commands"""
        cache_file = config.get_cache_path("pipelines_cache.db")
        
        if not args.cache_action:
            # Default to showing stats
            args.cache_action = "stats"
        
        if args.cache_action == "stats":
            self.show_stats(cache_file, args)
        elif args.cache_action == "clear":
            self.clear_cache(cache_file, args)
        elif args.cache_action == "list":
            self.list_cache(cache_file, args)
        elif args.cache_action == "info":
            self.show_info(config, cache_file)
    
    def show_stats(self, cache_file, args):
        """Show cache statistics"""
        if not cache_file.exists():
            print("Cache file does not exist yet.")
            print(f"Location: {cache_file}")
            return
        
        conn = sqlite3.connect(cache_file)
        cur = conn.cursor()
        
        # Get basic stats
        cur.execute("SELECT COUNT(*) FROM pipelines")
        total_pipelines = cur.fetchone()[0]
        
        # Get cache size
        file_size = cache_file.stat().st_size
        
        # Get date range
        cur.execute("SELECT MIN(created_at), MAX(created_at) FROM pipelines")
        date_range = cur.fetchone()
        
        print("=" * 60)
        print("Cache Statistics")
        print("=" * 60)
        print(f"Location:          {cache_file}")
        print(f"Size:              {self._format_size(file_size)}")
        print(f"Cached pipelines:  {total_pipelines}")
        
        if date_range[0] and date_range[1]:
            oldest = date_range[0][:10] if date_range[0] else "N/A"
            newest = date_range[1][:10] if date_range[1] else "N/A"
            print(f"Date range:        {oldest} to {newest}")
        
        if args.detailed and total_pipelines > 0:
            print("\nDetailed Breakdown:")
            print("-" * 40)
            
            # Get status breakdown
            cur.execute("""
                SELECT 
                    json_extract(data, '$.pipeline.status') as status,
                    COUNT(*) as count
                FROM pipelines 
                GROUP BY status
                ORDER BY count DESC
            """)
            
            status_breakdown = cur.fetchall()
            if status_breakdown:
                print("\nBy Status:")
                for status, count in status_breakdown:
                    status_str = status or "unknown"
                    print(f"  {status_str:15} {count:5} pipelines")
            
            # Get size per pipeline
            cur.execute("""
                SELECT 
                    pipeline_id,
                    LENGTH(data) as data_size,
                    created_at
                FROM pipelines
                ORDER BY data_size DESC
                LIMIT 5
            """)
            
            largest = cur.fetchall()
            if largest:
                print("\nLargest Cached Pipelines:")
                for pid, size, created in largest:
                    print(f"  #{pid:10} {self._format_size(size):>10} ({created[:16]})")
        
        conn.close()
    
    def clear_cache(self, cache_file, args):
        """Clear cache based on criteria"""
        if not cache_file.exists():
            print("Cache file does not exist.")
            return
        
        conn = sqlite3.connect(cache_file)
        cur = conn.cursor()
        
        if args.pipeline:
            # Clear specific pipeline
            cur.execute("DELETE FROM pipelines WHERE pipeline_id = ?", (args.pipeline,))
            affected = cur.rowcount
            conn.commit()
            print(f"Cleared pipeline {args.pipeline} from cache ({affected} entries removed)")
        
        elif args.older_than:
            # Clear pipelines older than N days
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=args.older_than)).isoformat()
            
            # First show what will be deleted
            cur.execute("SELECT COUNT(*) FROM pipelines WHERE created_at < ?", (cutoff_date,))
            count = cur.fetchone()[0]
            
            if count == 0:
                print(f"No pipelines older than {args.older_than} days found")
                return
            
            if not args.force:
                response = input(f"Delete {count} pipelines older than {args.older_than} days? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled")
                    return
            
            cur.execute("DELETE FROM pipelines WHERE created_at < ?", (cutoff_date,))
            affected = cur.rowcount
            conn.commit()
            print(f"Cleared {affected} pipelines older than {args.older_than} days")
        
        elif args.all:
            # Clear all cache
            cur.execute("SELECT COUNT(*) FROM pipelines")
            count = cur.fetchone()[0]
            
            if not args.force:
                response = input(f"Delete ALL {count} cached pipelines? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled")
                    return
            
            cur.execute("DELETE FROM pipelines")
            affected = cur.rowcount
            conn.commit()
            
            # Vacuum to reclaim space
            cur.execute("VACUUM")
            conn.commit()
            
            print(f"Cleared all {affected} pipelines from cache")
            new_size = cache_file.stat().st_size
            print(f"Cache file size: {self._format_size(new_size)}")
        else:
            print("Please specify what to clear:")
            print("  --all              Clear all cache")
            print("  --pipeline <id>    Clear specific pipeline")
            print("  --older-than <days> Clear pipelines older than N days")
        
        conn.close()
    
    def list_cache(self, cache_file, args):
        """List cached pipelines"""
        if not cache_file.exists():
            print("Cache file does not exist yet.")
            return
        
        conn = sqlite3.connect(cache_file)
        cur = conn.cursor()
        
        # Build query based on sort order
        if args.sort == "id":
            order_by = "pipeline_id DESC"
        elif args.sort == "size":
            order_by = "LENGTH(data) DESC"
        else:  # date
            order_by = "created_at DESC"
        
        query = f"""
            SELECT 
                pipeline_id,
                created_at,
                LENGTH(data) as data_size,
                json_extract(data, '$.pipeline.status') as status,
                json_extract(data, '$.pipeline.ref') as ref
            FROM pipelines
            ORDER BY {order_by}
            LIMIT ?
        """
        
        cur.execute(query, (args.limit,))
        pipelines = cur.fetchall()
        
        if not pipelines:
            print("No cached pipelines found")
            return
        
        print("=" * 80)
        print(f"Cached Pipelines (sorted by {args.sort}, limit {args.limit})")
        print("=" * 80)
        print(f"{'Pipeline ID':<12} {'Status':<10} {'Branch/Tag':<20} {'Cached At':<20} {'Size':<10}")
        print("-" * 80)
        
        for pid, created, size, status, ref in pipelines:
            ref_display = ref[:17] + "..." if ref and len(ref) > 20 else (ref or "N/A")
            status_display = status or "unknown"
            created_display = created[:16] if created else "N/A"
            size_display = self._format_size(size)
            
            print(f"{pid:<12} {status_display:<10} {ref_display:<20} {created_display:<20} {size_display:<10}")
        
        # Show total count if more than limit
        cur.execute("SELECT COUNT(*) FROM pipelines")
        total = cur.fetchone()[0]
        if total > args.limit:
            print(f"\n... and {total - args.limit} more cached pipelines")
        
        conn.close()
    
    def show_info(self, config, cache_file):
        """Show cache configuration and location"""
        print("=" * 60)
        print("Cache Configuration")
        print("=" * 60)
        print(f"Cache directory:   {config.cache_dir}")
        print(f"Database file:     {cache_file}")
        print(f"Database exists:   {cache_file.exists()}")
        
        if cache_file.exists():
            size = cache_file.stat().st_size
            print(f"Database size:     {self._format_size(size)}")
            
            # Check if accessible
            try:
                conn = sqlite3.connect(cache_file)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM pipelines")
                count = cur.fetchone()[0]
                conn.close()
                print(f"Cached pipelines:  {count}")
                print(f"Status:            ✅ Accessible and working")
            except Exception as e:
                print(f"Status:            ❌ Error accessing cache: {e}")
        else:
            print(f"Status:            Cache not yet created")
        
        print("\nCache Behavior:")
        print("  - Only completed pipelines are cached (success, failed, canceled, skipped)")
        print("  - Running pipelines are always fetched fresh from API")
        print("  - Cache is automatically used when fetching pipeline details")
        print("  - Use --verbose flag to see cache hits/misses")
    
    def _format_size(self, size_bytes):
        """Format size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"