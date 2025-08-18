#!/usr/bin/env python3
# Copyright 2024 BeardedGiant
# Refactored CLI v3 - More intuitive, exploratory interface

import sys
import argparse
import json
from typing import List

from .config import Config
from .cli import PipelineCLI


class GitLabCLIv3:
    """Main CLI class with intuitive ID-based commands"""

    def __init__(self):
        self.config = Config()

    def create_parser(self):
        """Create the main argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            prog="gl",
            description="GitLab CLI - Explore pipelines, jobs, and merge requests",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add global verbose flag
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output (shows caching, timing, etc.)",
        )

        # Create subparsers for each area (using plurals)
        subparsers = parser.add_subparsers(
            dest="area",
            title="Available areas",
            description="Use `gl <area> --help` for area-specific commands",
            metavar="<area>",
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
            "branches",
            help="Branch operations",
            description="List merge requests for branches",
        )

        parser.add_argument(
            "branch_name", nargs="?", help="Branch name (defaults to current branch)"
        )
        parser.add_argument(
            "--state",
            choices=["opened", "merged", "closed", "all"],
            default="opened",
            help="Filter by MR state (default: opened)",
        )
        parser.add_argument(
            "--latest", action="store_true", help="Show only the latest MR"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def _add_mrs_commands(self, subparsers):
        """Add merge request commands"""
        parser = subparsers.add_parser(
            "mrs",
            help="Merge request operations",
            description="Show merge request information",
        )

        # First positional argument
        parser.add_argument(
            "action",
            nargs="?",  # Make it optional so --help works
            help='MR ID(s) or action: <id>, <id,id,...>, or "detail"',
        )

        # Second positional for the ID when using actions
        parser.add_argument("mr_id", nargs="?", help='MR ID (when using "detail")')
        parser.add_argument(
            "--pipelines", action="store_true", help="Show pipeline information"
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Show full details including description",
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def _add_pipelines_commands(self, subparsers):
        """Add pipeline commands"""
        parser = subparsers.add_parser(
            "pipelines",
            help="Pipeline operations",
            description="Show pipeline information and job summaries",
        )

        # First positional argument
        parser.add_argument(
            "action",
            nargs="?",  # Make it optional so --help works
            help='Pipeline ID(s) or action: <id>, <id,id,...>, "detail", "retry", or "cancel"',
        )

        # Second positional for the ID when using actions
        parser.add_argument(
            "pipeline_id", nargs="?", help='Pipeline ID (when using "detail", "retry", or "cancel")'
        )

        # Status filters for drilling down
        status_group = parser.add_mutually_exclusive_group()
        status_group.add_argument(
            "--failed", action="store_true", help="Show failed jobs"
        )
        status_group.add_argument(
            "--running", action="store_true", help="Show running jobs"
        )
        status_group.add_argument(
            "--success", action="store_true", help="Show successful jobs"
        )
        status_group.add_argument(
            "--skipped", action="store_true", help="Show skipped jobs"
        )

        parser.add_argument(
            "--jobs", action="store_true", help="List all jobs (instead of summary)"
        )
        parser.add_argument("--stage", help="Filter by stage name")
        parser.add_argument(
            "--job-search", help="Search for jobs by name pattern (case-insensitive)"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

    def _add_jobs_commands(self, subparsers):
        """Add job commands"""
        parser = subparsers.add_parser(
            "jobs",
            help="Job operations",
            description="Show job information and failure details",
        )

        # First positional argument
        parser.add_argument(
            "action",
            nargs="?",  # Make it optional so --help works
            help='Job ID(s) or action: <id>, <id,id,...>, "detail", "logs", "retry", or "play"',
        )

        # Second positional for the ID when using actions
        parser.add_argument(
            "job_id", nargs="?", help='Job ID (when using "detail", "logs", "retry", or "play")'
        )
        parser.add_argument(
            "--failures", action="store_true", help="Show detailed failure information"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def _add_config_commands(self, subparsers):
        """Add config commands"""
        parser = subparsers.add_parser(
            "config",
            help="Configuration management",
            description="Manage GitLab CLI configuration",
        )

        subparsers = parser.add_subparsers(
            dest="action", title="Config commands", metavar="<action>"
        )

        # config show
        show_parser = subparsers.add_parser("show", help="Show current configuration")

        # config set
        set_parser = subparsers.add_parser("set", help="Set configuration values")
        set_parser.add_argument("--gitlab-url", help="GitLab server URL")
        set_parser.add_argument("--project", help="GitLab project path")
        set_parser.add_argument(
            "--default-format",
            choices=["friendly", "table", "json"],
            help="Default output format",
        )

    def parse_ids(self, id_string: str) -> List[int]:
        """Parse comma-separated IDs"""
        ids = []
        for part in id_string.split(","):
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
        if len(sys.argv) == 1 or (
            len(sys.argv) == 2 and sys.argv[1] in ["help", "--help", "-h"]
        ):
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
        print("  pipelines detail <id> Show comprehensive pipeline details")
        print("  jobs <id,...>        Show job summaries")
        print("  jobs detail <id>     Show comprehensive job details")
        print("  jobs logs <id>       Show full job logs/trace")
        print("  mrs detail <id>      Show comprehensive MR details")
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
        if args.area == "config":
            self.handle_config(args)
            return

        # Validate configuration for other commands
        valid, message = self.config.validate()
        if not valid:
            print(f"Error: {message}", file=sys.stderr)
            sys.exit(1)

        # Initialize the CLI with config
        verbose = getattr(args, "verbose", False)
        cli = PipelineCLI(self.config, verbose=verbose)

        # Get output format
        output_format = getattr(args, "format", None) or self.config.default_format

        # Route based on area
        if args.area == "branches":
            self.handle_branches(cli, args, output_format)

        elif args.area == "mrs":
            # Check if action was provided
            if not args.action:
                print("Error: Please provide MR ID(s) or use 'gl mrs --help' for help")
                sys.exit(1)
            # Check if action is 'detail'
            elif args.action == "detail":
                if args.mr_id:
                    try:
                        mr_id = int(args.mr_id)
                        self.handle_mr_detail(cli, mr_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid MR ID: {args.mr_id}")
                        sys.exit(1)
                else:
                    print("Error: 'detail' requires an MR ID")
                    sys.exit(1)
            else:
                # It's MR IDs
                ids = self.parse_ids(args.action)
                self.handle_mrs(cli, ids, args, output_format)

        elif args.area == "pipelines":
            # Check if action was provided
            if not args.action:
                print(
                    "Error: Please provide pipeline ID(s) or use 'gl pipelines --help' for help"
                )
                sys.exit(1)
            # Check if action is 'detail', 'retry', or 'cancel'
            elif args.action == "detail":
                if args.pipeline_id:
                    try:
                        pipeline_id = int(args.pipeline_id)
                        self.handle_pipeline_detail(
                            cli, pipeline_id, args, output_format
                        )
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
                        self.handle_pipeline_retry(cli, pipeline_id, args, output_format)
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
                        self.handle_pipeline_cancel(cli, pipeline_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid pipeline ID: {args.pipeline_id}")
                        sys.exit(1)
                else:
                    print("Error: 'cancel' requires a pipeline ID")
                    sys.exit(1)
            else:
                # It's pipeline IDs
                ids = self.parse_ids(args.action)
                self.handle_pipelines(cli, ids, args, output_format)

        elif args.area == "jobs":
            # Check if action was provided
            if not args.action:
                print(
                    "Error: Please provide job ID(s) or use 'gl jobs --help' for help"
                )
                sys.exit(1)
            # Check if action is 'detail' or 'logs'
            elif args.action == "detail":
                if args.job_id:
                    try:
                        job_id = int(args.job_id)
                        self.handle_job_detail(cli, job_id, args, output_format)
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
                        self.handle_job_logs(cli, job_id, args, output_format)
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
                        self.handle_job_retry(cli, job_id, args, output_format)
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
                        self.handle_job_play(cli, job_id, args, output_format)
                    except ValueError:
                        print(f"Error: Invalid job ID: {args.job_id}")
                        sys.exit(1)
                else:
                    print("Error: 'play' requires a job ID")
                    sys.exit(1)
            else:
                # It's job IDs
                ids = self.parse_ids(args.action)
                self.handle_jobs(cli, ids, args, output_format)

    def handle_branches(self, cli, args, output_format):
        """Handle branch commands"""
        # Get current branch if not specified
        if not args.branch_name:
            import subprocess

            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
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
        all_mrs = []

        for mr_id in ids:
            if output_format == "json":
                # For JSON, collect all data
                self.show_mr_json(cli, mr_id, args)
            elif output_format == "table":
                # Collect for table display
                try:
                    mr = cli.explorer.project.mergerequests.get(mr_id)
                    all_mrs.append(
                        {
                            "iid": mr.iid,
                            "state": mr.state,
                            "author": mr.author["username"],
                            "target": mr.target_branch,
                            "created": mr.created_at[:10],
                            "title": mr.title,
                        }
                    )
                except Exception as e:
                    print(f"Error fetching MR {mr_id}: {e}")
            else:
                self.show_mr_summary(cli, mr_id, args, output_format)

            if len(ids) > 1 and output_format == "friendly":
                print("-" * 80)

        if output_format == "table" and all_mrs:
            # Display MRs in table format
            print("\nMerge Requests")
            print("-" * 120)
            print(
                f"{'MR':<8} {'State':<10} {'Author':<15} {'Target':<20} {'Created':<12} {'Title':<50}"
            )
            print("-" * 120)
            for mr_info in all_mrs:
                title = (
                    mr_info["title"][:47] + "..."
                    if len(mr_info["title"]) > 50
                    else mr_info["title"]
                )
                print(
                    f"!{mr_info['iid']:<7} {mr_info['state']:<10} {mr_info['author']:<15} {mr_info['target']:<20} {mr_info['created']:<12} {title:<50}"
                )
            print("-" * 120)

    def show_mr_summary(self, cli, mr_id, args, output_format):
        """Show MR summary"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)

            # Summary view
            status_color = {
                "opened": "\033[92m",  # Green
                "merged": "\033[94m",  # Blue
                "closed": "\033[91m",  # Red
            }.get(mr.state, "")

            print(f"\nMR !{mr.iid}: {mr.title}")
            print(
                f"Status: {status_color}{mr.state.upper()}\033[0m | Author: {mr.author['username']} | Target: {mr.target_branch}"
            )
            print(f"Created: {mr.created_at[:10]} | Updated: {mr.updated_at[:10]}")

            # Pipeline status if available
            if hasattr(mr, "head_pipeline") and mr.head_pipeline:
                p_status = mr.head_pipeline.get("status", "unknown")
                p_color = {
                    "success": "\033[92m✅",
                    "failed": "\033[91m❌",
                    "running": "\033[93m🔄",
                }.get(p_status, "⏸")
                print(
                    f"Pipeline: {p_color} {p_status}\033[0m (ID: {mr.head_pipeline.get('id')})"
                )

            if args.pipelines:
                # Show recent pipelines
                pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
                if pipelines:
                    print("\nRecent Pipelines:")
                    for p in pipelines:
                        status_icon = {
                            "success": "✅",
                            "failed": "❌",
                            "running": "🔄",
                        }.get(p["status"], "⏸")
                        print(
                            f"  {status_icon} {p['id']} - {p['status']} ({p['created_at'][:16]})"
                        )

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
                "id": mr.id,
                "iid": mr.iid,
                "title": mr.title,
                "state": mr.state,
                "author": mr.author["username"],
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "created_at": mr.created_at,
                "updated_at": mr.updated_at,
                "web_url": mr.web_url,
            }

            if hasattr(mr, "head_pipeline") and mr.head_pipeline:
                output["pipeline"] = mr.head_pipeline

            if args.pipelines:
                output["recent_pipelines"] = cli.explorer.get_pipelines_for_mr(mr_id)[
                    :10
                ]

            print(json.dumps(output, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))

    def handle_pipelines(self, cli, ids, args, output_format):
        """Handle pipeline commands - show summaries by default"""
        # Determine what status filter was used
        status_filter = None
        if args.failed:
            status_filter = "failed"
        elif args.running:
            status_filter = "running"
        elif args.success:
            status_filter = "success"
        elif args.skipped:
            status_filter = "skipped"

        for pipeline_id in ids:
            if args.job_search:
                # Search for jobs by name pattern
                self.search_pipeline_jobs(
                    cli, pipeline_id, args.job_search, output_format
                )
            elif args.jobs or status_filter:
                # Show jobs (filtered if status provided)
                args.pipeline_id = pipeline_id
                args.status = status_filter
                args.format = output_format
                cli.cmd_pipeline_jobs(args)
            else:
                # Show pipeline summary
                self.show_pipeline_summary(cli, pipeline_id, args, output_format)

            if len(ids) > 1 and output_format != "json":
                print("-" * 80)

    def search_pipeline_jobs(self, cli, pipeline_id, search_pattern, output_format):
        """Search for jobs in a pipeline by name pattern"""
        try:
            # Get all jobs for the pipeline, including bridges (trigger jobs)
            pipeline = cli.explorer.project.pipelines.get(pipeline_id)

            # Get regular jobs
            jobs = pipeline.jobs.list(all=True)

            # Also get bridges (trigger jobs) - these are shown as "Trigger job" in UI
            try:
                bridges = pipeline.bridges.list(all=True)
                # Combine jobs and bridges
                all_jobs = list(jobs) + list(bridges)
            except:
                # If bridges API is not available, just use regular jobs
                all_jobs = list(jobs)

            # Filter jobs by name pattern (case-insensitive)
            pattern_lower = search_pattern.lower()
            matching_jobs = [
                job for job in all_jobs if pattern_lower in job.name.lower()
            ]

            if not matching_jobs:
                # Debug: show what jobs we found
                if cli.verbose:
                    print(
                        f"Debug: Found {len(all_jobs)} total jobs in pipeline {pipeline_id}"
                    )
                    for job in all_jobs[:5]:
                        print(f"  - {job.name} (type: {type(job).__name__})")
                print(
                    f"No jobs found matching '{search_pattern}' in pipeline {pipeline_id}"
                )
                return

            if output_format == "json":
                # JSON output
                output = {
                    "pipeline_id": pipeline_id,
                    "search_pattern": search_pattern,
                    "matching_jobs": [
                        {
                            "id": job.id,
                            "name": job.name,
                            "status": job.status,
                            "stage": job.stage,
                            "duration": job.duration,
                            "created_at": job.created_at,
                            "started_at": job.started_at,
                            "finished_at": job.finished_at,
                            "web_url": job.web_url,
                        }
                        for job in matching_jobs
                    ],
                }
                print(json.dumps(output, indent=2))
            elif output_format == "table":
                # Table format
                print(f"\nJobs matching '{search_pattern}' in Pipeline {pipeline_id}")
                print("-" * 100)
                print(
                    f"{'ID':<12} {'Status':<10} {'Stage':<15} {'Duration':<10} {'Name':<50}"
                )
                print("-" * 100)
                for job in matching_jobs:
                    name = job.name[:47] + "..." if len(job.name) > 50 else job.name
                    status_display = job.status.upper()[:10]
                    duration = cli.explorer.format_duration(job.duration)
                    print(
                        f"{job.id:<12} {status_display:<10} {job.stage:<15} {duration:<10} {name:<50}"
                    )
                print("-" * 100)
                print(f"Found {len(matching_jobs)} job(s) matching '{search_pattern}'")
            else:
                # Friendly format
                print(
                    f"\n🔍 Jobs matching '{search_pattern}' in Pipeline {pipeline_id}:"
                )
                print("-" * 60)

                for job in matching_jobs:
                    # Check if job is allowed to fail and has failed
                    is_allowed_failure = (
                        getattr(job, "allow_failure", False) and job.status == "failed"
                    )

                    if is_allowed_failure:
                        status_icon = "⚠️"  # Warning icon for allowed failures
                        status_text = f"{job.status} (allowed)"
                    else:
                        status_icon = {
                            "success": "✅",
                            "failed": "❌",
                            "running": "🔄",
                            "skipped": "⏭",
                            "canceled": "⏹",
                            "manual": "👆",
                        }.get(job.status, "⏸")
                        status_text = job.status

                    # Check if it's a bridge/trigger job
                    job_type = (
                        " (Trigger job)" if hasattr(job, "downstream_pipeline") else ""
                    )

                    print(f"\n{status_icon} {job.name}{job_type}")
                    print(
                        f"   ID: {job.id} | Status: {status_text} | Stage: {job.stage}"
                    )

                    # Duration might not exist for bridges
                    duration = getattr(job, "duration", None)
                    if duration is not None:
                        print(f"   Duration: {cli.explorer.format_duration(duration)}")

                    # Show downstream pipeline for trigger jobs
                    if hasattr(job, "downstream_pipeline") and job.downstream_pipeline:
                        downstream = job.downstream_pipeline
                        print(
                            f"   Triggered Pipeline: #{downstream.get('id')} - {downstream.get('status')}"
                        )

                    if job.status == "failed":
                        print(f"   URL: {job.web_url}")

                print(
                    f"\nFound {len(matching_jobs)} job(s) matching '{search_pattern}'"
                )

        except Exception as e:
            print(f"Error searching jobs in pipeline {pipeline_id}: {e}")

    def show_pipeline_summary(self, cli, pipeline_id, args, output_format):
        """Show pipeline summary"""
        summary = cli.explorer.get_job_status_summary(pipeline_id, verbose=cli.verbose)

        if not summary:
            print(f"Could not fetch pipeline {pipeline_id}")
            return

        if output_format == "json":
            output = {
                "pipeline_id": pipeline_id,
                "status": summary["pipeline_status"],
                "created_at": summary["created_at"],
                "duration": summary["duration"],
                "job_counts": {
                    "total": summary["total"],
                    "failed": summary["failed"],
                    "success": summary["success"],
                    "running": summary["running"],
                    "skipped": summary["skipped"],
                    "pending": summary["pending"],
                },
            }
            # Always include stages in JSON output
            output["stages"] = summary["stages"]
            print(json.dumps(output, indent=2))
        elif output_format == "table":
            # Table format for pipeline summary
            print(f"\nPipeline {pipeline_id} Summary")
            print("-" * 60)
            print(f"{'Status':<15} {summary['pipeline_status'].upper()}")
            print(f"{'Created':<15} {summary['created_at'][:16]}")
            print(
                f"{'Duration':<15} {cli.explorer.format_duration(summary['duration'])}"
            )
            print("-" * 60)
            print(f"{'Job Status':<15} {'Count':>10}")
            print("-" * 60)
            print(f"{'Total':<15} {summary['total']:>10}")
            if summary["success"] > 0:
                print(f"{'Success':<15} {summary['success']:>10}")
            if summary["failed"] > 0:
                print(f"{'Failed':<15} {summary['failed']:>10}")
            if summary["running"] > 0:
                print(f"{'Running':<15} {summary['running']:>10}")
            if summary["skipped"] > 0:
                print(f"{'Skipped':<15} {summary['skipped']:>10}")
            if summary["pending"] > 0:
                print(f"{'Pending':<15} {summary['pending']:>10}")
            print("-" * 60)

            # Show failed jobs in table format
            if summary["failed_jobs"]:
                print("\nFailed Jobs:")
                print("-" * 80)
                print(f"{'ID':<12} {'Stage':<15} {'Name':<50}")
                print("-" * 80)
                for job in summary["failed_jobs"][:10]:
                    name = (
                        job["name"][:47] + "..."
                        if len(job["name"]) > 50
                        else job["name"]
                    )
                    print(f"{job['id']:<12} {job['stage']:<15} {name:<50}")
                if len(summary["failed_jobs"]) > 10:
                    print(f"... and {len(summary['failed_jobs']) - 10} more")
        else:
            # Friendly summary
            status_icon = {"success": "✅", "failed": "❌", "running": "🔄"}.get(
                summary["pipeline_status"], "⏸"
            )

            print(
                f"\nPipeline {pipeline_id}: {status_icon} {summary['pipeline_status'].upper()}"
            )
            print(
                f"Created: {summary['created_at'][:16]} | Duration: {cli.explorer.format_duration(summary['duration'])}"
            )

            # Quick stats
            print(f"Jobs: {summary['total']} total | ", end="")
            if summary["failed"] > 0:
                print(f"❌ {summary['failed']} failed | ", end="")
            if summary["success"] > 0:
                print(f"✅ {summary['success']} success | ", end="")
            if summary["running"] > 0:
                print(f"🔄 {summary['running']} running | ", end="")
            if summary["skipped"] > 0:
                print(f"⏭ {summary['skipped']} skipped", end="")
            print()

            # Show failed jobs if any
            if summary["failed_jobs"]:
                print("\nFailed Jobs:")
                for job in summary["failed_jobs"][:5]:
                    print(f"  ❌ {job['id']} - {job['name']} ({job['stage']})")
                if len(summary["failed_jobs"]) > 5:
                    print(f"  ... and {len(summary['failed_jobs']) - 5} more")
                print("\n💡 Use --failed to see all failed jobs")

    def handle_jobs(self, cli, ids, args, output_format):
        """Handle job commands - show summaries by default"""
        all_jobs = []

        for job_id in ids:
            try:
                job = cli.explorer.project.jobs.get(job_id)

                if output_format == "json":
                    job_data = {
                        "id": job.id,
                        "name": job.name,
                        "status": job.status,
                        "stage": job.stage,
                        "duration": job.duration,
                        "created_at": job.created_at,
                        "started_at": job.started_at,
                        "finished_at": job.finished_at,
                        "web_url": job.web_url,
                    }

                    if args.failures and job.status == "failed":
                        # Get failure details
                        details = cli.explorer.get_failed_job_details(job_id)
                        job_data["failures"] = details.get("failures", {})

                    all_jobs.append(job_data)
                elif output_format == "table":
                    # Collect for table display
                    all_jobs.append(
                        {
                            "id": job.id,
                            "name": job.name,
                            "status": job.status,
                            "stage": job.stage,
                            "duration": cli.explorer.format_duration(job.duration),
                        }
                    )
                else:
                    # Friendly summary
                    # Check if job is allowed to fail and has failed
                    is_allowed_failure = (
                        getattr(job, "allow_failure", False) and job.status == "failed"
                    )

                    if is_allowed_failure:
                        status_icon = "⚠️"
                        status_display = f"{job.status} (allowed)"
                    else:
                        status_icon = {
                            "success": "✅",
                            "failed": "❌",
                            "running": "🔄",
                            "skipped": "⏭",
                        }.get(job.status, "⏸")
                        status_display = job.status

                    print(f"\nJob {job.id}: {job.name}")
                    print(
                        f"Status: {status_icon} {status_display} | Stage: {job.stage} | Duration: {cli.explorer.format_duration(job.duration)}"
                    )

                    if args.failures and job.status == "failed":
                        details = cli.explorer.get_failed_job_details(job_id)
                        failures = details.get("failures", {})
                        if failures.get("short_summary"):
                            print("\nFailure Summary:")
                            for line in failures["short_summary"].split("\n")[:5]:
                                if "FAILED" in line:
                                    print(f"  • {line.strip()}")

                    if len(ids) > 1:
                        print("-" * 60)

            except Exception as e:
                if output_format == "json":
                    all_jobs.append({"id": job_id, "error": str(e)})
                else:
                    print(f"Error fetching job {job_id}: {e}")

        if output_format == "json":
            print(json.dumps({"jobs": all_jobs}, indent=2))
        elif output_format == "table" and all_jobs:
            # Display jobs in table format
            print("\nJobs Summary")
            print("-" * 100)
            print(
                f"{'ID':<12} {'Status':<10} {'Stage':<15} {'Duration':<10} {'Name':<50}"
            )
            print("-" * 100)
            for job_info in all_jobs:
                name = (
                    job_info["name"][:47] + "..."
                    if len(job_info["name"]) > 50
                    else job_info["name"]
                )
                status_display = job_info["status"].upper()[:10]
                print(
                    f"{job_info['id']:<12} {status_display:<10} {job_info['stage']:<15} {job_info['duration']:<10} {name:<50}"
                )
            print("-" * 100)

    def handle_pipeline_detail(self, cli, pipeline_id, args, output_format):
        """Handle pipeline detail subcommand - show comprehensive pipeline information"""
        try:
            # Get pipeline details
            pipeline = cli.explorer.project.pipelines.get(pipeline_id)

            # Get job summary
            summary = cli.explorer.get_job_status_summary(
                pipeline_id, verbose=cli.verbose
            )

            if output_format == "json":
                # Comprehensive JSON output
                output = {
                    "id": pipeline.id,
                    "iid": pipeline.iid if hasattr(pipeline, "iid") else None,
                    "status": pipeline.status,
                    "ref": pipeline.ref,
                    "sha": pipeline.sha,
                    "source": pipeline.source,
                    "created_at": pipeline.created_at,
                    "updated_at": pipeline.updated_at,
                    "started_at": pipeline.started_at,
                    "finished_at": pipeline.finished_at,
                    "duration": pipeline.duration,
                    "queued_duration": (
                        pipeline.queued_duration
                        if hasattr(pipeline, "queued_duration")
                        else None
                    ),
                    "coverage": (
                        pipeline.coverage if hasattr(pipeline, "coverage") else None
                    ),
                    "web_url": pipeline.web_url,
                    "user": (
                        {
                            "username": pipeline.user["username"],
                            "name": pipeline.user["name"],
                        }
                        if hasattr(pipeline, "user") and pipeline.user
                        else None
                    ),
                    "commit": {
                        "message": (
                            pipeline.commit["message"]
                            if hasattr(pipeline, "commit")
                            else None
                        ),
                        "author": (
                            pipeline.commit.get("author_name")
                            if hasattr(pipeline, "commit")
                            else None
                        ),
                    },
                    "job_statistics": {
                        "total": summary["total"],
                        "failed": summary["failed"],
                        "success": summary["success"],
                        "running": summary["running"],
                        "skipped": summary["skipped"],
                        "pending": summary["pending"],
                    },
                    "stages": summary["stages"],
                }
                print(json.dumps(output, indent=2))
            elif output_format == "table":
                # Table format for pipeline details
                print(f"\nPipeline #{pipeline.id} Details")
                print("=" * 80)
                print(f"{'Field':<20} {'Value':<60}")
                print("-" * 80)
                print(f"{'Status':<20} {pipeline.status.upper()}")
                print(f"{'Source':<20} {pipeline.source}")
                print(f"{'Branch/Tag':<20} {pipeline.ref}")
                print(f"{'SHA':<20} {pipeline.sha[:8]}")
                if hasattr(pipeline, "user") and pipeline.user:
                    print(
                        f"{'Started by':<20} {pipeline.user['name']} (@{pipeline.user['username']})"
                    )
                print(f"{'Created':<20} {pipeline.created_at}")
                print(f"{'Started':<20} {pipeline.started_at or 'Not started'}")
                print(f"{'Finished':<20} {pipeline.finished_at or 'Still running'}")
                print(
                    f"{'Duration':<20} {cli.explorer.format_duration(pipeline.duration)}"
                )
                if hasattr(pipeline, "queued_duration") and pipeline.queued_duration:
                    print(
                        f"{'Queued':<20} {cli.explorer.format_duration(pipeline.queued_duration)}"
                    )
                print("-" * 80)
                print(f"\nJob Statistics:")
                print("-" * 40)
                print(f"{'Status':<15} {'Count':>10}")
                print("-" * 40)
                print(f"{'Total':<15} {summary['total']:>10}")
                if summary["success"] > 0:
                    print(f"{'Success':<15} {summary['success']:>10}")
                if summary["failed"] > 0:
                    print(f"{'Failed':<15} {summary['failed']:>10}")
                if summary["running"] > 0:
                    print(f"{'Running':<15} {summary['running']:>10}")
                if summary["skipped"] > 0:
                    print(f"{'Skipped':<15} {summary['skipped']:>10}")
                if summary["pending"] > 0:
                    print(f"{'Pending':<15} {summary['pending']:>10}")
                print("-" * 40)
                print(f"\nURL: {pipeline.web_url}")
            else:
                # Friendly detailed output
                status_icon = {
                    "success": "✅",
                    "failed": "❌",
                    "running": "🔄",
                    "canceled": "⏹",
                    "skipped": "⏭",
                }.get(pipeline.status, "⏸")

                print(f"\n{'='*60}")
                print(f"Pipeline #{pipeline.id}")
                print(f"{'='*60}\n")

                print(f"Status:       {status_icon} {pipeline.status.upper()}")
                print(f"Source:       {pipeline.source}")
                print(f"Branch/Tag:   {pipeline.ref}")

                if hasattr(pipeline, "user") and pipeline.user:
                    print(
                        f"Started by:   {pipeline.user['name']} (@{pipeline.user['username']})"
                    )

                print(f"\nTiming:")
                print(f"  Created:    {pipeline.created_at}")
                print(f"  Started:    {pipeline.started_at or 'Not started'}")
                print(f"  Finished:   {pipeline.finished_at or 'Still running'}")
                print(
                    f"  Duration:   {cli.explorer.format_duration(pipeline.duration)}"
                )
                if hasattr(pipeline, "queued_duration") and pipeline.queued_duration:
                    print(
                        f"  Queued:     {cli.explorer.format_duration(pipeline.queued_duration)}"
                    )

                print(f"\nCommit:")
                print(f"  SHA:        {pipeline.sha[:8]}")
                if hasattr(pipeline, "commit") and pipeline.commit:
                    commit_msg = pipeline.commit["message"].split("\\n")[0][:60]
                    print(f"  Message:    {commit_msg}")
                    if "author_name" in pipeline.commit:
                        print(f"  Author:     {pipeline.commit['author_name']}")

                print(f"\nJob Statistics:")
                print(f"  Total:      {summary['total']} jobs")
                if summary["failed"] > 0:
                    print(f"  Failed:     ❌ {summary['failed']}")
                if summary["success"] > 0:
                    print(f"  Success:    ✅ {summary['success']}")
                if summary["running"] > 0:
                    print(f"  Running:    🔄 {summary['running']}")
                if summary["skipped"] > 0:
                    print(f"  Skipped:    ⏭ {summary['skipped']}")
                if summary["pending"] > 0:
                    print(f"  Pending:    ⏸ {summary['pending']}")

                # Show stage breakdown
                if summary["stages"]:
                    print(f"\nStages:")
                    for stage_name, stage_info in summary["stages"].items():
                        stage_icon = {
                            "success": "✅",
                            "failed": "❌",
                            "running": "🔄",
                            "skipped": "⏭",
                        }.get(stage_info["status"], "⏸")
                        print(
                            f"  {stage_icon} {stage_name}: {stage_info['count']} jobs"
                        )
                        if stage_info["failed_jobs"]:
                            for job in stage_info["failed_jobs"][:3]:
                                print(f"      ❌ {job['id']} - {job['name']}")

                print(f"\nPipeline URL: {pipeline.web_url}")

        except Exception as e:
            print(f"Error fetching pipeline {pipeline_id} details: {e}")

    def handle_pipeline_retry(self, cli, pipeline_id, args, output_format):
        """Handle pipeline retry - retry failed jobs in pipeline"""
        try:
            pipeline = cli.explorer.project.pipelines.get(pipeline_id)
            
            # Retry the pipeline
            result = pipeline.retry()
            
            if output_format == "json":
                print(json.dumps({
                    "action": "retry",
                    "pipeline_id": pipeline_id,
                    "status": "success",
                    "new_pipeline": {
                        "id": result.id if hasattr(result, 'id') else pipeline_id,
                        "status": result.status if hasattr(result, 'status') else "pending"
                    }
                }, indent=2))
            else:
                print(f"✅ Pipeline #{pipeline_id} retry initiated")
                if hasattr(result, 'id'):
                    print(f"New pipeline: #{result.id}")
                print(f"Status: {result.status if hasattr(result, 'status') else 'pending'}")
                
        except Exception as e:
            if output_format == "json":
                print(json.dumps({
                    "action": "retry",
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "error": str(e)
                }, indent=2))
            else:
                print(f"❌ Error retrying pipeline {pipeline_id}: {e}")
            sys.exit(1)

    def handle_pipeline_cancel(self, cli, pipeline_id, args, output_format):
        """Handle pipeline cancel - cancel a running pipeline"""
        try:
            pipeline = cli.explorer.project.pipelines.get(pipeline_id)
            
            # Check if pipeline is in a cancellable state
            if pipeline.status in ["success", "failed", "canceled", "skipped"]:
                if output_format == "json":
                    print(json.dumps({
                        "action": "cancel",
                        "pipeline_id": pipeline_id,
                        "status": "error",
                        "error": f"Pipeline is already {pipeline.status}"
                    }, indent=2))
                else:
                    print(f"⚠️  Pipeline #{pipeline_id} is already {pipeline.status}")
                return
            
            # Cancel the pipeline
            result = pipeline.cancel()
            
            if output_format == "json":
                print(json.dumps({
                    "action": "cancel",
                    "pipeline_id": pipeline_id,
                    "status": "success",
                    "pipeline_status": result.status if hasattr(result, 'status') else "canceled"
                }, indent=2))
            else:
                print(f"✅ Pipeline #{pipeline_id} canceled")
                print(f"Status: {result.status if hasattr(result, 'status') else 'canceled'}")
                
        except Exception as e:
            if output_format == "json":
                print(json.dumps({
                    "action": "cancel",
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "error": str(e)
                }, indent=2))
            else:
                print(f"❌ Error canceling pipeline {pipeline_id}: {e}")
            sys.exit(1)

    def handle_job_detail(self, cli, job_id, args, output_format):
        """Handle job detail subcommand - show comprehensive job information"""
        try:
            # Get job details
            job = cli.explorer.project.jobs.get(job_id)

            if output_format == "json":
                # Comprehensive JSON output
                output = {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "stage": job.stage,
                    "ref": job.ref,
                    "tag": job.tag,
                    "created_at": job.created_at,
                    "started_at": job.started_at,
                    "finished_at": job.finished_at,
                    "duration": job.duration,
                    "queued_duration": getattr(job, "queued_duration", None),
                    "coverage": getattr(job, "coverage", None),
                    "allow_failure": job.allow_failure,
                    "web_url": job.web_url,
                    "artifacts": getattr(job, "artifacts", None),
                    "artifacts_expire_at": getattr(job, "artifacts_expire_at", None),
                }

                # Add runner info if available
                runner_info = getattr(job, "runner", None)
                if runner_info:
                    # Check if it's a method or property
                    if callable(runner_info):
                        runner_info = runner_info()
                    if runner_info and isinstance(runner_info, dict):
                        output["runner"] = {
                            "id": runner_info.get("id"),
                            "description": runner_info.get("description"),
                            "active": runner_info.get("active"),
                            "is_shared": runner_info.get("is_shared"),
                        }
                    else:
                        output["runner"] = None
                else:
                    output["runner"] = None

                # Add pipeline info if available
                pipeline_info = getattr(job, "pipeline", None)
                if pipeline_info and isinstance(pipeline_info, dict):
                    output["pipeline"] = {
                        "id": pipeline_info.get("id"),
                        "status": pipeline_info.get("status"),
                        "ref": pipeline_info.get("ref"),
                        "sha": pipeline_info.get("sha"),
                    }
                else:
                    output["pipeline"] = None

                # Add user info if available
                user_info = getattr(job, "user", None)
                if user_info and isinstance(user_info, dict):
                    output["user"] = {
                        "username": user_info.get("username"),
                        "name": user_info.get("name"),
                    }
                else:
                    output["user"] = None

                # Add failure details if failed
                if job.status == "failed":
                    details = cli.explorer.get_failed_job_details(job_id)
                    output["failure_reason"] = (
                        job.failure_reason if hasattr(job, "failure_reason") else None
                    )
                    output["failures"] = details.get("failures", {})

                print(json.dumps(output, indent=2))
            else:
                # Friendly detailed output
                # Check if job is allowed to fail and has failed
                is_allowed_failure = job.allow_failure and job.status == "failed"

                if is_allowed_failure:
                    status_icon = "⚠️"
                    status_display = f"{job.status.upper()} (ALLOWED TO FAIL)"
                else:
                    status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "canceled": "⏹",
                        "skipped": "⏭",
                        "manual": "👆",
                    }.get(job.status, "⏸")
                    status_display = job.status.upper()

                print(f"\n{'='*60}")
                print(f"{job.name}")
                print(f"{'='*60}\n")

                print(f"Status:       {status_icon} {status_display}")
                if job.status == "failed" and hasattr(job, "failure_reason"):
                    print(f"Failure:      {job.failure_reason}")

                print(f"Stage:        {job.stage}")
                print(f"Job ID:       {job.id}")

                if hasattr(job, "user") and job.user:
                    print(f"Started by:   {job.user['name']} (@{job.user['username']})")

                print(f"\nTiming:")
                print(f"  Created:    {job.created_at}")
                print(f"  Started:    {job.started_at or 'Not started'}")
                print(f"  Finished:   {job.finished_at or 'Still running'}")
                print(f"  Duration:   {cli.explorer.format_duration(job.duration)}")
                if hasattr(job, "queued_duration") and job.queued_duration:
                    print(
                        f"  Queued:     {cli.explorer.format_duration(job.queued_duration)}"
                    )

                if hasattr(job, "coverage") and job.coverage:
                    print(f"\nCoverage:     {job.coverage}%")

                runner_info = getattr(job, "runner", None)
                if runner_info:
                    if callable(runner_info):
                        runner_info = runner_info()
                    if runner_info and isinstance(runner_info, dict):
                        print(f"\nRunner:")
                        print(f"  ID:         #{runner_info.get('id', 'N/A')}")
                        print(f"  Name:       {runner_info.get('description', 'N/A')}")
                        print(
                            f"  Type:       {'Shared' if runner_info.get('is_shared') else 'Specific'}"
                        )

                print(f"\nSource:")
                print(f"  Branch/Tag: {job.ref}")
                print(
                    f"  Commit:     {job.commit['short_id'] if hasattr(job, 'commit') else 'N/A'}"
                )

                if hasattr(job, "pipeline"):
                    p_status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                    }.get(job.pipeline["status"], "⏸")
                    print(f"\nPipeline:")
                    print(f"  ID:         #{job.pipeline['id']}")
                    print(f"  Status:     {p_status_icon} {job.pipeline['status']}")

                artifacts_info = getattr(job, "artifacts", None)
                if artifacts_info:
                    if callable(artifacts_info):
                        try:
                            artifacts_info = artifacts_info()
                        except:
                            artifacts_info = None

                    if artifacts_info and isinstance(artifacts_info, (list, tuple)):
                        print(f"\nArtifacts:")
                        for artifact in artifacts_info:
                            if isinstance(artifact, dict):
                                print(
                                    f"  • {artifact.get('filename', 'Unknown')} ({artifact.get('size', 0)} bytes)"
                                )
                            else:
                                print(f"  • {str(artifact)}")

                        expire_at = getattr(job, "artifacts_expire_at", None)
                        if expire_at:
                            print(f"  Expires:    {expire_at}")

                # Show failure details if failed
                if job.status == "failed":
                    details = cli.explorer.get_failed_job_details(job_id)
                    failures = details.get("failures", {})
                    if failures.get("short_summary"):
                        print(f"\nFailure Details:")
                        for line in failures["short_summary"].split("\n")[:10]:
                            if line.strip():
                                print(f"  {line.strip()}")

                print(f"\nJob URL: {job.web_url}")

        except Exception as e:
            print(f"Error fetching job {job_id} details: {e}")

    def handle_job_logs(self, cli, job_id, args, output_format):
        """Handle job logs subcommand - show full job trace/logs"""
        try:
            # Get job and its trace
            job = cli.explorer.project.jobs.get(job_id)
            trace = job.trace()

            if isinstance(trace, bytes):
                trace = trace.decode("utf-8", errors="replace")

            if output_format == "json":
                # JSON output
                output = {
                    "job_id": job_id,
                    "name": job.name,
                    "status": job.status,
                    "trace": trace,
                }

                # Also include smart failure extraction
                if job.status == "failed":
                    failures = cli.explorer.extract_failures_from_trace(trace, job.name)
                    output["extracted_failures"] = failures

                print(json.dumps(output, indent=2))
            else:
                # Friendly output - show the trace with some context
                print(f"\n{'='*60}")
                print(f"Job Logs: {job.name} (#{job_id})")
                print(f"Status: {job.status.upper()}")
                print(f"{'='*60}\n")

                # For failed jobs, first show extracted failures
                if job.status == "failed":
                    failures = cli.explorer.extract_failures_from_trace(trace, job.name)

                    if failures.get("short_summary"):
                        print("📋 Extracted Failures:")
                        print("-" * 40)
                        print(failures["short_summary"])
                        print("-" * 40)
                        print()

                        # Ask if they want to see full logs
                        print("Full job trace follows...\n")
                        print("=" * 60)

                # Print the full trace
                print(trace)

                print(f"\n{'='*60}")
                print(f"End of logs for job #{job_id}")

        except Exception as e:
            print(f"Error fetching job {job_id} logs: {e}")

    def handle_job_retry(self, cli, job_id, args, output_format):
        """Handle job retry - retry a failed job"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            
            # Check if job can be retried
            if job.status not in ["failed", "canceled"]:
                if output_format == "json":
                    print(json.dumps({
                        "action": "retry",
                        "job_id": job_id,
                        "status": "error",
                        "error": f"Job is {job.status}, only failed or canceled jobs can be retried"
                    }, indent=2))
                else:
                    print(f"⚠️  Job #{job_id} is {job.status}, only failed or canceled jobs can be retried")
                return
            
            # Retry the job
            result = job.retry()
            
            if output_format == "json":
                print(json.dumps({
                    "action": "retry",
                    "job_id": job_id,
                    "status": "success",
                    "new_job": {
                        "id": result.id if hasattr(result, 'id') else job_id,
                        "status": result.status if hasattr(result, 'status') else "pending"
                    }
                }, indent=2))
            else:
                print(f"✅ Job #{job_id} retry initiated")
                if hasattr(result, 'id') and result.id != job_id:
                    print(f"New job: #{result.id}")
                print(f"Status: {result.status if hasattr(result, 'status') else 'pending'}")
                
        except Exception as e:
            if output_format == "json":
                print(json.dumps({
                    "action": "retry",
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                }, indent=2))
            else:
                print(f"❌ Error retrying job {job_id}: {e}")
            sys.exit(1)

    def handle_job_play(self, cli, job_id, args, output_format):
        """Handle job play - play/trigger a manual job"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            
            # Check if job is manual
            if not hasattr(job, 'status') or job.status != "manual":
                if output_format == "json":
                    print(json.dumps({
                        "action": "play",
                        "job_id": job_id,
                        "status": "error",
                        "error": f"Job is {job.status if hasattr(job, 'status') else 'unknown'}, only manual jobs can be played"
                    }, indent=2))
                else:
                    print(f"⚠️  Job #{job_id} is {job.status if hasattr(job, 'status') else 'unknown'}, only manual jobs can be played")
                return
            
            # Play the job
            result = job.play()
            
            if output_format == "json":
                print(json.dumps({
                    "action": "play",
                    "job_id": job_id,
                    "status": "success",
                    "job_status": result.status if hasattr(result, 'status') else "pending"
                }, indent=2))
            else:
                print(f"✅ Job #{job_id} triggered")
                print(f"Status: {result.status if hasattr(result, 'status') else 'pending'}")
                
        except Exception as e:
            if output_format == "json":
                print(json.dumps({
                    "action": "play",
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                }, indent=2))
            else:
                print(f"❌ Error playing job {job_id}: {e}")
            sys.exit(1)

    def handle_mr_detail(self, cli, mr_id, args, output_format):
        """Handle MR detail subcommand - show comprehensive MR information"""
        try:
            # Get MR details
            mr = cli.explorer.project.mergerequests.get(mr_id)

            if output_format == "json":
                # Comprehensive JSON output
                output = {
                    "id": mr.id,
                    "iid": mr.iid,
                    "title": mr.title,
                    "description": mr.description,
                    "state": mr.state,
                    "created_at": mr.created_at,
                    "updated_at": mr.updated_at,
                    "merged_at": mr.merged_at if hasattr(mr, "merged_at") else None,
                    "closed_at": mr.closed_at if hasattr(mr, "closed_at") else None,
                    "source_branch": mr.source_branch,
                    "target_branch": mr.target_branch,
                    "author": {
                        "username": mr.author["username"],
                        "name": mr.author["name"],
                    },
                    "assignee": mr.assignee if hasattr(mr, "assignee") else None,
                    "assignees": mr.assignees if hasattr(mr, "assignees") else [],
                    "reviewers": mr.reviewers if hasattr(mr, "reviewers") else [],
                    "merge_user": mr.merge_user if hasattr(mr, "merge_user") else None,
                    "merge_status": (
                        mr.merge_status if hasattr(mr, "merge_status") else None
                    ),
                    "draft": mr.draft if hasattr(mr, "draft") else False,
                    "work_in_progress": (
                        mr.work_in_progress
                        if hasattr(mr, "work_in_progress")
                        else False
                    ),
                    "merge_when_pipeline_succeeds": (
                        mr.merge_when_pipeline_succeeds
                        if hasattr(mr, "merge_when_pipeline_succeeds")
                        else False
                    ),
                    "has_conflicts": (
                        mr.has_conflicts if hasattr(mr, "has_conflicts") else False
                    ),
                    "blocking_discussions_resolved": (
                        mr.blocking_discussions_resolved
                        if hasattr(mr, "blocking_discussions_resolved")
                        else True
                    ),
                    "approvals_before_merge": (
                        mr.approvals_before_merge
                        if hasattr(mr, "approvals_before_merge")
                        else None
                    ),
                    "reference": mr.reference,
                    "web_url": mr.web_url,
                    "labels": mr.labels,
                    "milestone": mr.milestone if hasattr(mr, "milestone") else None,
                    "head_pipeline": (
                        mr.head_pipeline if hasattr(mr, "head_pipeline") else None
                    ),
                    "diff_stats": {
                        "additions": mr.additions if hasattr(mr, "additions") else 0,
                        "deletions": mr.deletions if hasattr(mr, "deletions") else 0,
                        "total": (mr.additions if hasattr(mr, "additions") else 0)
                        + (mr.deletions if hasattr(mr, "deletions") else 0),
                    },
                }

                # Get recent pipelines
                pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
                if pipelines:
                    output["recent_pipelines"] = pipelines

                print(json.dumps(output, indent=2))
            else:
                # Friendly detailed output
                status_color = {
                    "opened": "\033[92m",  # Green
                    "merged": "\033[94m",  # Blue
                    "closed": "\033[91m",  # Red
                }.get(mr.state, "")

                print(f"\n{'='*60}")
                print(f"MR !{mr.iid}: {mr.title}")
                print(f"{'='*60}\n")

                print(f"Status:       {status_color}{mr.state.upper()}\033[0m")
                if hasattr(mr, "draft") and mr.draft:
                    print(f"              📝 DRAFT")

                print(f"Author:       {mr.author['name']} (@{mr.author['username']})")

                if hasattr(mr, "assignees") and mr.assignees:
                    assignee_names = [f"@{a['username']}" for a in mr.assignees]
                    print(f"Assignees:    {', '.join(assignee_names)}")

                if hasattr(mr, "reviewers") and mr.reviewers:
                    reviewer_names = [f"@{r['username']}" for r in mr.reviewers]
                    print(f"Reviewers:    {', '.join(reviewer_names)}")

                print(f"\nBranches:")
                print(f"  Source:     {mr.source_branch}")
                print(f"  Target:     {mr.target_branch}")

                print(f"\nTiming:")
                print(f"  Created:    {mr.created_at}")
                print(f"  Updated:    {mr.updated_at}")
                if hasattr(mr, "merged_at") and mr.merged_at:
                    print(f"  Merged:     {mr.merged_at}")
                    if hasattr(mr, "merge_user") and mr.merge_user:
                        print(f"  Merged by:  @{mr.merge_user['username']}")
                elif hasattr(mr, "closed_at") and mr.closed_at:
                    print(f"  Closed:     {mr.closed_at}")

                # Merge status
                if mr.state == "opened":
                    print(f"\nMerge Status:")
                    if hasattr(mr, "has_conflicts") and mr.has_conflicts:
                        print(f"  ❌ Has conflicts")
                    if hasattr(mr, "work_in_progress") and mr.work_in_progress:
                        print(f"  📝 Work in progress")
                    if (
                        hasattr(mr, "merge_when_pipeline_succeeds")
                        and mr.merge_when_pipeline_succeeds
                    ):
                        print(f"  🔄 Set to merge when pipeline succeeds")
                    if hasattr(mr, "blocking_discussions_resolved"):
                        if mr.blocking_discussions_resolved:
                            print(f"  ✅ All discussions resolved")
                        else:
                            print(f"  💬 Unresolved discussions")

                # Diff stats
                if hasattr(mr, "additions") or hasattr(mr, "deletions"):
                    additions = mr.additions if hasattr(mr, "additions") else 0
                    deletions = mr.deletions if hasattr(mr, "deletions") else 0
                    print(f"\nChanges:")
                    print(f"  Additions:  +{additions}")
                    print(f"  Deletions:  -{deletions}")
                    print(f"  Total:      {additions + deletions} lines")

                # Pipeline status
                if hasattr(mr, "head_pipeline") and mr.head_pipeline:
                    p_status = mr.head_pipeline.get("status", "unknown")
                    p_color = {
                        "success": "\033[92m✅",
                        "failed": "\033[91m❌",
                        "running": "\033[93m🔄",
                    }.get(p_status, "⏸")
                    print(f"\nCurrent Pipeline:")
                    print(
                        f"  {p_color} {p_status}\033[0m (ID: {mr.head_pipeline.get('id')})"
                    )
                    print(f"  SHA: {mr.head_pipeline.get('sha', '')[:8]}")

                # Recent pipelines
                pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
                if pipelines:
                    print(f"\nRecent Pipelines:")
                    for p in pipelines:
                        status_icon = {
                            "success": "✅",
                            "failed": "❌",
                            "running": "🔄",
                        }.get(p["status"], "⏸")
                        print(
                            f"  {status_icon} {p['id']} - {p['status']} ({p['created_at'][:16]})"
                        )

                # Labels
                if mr.labels:
                    print(f"\nLabels: {', '.join(mr.labels)}")

                # Milestone
                if hasattr(mr, "milestone") and mr.milestone:
                    print(f"Milestone: {mr.milestone['title']}")

                # Description preview
                if mr.description:
                    print(f"\nDescription (preview):")
                    desc_lines = mr.description.split("\n")[:5]
                    for line in desc_lines:
                        print(f"  {line[:80]}")
                    if len(mr.description.split("\n")) > 5:
                        print(f"  ... (truncated)")

                print(f"\nMR URL: {mr.web_url}")

        except Exception as e:
            print(f"Error fetching MR {mr_id} details: {e}")

    def handle_config(self, args):
        """Handle configuration commands"""
        if not hasattr(args, "action") or not args.action:
            # Default to show
            args.action = "show"

        if args.action == "show":
            print(f"GitLab URL:     {self.config.gitlab_url or 'Not set'}")
            print(
                f"Project:        {self.config.project_path or 'Not set (auto-detected)'}"
            )
            print(f"Token:          {'Set' if self.config.gitlab_token else 'Not set'}")
            print(f"Default format: {self.config.default_format}")
            print(f"Cache dir:      {self.config.cache_dir}")

        elif args.action == "set":
            update = {}
            if hasattr(args, "gitlab_url") and args.gitlab_url:
                update["gitlab_url"] = args.gitlab_url
            if hasattr(args, "project") and args.project:
                update["project_path"] = args.project
            if hasattr(args, "default_format") and args.default_format:
                update["default_format"] = args.default_format

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

