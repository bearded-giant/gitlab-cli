"""Pipeline command handlers for GitLab CLI"""

import sys
import json
from collections import defaultdict
from .base import BaseCommand


class PipelineCommands(BaseCommand):
    """Handles all pipeline-related commands"""

    def add_list_arguments(self, parser):
        """Add arguments for pipeline listing/filtering"""
        parser.add_argument(
            "--since",
            help="Show pipelines since (e.g., '2d', '3h', '1w', '2 days ago', '2024-01-15')"
        )
        parser.add_argument(
            "--before", 
            help="Show pipelines before (e.g., '1d', '2h', '1 week ago', '2024-01-20')"
        )
        parser.add_argument(
            "--status",
            choices=["success", "failed", "running", "pending", "canceled", "skipped"],
            help="Filter by pipeline status"
        )
        parser.add_argument(
            "--ref",
            help="Filter by ref/branch name"
        )
        parser.add_argument(
            "--user",
            help="Filter by username who triggered the pipeline"
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
    
    def handle_pipelines(self, cli, ids, args, output_format):
        """Handle pipeline commands - show summaries by default"""
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
                self.search_pipeline_jobs(
                    cli, pipeline_id, args.job_search, output_format
                )
            elif args.jobs or status_filter:
                args.pipeline_id = pipeline_id
                args.status = status_filter
                args.format = output_format
                cli.cmd_pipeline_jobs(args)
            else:
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
                print(
                    f"\nJobs matching '{search_pattern}' in Pipeline {pipeline_id}:"
                )
                print("-" * 60)

                for job in matching_jobs:
                    # Check if job is allowed to fail and has failed
                    is_allowed_failure = (
                        getattr(job, "allow_failure", False) and job.status == "failed"
                    )

                    if is_allowed_failure:
                        status_icon = "⚠️"
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
        # Show cache location if verbose
        if cli.verbose:
            from pathlib import Path
            cache_path = Path(cli.explorer.db_file)
            print(f"\n📁 Cache location: {cache_path}")
            print(f"   Cache exists: {cache_path.exists()}")
            if cache_path.exists():
                print(f"   Cache size: {cache_path.stat().st_size:,} bytes")
        
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

    def handle_pipeline_detail(self, cli, pipeline_id, args, output_format):
        """Handle pipeline detail subcommand - show comprehensive pipeline information"""
        try:
            # Get pipeline details
            pipeline = cli.explorer.project.pipelines.get(pipeline_id)
            
            # Get pipeline variables if requested
            pipeline_variables = None
            if getattr(args, 'show_variables', False):
                try:
                    pipeline_variables = pipeline.variables.list(all=True)
                except Exception as e:
                    # Some pipelines might not have variables accessible
                    if cli.verbose:
                        print(f"Warning: Could not fetch variables: {e}")

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
                
                # Add variables if fetched
                if pipeline_variables is not None:
                    output["variables"] = [
                        {
                            "key": var.key,
                            "value": var.value,
                            "variable_type": getattr(var, "variable_type", "env_var")
                        }
                        for var in pipeline_variables
                    ]
                
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

                # Show variables if requested
                if pipeline_variables is not None and len(pipeline_variables) > 0:
                    print(f"\n{'='*60}")
                    print("Pipeline Variables:")
                    print(f"{'='*60}")
                    
                    # Group variables by type
                    env_vars = []
                    file_vars = []
                    
                    for var in pipeline_variables:
                        var_type = getattr(var, "variable_type", "env_var")
                        if var_type == "file":
                            file_vars.append(var)
                        else:
                            env_vars.append(var)
                    
                    if env_vars:
                        print("\nEnvironment Variables:")
                        for var in env_vars:
                            # Mask sensitive values (show first and last 2 chars if long enough)
                            value = var.value
                            if len(value) > 10:
                                masked_value = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
                            elif len(value) > 4:
                                masked_value = f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
                            else:
                                masked_value = "*" * len(value)
                            
                            print(f"  {var.key}: {masked_value}")
                    
                    if file_vars:
                        print("\nFile Variables:")
                        for var in file_vars:
                            print(f"  {var.key}: [File content, {len(var.value)} bytes]")
                    
                    print(f"\nTotal variables: {len(pipeline_variables)}")
                elif getattr(args, 'show_variables', False):
                    print("\nNo pipeline variables found or accessible.")
                
                print(f"\nPIPELINE_URL: {pipeline.web_url}")
                print(f"PIPELINE_ID: {pipeline.id}")

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

    def handle_pipeline_rerun(self, cli, pipeline_id, args, output_format):
        """Handle pipeline rerun - create a new pipeline for the same commit"""
        try:
            # Get the original pipeline details
            original_pipeline = cli.explorer.project.pipelines.get(pipeline_id)
            
            # Create a new pipeline for the same ref/commit
            new_pipeline = cli.explorer.project.pipelines.create({
                'ref': original_pipeline.ref,
                'variables': []  # You can add variables if needed
            })
            
            if output_format == "json":
                print(json.dumps({
                    "action": "rerun",
                    "original_pipeline_id": pipeline_id,
                    "new_pipeline_id": new_pipeline.id,
                    "status": "success",
                    "ref": new_pipeline.ref,
                    "sha": new_pipeline.sha,
                    "web_url": new_pipeline.web_url
                }, indent=2))
            else:
                print(f"✅ New pipeline created for same commit")
                print(f"Original pipeline: #{pipeline_id}")
                print(f"New pipeline: #{new_pipeline.id}")
                print(f"Ref: {new_pipeline.ref}")
                print(f"SHA: {new_pipeline.sha[:8]}")
                print(f"Status: {new_pipeline.status}")
                print(f"URL: {new_pipeline.web_url}")
                
        except Exception as e:
            if output_format == "json":
                print(json.dumps({
                    "action": "rerun",
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "error": str(e)
                }, indent=2))
            else:
                print(f"❌ Error creating new pipeline for #{pipeline_id}: {e}")
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
    
    def handle_pipeline_graph(self, cli, pipeline_id, args, output_format):
        """Display pipeline graph visualization"""
        try:
            pipeline = cli.explorer.project.pipelines.get(pipeline_id)
            jobs = pipeline.jobs.list(all=True)
            
            # Organize jobs by stage
            stages = defaultdict(list)
            stage_order = []
            
            for job in jobs:
                if job.stage not in stage_order:
                    stage_order.append(job.stage)
                stages[job.stage].append(job)
            
            if output_format == "json":
                # JSON output with structured data
                graph_data = {
                    "pipeline_id": pipeline_id,
                    "status": pipeline.status,
                    "stages": []
                }
                for stage in stage_order:
                    stage_jobs = []
                    for job in stages[stage]:
                        stage_jobs.append({
                            "id": job.id,
                            "name": job.name,
                            "status": job.status,
                            "duration": job.duration,
                            "needs": getattr(job, 'needs', [])
                        })
                    graph_data["stages"].append({
                        "name": stage,
                        "jobs": stage_jobs
                    })
                print(json.dumps(graph_data, indent=2))
            else:
                # ASCII graph visualization
                print(f"\n{'='*80}")
                print(f"Pipeline #{pipeline_id} Graph")
                print(f"Status: {self._get_status_icon(pipeline.status)} {pipeline.status}")
                print(f"{'='*80}\n")
                
                # Display stage flow
                stage_line = " → ".join(stage_order)
                print(f"Stage Flow: {stage_line}\n")
                print("-" * 80)
                
                # Display jobs by stage with visual tree
                for i, stage in enumerate(stage_order):
                    stage_jobs = stages[stage]
                    print(f"\n📦 Stage: {stage}")
                    print("  " + "─" * (76 - len(stage)))
                    
                    # Sort jobs for better display
                    stage_jobs.sort(key=lambda x: x.name)
                    
                    for j, job in enumerate(stage_jobs):
                        is_last = (j == len(stage_jobs) - 1)
                        prefix = "  └─" if is_last else "  ├─"
                        
                        status_icon = self._get_status_icon(job.status)
                        duration_str = self.format_duration(job.duration) if job.duration else "N/A"
                        
                        # Check if it's a parallel job
                        is_parallel = "parallel" in job.name.lower()
                        parallel_marker = " [P]" if is_parallel else ""
                        
                        print(f"{prefix} {status_icon} {job.name}{parallel_marker}")
                        print(f"  {'  ' if not is_last else '  '}  Duration: {duration_str} | ID: {job.id}")
                        
                        # Show dependencies if any
                        if hasattr(job, 'needs') and job.needs:
                            needs_str = ", ".join([n['name'] if isinstance(n, dict) else str(n) for n in job.needs])
                            print(f"  {'  ' if not is_last else '  '}  Needs: {needs_str}")
                
                # Test duration graph for parallel jobs
                self._display_test_duration_graph(stages, stage_order)
                
                print(f"\n{'='*80}")
        
        except Exception as e:
            if output_format == "json":
                print(json.dumps({
                    "error": str(e),
                    "pipeline_id": pipeline_id
                }, indent=2))
            else:
                print(f"❌ Error generating pipeline graph: {e}")
            sys.exit(1)
    
    def _get_status_icon(self, status):
        """Get icon for job/pipeline status"""
        return {
            "success": "✅",
            "failed": "❌",
            "running": "🔄",
            "pending": "⏳",
            "canceled": "🚫",
            "skipped": "⏭",
            "manual": "🎮",
            "created": "🆕"
        }.get(status, "❓")
    
    def _display_test_duration_graph(self, stages, stage_order):
        """Display duration graph for parallel test jobs"""
        # Find parallel test jobs
        parallel_jobs = []
        
        for stage in stage_order:
            for job in stages[stage]:
                if "parallel" in job.name.lower() and job.duration:
                    # Extract parallel number if available
                    import re
                    match = re.search(r'(\d+)/(\d+)', job.name)
                    if match:
                        parallel_num = int(match.group(1))
                        parallel_total = int(match.group(2))
                    else:
                        parallel_num = 0
                        parallel_total = 0
                    
                    parallel_jobs.append({
                        'name': job.name,
                        'duration': job.duration,
                        'status': job.status,
                        'num': parallel_num,
                        'total': parallel_total
                    })
        
        if not parallel_jobs:
            return
        
        # Sort by parallel number
        parallel_jobs.sort(key=lambda x: x['num'])
        
        print(f"\n{'='*80}")
        print("Parallel Test Duration Graph")
        print(f"{'='*80}")
        
        # Find max duration for scaling
        max_duration = max(job['duration'] for job in parallel_jobs)
        max_bar_width = 50
        
        # Display histogram
        for job in parallel_jobs[:20]:  # Limit to first 20 for readability
            # Calculate bar width
            bar_width = int((job['duration'] / max_duration) * max_bar_width)
            bar = "█" * bar_width
            
            # Format job name (shorten if needed)
            if job['num'] > 0:
                job_label = f"Test {job['num']:3d}/{job['total']}"
            else:
                job_label = job['name'][:15]
            
            duration_str = self.format_duration(job['duration'])
            status_icon = self._get_status_icon(job['status'])
            
            print(f"{job_label:15} {status_icon} |{bar:<{max_bar_width}} {duration_str}")
        
        if len(parallel_jobs) > 20:
            print(f"\n... and {len(parallel_jobs) - 20} more parallel jobs")
        
        # Show statistics
        durations = [j['duration'] for j in parallel_jobs]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print(f"\nStatistics:")
        print(f"  Total parallel jobs: {len(parallel_jobs)}")
        print(f"  Average duration: {self.format_duration(avg_duration)}")
        print(f"  Min duration: {self.format_duration(min_duration)}")
        print(f"  Max duration: {self.format_duration(max_duration)}")