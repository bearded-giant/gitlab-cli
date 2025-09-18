"""Job command handlers for GitLab CLI"""

import sys
import json
import time
from .base import BaseCommand


class JobCommands(BaseCommand):
    """Handles all job-related commands"""

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
                        details = cli.explorer.get_failed_job_details(job_id)
                        job_data["failures"] = details.get("failures", {})

                    all_jobs.append(job_data)
                elif output_format == "table":
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
                    self._display_job_summary(cli, job, job_id, args, len(ids))

            except Exception as e:
                if output_format == "json":
                    all_jobs.append({"id": job_id, "error": str(e)})
                else:
                    print(f"Error fetching job {job_id}: {e}")

        if output_format == "json":
            self.output_json({"jobs": all_jobs})
        elif output_format == "table" and all_jobs:
            self._display_jobs_table(all_jobs)

    def handle_job_detail(self, cli, job_id, args, output_format):
        """Handle job detail subcommand - show comprehensive job information"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            dependencies = self._get_job_dependencies(cli, job)

            if output_format == "json":
                output = self._build_job_detail_json(cli, job, job_id)
                output["dependencies"] = dependencies
                self.output_json(output)
            else:
                self._display_job_detail_friendly(cli, job, job_id, dependencies)

        except Exception as e:
            self.output_error(f"Error fetching job {job_id}: {e}", output_format)

    def handle_job_logs(self, cli, job_id, args, output_format):
        """Handle job logs subcommand - show full job trace/logs"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            trace = job.trace()

            if isinstance(trace, bytes):
                trace = trace.decode("utf-8", errors="replace")

            if output_format == "json":
                output = {
                    "job_id": job_id,
                    "name": job.name,
                    "status": job.status,
                    "trace": trace,
                }

                if job.status == "failed":
                    failures = cli.explorer.extract_failures_from_trace(trace, job.name)
                    output["extracted_failures"] = failures

                self.output_json(output)
            else:
                self._display_job_logs_friendly(cli, job, job_id, trace)

        except Exception as e:
            self.output_error(f"Error fetching job {job_id} logs: {e}", output_format)

    def handle_job_tail(self, cli, job_id, args, output_format):
        """Tail job logs in real-time"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            
            print(f"Tailing logs for job #{job_id}: {job.name}")
            print(f"Status: {job.status}")
            print(f"{'='*60}")
            
            last_size = 0
            poll_interval = 2  # seconds
            completed_statuses = ["success", "failed", "canceled", "skipped"]
            
            while True:
                # Refresh job status
                job = cli.explorer.project.jobs.get(job_id)
                try:
                    trace = job.trace()
                    if isinstance(trace, bytes):
                        trace = trace.decode("utf-8", errors="replace")
                except Exception as e:
                    if "404" in str(e):
                        print("\n⏳ Waiting for job to start...")
                        time.sleep(poll_interval)
                        continue
                    else:
                        raise e
                current_size = len(trace)
                if current_size > last_size:
                    # Print only the new content
                    new_content = trace[last_size:]
                    sys.stdout.write(new_content)
                    sys.stdout.flush()
                    last_size = current_size
                if job.status in completed_statuses:
                    print(f"\n{'='*60}")
                    print(f"Job completed with status: {job.status}")
                    if job.status == "failed" and getattr(args, "failures", False):
                        failures = cli.explorer.extract_failures_from_trace(trace, job.name)
                        if failures.get("summary") or failures.get("details"):
                            print(f"\n{'='*60}")
                            print("Failure Analysis:")
                            print(f"{'='*60}")
                            if failures.get("summary"):
                                print("\nSummary:")
                                for line in failures["summary"]:
                                    print(f"  {line}")
                            if failures.get("details"):
                                print("\nDetails:")
                                for line in failures["details"][:50]:
                                    print(f"  {line}")
                    break
                
                # Wait before next poll
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹ Tail interrupted by user")
            sys.exit(0)
        except Exception as e:
            self.output_error(f"Error tailing job {job_id}: {e}", output_format)

    def handle_job_retry(self, cli, job_id, args, output_format):
        """Handle job retry - retry a failed job"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            
            if job.status not in ["failed", "canceled"]:
                error_msg = f"Job is {job.status}, only failed or canceled jobs can be retried"
                if output_format == "json":
                    self.output_json({
                        "action": "retry",
                        "job_id": job_id,
                        "status": "error",
                        "error": error_msg
                    })
                else:
                    print(f"⚠️  Job #{job_id} is {job.status}, only failed or canceled jobs can be retried")
                return
            
            result = job.retry()
            
            if output_format == "json":
                self.output_json({
                    "action": "retry",
                    "job_id": job_id,
                    "status": "success",
                    "new_job": {
                        "id": result.id if hasattr(result, 'id') else job_id,
                        "status": result.status if hasattr(result, 'status') else "pending"
                    }
                })
            else:
                print(f"✅ Job #{job_id} retry initiated")
                if hasattr(result, 'id') and result.id != job_id:
                    print(f"New job: #{result.id}")
                print(f"Status: {result.status if hasattr(result, 'status') else 'pending'}")
                
        except Exception as e:
            if output_format == "json":
                self.output_json({
                    "action": "retry",
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                })
            else:
                print(f"❌ Error retrying job {job_id}: {e}")
            sys.exit(1)

    def handle_job_play(self, cli, job_id, args, output_format):
        """Handle job play - play/trigger a manual job"""
        try:
            job = cli.explorer.project.jobs.get(job_id)
            
            if not hasattr(job, 'status') or job.status != "manual":
                error_msg = f"Job is {job.status if hasattr(job, 'status') else 'unknown'}, only manual jobs can be played"
                if output_format == "json":
                    self.output_json({
                        "action": "play",
                        "job_id": job_id,
                        "status": "error",
                        "error": error_msg
                    })
                else:
                    print(f"⚠️  Job #{job_id} is {job.status if hasattr(job, 'status') else 'unknown'}, only manual jobs can be played")
                return
            
            result = job.play()
            
            if output_format == "json":
                self.output_json({
                    "action": "play",
                    "job_id": job_id,
                    "status": "success",
                    "job_status": result.status if hasattr(result, 'status') else "pending"
                })
            else:
                print(f"✅ Job #{job_id} triggered")
                print(f"Status: {result.status if hasattr(result, 'status') else 'pending'}")
                
        except Exception as e:
            if output_format == "json":
                self.output_json({
                    "action": "play",
                    "job_id": job_id,
                    "status": "error",
                    "error": str(e)
                })
            else:
                print(f"❌ Error playing job {job_id}: {e}")
            sys.exit(1)

    def _display_job_summary(self, cli, job, job_id, args, total_jobs):
        """Display friendly job summary"""

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

        if total_jobs > 1:
            print("-" * 60)

    def _display_jobs_table(self, all_jobs):
        """Display jobs in table format"""
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

    def _build_job_detail_json(self, cli, job, job_id):
        """Build comprehensive JSON output for job detail"""
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
        runner_info = getattr(job, "runner", None)
        if runner_info:
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
        user_info = getattr(job, "user", None)
        if user_info and isinstance(user_info, dict):
            output["user"] = {
                "username": user_info.get("username"),
                "name": user_info.get("name"),
            }
        else:
            output["user"] = None
        if job.status == "failed":
            details = cli.explorer.get_failed_job_details(job_id)
            output["failure_reason"] = (
                job.failure_reason if hasattr(job, "failure_reason") else None
            )
            output["failures"] = details.get("failures", {})

        return output

    def _get_job_dependencies(self, cli, job):
        """Get job dependencies (needs and dependent jobs)"""
        dependencies = {
            "needs": [],
            "needed_by": []
        }
        
        try:

            if hasattr(job, 'needs') and job.needs:
                for need in job.needs:
                    if isinstance(need, dict):
                        dependencies["needs"].append({
                            "name": need.get("name", "Unknown"),
                            "artifacts": need.get("artifacts", True)
                        })
                    else:
                        dependencies["needs"].append({
                            "name": str(need),
                            "artifacts": True
                        })
            # We need to check all jobs in the pipeline
            if hasattr(job, 'pipeline') and job.pipeline:
                pipeline_id = job.pipeline.get('id') if isinstance(job.pipeline, dict) else job.pipeline.id
                all_jobs = cli.explorer.project.pipelines.get(pipeline_id).jobs.list(all=True)
                
                for other_job in all_jobs:
                    if hasattr(other_job, 'needs') and other_job.needs:
                        for need in other_job.needs:
                            need_name = need.get("name") if isinstance(need, dict) else str(need)
                            if need_name == job.name:
                                dependencies["needed_by"].append({
                                    "id": other_job.id,
                                    "name": other_job.name,
                                    "status": other_job.status
                                })
                                break
        except Exception as e:
            # Dependencies might not be available for all jobs
            if cli.verbose:
                print(f"Note: Could not fully resolve dependencies: {e}")
        
        return dependencies
    
    def _display_job_detail_friendly(self, cli, job, job_id, dependencies=None):
        """Display friendly detailed job information"""

        is_allowed_failure = job.allow_failure and job.status == "failed"

        if is_allowed_failure:
            status_icon = "⚠️"
            status_display = f"{job.status.upper()} (ALLOWED TO FAIL)"
        else:
            status_icon = {
                "success": "✅",
                "failed": "❌",
                "running": "🔄",
                "skipped": "⏭",
                "manual": "🎮",
                "canceled": "🚫",
                "pending": "⏳",
            }.get(job.status, "⏸")
            status_display = job.status.upper()

        print(f"\n{'='*60}")
        print(f"Job Details: {job.name} (#{job.id})")
        print(f"{'='*60}")
        print(f"Status: {status_icon} {status_display}")
        print(f"Stage: {job.stage}")
        print(f"Ref: {job.ref}")
        
        if hasattr(job, 'tag') and job.tag:
            print(f"Tag: {job.tag}")
        
        print(f"Duration: {cli.explorer.format_duration(job.duration)}")
        
        if hasattr(job, 'queued_duration') and job.queued_duration:
            print(f"Queued Duration: {cli.explorer.format_duration(job.queued_duration)}")
        
        print(f"Created: {job.created_at}")
        
        if job.started_at:
            print(f"Started: {job.started_at}")
        
        if job.finished_at:
            print(f"Finished: {job.finished_at}")
        
        print(f"\nJOB_URL: {job.web_url}")
        print(f"JOB_ID: {job.id}")
        pipeline_info = getattr(job, "pipeline", None)
        if pipeline_info and isinstance(pipeline_info, dict):
            print(f"\nPipeline: #{pipeline_info.get('id')} ({pipeline_info.get('status')})")
            print(f"Pipeline Ref: {pipeline_info.get('ref')}")
            print(f"Pipeline SHA: {pipeline_info.get('sha', '')[:8]}...")
        runner_info = getattr(job, "runner", None)
        if runner_info:
            if callable(runner_info):
                runner_info = runner_info()
            if runner_info and isinstance(runner_info, dict):
                print(f"\nRunner: #{runner_info.get('id')} - {runner_info.get('description', 'N/A')}")
                print(f"Active: {runner_info.get('active', 'Unknown')}")
                print(f"Shared: {runner_info.get('is_shared', 'Unknown')}")
        user_info = getattr(job, "user", None)
        if user_info and isinstance(user_info, dict):
            print(f"\nUser: {user_info.get('username')} ({user_info.get('name')})")
        artifacts = getattr(job, "artifacts", None)
        if artifacts:
            print(f"\nArtifacts: Available")
            artifacts_expire_at = getattr(job, "artifacts_expire_at", None)
            if artifacts_expire_at:
                print(f"Artifacts Expire: {artifacts_expire_at}")
        coverage = getattr(job, "coverage", None)
        if coverage:
            print(f"Coverage: {coverage}%")
        if job.status == "failed":
            print(f"\n{'='*60}")
            print("FAILURE DETAILS")
            print(f"{'='*60}")
            
            failure_reason = getattr(job, "failure_reason", None)
            if failure_reason:
                print(f"Failure Reason: {failure_reason}")
            details = cli.explorer.get_failed_job_details(job_id)
            failures = details.get("failures", {})
            
            if failures.get("short_summary"):
                print("\nFailure Summary:")
                print("-" * 40)
                print(failures["short_summary"])
            
            if failures.get("error_types"):
                print(f"\nError Types: {', '.join(failures['error_types'])}")
            
            if failures.get("failed_tests"):
                print(f"\nFailed Tests: {failures['failed_tests']}")
        if dependencies:
            has_deps = bool(dependencies.get("needs") or dependencies.get("needed_by"))
            if has_deps:
                print(f"\n{'='*60}")
                print("JOB DEPENDENCIES")
                print(f"{'='*60}")
                if dependencies.get("needs"):
                    print("\n🔼 This job depends on (needs):")
                    for need in dependencies["needs"]:
                        artifacts_str = " (with artifacts)" if need.get("artifacts") else " (no artifacts)"
                        print(f"  • {need['name']}{artifacts_str}")
                if dependencies.get("needed_by"):
                    print("\n🔽 Jobs that depend on this job:")
                    for dependent in dependencies["needed_by"]:
                        status_icon = {
                            "success": "✅",
                            "failed": "❌",
                            "running": "🔄",
                            "skipped": "⏭",
                            "manual": "🎮",
                            "canceled": "🚫",
                            "pending": "⏳",
                        }.get(dependent["status"], "⏸")
                        print(f"  • {dependent['name']} (#{dependent['id']}) {status_icon} {dependent['status']}")

        print(f"\n{'='*60}")

    def _display_job_logs_friendly(self, cli, job, job_id, trace):
        """Display friendly job logs output"""
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

                print("Full job trace follows...\n")
                print("=" * 60)

        # Print the full trace
        print(trace)

        print(f"\n{'='*60}")
        print(f"End of logs for job #{job_id}")