#!/usr/bin/env python3
# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

import sys
import argparse
import gitlab
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import re
from pathlib import Path

from .config import Config

COMPLETE_STATUSES = {"success", "failed", "canceled", "skipped"}


class GitLabExplorer:
    def __init__(self, config: Config):
        self.config = config
        self.gl = gitlab.Gitlab(config.gitlab_url, private_token=config.gitlab_token)
        self.project = self.gl.projects.get(config.project_path)
        self.db_file = config.get_cache_path("pipelines_cache.db")
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pipelines (
                pipeline_id INTEGER PRIMARY KEY,
                created_at TEXT,
                data TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS merge_request_pipelines (
                mr_id INTEGER,
                pipeline_id INTEGER,
                created_at TEXT,
                PRIMARY KEY (mr_id, pipeline_id)
            )
            """
        )
        conn.commit()
        conn.close()

    def get_mrs_for_branch(self, branch_name: str, state: str = 'opened') -> List[Dict[str, Any]]:
        """Get all merge requests for a given branch."""
        try:
            # Search for MRs with this source branch
            mrs = self.project.mergerequests.list(
                source_branch=branch_name,
                state=state,
                order_by='created_at',
                sort='desc',
                all=True
            )
            
            results = []
            for mr in mrs:
                mr_data = {
                    'id': mr.id,
                    'iid': mr.iid,
                    'title': mr.title,
                    'state': mr.state,
                    'author': mr.author['username'],
                    'target_branch': mr.target_branch,
                    'created_at': mr.created_at,
                    'updated_at': mr.updated_at,
                    'web_url': mr.web_url,
                    'has_conflicts': mr.has_conflicts if hasattr(mr, 'has_conflicts') else None,
                    'merge_status': mr.merge_status if hasattr(mr, 'merge_status') else None,
                }
                
                # Get latest pipeline status if available
                if hasattr(mr, 'head_pipeline') and mr.head_pipeline:
                    mr_data['pipeline_status'] = mr.head_pipeline.get('status', 'unknown')
                    mr_data['pipeline_id'] = mr.head_pipeline.get('id')
                else:
                    mr_data['pipeline_status'] = None
                    mr_data['pipeline_id'] = None
                    
                results.append(mr_data)
            
            return results
        except Exception as e:
            print(f"Error fetching MRs for branch {branch_name}: {e}")
            return []

    def get_pipelines_for_mr(self, mr_id: int) -> List[Dict[str, Any]]:
        """Get all pipelines for a given merge request."""
        try:
            mr = self.project.mergerequests.get(mr_id)
            pipelines = mr.pipelines()
            
            results = []
            for pipeline in pipelines:
                pipeline_data = {
                    'id': pipeline['id'],
                    'status': pipeline['status'],
                    'ref': pipeline['ref'],
                    'sha': pipeline['sha'][:8],
                    'created_at': pipeline['created_at'],
                    'updated_at': pipeline.get('updated_at', ''),
                }
                results.append(pipeline_data)
            
            # Sort by created_at descending (newest first)
            results.sort(key=lambda x: x['created_at'], reverse=True)
            return results
        except Exception as e:
            print(f"Error fetching pipelines for MR {mr_id}: {e}")
            return []

    def get_pipeline_details(self, pipeline_id: int, use_cache: bool = True, verbose: bool = False) -> Optional[Dict[str, Any]]:
        """Get detailed information about a pipeline."""
        # Check cache first
        if use_cache:
            if verbose:
                import time
                start = time.time()
            cached = self.get_pipeline_from_cache(pipeline_id, verbose=verbose)
            if cached:
                if verbose:
                    print(f"✓ Retrieved pipeline {pipeline_id} from cache ({time.time() - start:.3f}s)")
                return cached
            elif verbose:
                print(f"✗ Pipeline {pipeline_id} not in cache ({time.time() - start:.3f}s)")

        # Fetch from API
        if verbose:
            print(f"→ Fetching pipeline {pipeline_id} from GitLab API...")
        try:
            pipeline = self.project.pipelines.get(pipeline_id)
            jobs = pipeline.jobs.list(all=True)
            
            data = {
                'pipeline': pipeline.attributes,
                'jobs': [job.attributes for job in jobs]
            }
            
            # Cache if complete
            if pipeline.attributes.get('status', '').lower() in COMPLETE_STATUSES:
                self.save_pipeline_to_cache(pipeline_id, data)
                if verbose:
                    print(f"✓ Cached completed pipeline {pipeline_id} (status: {pipeline.attributes.get('status')})")
            elif verbose:
                print(f"✗ Not caching pipeline {pipeline_id} (status: {pipeline.attributes.get('status')} - still running)")
            
            return data
        except Exception as e:
            print(f"Error fetching pipeline {pipeline_id}: {e}")
            return None

    def get_pipeline_from_cache(self, pipeline_id: int, verbose: bool = False) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        
        # Debug: show what's in cache if verbose
        if verbose:
            cur.execute("SELECT COUNT(*) FROM pipelines")
            count = cur.fetchone()[0]
            print(f"Cache contains {count} total pipelines")
            
            # Show recent cached pipelines
            cur.execute("SELECT pipeline_id, created_at FROM pipelines ORDER BY created_at DESC LIMIT 5")
            recent = cur.fetchall()
            if recent:
                print("Recent cached pipelines:")
                for pid, created in recent:
                    print(f"  - Pipeline {pid} (created: {created[:16]})")
        
        cur.execute("SELECT data FROM pipelines WHERE pipeline_id = ?", (pipeline_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            try:
                return json.loads(row[0])
            except Exception as e:
                print(f"Error loading cached data for pipeline {pipeline_id}: {e}")
        return None

    def save_pipeline_to_cache(self, pipeline_id: int, data: Dict[str, Any]):
        created_at = data["pipeline"].get("created_at", "")
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO pipelines (pipeline_id, created_at, data) VALUES (?, ?, ?)",
            (pipeline_id, created_at, json.dumps(data)),
        )
        conn.commit()
        conn.close()

    def get_job_status_summary(self, pipeline_id: int, verbose: bool = False) -> Dict[str, Any]:
        """Get a summary of job statuses for a pipeline."""
        data = self.get_pipeline_details(pipeline_id, verbose=verbose)
        if not data:
            return {}
        
        jobs = data.get('jobs', [])
        pipeline_info = data.get('pipeline', {})
        
        summary = {
            'pipeline_status': pipeline_info.get('status', 'unknown'),
            'created_at': pipeline_info.get('created_at', ''),
            'updated_at': pipeline_info.get('updated_at', ''),
            'duration': pipeline_info.get('duration'),
            'total': len(jobs),
            'success': 0,
            'failed': 0,
            'running': 0,
            'pending': 0,
            'canceled': 0,
            'skipped': 0,
            'manual': 0,
            'failed_jobs': [],
            'stages': {},
            'jobs_by_stage': {}
        }
        
        # Collect stage information
        for job in jobs:
            status = job.get('status', '').lower()
            stage = job.get('stage', 'unknown')
            
            # Count by status
            if status in summary:
                summary[status] += 1
            
            # Track stages
            if stage not in summary['stages']:
                summary['stages'][stage] = {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'running': 0,
                    'pending': 0,
                    'canceled': 0,
                    'skipped': 0,
                    'manual': 0
                }
                summary['jobs_by_stage'][stage] = []
            
            summary['stages'][stage]['total'] += 1
            if status in summary['stages'][stage]:
                summary['stages'][stage][status] += 1
            
            # Store job details by stage
            summary['jobs_by_stage'][stage].append({
                'id': job['id'],
                'name': job['name'],
                'status': job['status'],
                'duration': job.get('duration'),
                'started_at': job.get('started_at'),
                'finished_at': job.get('finished_at')
            })
            
            if status == 'failed':
                summary['failed_jobs'].append({
                    'id': job['id'],
                    'name': job['name'],
                    'stage': stage,
                    'duration': job.get('duration'),
                    'finished_at': job.get('finished_at', '')
                })
        
        # Calculate progress
        completed = summary['success'] + summary['failed'] + summary['canceled'] + summary['skipped']
        summary['progress'] = {
            'completed': completed,
            'total': summary['total'],
            'percentage': int((completed / summary['total'] * 100)) if summary['total'] > 0 else 0
        }
        
        return summary

    def get_failed_job_details(self, job_id: int) -> Dict[str, Any]:
        """Get detailed failure information for a specific job."""
        try:
            job = self.project.jobs.get(job_id)
            trace = job.trace()
            if isinstance(trace, bytes):
                trace = trace.decode("utf-8", errors="replace")
            
            # Extract failure information
            result = {
                'id': job.id,
                'name': job.name,
                'status': job.status,
                'stage': job.stage,
                'duration': job.duration,
                'finished_at': job.finished_at,
                'web_url': job.web_url,
                'failures': self.extract_failures_from_trace(trace, job.name)
            }
            
            return result
        except Exception as e:
            print(f"Error fetching job {job_id}: {e}")
            return {}

    def extract_failures_from_trace(self, trace: str, job_name: str = '') -> Dict[str, Any]:
        """Extract failure information from job trace based on job type."""
        failures = {
            'short_summary': None,
            'detailed_failures': None,
            'stderr': None,
            'error_lines': [],
            'type': 'generic'  # Type of failure extraction used
        }
        
        # Determine job type and use appropriate extraction
        job_name_lower = job_name.lower()
        
        # Pylint jobs
        if 'pylint' in job_name_lower:
            failures['type'] = 'pylint'
            return self.extract_pylint_failures(trace, failures)
        
        # Integration/unit test jobs (pytest)
        elif any(test_word in job_name_lower for test_word in ['test', 'pytest', 'integration', 'unit']):
            failures['type'] = 'pytest'
            return self.extract_pytest_failures(trace, failures)
        
        # Ruff/linting jobs
        elif 'ruff' in job_name_lower or 'lint' in job_name_lower:
            failures['type'] = 'linting'
            return self.extract_linting_failures(trace, failures)
        
        # Type checking jobs
        elif 'mypy' in job_name_lower or 'type' in job_name_lower:
            failures['type'] = 'typecheck'
            return self.extract_typecheck_failures(trace, failures)
        
        # Default: generic extraction
        else:
            return self.extract_generic_failures(trace, failures)
    
    def extract_pytest_failures(self, trace: str, failures: Dict) -> Dict[str, Any]:
        """Extract pytest-specific failure information."""
        # Short test summary
        summary_pattern = re.compile(
            r"(^=+\s*short test summary info\s*=+\n.*?)(?=^=+|\Z)",
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        summary_match = summary_pattern.search(trace)
        if summary_match:
            failures['short_summary'] = summary_match.group(1).strip()
        
        # Detailed failures
        failures_pattern = re.compile(
            r"(^=+\s*FAILURES\s*=+\n.*?)(?=^[-=]+\s*Captured stderr call\s*[-=]+|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        failures_match = failures_pattern.search(trace)
        if failures_match:
            failures['detailed_failures'] = failures_match.group(1).strip()
        
        # Captured stderr
        stderr_pattern = re.compile(
            r"(?:^-{5,}\s*Captured stderr call\s*-{5,}\n)(.*?)(?=^=+|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        stderr_match = stderr_pattern.search(trace)
        if stderr_match:
            failures['stderr'] = stderr_match.group(1).strip()
        
        return failures
    
    def extract_pylint_failures(self, trace: str, failures: Dict) -> Dict[str, Any]:
        """Extract pylint-specific violations."""
        # Look for pylint violation patterns
        violations = []
        violation_pattern = re.compile(r'^\*+\s*Module\s+(.+)$', re.MULTILINE)
        
        # Find all module sections with violations
        module_matches = violation_pattern.finditer(trace)
        
        for match in module_matches:
            module_name = match.group(1)
            module_start = match.end()
            
            # Find the next module or end of violations
            next_module = violation_pattern.search(trace, module_start)
            module_end = next_module.start() if next_module else len(trace)
            
            # Extract violations for this module
            module_section = trace[module_start:module_end]
            violation_lines = []
            
            for line in module_section.split('\n'):
                # Match pylint violation format: file.py:line:col: CODE: message
                if re.match(r'^.+\.py:\d+:\d+:\s+[A-Z]\d+:', line):
                    violation_lines.append(line.strip())
            
            if violation_lines:
                violations.extend(violation_lines)
        
        if violations:
            failures['short_summary'] = f"Pylint found {len(violations)} violation(s):\n" + '\n'.join(violations[:20])
            if len(violations) > 20:
                failures['short_summary'] += f"\n... and {len(violations) - 20} more violations"
        
        # Also check for the exit code message
        exit_pattern = re.compile(r'ERROR: Job failed: command terminated with exit code (\d+)')
        exit_match = exit_pattern.search(trace)
        if exit_match and not violations:
            failures['short_summary'] = f"Pylint failed with exit code {exit_match.group(1)}"
        
        return failures
    
    def extract_linting_failures(self, trace: str, failures: Dict) -> Dict[str, Any]:
        """Extract linting failures (ruff, flake8, etc)."""
        # Look for common linting output patterns
        lint_errors = []
        
        # Ruff format: file.py:line:col: CODE message
        ruff_pattern = re.compile(r'^(.+\.py):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$', re.MULTILINE)
        for match in ruff_pattern.finditer(trace):
            lint_errors.append(match.group(0).strip())
        
        if lint_errors:
            failures['short_summary'] = f"Linting found {len(lint_errors)} issue(s):\n" + '\n'.join(lint_errors[:15])
            if len(lint_errors) > 15:
                failures['short_summary'] += f"\n... and {len(lint_errors) - 15} more issues"
        
        return failures
    
    def extract_typecheck_failures(self, trace: str, failures: Dict) -> Dict[str, Any]:
        """Extract type checking failures (mypy, etc)."""
        # Look for mypy error format
        type_errors = []
        
        # Mypy format: file.py:line: error: message
        mypy_pattern = re.compile(r'^(.+\.py):(\d+):\s+error:\s+(.+)$', re.MULTILINE)
        for match in mypy_pattern.finditer(trace):
            type_errors.append(match.group(0).strip())
        
        if type_errors:
            failures['short_summary'] = f"Type checking found {len(type_errors)} error(s):\n" + '\n'.join(type_errors[:15])
            if len(type_errors) > 15:
                failures['short_summary'] += f"\n... and {len(type_errors) - 15} more errors"
        
        return failures
    
    def extract_generic_failures(self, trace: str, failures: Dict) -> Dict[str, Any]:
        """Generic failure extraction for unknown job types."""
        # Look for the last 30 lines before "Job failed"
        lines = trace.split('\n')
        
        # Find where the job failed
        failed_index = -1
        for i, line in enumerate(lines):
            if 'ERROR: Job failed' in line or 'Job failed' in line:
                failed_index = i
                break
        
        if failed_index > 0:
            # Get the last 30 lines before failure
            start_index = max(0, failed_index - 30)
            context_lines = lines[start_index:failed_index + 1]
            failures['short_summary'] = "Job failed. Last 30 lines:\n" + '\n'.join(context_lines)
        else:
            # Generic error line extraction
            error_lines = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception', 'fatal', 'abort']):
                    error_lines.append(line.strip())
            
            if error_lines:
                failures['short_summary'] = "Error lines found:\n" + '\n'.join(error_lines[:20])
                failures['error_lines'] = error_lines[:20]
        
        return failures

    def format_duration(self, duration: Optional[float]) -> str:
        """Format duration in seconds to human-readable format."""
        if duration is None:
            return "N/A"
        minutes, seconds = divmod(duration, 60)
        return f"{int(minutes)}m{int(seconds)}s"


class PipelineCLI:
    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.explorer = GitLabExplorer(config)
        self.verbose = verbose
        self.default_format = config.default_format

    def cmd_branch_mrs(self, args):
        """List merge requests for a branch."""
        mrs = self.explorer.get_mrs_for_branch(args.branch_name, args.state)
        
        if not mrs:
            print(f"No {args.state} MRs found for branch '{args.branch_name}'")
            return
        
        print(f"\nMerge Requests for branch '{args.branch_name}' (state: {args.state}):")
        print("-" * 120)
        print(f"{'MR':<8} {'Status':<10} {'Pipeline':<12} {'Title':<50} {'Author':<15} {'Target'}")
        print("-" * 120)
        
        for mr in mrs:
            # Format MR status
            mr_state = mr['state']
            if mr_state == 'opened':
                state_display = f"\033[92m{mr_state:<10}\033[0m"  # Green
            elif mr_state == 'merged':
                state_display = f"\033[94m{mr_state:<10}\033[0m"  # Blue
            elif mr_state == 'closed':
                state_display = f"\033[91m{mr_state:<10}\033[0m"  # Red
            else:
                state_display = f"{mr_state:<10}"
            
            # Format pipeline status
            if mr['pipeline_status']:
                p_status = mr['pipeline_status']
                if p_status == 'success':
                    pipeline_display = f"\033[92m✅ {mr['pipeline_id']}\033[0m"
                elif p_status == 'failed':
                    pipeline_display = f"\033[91m❌ {mr['pipeline_id']}\033[0m"
                elif p_status == 'running':
                    pipeline_display = f"\033[93m🔄 {mr['pipeline_id']}\033[0m"
                else:
                    pipeline_display = f"{p_status[:3]} {mr['pipeline_id']}"
            else:
                pipeline_display = "No pipeline"
            
            title = mr['title'][:50]
            if len(mr['title']) > 50:
                title += "..."
            
            print(f"!{mr['iid']:<7} {state_display} {pipeline_display:<12} {title:<50} {mr['author']:<15} {mr['target_branch']}")
        
        if args.latest and mrs:
            latest_mr = mrs[0]
            print(f"\nLatest MR: !{latest_mr['iid']} (ID: {latest_mr['id']})")
            if latest_mr['pipeline_id']:
                print(f"Latest pipeline: {latest_mr['pipeline_id']} (status: {latest_mr['pipeline_status']})")

    def cmd_mr_info(self, args):
        """Get detailed information about a merge request."""
        try:
            mr = self.explorer.project.mergerequests.get(args.mr_id)
            
            # Determine status color
            if mr.state == 'opened':
                state_display = f"\033[92m{mr.state.upper()}\033[0m"  # Green
            elif mr.state == 'merged':
                state_display = f"\033[94m{mr.state.upper()}\033[0m"  # Blue
            elif mr.state == 'closed':
                state_display = f"\033[91m{mr.state.upper()}\033[0m"  # Red
            else:
                state_display = mr.state.upper()
            
            print(f"\n{'='*80}")
            print(f"MR !{mr.iid}: {mr.title}")
            print(f"{'='*80}")
            print(f"Status:        {state_display}")
            print(f"Author:        {mr.author['username']} ({mr.author['name']})")
            print(f"Source Branch: {mr.source_branch}")
            print(f"Target Branch: {mr.target_branch}")
            print(f"Created:       {mr.created_at}")
            print(f"Updated:       {mr.updated_at}")
            
            if hasattr(mr, 'merged_at') and mr.merged_at:
                print(f"Merged:        {mr.merged_at}")
                if hasattr(mr, 'merged_by') and mr.merged_by:
                    print(f"Merged By:     {mr.merged_by['username']}")
            
            # Merge status
            if mr.state == 'opened':
                merge_status = getattr(mr, 'merge_status', 'unknown')
                if merge_status == 'can_be_merged':
                    merge_display = "\033[92m✅ Can be merged\033[0m"
                elif merge_status == 'cannot_be_merged':
                    merge_display = "\033[91m❌ Cannot be merged (conflicts)\033[0m"
                else:
                    merge_display = f"⚠️  {merge_status}"
                print(f"Merge Status:  {merge_display}")
                
                if hasattr(mr, 'has_conflicts') and mr.has_conflicts:
                    print(f"Conflicts:     \033[91m⚠️  Has conflicts\033[0m")
            
            # Pipeline status
            if hasattr(mr, 'head_pipeline') and mr.head_pipeline:
                pipeline_status = mr.head_pipeline.get('status', 'unknown')
                if pipeline_status == 'success':
                    pipeline_display = f"\033[92m✅ {pipeline_status}\033[0m"
                elif pipeline_status == 'failed':
                    pipeline_display = f"\033[91m❌ {pipeline_status}\033[0m"
                elif pipeline_status == 'running':
                    pipeline_display = f"\033[93m🔄 {pipeline_status}\033[0m"
                else:
                    pipeline_display = pipeline_status
                print(f"Pipeline:      {pipeline_display} (ID: {mr.head_pipeline.get('id')})")
            
            # Approvals
            if hasattr(mr, 'approvals_required'):
                approvals = mr.approvals.get()
                approved_by = [u['user']['username'] for u in approvals.approved_by] if hasattr(approvals, 'approved_by') else []
                approval_status = f"{len(approved_by)}/{approvals.approvals_required}"
                if len(approved_by) >= approvals.approvals_required:
                    print(f"Approvals:     \033[92m✅ {approval_status}\033[0m - {', '.join(approved_by)}")
                else:
                    print(f"Approvals:     ⏸ {approval_status}" + (f" - {', '.join(approved_by)}" if approved_by else ""))
            
            print(f"Web URL:       {mr.web_url}")
            
            # Description
            if mr.description:
                print(f"\nDescription:")
                print("-" * 40)
                # Limit description to first 500 chars or 10 lines
                desc_lines = mr.description.split('\n')[:10]
                desc_text = '\n'.join(desc_lines)
                if len(desc_text) > 500:
                    desc_text = desc_text[:500] + "..."
                print(desc_text)
            
            # Show recent pipelines if requested
            if args.pipelines:
                print(f"\n{'='*80}")
                print("Recent Pipelines:")
                self.cmd_mr_pipelines(args)
                
        except Exception as e:
            print(f"Error fetching MR {args.mr_id}: {e}")
    
    def cmd_mr_pipelines(self, args):
        """List pipelines for a merge request."""
        pipelines = self.explorer.get_pipelines_for_mr(args.mr_id)
        
        if not pipelines:
            print(f"No pipelines found for MR {args.mr_id}")
            return
        
        if not hasattr(args, 'pipelines') or not args.pipelines:
            print(f"\nPipelines for MR #{args.mr_id}:")
        print("-" * 80)
        print(f"{'ID':<10} {'Status':<12} {'Ref':<30} {'SHA':<10} {'Created'}")
        print("-" * 80)
        
        for p in pipelines[:10]:  # Limit to 10 most recent
            created = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
            created_str = created.strftime('%Y-%m-%d %H:%M')
            
            # Color-code status
            status = p['status']
            if status == 'success':
                status_display = f"\033[92m{status:<12}\033[0m"  # Green
            elif status == 'failed':
                status_display = f"\033[91m{status:<12}\033[0m"  # Red
            elif status == 'running':
                status_display = f"\033[93m{status:<12}\033[0m"  # Yellow
            else:
                status_display = f"{status:<12}"
            
            print(f"{p['id']:<10} {status_display} {p['ref'][:30]:<30} {p['sha']:<10} {created_str}")
        
        if args.latest:
            print(f"\nLatest pipeline: {pipelines[0]['id']}")

    def cmd_pipeline_status(self, args):
        """Show job status summary for a pipeline."""
        summary = self.explorer.get_job_status_summary(args.pipeline_id, verbose=self.verbose)
        
        if not summary:
            print(f"Could not fetch pipeline {args.pipeline_id}")
            return
        
        # Check output format (use configured default if not specified)
        output_format = getattr(args, 'format', self.default_format)
        
        if output_format == 'json':
            # JSON output for scripting
            import json
            output = {
                'pipeline_id': args.pipeline_id,
                'status': summary['pipeline_status'],
                'created_at': summary['created_at'],
                'updated_at': summary['updated_at'],
                'duration': summary['duration'],
                'progress': summary['progress'],
                'job_counts': {
                    'total': summary['total'],
                    'success': summary['success'],
                    'failed': summary['failed'],
                    'running': summary['running'],
                    'pending': summary['pending'],
                    'canceled': summary['canceled'],
                    'skipped': summary['skipped'],
                    'manual': summary['manual']
                },
                'failed_jobs': summary['failed_jobs'],
                'stages': summary['stages']
            }
            print(json.dumps(output, indent=2))
            return
        
        # Pipeline header with progress bar
        pipeline_status = summary['pipeline_status']
        if pipeline_status == 'success':
            status_icon = "✅"
        elif pipeline_status == 'failed':
            status_icon = "❌"
        elif pipeline_status == 'running':
            status_icon = "🔄"
        else:
            status_icon = "⏸"
        
        print(f"\n{status_icon} Pipeline {args.pipeline_id} - {pipeline_status.upper()}")
        
        # Progress bar
        progress = summary['progress']
        bar_width = 40
        filled = int(bar_width * progress['percentage'] / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        print(f"Progress: [{bar}] {progress['completed']}/{progress['total']} ({progress['percentage']}%)")
        
        if summary['duration']:
            print(f"Duration: {self.explorer.format_duration(summary['duration'])}")
        
        print("-" * 80)
        
        if args.detailed:
            # Detailed stage-by-stage view
            print("\nStage Progress:")
            print("-" * 80)
            
            # Define typical stage order (customize as needed)
            stage_order = ['build', 'test', 'deploy', 'cleanup']
            all_stages = list(summary['stages'].keys())
            # Add any stages not in our predefined order
            for stage in all_stages:
                if stage not in stage_order:
                    stage_order.append(stage)
            
            for stage in stage_order:
                if stage not in summary['stages']:
                    continue
                    
                stage_info = summary['stages'][stage]
                jobs = summary['jobs_by_stage'][stage]
                
                # Stage header
                stage_complete = stage_info['success'] + stage_info['failed'] + stage_info['canceled'] + stage_info['skipped']
                stage_progress = f"{stage_complete}/{stage_info['total']}"
                
                # Determine stage status icon
                if stage_info['failed'] > 0:
                    stage_icon = "❌"
                elif stage_info['running'] > 0:
                    stage_icon = "🔄"
                elif stage_info['pending'] > 0:
                    stage_icon = "⏸"
                elif stage_info['success'] == stage_info['total']:
                    stage_icon = "✅"
                else:
                    stage_icon = "⚠️"
                
                print(f"\n{stage_icon} Stage: {stage.upper()} [{stage_progress}]")
                print("  " + "-" * 76)
                
                # Show jobs in this stage
                for job in sorted(jobs, key=lambda x: x['name']):
                    status = job['status'].lower()
                    if status == 'success':
                        job_icon = "✅"
                        status_color = "\033[92m"
                    elif status == 'failed':
                        job_icon = "❌"
                        status_color = "\033[91m"
                    elif status == 'running':
                        job_icon = "🔄"
                        status_color = "\033[93m"
                    elif status == 'pending':
                        job_icon = "⏸"
                        status_color = "\033[90m"
                    elif status == 'skipped':
                        job_icon = "⏭"
                        status_color = "\033[90m"
                    else:
                        job_icon = "  "
                        status_color = ""
                    
                    duration = self.explorer.format_duration(job['duration']) if job['duration'] else '-'
                    job_name = job['name'][:50]
                    
                    if status_color:
                        print(f"  {job_icon} {status_color}{job['id']:<10} {job_name:<50} {duration:<10}\033[0m")
                    else:
                        print(f"  {job_icon} {job['id']:<10} {job_name:<50} {duration:<10}")
        else:
            # Summary view (original)
            print(f"Total Jobs:    {summary['total']}")
            print(f"  ✅ Success:  {summary['success']}")
            print(f"  ❌ Failed:   {summary['failed']}")
            print(f"  🔄 Running:  {summary['running']}")
            print(f"  ⏸  Pending:  {summary['pending']}")
            print(f"  ⏭  Skipped:  {summary['skipped']}")
            print(f"  🚫 Canceled: {summary['canceled']}")
            print(f"  👤 Manual:   {summary['manual']}")
            
            if summary['failed_jobs']:
                print("\nFailed Jobs:")
                print("-" * 60)
                print(f"{'ID':<12} {'Stage':<15} {'Name':<40} {'Duration'}")
                print("-" * 60)
                for job in summary['failed_jobs']:
                    duration = self.explorer.format_duration(job['duration'])
                    print(f"{job['id']:<12} {job['stage']:<15} {job['name'][:40]:<40} {duration}")

    def cmd_pipeline_jobs(self, args):
        """List all jobs in a pipeline with optional filtering."""
        data = self.explorer.get_pipeline_details(args.pipeline_id, verbose=self.verbose)
        
        if not data:
            print(f"Could not fetch pipeline {args.pipeline_id}")
            return
        
        jobs = data.get('jobs', [])
        
        # Filter by status if specified
        if hasattr(args, 'status') and args.status:
            jobs = [j for j in jobs if j.get('status', '').lower() == args.status.lower()]
        
        # Filter by stage if specified
        if hasattr(args, 'stage') and args.stage:
            jobs = [j for j in jobs if j.get('stage', '').lower() == args.stage.lower()]
        
        # Sort jobs
        sort_field = getattr(args, 'sort', 'created')
        if sort_field == 'duration':
            jobs.sort(key=lambda x: x.get('duration', 0) or 0, reverse=True)
        elif sort_field == 'name':
            jobs.sort(key=lambda x: x.get('name', ''))
        else:  # Default: by created_at
            jobs.sort(key=lambda x: x.get('created_at', ''))
        
        # Output format (use configured default if not specified)
        output_format = getattr(args, 'format', self.default_format)
        
        if output_format == 'json':
            # JSON output for scripting
            import json
            output = {
                'pipeline_id': args.pipeline_id,
                'total_jobs': len(jobs),
                'jobs': []
            }
            for job in jobs:
                output['jobs'].append({
                    'id': job['id'],
                    'name': job['name'],
                    'status': job['status'],
                    'stage': job.get('stage', ''),
                    'duration': job.get('duration'),
                    'created_at': job.get('created_at', ''),
                    'started_at': job.get('started_at', ''),
                    'finished_at': job.get('finished_at', ''),
                    'web_url': job.get('web_url', '')
                })
            print(json.dumps(output, indent=2))
            
        elif output_format == 'table':
            # Pure table output (no colors, fixed width)
            print(f"{'ID':<12} {'Status':<10} {'Stage':<15} {'Name':<40} {'Duration':<10}")
            print("-" * 87)
            for job in jobs:
                duration = self.explorer.format_duration(job.get('duration'))
                print(f"{job['id']:<12} {job['status']:<10} {job.get('stage', ''):<15} {job['name'][:40]:<40} {duration:<10}")
                
        else:  # friendly (default)
            print(f"\nJobs in Pipeline {args.pipeline_id}:")
            print("-" * 100)
            print(f"{'ID':<12} {'Status':<10} {'Stage':<15} {'Name':<40} {'Duration':<10} {'Finished'}")
            print("-" * 100)
            
            for job in jobs:
                status = job.get('status', 'unknown')
                # Color-code status
                if status == 'success':
                    status_display = f"\033[92m{status:<10}\033[0m"
                elif status == 'failed':
                    status_display = f"\033[91m{status:<10}\033[0m"
                elif status == 'running':
                    status_display = f"\033[93m{status:<10}\033[0m"
                else:
                    status_display = f"{status:<10}"
                
                duration = self.explorer.format_duration(job.get('duration'))
                finished = job.get('finished_at', '')
                if finished:
                    finished = datetime.fromisoformat(finished.replace('Z', '+00:00')).strftime('%H:%M:%S')
                
                print(f"{job['id']:<12} {status_display} {job.get('stage', ''):<15} {job['name'][:40]:<40} {duration:<10} {finished}")

    def cmd_job_failures(self, args):
        """Show detailed failure information for a job."""
        details = self.explorer.get_failed_job_details(args.job_id)
        
        if not details:
            print(f"Could not fetch job {args.job_id}")
            return
        
        print(f"\nJob {details['id']}: {details['name']}")
        print(f"Status: {details['status']} | Stage: {details['stage']}")
        print(f"Duration: {self.explorer.format_duration(details['duration'])}")
        print(f"URL: {details['web_url']}")
        print("-" * 80)
        
        failures = details['failures']
        
        if args.verbose:
            # Show all failure information
            if failures['short_summary']:
                print("\n📋 Short Test Summary:")
                print(failures['short_summary'])
            
            if failures['detailed_failures']:
                print("\n❌ Detailed Failures:")
                print(failures['detailed_failures'])
            
            if failures['stderr']:
                print("\n⚠️  Captured Stderr:")
                print(failures['stderr'])
        else:
            # Show condensed failure information
            if failures['short_summary']:
                print("\n📋 Test Failures:")
                # Extract just the FAILED lines
                for line in failures['short_summary'].split('\n'):
                    if 'FAILED' in line:
                        print(f"  • {line.strip()}")
            
            if failures['error_lines'] and not failures['short_summary']:
                print("\n⚠️  Error Lines:")
                for line in failures['error_lines'][:10]:
                    if line:
                        print(f"  • {line}")

    def cmd_batch_failures(self, args):
        """Show failures for multiple jobs."""
        for job_id in args.job_ids:
            print(f"\n{'='*80}")
            details = self.explorer.get_failed_job_details(job_id)
            
            if not details:
                print(f"Could not fetch job {job_id}")
                continue
            
            print(f"Job {details['id']}: {details['name']}")
            print(f"Status: {details['status']} | Duration: {self.explorer.format_duration(details['duration'])}")
            
            failures = details['failures']
            if failures['short_summary']:
                # Extract just the FAILED lines
                failed_tests = []
                for line in failures['short_summary'].split('\n'):
                    if 'FAILED' in line:
                        failed_tests.append(line.strip())
                
                if failed_tests:
                    print("Failed tests:")
                    for test in failed_tests[:5]:  # Show first 5
                        print(f"  • {test}")
                    if len(failed_tests) > 5:
                        print(f"  ... and {len(failed_tests) - 5} more")

    def run(self):
        parser = argparse.ArgumentParser(
            description='GitLab Pipeline Explorer - Interactive CLI for exploring pipeline and job statuses',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get MRs for current branch
  %(prog)s branch $(git branch --show-current)
  %(prog)s branch feature-xyz --state all

  # Get pipelines for a merge request
  %(prog)s mr 1234
  %(prog)s mr 1234 --latest

  # Get job summary for a pipeline
  %(prog)s status 567890

  # List all jobs in a pipeline
  %(prog)s jobs 567890
  %(prog)s jobs 567890 --status failed
  %(prog)s jobs 567890 --sort duration

  # Get failure details for a job
  %(prog)s failures 123456
  %(prog)s failures 123456 --verbose

  # Get failures for multiple jobs
  %(prog)s batch-failures 123456 123457 123458
  
  # Full workflow from current branch
  %(prog)s branch $(git branch --show-current) --latest
  %(prog)s mr <mr_id_from_above>
  %(prog)s status <pipeline_id_from_above>
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Branch MRs command
        branch_parser = subparsers.add_parser('branch', help='Get merge requests for a branch')
        branch_parser.add_argument('branch_name', help='Branch name (use $(git branch --show-current) for current)')
        branch_parser.add_argument('--state', choices=['opened', 'merged', 'closed', 'all'], 
                                  default='opened', help='MR state filter')
        branch_parser.add_argument('--latest', action='store_true', help='Show latest MR and pipeline IDs')
        
        # MR pipelines command
        mr_parser = subparsers.add_parser('mr', help='Get pipelines for a merge request')
        mr_parser.add_argument('mr_id', type=int, help='Merge request ID')
        mr_parser.add_argument('--latest', action='store_true', help='Show latest pipeline ID')
        
        # MR info command
        mr_info_parser = subparsers.add_parser('mr-info', help='Get detailed information about a merge request')
        mr_info_parser.add_argument('mr_id', type=int, help='Merge request ID')
        mr_info_parser.add_argument('--pipelines', '-p', action='store_true', 
                                   help='Also show recent pipelines')
        
        # Pipeline status command
        status_parser = subparsers.add_parser('status', help='Get job status summary for a pipeline')
        status_parser.add_argument('pipeline_id', type=int, help='Pipeline ID')
        status_parser.add_argument('--detailed', '-d', action='store_true', 
                                  help='Show detailed stage-by-stage progress with all jobs')
        
        # Pipeline jobs command
        jobs_parser = subparsers.add_parser('jobs', help='List all jobs in a pipeline')
        jobs_parser.add_argument('pipeline_id', type=int, help='Pipeline ID')
        jobs_parser.add_argument('--status', help='Filter by status (success, failed, running, etc.)')
        jobs_parser.add_argument('--stage', help='Filter by stage name')
        jobs_parser.add_argument('--sort', choices=['duration', 'name', 'created'], default='created',
                                help='Sort jobs by field')
        
        # Job failures command
        failures_parser = subparsers.add_parser('failures', help='Get failure details for a job')
        failures_parser.add_argument('job_id', type=int, help='Job ID')
        failures_parser.add_argument('--verbose', '-v', action='store_true', 
                                    help='Show detailed failure information')
        
        # Batch failures command
        batch_parser = subparsers.add_parser('batch-failures', help='Get failures for multiple jobs')
        batch_parser.add_argument('job_ids', type=int, nargs='+', help='Job IDs')
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Route to appropriate command
        if args.command == 'branch':
            self.cmd_branch_mrs(args)
        elif args.command == 'mr':
            self.cmd_mr_pipelines(args)
        elif args.command == 'mr-info':
            self.cmd_mr_info(args)
        elif args.command == 'status':
            self.cmd_pipeline_status(args)
        elif args.command == 'jobs':
            self.cmd_pipeline_jobs(args)
        elif args.command == 'failures':
            self.cmd_job_failures(args)
        elif args.command == 'batch-failures':
            self.cmd_batch_failures(args)


def main():
    """Main entry point for the CLI"""
    config = Config()
    
    # Check if this is a config command first
    if len(sys.argv) > 1 and sys.argv[1] == 'config':
        parser = argparse.ArgumentParser(description='Configure GitLab CLI')
        parser.add_argument('config', help='Config command')
        parser.add_argument('--gitlab-url', help='GitLab server URL')
        parser.add_argument('--project', help='GitLab project path (e.g., group/project)')
        parser.add_argument('--show', action='store_true', help='Show current configuration')
        
        args = parser.parse_args()
        
        if args.show:
            print(f"GitLab URL: {config.gitlab_url or 'Not set'}")
            print(f"Project: {config.project_path or 'Not set'}")
            print(f"Token: {'Set' if config.gitlab_token else 'Not set'}")
            print(f"Cache dir: {config.cache_dir}")
            return
        
        update = {}
        if args.gitlab_url:
            update['gitlab_url'] = args.gitlab_url
        if args.project:
            update['project_path'] = args.project
        
        if update:
            config.save_config(**update)
            print("Configuration saved")
        return
    
    # Validate configuration
    valid, message = config.validate()
    if not valid:
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)
    
    # Run the main CLI
    cli = PipelineCLI(config)
    cli.run()


if __name__ == "__main__":
    main()