#!/usr/bin/env python3
"""GitLab CLI v3 - Refactored with modular command handlers"""

import sys
import argparse
from typing import List

from .config import Config
from .cli import PipelineCLI
from .commands import (
    BranchesCommand,
    PipelineCommands,
    JobCommands,
    MRsCommand,
    ConfigCommand,
)


class GitLabCLIv3:
    """Main CLI class with modular command architecture"""

    def __init__(self):
        self.config = Config()
        self.branches_cmd = BranchesCommand()
        self.pipelines_cmd = PipelineCommands()
        self.jobs_cmd = JobCommands()
        self.mrs_cmd = MRsCommand()
        self.config_cmd = ConfigCommand()

    def create_parser(self):
        """Create the main argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            prog="gl",
            description="GitLab CLI - Explore pipelines, jobs, and merge requests",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output (shows caching, timing, etc.)",
        )

        # Create subparsers for each area
        subparsers = parser.add_subparsers(
            dest="area",
            title="Available areas",
            description="Use `gl <area> --help` for area-specific commands",
            metavar="<area>",
        )

        # Add command parsers
        self._add_branches_parser(subparsers)
        self._add_mrs_parser(subparsers)
        self._add_pipelines_parser(subparsers)
        self._add_jobs_parser(subparsers)
        self.config_cmd.add_arguments(subparsers)

        return parser

    def _add_branches_parser(self, subparsers):
        """Add branches command parser"""
        parser = subparsers.add_parser(
            "branches",
            help="Branch operations",
            description="List merge requests for branches",
        )
        self.branches_cmd.add_arguments(parser)

    def _add_mrs_parser(self, subparsers):
        """Add MRs command parser"""
        parser = subparsers.add_parser(
            "mrs",
            help="Merge request operations",
            description="Show merge request information",
        )
        self.mrs_cmd.add_arguments(parser)

    def _add_pipelines_parser(self, subparsers):
        """Add pipelines command parser"""
        parser = subparsers.add_parser(
            "pipelines",
            help="Pipeline operations",
            description="Show pipeline information and job summaries",
        )

        parser.add_argument(
            "action",
            nargs="?",
            help='Pipeline ID(s) or action: <id>, <id,id,...>, "detail", "retry", or "cancel"',
        )
        parser.add_argument(
            "pipeline_id",
            nargs="?",
            help='Pipeline ID (when using "detail", "retry", or "cancel")',
        )

        # Status filters
        status_group = parser.add_mutually_exclusive_group()
        status_group.add_argument("--failed", action="store_true", help="Show failed jobs")
        status_group.add_argument("--running", action="store_true", help="Show running jobs")
        status_group.add_argument("--success", action="store_true", help="Show successful jobs")
        status_group.add_argument("--skipped", action="store_true", help="Show skipped jobs")

        parser.add_argument("--jobs", action="store_true", help="List all jobs (instead of summary)")
        parser.add_argument("--stage", help="Filter by stage name")
        parser.add_argument(
            "--job-search",
            help="Search for jobs by name pattern (case-insensitive)"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )
        parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    def _add_jobs_parser(self, subparsers):
        """Add jobs command parser"""
        parser = subparsers.add_parser(
            "jobs",
            help="Job operations",
            description="Show job information and failure details",
        )

        parser.add_argument(
            "action",
            nargs="?",
            help='Job ID(s) or action: <id>, <id,id,...>, "detail", "logs", "retry", or "play"',
        )
        parser.add_argument(
            "job_id",
            nargs="?",
            help='Job ID (when using "detail", "logs", "retry", or "play")',
        )
        parser.add_argument(
            "--failures", action="store_true", help="Show detailed failure information"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def print_main_help(self):
        """Print friendly main help"""
        print("GitLab CLI - Explore pipelines, jobs, and merge requests\n")
        print("Usage: gl <area> <id(s)> [options]\n")
        print("Areas:")
        print("  branches [name]      List MRs for a branch")
        print("  mrs <id,...>         Show MR summaries")
        print("  pipelines <id,...>   Show pipeline summaries")
        print("  jobs <id,...>        Show job summaries")
        print("  config               Manage configuration\n")
        print("Actions:")
        print("  gl pipelines detail <id>    Show comprehensive pipeline info")
        print("  gl pipelines retry <id>     Retry failed jobs in pipeline")
        print("  gl pipelines cancel <id>    Cancel running pipeline")
        print("  gl jobs detail <id>         Show comprehensive job info")
        print("  gl jobs logs <id>           Show job logs/trace")
        print("  gl jobs retry <id>          Retry a failed job")
        print("  gl jobs play <id>           Play/trigger a manual job")
        print("  gl mrs detail <id>          Show comprehensive MR info\n")
        print("Common options:")
        print("  --format <type>      Output as friendly, table, or json")
        print("  --help               Show help for any command\n")
        print("Examples:")
        print("  gl branches                 # List MRs for current branch")
        print("  gl pipelines 123456         # Show pipeline summary")
        print("  gl jobs 789012 --failures   # Show job with failure details")
        print("  gl mrs 5678                 # Show MR summary")

    def route_command(self, args):
        """Route commands to appropriate handlers"""
        # Handle config separately
        if args.area == "config":
            self.config_cmd.handle(self.config, args)
            return

        # Validate configuration for other commands
        valid, message = self.config.validate()
        if not valid:
            print(f"Error: {message}", file=sys.stderr)
            sys.exit(1)

        # Initialize CLI with config
        verbose = getattr(args, "verbose", False)
        cli = PipelineCLI(self.config, verbose=verbose)

        # Get output format
        output_format = getattr(args, "format", None) or self.config.default_format

        # Route based on area
        if args.area == "branches":
            self.branches_cmd.handle(cli, args, output_format)

        elif args.area == "mrs":
            if not args.action:
                print("Error: Please provide MR ID(s) or use 'gl mrs --help' for help")
                sys.exit(1)
            elif args.action == "detail":
                if args.mr_id:
                    try:
                        mr_id = int(args.mr_id)
                        self.mrs_cmd.handle_detail(cli, mr_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid MR ID: {args.mr_id}")
                        sys.exit(1)
                else:
                    print("Error: 'detail' requires an MR ID")
                    sys.exit(1)
            else:
                self.mrs_cmd.handle(cli, args, output_format, action=args.action)

        elif args.area == "pipelines":
            if not args.action:
                print("Error: Please provide pipeline ID(s) or use 'gl pipelines --help' for help")
                sys.exit(1)
            elif args.action == "detail":
                if args.pipeline_id:
                    try:
                        pipeline_id = int(args.pipeline_id)
                        self.pipelines_cmd.handle_pipeline_detail(cli, pipeline_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid pipeline ID: {args.pipeline_id}")
                        sys.exit(1)
                else:
                    print("Error: 'detail' requires a pipeline ID")
                    sys.exit(1)
            elif args.action == "retry":
                if args.pipeline_id:
                    try:
                        pipeline_id = int(args.pipeline_id)
                        self.pipelines_cmd.handle_pipeline_retry(cli, pipeline_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid pipeline ID: {args.pipeline_id}")
                        sys.exit(1)
                else:
                    print("Error: 'retry' requires a pipeline ID")
                    sys.exit(1)
            elif args.action == "cancel":
                if args.pipeline_id:
                    try:
                        pipeline_id = int(args.pipeline_id)
                        self.pipelines_cmd.handle_pipeline_cancel(cli, pipeline_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid pipeline ID: {args.pipeline_id}")
                        sys.exit(1)
                else:
                    print("Error: 'cancel' requires a pipeline ID")
                    sys.exit(1)
            else:
                # It's pipeline IDs
                ids = self.pipelines_cmd.parse_ids(args.action)
                self.pipelines_cmd.handle_pipelines(cli, ids, args, output_format)

        elif args.area == "jobs":
            if not args.action:
                print("Error: Please provide job ID(s) or use 'gl jobs --help' for help")
                sys.exit(1)
            elif args.action == "detail":
                if args.job_id:
                    try:
                        job_id = int(args.job_id)
                        self.jobs_cmd.handle_job_detail(cli, job_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid job ID: {args.job_id}")
                        sys.exit(1)
                else:
                    print("Error: 'detail' requires a job ID")
                    sys.exit(1)
            elif args.action == "logs":
                if args.job_id:
                    try:
                        job_id = int(args.job_id)
                        self.jobs_cmd.handle_job_logs(cli, job_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid job ID: {args.job_id}")
                        sys.exit(1)
                else:
                    print("Error: 'logs' requires a job ID")
                    sys.exit(1)
            elif args.action == "retry":
                if args.job_id:
                    try:
                        job_id = int(args.job_id)
                        self.jobs_cmd.handle_job_retry(cli, job_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid job ID: {args.job_id}")
                        sys.exit(1)
                else:
                    print("Error: 'retry' requires a job ID")
                    sys.exit(1)
            elif args.action == "play":
                if args.job_id:
                    try:
                        job_id = int(args.job_id)
                        self.jobs_cmd.handle_job_play(cli, job_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid job ID: {args.job_id}")
                        sys.exit(1)
                else:
                    print("Error: 'play' requires a job ID")
                    sys.exit(1)
            else:
                # It's job IDs
                ids = self.jobs_cmd.parse_ids(args.action)
                self.jobs_cmd.handle_jobs(cli, ids, args, output_format)

    def run(self):
        """Main entry point"""
        parser = self.create_parser()

        # Handle no arguments or help
        if len(sys.argv) == 1 or (
            len(sys.argv) == 2 and sys.argv[1] in ["help", "--help", "-h"]
        ):
            self.print_main_help()
            sys.exit(0)

        # Parse arguments
        args = parser.parse_args()

        # Route to the appropriate handler
        self.route_command(args)


def main():
    """Main entry point for v3 CLI"""
    cli = GitLabCLIv3()
    cli.run()


if __name__ == "__main__":
    main()