#!/usr/bin/env python3
# Copyright 2024 BeardedGiant
# Refactored CLI with area-based command structure

import sys
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any

from .config import Config
from .cli import GitLabExplorer, PipelineCLI


class GitLabCLIv2:
    """Main CLI class with area-based command structure"""
    
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
        
        # Create subparsers for each area
        subparsers = parser.add_subparsers(
            dest='area',
            title='Available areas',
            description='Use `gl <area> --help` for area-specific commands',
            metavar='<area>'
        )
        
        # Branch area
        self._add_branch_commands(subparsers)
        
        # MR area
        self._add_mr_commands(subparsers)
        
        # Pipeline area
        self._add_pipeline_commands(subparsers)
        
        # Job area
        self._add_job_commands(subparsers)
        
        # Config area
        self._add_config_commands(subparsers)
        
        return parser
    
    def _add_branch_commands(self, subparsers):
        """Add branch-related commands"""
        branch_parser = subparsers.add_parser(
            'branch',
            help='Branch and merge request operations',
            description='Commands for working with branches and their merge requests'
        )
        
        branch_subparsers = branch_parser.add_subparsers(
            dest='action',
            title='Branch commands',
            metavar='<action>'
        )
        
        # branch list command
        list_parser = branch_subparsers.add_parser(
            'list',
            help='List merge requests for a branch',
            description='List all merge requests associated with a branch'
        )
        list_parser.add_argument(
            'branch_name',
            nargs='?',
            help='Branch name (defaults to current branch)'
        )
        list_parser.add_argument(
            '--state',
            choices=['opened', 'merged', 'closed', 'all'],
            default='opened',
            help='Filter by MR state (default: opened)'
        )
        list_parser.add_argument(
            '--latest',
            action='store_true',
            help='Show only the latest MR with its pipeline'
        )
    
    def _add_mr_commands(self, subparsers):
        """Add merge request commands"""
        mr_parser = subparsers.add_parser(
            'mr',
            help='Merge request operations',
            description='Commands for working with merge requests'
        )
        
        mr_subparsers = mr_parser.add_subparsers(
            dest='action',
            title='MR commands',
            metavar='<action>'
        )
        
        # mr show command
        show_parser = mr_subparsers.add_parser(
            'show',
            help='Show detailed MR information',
            description='Display detailed information about a merge request'
        )
        show_parser.add_argument('mr_id', type=int, help='Merge request ID')
        show_parser.add_argument(
            '--pipelines', '-p',
            action='store_true',
            help='Include recent pipelines'
        )
        
        # mr pipelines command
        pipelines_parser = mr_subparsers.add_parser(
            'pipelines',
            help='List pipelines for an MR',
            description='List all pipelines associated with a merge request'
        )
        pipelines_parser.add_argument('mr_id', type=int, help='Merge request ID')
        pipelines_parser.add_argument(
            '--latest',
            action='store_true',
            help='Show only the latest pipeline'
        )
    
    def _add_pipeline_commands(self, subparsers):
        """Add pipeline commands"""
        pipeline_parser = subparsers.add_parser(
            'pipeline',
            help='Pipeline operations',
            description='Commands for working with pipelines'
        )
        
        pipeline_subparsers = pipeline_parser.add_subparsers(
            dest='action',
            title='Pipeline commands',
            metavar='<action>'
        )
        
        # pipeline status command
        status_parser = pipeline_subparsers.add_parser(
            'status',
            help='Show pipeline status summary',
            description='Display status summary and progress for a pipeline'
        )
        status_parser.add_argument('pipeline_id', type=int, help='Pipeline ID')
        status_parser.add_argument(
            '--detailed', '-d',
            action='store_true',
            help='Show detailed stage-by-stage progress'
        )
        status_parser.add_argument(
            '--format',
            choices=['friendly', 'json'],
            help='Output format (uses configured default if not specified)'
        )
        status_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output (shows caching, timing, etc.)'
        )
        
        # pipeline jobs command
        jobs_parser = pipeline_subparsers.add_parser(
            'jobs',
            help='List jobs in a pipeline',
            description='List all jobs in a pipeline with filtering options'
        )
        jobs_parser.add_argument('pipeline_id', type=int, help='Pipeline ID')
        
        # Status filters
        status_group = jobs_parser.add_mutually_exclusive_group()
        status_group.add_argument(
            '--status',
            help='Filter by specific job status'
        )
        status_group.add_argument(
            '--failed',
            action='store_const',
            const='failed',
            dest='status',
            help='Show only failed jobs'
        )
        status_group.add_argument(
            '--running',
            action='store_const',
            const='running',
            dest='status',
            help='Show only running jobs'
        )
        status_group.add_argument(
            '--success',
            action='store_const',
            const='success',
            dest='status',
            help='Show only successful jobs'
        )
        status_group.add_argument(
            '--skipped',
            action='store_const',
            const='skipped',
            dest='status',
            help='Show only skipped jobs'
        )
        status_group.add_argument(
            '--pending',
            action='store_const',
            const='pending',
            dest='status',
            help='Show only pending jobs'
        )
        
        jobs_parser.add_argument(
            '--stage',
            help='Filter by stage name'
        )
        jobs_parser.add_argument(
            '--sort',
            choices=['duration', 'name', 'created'],
            default='created',
            help='Sort jobs by field (default: created)'
        )
        jobs_parser.add_argument(
            '--format',
            choices=['friendly', 'table', 'json'],
            help='Output format (uses configured default if not specified)'
        )
        jobs_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output (shows caching, timing, etc.)'
        )
    
    def _add_job_commands(self, subparsers):
        """Add job commands"""
        job_parser = subparsers.add_parser(
            'job',
            help='Job operations',
            description='Commands for working with pipeline jobs'
        )
        
        job_subparsers = job_parser.add_subparsers(
            dest='action',
            title='Job commands',
            metavar='<action>'
        )
        
        # job show command (failures)
        show_parser = job_subparsers.add_parser(
            'show',
            help='Show job details and failures',
            description='Display detailed information about a job, including failure details'
        )
        show_parser.add_argument('job_id', type=int, help='Job ID')
        show_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show verbose failure information'
        )
        
        # job batch command
        batch_parser = job_subparsers.add_parser(
            'batch',
            help='Show failures for multiple jobs',
            description='Display failure information for multiple jobs at once'
        )
        batch_parser.add_argument(
            'job_ids',
            type=int,
            nargs='+',
            help='Job IDs to analyze'
        )
    
    def _add_config_commands(self, subparsers):
        """Add config commands"""
        config_parser = subparsers.add_parser(
            'config',
            help='Configuration management',
            description='Commands for managing GitLab CLI configuration'
        )
        
        config_subparsers = config_parser.add_subparsers(
            dest='action',
            title='Config commands',
            metavar='<action>'
        )
        
        # config show command
        show_parser = config_subparsers.add_parser(
            'show',
            help='Show current configuration',
            description='Display the current GitLab CLI configuration'
        )
        
        # config set command
        set_parser = config_subparsers.add_parser(
            'set',
            help='Set configuration values',
            description='Set GitLab CLI configuration values'
        )
        set_parser.add_argument('--gitlab-url', help='GitLab server URL')
        set_parser.add_argument('--project', help='GitLab project path')
        set_parser.add_argument(
            '--default-format',
            choices=['friendly', 'table', 'json'],
            help='Default output format for commands'
        )
    
    def run(self):
        """Main entry point"""
        parser = self.create_parser()
        
        # Handle no arguments or 'help'
        if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ['help', '--help', '-h']):
            self.print_main_help(parser)
            sys.exit(0)
        
        # Handle 'gl help <area>' or 'gl <area> help'
        if len(sys.argv) == 3:
            if sys.argv[1] == 'help' and sys.argv[2] in ['branch', 'mr', 'pipeline', 'job', 'config']:
                # gl help pipeline -> show pipeline help
                self.print_area_help(sys.argv[2])
                sys.exit(0)
            elif sys.argv[2] in ['help', '--help', '-h']:
                # gl pipeline help -> show pipeline help
                if sys.argv[1] in ['branch', 'mr', 'pipeline', 'job', 'config']:
                    self.print_area_help(sys.argv[1])
                    sys.exit(0)
        
        # Parse arguments normally
        try:
            args = parser.parse_args()
        except SystemExit as e:
            # Catch argparse errors and make them friendlier
            if e.code != 0:
                print("\n💡 Try 'gl help' or 'gl <area> help' for usage information")
            sys.exit(e.code)
        
        # Handle area without action
        if args.area and not hasattr(args, 'action') or not args.action:
            self.print_area_help(args.area)
            return
        
        # Route to the appropriate handler
        self.route_command(args)
    
    def print_main_help(self, parser):
        """Print friendly main help"""
        print("GitLab CLI - Explore pipelines, jobs, and merge requests\n")
        print("Usage: gl <area> <action> [options]\n")
        print("Areas:")
        print("  branch     Branch and merge request operations")
        print("  mr         Merge request operations")
        print("  pipeline   Pipeline operations")
        print("  job        Job operations")
        print("  config     Configuration management")
        print("\nExamples:")
        print("  gl branch list                    # List MRs for current branch")
        print("  gl mr show 1234                   # Show MR details")
        print("  gl pipeline status 567890         # Show pipeline status")
        print("  gl job show 123456                # Show job details")
        print("\nFor area-specific help:")
        print("  gl <area> help                    # e.g., gl pipeline help")
        print("  gl help <area>                    # e.g., gl help pipeline")
        print("\nGlobal options:")
        print("  --verbose, -v                     # Show caching and timing info")
    
    def print_area_help(self, area):
        """Print friendly help for a specific area"""
        if area == 'branch':
            print("Branch Commands\n")
            print("Usage: gl branch <action> [options]\n")
            print("Actions:")
            print("  list [branch]        List merge requests for a branch")
            print("\nOptions:")
            print("  --state STATE        Filter by MR state (opened, merged, closed, all)")
            print("  --latest             Show only the latest MR")
            print("\nExamples:")
            print("  gl branch list                    # List MRs for current branch")
            print("  gl branch list feature-xyz        # List MRs for specific branch")
            print("  gl branch list --state all        # Show all MRs")
            
        elif area == 'mr':
            print("Merge Request Commands\n")
            print("Usage: gl mr <action> <id> [options]\n")
            print("Actions:")
            print("  show <id>            Show detailed MR information")
            print("  pipelines <id>       List pipelines for an MR")
            print("\nOptions:")
            print("  --pipelines, -p      Include pipelines in 'show' output")
            print("  --latest             Show only latest pipeline")
            print("\nExamples:")
            print("  gl mr show 1234                   # Show MR details")
            print("  gl mr show 1234 --pipelines       # Include pipeline list")
            print("  gl mr pipelines 1234              # List all pipelines")
            
        elif area == 'pipeline':
            print("Pipeline Commands\n")
            print("Usage: gl pipeline <action> <id> [options]\n")
            print("Actions:")
            print("  status <id>          Show pipeline status summary")
            print("  jobs <id>            List jobs in a pipeline")
            print("\nOptions for 'status':")
            print("  --detailed, -d       Show stage-by-stage progress")
            print("  --verbose, -v        Show cache hits and timing")
            print("\nOptions for 'jobs':")
            print("  --status STATUS      Filter by job status (failed, success, etc.)")
            print("  --stage STAGE        Filter by stage name")
            print("  --sort FIELD         Sort by duration, name, or created")
            print("  --verbose, -v        Show cache hits and timing")
            print("\nExamples:")
            print("  gl pipeline status 567890         # Show pipeline summary")
            print("  gl pipeline status 567890 -d      # Detailed view")
            print("  gl pipeline jobs 567890 --status failed")
            
        elif area == 'job':
            print("Job Commands\n")
            print("Usage: gl job <action> <id(s)> [options]\n")
            print("Actions:")
            print("  show <id>            Show job details and failures")
            print("  batch <id> [id...]   Analyze multiple failed jobs")
            print("\nOptions:")
            print("  --verbose, -v        Show detailed failure information")
            print("\nExamples:")
            print("  gl job show 123456                # Show job details")
            print("  gl job show 123456 -v             # Verbose failure info")
            print("  gl job batch 123456 123457        # Multiple jobs")
            
        elif area == 'config':
            print("Configuration Commands\n")
            print("Usage: gl config <action> [options]\n")
            print("Actions:")
            print("  show                 Show current configuration")
            print("  set                  Set configuration values")
            print("\nOptions for 'set':")
            print("  --gitlab-url URL     Set GitLab server URL")
            print("  --project PATH       Set project path (rarely needed)")
            print("\nExamples:")
            print("  gl config show")
            print("  gl config set --gitlab-url https://gitlab.example.com")
        else:
            print(f"Unknown area: {area}")
            print("Valid areas: branch, mr, pipeline, job, config")
    
    def route_command(self, args):
        """Route commands to appropriate handlers"""
        # Special handling for config commands that don't need validation
        if args.area == 'config':
            self.handle_config(args)
            return
        
        # Validate configuration for other commands
        valid, message = self.config.validate()
        if not valid:
            print(f"Error: {message}", file=sys.stderr)
            sys.exit(1)
        
        # Initialize the CLI with config and verbose flag
        # Check for verbose at both global level and command level
        verbose = getattr(args, 'verbose', False)
        cli = PipelineCLI(self.config, verbose=verbose)
        
        # Route based on area and action
        if args.area == 'branch':
            if args.action == 'list':
                # Get current branch if not specified
                if not hasattr(args, 'branch_name') or not args.branch_name:
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
                cli.cmd_branch_mrs(args)
        
        elif args.area == 'mr':
            if args.action == 'show':
                cli.cmd_mr_info(args)
            elif args.action == 'pipelines':
                cli.cmd_mr_pipelines(args)
        
        elif args.area == 'pipeline':
            if args.action == 'status':
                cli.cmd_pipeline_status(args)
            elif args.action == 'jobs':
                cli.cmd_pipeline_jobs(args)
        
        elif args.area == 'job':
            if args.action == 'show':
                # Map to failures command
                args.job_id = args.job_id  # Already set
                cli.cmd_job_failures(args)
            elif args.action == 'batch':
                cli.cmd_batch_failures(args)
    
    def handle_config(self, args):
        """Handle configuration commands"""
        if args.action == 'show':
            print(f"GitLab URL:     {self.config.gitlab_url or 'Not set'}")
            print(f"Project:        {self.config.project_path or 'Not set (auto-detected from git)'}")
            print(f"Token:          {'Set' if self.config.gitlab_token else 'Not set'}")
            print(f"Cache dir:      {self.config.cache_dir}")
            print(f"Default format: {self.config.default_format}")
        
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
                if 'default_format' in update:
                    print(f"Default output format set to: {update['default_format']}")
            else:
                print("No configuration values provided")


def main():
    """Main entry point for v2 CLI"""
    cli = GitLabCLIv2()
    cli.run()


if __name__ == "__main__":
    main()