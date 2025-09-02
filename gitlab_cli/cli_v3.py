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
    CacheCommand,
    BranchCommand,
)
from .commands.search import SearchCommand
from .commands.mr_context import MRContextCommand


class GitLabCLIv3:
    """Main CLI class with modular command architecture"""

    def __init__(self):
        self.config = Config()
        self.branches_cmd = BranchesCommand()
        self.branch_cmd = BranchCommand()  # New contextual branch command
        self.pipelines_cmd = PipelineCommands()
        self.jobs_cmd = JobCommands()
        self.mrs_cmd = MRsCommand()
        self.mr_context_cmd = MRContextCommand()  # New contextual MR command
        self.config_cmd = ConfigCommand()
        self.cache_cmd = CacheCommand()
        self.search_cmd = SearchCommand()

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
        self._add_branch_parser(subparsers)
        self._add_mr_parser(subparsers)
        self._add_pipeline_parser(subparsers)
        self._add_job_parser(subparsers)
        self.config_cmd.add_arguments(subparsers)
        self.cache_cmd.add_arguments(subparsers)

        return parser

    def _add_branch_parser(self, subparsers):
        """Add branch command parser"""
        parser = subparsers.add_parser(
            "branch",
            help="Branch operations",
            description="Show branch information and related resources",
        )
        self.branch_cmd.add_arguments(parser)

    def _add_mr_parser(self, subparsers):
        """Add MR command parser"""
        # Add 'mr' parser
        parser = subparsers.add_parser(
            "mr",
            aliases=["merge-request"],
            help="Merge request operations",
            description="Show merge request information and related resources",
        )
        
        # Add primary arguments for contextual command
        parser.add_argument(
            "mr_id",
            nargs="?",
            help="MR ID or IID",
        )
        parser.add_argument(
            "resource",
            nargs="?",
            choices=["diff", "pipeline", "commit", "discussion", "approve", "info", "search", "detail"],
            help="Resource to show for MR (diff, pipeline, commit, discussion, approve, info)",
        )
        
        # Diff-specific options
        parser.add_argument(
            "--view",
            choices=["inline", "split", "unified"],
            help="Diff view mode (inline, split, unified)"
        )
        parser.add_argument(
            "--context",
            type=int,
            default=3,
            help="Number of context lines for diff (default: 3)"
        )
        parser.add_argument(
            "--file",
            help="Show diff for specific file only"
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable color output for diffs"
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show diff statistics only"
        )
        parser.add_argument(
            "--name-only",
            action="store_true",
            help="Show only file names that changed"
        )
        
        # Search filters
        parser.add_argument(
            "--author",
            help="Filter by author username"
        )
        parser.add_argument(
            "--assignee",
            help="Filter by assignee username"
        )
        parser.add_argument(
            "--reviewer",
            help="Filter by reviewer username"
        )
        parser.add_argument(
            "--state",
            choices=["opened", "closed", "merged", "all"],
            default="opened",
            help="Filter by MR state (default: opened)"
        )
        parser.add_argument(
            "--labels",
            help="Filter by labels (comma-separated)"
        )
        parser.add_argument(
            "--search",
            help="Search in title and description"
        )
        parser.add_argument(
            "--target-branch",
            dest="target_branch",
            help="Filter by target branch"
        )
        parser.add_argument(
            "--source-branch",
            dest="source_branch",
            help="Filter by source branch"
        )
        parser.add_argument(
            "--wip",
            action="store_true",
            help="Show only WIP/Draft MRs"
        )
        parser.add_argument(
            "--created-after",
            dest="created_after",
            help="Show MRs created after (e.g., '2d', '3h', '1w', '2 days ago')"
        )
        parser.add_argument(
            "--updated-after",
            dest="updated_after",
            help="Show MRs updated after (e.g., '2d', '3h', '1w', '2 days ago')"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of MRs to show (default: 20)"
        )
        parser.add_argument(
            "--format",
            choices=["friendly", "table", "json"],
            help="Output format"
        )

    def _add_pipeline_parser(self, subparsers):
        """Add pipeline command parser"""
        parser = subparsers.add_parser(
            "pipeline",
            help="Pipeline operations",
            description="Show pipeline information and job summaries",
        )

        parser.add_argument(
            "action",
            nargs="?",
            help='Pipeline ID(s) or action: <id>, <id,id,...>, "list", "detail", "graph", "retry", "rerun", or "cancel"',
        )
        parser.add_argument(
            "pipeline_id",
            nargs="?",
            help='Pipeline ID (when using "detail", "graph", "retry", "rerun", or "cancel")',
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
            "--show-variables", 
            action="store_true", 
            help="Show pipeline variables (for detail command)"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )
        parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
        
        # Add time-based filters for list action
        parser.add_argument(
            "--since",
            help="Show pipelines since (e.g., '2d', '3h', '1w', '2 days ago', '2024-01-15')"
        )
        parser.add_argument(
            "--before", 
            help="Show pipelines before (e.g., '1d', '2h', '1 week ago', '2024-01-20')"
        )
        parser.add_argument(
            "--user",
            help="Filter by username who triggered the pipeline"
        )
        parser.add_argument(
            "--ref",
            help="Filter by ref/branch name"
        )
        parser.add_argument(
            "--source",
            choices=["push", "web", "trigger", "schedule", "api", "external", "pipeline", "chat", "merge_request_event"],
            help="Filter by pipeline source"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of pipelines to show (default: 20)"
        )

    def _add_job_parser(self, subparsers):
        """Add job command parser"""
        parser = subparsers.add_parser(
            "job",
            help="Job operations",
            description="Show job information and failure details",
        )

        parser.add_argument(
            "action",
            nargs="?",
            help='Job ID(s) or action: <id>, <id,id,...>, "detail", "logs", "tail", "retry", or "play"',
        )
        parser.add_argument(
            "job_id",
            nargs="?",
            help='Job ID (when using "detail", "logs", "tail", "retry", or "play")',
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
        print("Usage: gl <area> [resource] [options]\n")
        print("Areas:")
        print("  branch [name]        Show branch info and related resources")
        print("  mr <id>              Show MR info and related resources")
        print("  pipeline <id>        Show pipeline info and jobs")
        print("  job <id>             Show job info and logs")
        print("  config               Manage configuration")
        print("  cache                Manage cache\n")
        print("Contextual Commands:")
        print("  gl branch                   # Show current branch info")
        print("  gl branch pipeline          # Show pipelines for current branch")
        print("  gl branch mr                # Show MRs for current branch")
        print("  gl branch commits           # Show commits for current branch")
        print("  gl branch <name>            # Show specific branch info")
        print("  gl branch <name> pipeline   # Show pipelines for specific branch")
        print("  gl branch --create-mr       # Create MR from current branch\n")
        print("  gl mr <id>                  # Show MR info")
        print("  gl mr <id> diff             # Show MR diff")
        print("  gl mr <id> pipeline         # Show MR pipelines")
        print("  gl mr <id> commit           # Show MR commits")
        print("  gl mr <id> discussion       # Show MR discussions\n")
        print("Actions:")
        print("  gl pipeline list            # List/search pipelines")
        print("  gl pipeline <id>            # Show pipeline summary")
        print("  gl pipeline detail <id>     # Show comprehensive info")
        print("  gl pipeline graph <id>      # Show pipeline graph")
        print("  gl pipeline retry <id>      # Retry failed jobs")
        print("  gl pipeline rerun <id>      # Create new pipeline for same commit")
        print("  gl pipeline cancel <id>     # Cancel pipeline\n")
        print("  gl job <id>                 # Show job summary")
        print("  gl job detail <id>          # Show comprehensive info")
        print("  gl job logs <id>            # Show job logs")
        print("  gl job tail <id>            # Tail job logs")
        print("  gl job retry <id>           # Retry job")
        print("  gl job play <id>            # Play manual job\n")
        print("  gl mr search                # Search MRs with filters\n")
        print("  gl cache stats              # Show cache statistics")
        print("  gl cache list               # List cached pipelines")
        print("  gl cache clear              # Clear cache\n")
        print("Diff View Options:")
        print("  gl mr <id> diff             # Default view (from config)")
        print("  gl mr <id> diff --view split    # Side-by-side diff")
        print("  gl mr <id> diff --view inline   # Inline diff with line numbers")
        print("  gl mr <id> diff --view unified  # Traditional git diff")
        print("  gl mr <id> diff --stats         # Show only statistics")
        print("  gl mr <id> diff --name-only     # Show only file names\n")
        print("Common options:")
        print("  --format <type>      Output as friendly, table, or json")
        print("  --help               Show help for any command")

    def route_command(self, args):
        """Route commands to appropriate handlers"""
        # Handle config and cache separately (don't need API connection)
        if args.area == "config":
            self.config_cmd.handle(self.config, args)
            return
        
        if args.area == "cache":
            self.cache_cmd.handle(self.config, args)
            return

        # Check if user is asking for help on any command
        if args.area in ["pipeline", "job", "mr", "merge-request", "branch"]:
            if (hasattr(args, 'action') and args.action == "help") or \
               (hasattr(args, 'mr_id') and args.mr_id == "help") or \
               (hasattr(args, 'branch_name') and args.branch_name == "help"):
                # Show help without requiring config
                parser = self.create_parser()
                parser.parse_args([args.area, '--help'])
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
        if args.area == "branch":
            # Use new contextual branch command
            self.branch_cmd.handle(cli, args, output_format)

        elif args.area in ["mr", "merge-request"]:
            # Handle MR contextual commands
            if not args.mr_id and not args.resource:
                print("Error: Please provide MR ID or use 'gl mr --help' for help")
                sys.exit(1)
            elif args.mr_id == "help":
                # Handle 'gl mr help' same as 'gl mr --help'
                parser = self.create_parser()
                parser.parse_args([args.area, '--help'])
            elif args.resource == "search" or (args.mr_id == "search" and not args.resource):
                # Search MRs with filters
                self.search_cmd.search_mrs(cli, args, output_format)
            elif args.resource == "detail" or (args.mr_id and args.resource == "detail"):
                # Legacy detail command support
                mr_id = args.mr_id if args.resource == "detail" else args.resource
                if mr_id and mr_id != "detail":
                    try:
                        mr_id = int(mr_id)
                        self.mrs_cmd.handle_detail(cli, mr_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid MR ID: {mr_id}")
                        sys.exit(1)
                else:
                    print("Error: 'detail' requires an MR ID")
                    sys.exit(1)
            elif args.mr_id:
                # Use new contextual MR command
                try:
                    # Validate MR ID is numeric
                    int(args.mr_id)
                    self.mr_context_cmd.handle(cli, args, output_format)
                except ValueError:
                    # Check if it's a legacy multi-ID format
                    if ',' in args.mr_id or args.mr_id.isdigit():
                        self.mrs_cmd.handle(cli, args, output_format, action=args.mr_id)
                    else:
                        print(f"Error: Invalid MR ID: {args.mr_id}")
                        sys.exit(1)
            else:
                print("Error: Please provide MR ID or use 'gl mr --help' for help")
                sys.exit(1)

        elif args.area == "pipeline":
            if not args.action:
                print("Error: Please provide pipeline ID(s) or use 'gl pipeline --help' for help")
                sys.exit(1)
            elif args.action == "help":
                # Handle 'gl pipeline help' same as 'gl pipeline --help'
                parser = self.create_parser()
                parser.parse_args([args.area, '--help'])
            elif args.action == "list":
                # List pipelines with filters
                self.search_cmd.list_pipelines(cli, args, output_format)
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
            elif args.action == "graph":
                if args.pipeline_id:
                    try:
                        pipeline_id = int(args.pipeline_id)
                        self.pipelines_cmd.handle_pipeline_graph(cli, pipeline_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid pipeline ID: {args.pipeline_id}")
                        sys.exit(1)
                else:
                    print("Error: 'graph' requires a pipeline ID")
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
            elif args.action == "rerun":
                if args.pipeline_id:
                    try:
                        pipeline_id = int(args.pipeline_id)
                        self.pipelines_cmd.handle_pipeline_rerun(cli, pipeline_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid pipeline ID: {args.pipeline_id}")
                        sys.exit(1)
                else:
                    print("Error: 'rerun' requires a pipeline ID")
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

        elif args.area == "job":
            if not args.action:
                print("Error: Please provide job ID(s) or use 'gl job --help' for help")
                sys.exit(1)
            elif args.action == "help":
                # Handle 'gl job help' same as 'gl job --help'
                parser = self.create_parser()
                parser.parse_args([args.area, '--help'])
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
            elif args.action == "tail":
                if args.job_id:
                    try:
                        job_id = int(args.job_id)
                        self.jobs_cmd.handle_job_tail(cli, job_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid job ID: {args.job_id}")
                        sys.exit(1)
                else:
                    print("Error: 'tail' requires a job ID")
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