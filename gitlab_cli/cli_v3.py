#!/usr/bin/env python3
# Copyright 2024 BeardedGiant
# Refactored CLI v3 - More intuitive, exploratory interface

import sys
import argparse
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from .config import Config
from .cli import GitLabExplorer, PipelineCLI


class GitLabCLIv3:
    """Main CLI class with intuitive ID-based commands"""
    
    def __init__(self):
        self.config = Config()
        
    def create_parser(self):
        """Create the main argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            prog='gl',
            description='GitLab CLI - Explore pipelines, jobs, and merge requests',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add global verbose flag
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output (shows caching, timing, etc.)'
        )
        
        # Create subparsers for each area (using plurals)
        subparsers = parser.add_subparsers(
            dest='area',
            title='Available areas',
            description='Use `gl <area> --help` for area-specific commands',
            metavar='<area>'
        )
        
        # Branches area
        self._add_branches_commands(subparsers)
        
        # MRs area
        self._add_mrs_commands(subparsers)
        
        # Pipelines area
        self._add_pipelines_commands(subparsers)
        
        # Jobs area
        self._add_jobs_commands(subparsers)
        
        # Config area
        self._add_config_commands(subparsers)
        
        return parser
    
    def _add_branches_commands(self, subparsers):
        """Add branch-related commands"""
        parser = subparsers.add_parser(
            'branches',
            help='Branch operations',
            description='List merge requests for branches'
        )
        
        parser.add_argument(
            'branch_name',
            nargs='?',
            help='Branch name (defaults to current branch)'
        )
        parser.add_argument(
            '--state',
            choices=['opened', 'merged', 'closed', 'all'],
            default='opened',
            help='Filter by MR state (default: opened)'
        )
        parser.add_argument(
            '--latest',
            action='store_true',
            help='Show only the latest MR'
        )
        parser.add_argument(
            '--format',
            choices=['friendly', 'table', 'json'],
            help='Output format'
        )
    
    def _add_mrs_commands(self, subparsers):
        """Add merge request commands"""
        parser = subparsers.add_parser(
            'mrs',
            help='Merge request operations',
            description='Show merge request information'
        )
        
        parser.add_argument(
            'mr_ids',
            help='Merge request ID(s) - can be comma-separated (e.g., 1234 or 1234,5678)'
        )
        parser.add_argument(
            '--pipelines',
            action='store_true',
            help='Show pipeline information'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Show full details including description'
        )
        parser.add_argument(
            '--format',
            choices=['friendly', 'table', 'json'],
            help='Output format'
        )
    
    def _add_pipelines_commands(self, subparsers):
        """Add pipeline commands"""
        parser = subparsers.add_parser(
            'pipelines',
            help='Pipeline operations',
            description='Show pipeline information and job summaries'
        )
        
        parser.add_argument(
            'pipeline_ids',
            help='Pipeline ID(s) - can be comma-separated'
        )
        
        # Status filters for drilling down
        status_group = parser.add_mutually_exclusive_group()
        status_group.add_argument(
            '--failed',
            action='store_true',
            help='Show failed jobs'
        )
        status_group.add_argument(
            '--running',
            action='store_true',
            help='Show running jobs'
        )
        status_group.add_argument(
            '--success',
            action='store_true',
            help='Show successful jobs'
        )
        status_group.add_argument(
            '--skipped',
            action='store_true',
            help='Show skipped jobs'
        )
        
        parser.add_argument(
            '--jobs',
            action='store_true',
            help='List all jobs (instead of summary)'
        )
        parser.add_argument(
            '--stage',
            help='Filter by stage name'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed stage-by-stage view'
        )
        parser.add_argument(
            '--format',
            choices=['friendly', 'table', 'json'],
            help='Output format'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
    
    def _add_jobs_commands(self, subparsers):
        """Add job commands"""
        parser = subparsers.add_parser(
            'jobs',
            help='Job operations',
            description='Show job information and failure details'
        )
        
        parser.add_argument(
            'job_ids',
            help='Job ID(s) - can be comma-separated'
        )
        parser.add_argument(
            '--failures',
            action='store_true',
            help='Show detailed failure information'
        )
        parser.add_argument(
            '--format',
            choices=['friendly', 'table', 'json'],
            help='Output format'
        )
    
    def _add_config_commands(self, subparsers):
        """Add config commands"""
        parser = subparsers.add_parser(
            'config',
            help='Configuration management',
            description='Manage GitLab CLI configuration'
        )
        
        subparsers = parser.add_subparsers(
            dest='action',
            title='Config commands',
            metavar='<action>'
        )
        
        # config show
        show_parser = subparsers.add_parser(
            'show',
            help='Show current configuration'
        )
        
        # config set
        set_parser = subparsers.add_parser(
            'set',
            help='Set configuration values'
        )
        set_parser.add_argument('--gitlab-url', help='GitLab server URL')
        set_parser.add_argument('--project', help='GitLab project path')
        set_parser.add_argument(
            '--default-format',
            choices=['friendly', 'table', 'json'],
            help='Default output format'
        )
    
    def parse_ids(self, id_string: str) -> List[int]:
        """Parse comma-separated IDs"""
        ids = []
        for part in id_string.split(','):
            try:
                ids.append(int(part.strip()))
            except ValueError:
                print(f"Invalid ID: {part}")
                sys.exit(1)
        return ids
    
    def run(self):
        """Main entry point"""
        parser = self.create_parser()
        
        # Handle no arguments or help
        if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['help', '--help', '-h']):
            self.print_main_help()
            sys.exit(0)
        
        # Parse arguments
        args = parser.parse_args()
        
        # Route to the appropriate handler
        self.route_command(args)
    
    def print_main_help(self):
        """Print friendly main help"""
        print("GitLab CLI - Explore pipelines, jobs, and merge requests\n")
        print("Usage: gl <area> <id(s)> [options]\n")
        print("Areas:")
        print("  branches [name]      List MRs for a branch")
        print("  mrs <id,...>         Show MR summaries")
        print("  pipelines <id,...>   Show pipeline summaries")
        print("  jobs <id,...>        Show job summaries")
        print("  config               Manage configuration")
        print("\nExamples:")
        print("  gl branches                       # List MRs for current branch")
        print("  gl mrs 1234                       # Show MR summary")
        print("  gl pipelines 567890               # Show pipeline summary")
        print("  gl pipelines 567890 --failed      # Show failed jobs")
        print("  gl jobs 123,456,789               # Show multiple job summaries")
        print("\nGlobal options:")
        print("  --verbose, -v                     # Show caching and timing info")
    
    def route_command(self, args):
        """Route commands to appropriate handlers"""
        # Special handling for config
        if args.area == 'config':
            self.handle_config(args)
            return
        
        # Validate configuration for other commands
        valid, message = self.config.validate()
        if not valid:
            print(f"Error: {message}", file=sys.stderr)
            sys.exit(1)
        
        # Initialize the CLI with config
        verbose = getattr(args, 'verbose', False)
        cli = PipelineCLI(self.config, verbose=verbose)
        
        # Get output format
        output_format = getattr(args, 'format', None) or self.config.default_format
        
        # Route based on area
        if args.area == 'branches':
            self.handle_branches(cli, args, output_format)
        
        elif args.area == 'mrs':
            ids = self.parse_ids(args.mr_ids)
            self.handle_mrs(cli, ids, args, output_format)
        
        elif args.area == 'pipelines':
            ids = self.parse_ids(args.pipeline_ids)
            self.handle_pipelines(cli, ids, args, output_format)
        
        elif args.area == 'jobs':
            ids = self.parse_ids(args.job_ids)
            self.handle_jobs(cli, ids, args, output_format)
    
    def handle_branches(self, cli, args, output_format):
        """Handle branch commands"""
        # Get current branch if not specified
        if not args.branch_name:
            import subprocess
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                args.branch_name = result.stdout.strip()
            else:
                print("Error: Not in a git repository or cannot determine branch")
                sys.exit(1)
        
        # Use existing command
        args.format = output_format
        cli.cmd_branch_mrs(args)
    
    def handle_mrs(self, cli, ids, args, output_format):
        """Handle MR commands - show summaries by default"""
        for mr_id in ids:
            if output_format == 'json':
                # For JSON, collect all data
                self.show_mr_json(cli, mr_id, args)
            else:
                self.show_mr_summary(cli, mr_id, args, output_format)
            
            if len(ids) > 1 and output_format != 'json':
                print("-" * 80)
    
    def show_mr_summary(self, cli, mr_id, args, output_format):
        """Show MR summary"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            
            # Summary view
            status_color = {
                'opened': '\033[92m',  # Green
                'merged': '\033[94m',  # Blue
                'closed': '\033[91m'   # Red
            }.get(mr.state, '')
            
            print(f"\nMR !{mr.iid}: {mr.title}")
            print(f"Status: {status_color}{mr.state.upper()}\033[0m | Author: {mr.author['username']} | Target: {mr.target_branch}")
            print(f"Created: {mr.created_at[:10]} | Updated: {mr.updated_at[:10]}")
            
            # Pipeline status if available
            if hasattr(mr, 'head_pipeline') and mr.head_pipeline:
                p_status = mr.head_pipeline.get('status', 'unknown')
                p_color = {
                    'success': '\033[92m✅',
                    'failed': '\033[91m❌',
                    'running': '\033[93m🔄'
                }.get(p_status, '⏸')
                print(f"Pipeline: {p_color} {p_status}\033[0m (ID: {mr.head_pipeline.get('id')})")
            
            if args.pipelines:
                # Show recent pipelines
                pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
                if pipelines:
                    print("\nRecent Pipelines:")
                    for p in pipelines:
                        status_icon = {'success': '✅', 'failed': '❌', 'running': '🔄'}.get(p['status'], '⏸')
                        print(f"  {status_icon} {p['id']} - {p['status']} ({p['created_at'][:16]})")
            
            if args.full:
                # Show description
                if mr.description:
                    print(f"\nDescription:\n{mr.description[:500]}...")
                    
        except Exception as e:
            print(f"Error fetching MR {mr_id}: {e}")
    
    def show_mr_json(self, cli, mr_id, args):
        """Show MR as JSON"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            output = {
                'id': mr.id,
                'iid': mr.iid,
                'title': mr.title,
                'state': mr.state,
                'author': mr.author['username'],
                'source_branch': mr.source_branch,
                'target_branch': mr.target_branch,
                'created_at': mr.created_at,
                'updated_at': mr.updated_at,
                'web_url': mr.web_url
            }
            
            if hasattr(mr, 'head_pipeline') and mr.head_pipeline:
                output['pipeline'] = mr.head_pipeline
            
            if args.pipelines:
                output['recent_pipelines'] = cli.explorer.get_pipelines_for_mr(mr_id)[:10]
            
            print(json.dumps(output, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}))
    
    def handle_pipelines(self, cli, ids, args, output_format):
        """Handle pipeline commands - show summaries by default"""
        # Determine what status filter was used
        status_filter = None
        if args.failed:
            status_filter = 'failed'
        elif args.running:
            status_filter = 'running'
        elif args.success:
            status_filter = 'success'
        elif args.skipped:
            status_filter = 'skipped'
        
        for pipeline_id in ids:
            if args.jobs or status_filter:
                # Show jobs (filtered if status provided)
                args.pipeline_id = pipeline_id
                args.status = status_filter
                args.format = output_format
                cli.cmd_pipeline_jobs(args)
            else:
                # Show pipeline summary
                self.show_pipeline_summary(cli, pipeline_id, args, output_format)
            
            if len(ids) > 1 and output_format != 'json':
                print("-" * 80)
    
    def show_pipeline_summary(self, cli, pipeline_id, args, output_format):
        """Show pipeline summary"""
        summary = cli.explorer.get_job_status_summary(pipeline_id, verbose=cli.verbose)
        
        if not summary:
            print(f"Could not fetch pipeline {pipeline_id}")
            return
        
        if output_format == 'json':
            output = {
                'pipeline_id': pipeline_id,
                'status': summary['pipeline_status'],
                'created_at': summary['created_at'],
                'duration': summary['duration'],
                'job_counts': {
                    'total': summary['total'],
                    'failed': summary['failed'],
                    'success': summary['success'],
                    'running': summary['running'],
                    'skipped': summary['skipped'],
                    'pending': summary['pending']
                }
            }
            if args.detailed:
                output['stages'] = summary['stages']
            print(json.dumps(output, indent=2))
        else:
            # Friendly summary
            status_icon = {
                'success': '✅',
                'failed': '❌',
                'running': '🔄'
            }.get(summary['pipeline_status'], '⏸')
            
            print(f"\nPipeline {pipeline_id}: {status_icon} {summary['pipeline_status'].upper()}")
            print(f"Created: {summary['created_at'][:16]} | Duration: {cli.explorer.format_duration(summary['duration'])}")
            
            # Quick stats
            print(f"Jobs: {summary['total']} total | ", end="")
            if summary['failed'] > 0:
                print(f"❌ {summary['failed']} failed | ", end="")
            if summary['success'] > 0:
                print(f"✅ {summary['success']} success | ", end="")
            if summary['running'] > 0:
                print(f"🔄 {summary['running']} running | ", end="")
            if summary['skipped'] > 0:
                print(f"⏭ {summary['skipped']} skipped", end="")
            print()
            
            # Show failed jobs if any
            if summary['failed_jobs'] and not args.detailed:
                print("\nFailed Jobs:")
                for job in summary['failed_jobs'][:5]:
                    print(f"  ❌ {job['id']} - {job['name']} ({job['stage']})")
                if len(summary['failed_jobs']) > 5:
                    print(f"  ... and {len(summary['failed_jobs']) - 5} more")
                print("\n💡 Use --failed to see all failed jobs")
    
    def handle_jobs(self, cli, ids, args, output_format):
        """Handle job commands - show summaries by default"""
        all_jobs = []
        
        for job_id in ids:
            try:
                job = cli.explorer.project.jobs.get(job_id)
                
                if output_format == 'json':
                    job_data = {
                        'id': job.id,
                        'name': job.name,
                        'status': job.status,
                        'stage': job.stage,
                        'duration': job.duration,
                        'created_at': job.created_at,
                        'started_at': job.started_at,
                        'finished_at': job.finished_at,
                        'web_url': job.web_url
                    }
                    
                    if args.failures and job.status == 'failed':
                        # Get failure details
                        details = cli.explorer.get_failed_job_details(job_id)
                        job_data['failures'] = details.get('failures', {})
                    
                    all_jobs.append(job_data)
                else:
                    # Friendly summary
                    status_icon = {
                        'success': '✅',
                        'failed': '❌',
                        'running': '🔄',
                        'skipped': '⏭'
                    }.get(job.status, '⏸')
                    
                    print(f"\nJob {job.id}: {job.name}")
                    print(f"Status: {status_icon} {job.status} | Stage: {job.stage} | Duration: {cli.explorer.format_duration(job.duration)}")
                    
                    if args.failures and job.status == 'failed':
                        details = cli.explorer.get_failed_job_details(job_id)
                        failures = details.get('failures', {})
                        if failures.get('short_summary'):
                            print("\nFailure Summary:")
                            for line in failures['short_summary'].split('\n')[:5]:
                                if 'FAILED' in line:
                                    print(f"  • {line.strip()}")
                    
                    if len(ids) > 1:
                        print("-" * 60)
                        
            except Exception as e:
                if output_format == 'json':
                    all_jobs.append({'id': job_id, 'error': str(e)})
                else:
                    print(f"Error fetching job {job_id}: {e}")
        
        if output_format == 'json':
            print(json.dumps({'jobs': all_jobs}, indent=2))
    
    def handle_config(self, args):
        """Handle configuration commands"""
        if not hasattr(args, 'action') or not args.action:
            # Default to show
            args.action = 'show'
        
        if args.action == 'show':
            print(f"GitLab URL:     {self.config.gitlab_url or 'Not set'}")
            print(f"Project:        {self.config.project_path or 'Not set (auto-detected)'}")
            print(f"Token:          {'Set' if self.config.gitlab_token else 'Not set'}")
            print(f"Default format: {self.config.default_format}")
            print(f"Cache dir:      {self.config.cache_dir}")
        
        elif args.action == 'set':
            update = {}
            if hasattr(args, 'gitlab_url') and args.gitlab_url:
                update['gitlab_url'] = args.gitlab_url
            if hasattr(args, 'project') and args.project:
                update['project_path'] = args.project
            if hasattr(args, 'default_format') and args.default_format:
                update['default_format'] = args.default_format
            
            if update:
                self.config.save_config(**update)
                print("Configuration saved")
            else:
                print("No configuration values provided")


def main():
    """Main entry point for v3 CLI"""
    cli = GitLabCLIv3()
    cli.run()


if __name__ == "__main__":
    main()