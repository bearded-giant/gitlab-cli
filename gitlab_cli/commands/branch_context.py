"""Branch context commands - show branch info and related resources"""

import subprocess
import json
from datetime import datetime
from typing import Optional
from .base import BaseCommand


class BranchCommand(BaseCommand):
    """Handle branch context commands"""
    
    def add_arguments(self, parser):
        """Add branch-specific arguments to parser"""
        parser.add_argument(
            "branch_name",
            nargs="?",
            help="Branch name (defaults to current branch)"
        )
        
        # Subcommands for branch context
        parser.add_argument(
            "resource",
            nargs="?",
            choices=["mr", "pipeline", "commit", "info"],
            help="Resource to show for branch (mr, pipeline, commit, info)"
        )
        
        # Filters
        parser.add_argument(
            "--state",
            choices=["opened", "merged", "closed", "all"],
            default="opened",
            help="Filter by state (for MRs)"
        )
        parser.add_argument(
            "--latest",
            action="store_true",
            help="Show only the latest/most recent MR"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Limit number of results (default: 10)"
        )
        parser.add_argument(
            "--format",
            choices=["friendly", "table", "json"],
            help="Output format"
        )
    
    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def get_branch_info(self, cli, branch_name: str) -> dict:
        """Get branch information from git and GitLab"""
        info = {
            "name": branch_name,
            "exists_locally": False,
            "exists_remote": False,
            "last_commit": None,
            "ahead_behind": None,
            "age": None,
            "author": None
        }
        
        # Check if branch exists locally
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                capture_output=True,
                text=True
            )
            info["exists_locally"] = result.returncode == 0
        except:
            pass
        
        # Get last commit info
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%an|%ae|%ar", branch_name],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                parts = result.stdout.strip().split('|')
                if len(parts) >= 5:
                    info["last_commit"] = {
                        "sha": parts[0][:8],
                        "message": parts[1][:60],
                        "author": parts[2],
                        "email": parts[3],
                        "age": parts[4]
                    }
                    info["age"] = parts[4]
                    info["author"] = parts[2]
        except:
            pass
        
        # Check ahead/behind from main/master
        try:
            # Try to find the main branch
            for main_branch in ["main", "master"]:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", f"origin/{main_branch}"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Get ahead/behind counts
                    result = subprocess.run(
                        ["git", "rev-list", "--left-right", "--count", f"origin/{main_branch}...{branch_name}"],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        behind, ahead = result.stdout.strip().split('\t')
                        info["ahead_behind"] = {
                            "ahead": int(ahead),
                            "behind": int(behind),
                            "base": main_branch
                        }
                    break
        except:
            pass
        
        # Get branch protection status and other GitLab info
        try:
            branches = cli.explorer.project.branches.list(search=branch_name)
            for branch in branches:
                if branch.name == branch_name:
                    info["exists_remote"] = True
                    info["protected"] = branch.protected
                    info["merged"] = branch.merged
                    info["web_url"] = f"{cli.explorer.project.web_url}/-/tree/{branch_name}"
                    if hasattr(branch, 'commit'):
                        info["remote_commit"] = branch.commit['id'][:8]
                    break
        except:
            pass
        
        return info
    
    def handle(self, cli, args, output_format):
        """Handle branch commands"""
        # Get branch name
        branch_name = args.branch_name
        if not branch_name:
            branch_name = self.get_current_branch()
            if not branch_name:
                print("Error: Not in a git repository or cannot determine branch")
                return
        
        # If --latest flag is used without specifying 'mr' resource, show latest MR
        if args.latest and not args.resource:
            args.resource = "mr"
        
        # If no resource specified, show branch info
        if not args.resource or args.resource == "info":
            self.show_branch_info(cli, branch_name, output_format)
        elif args.resource == "mr":
            self.show_branch_mrs(cli, branch_name, args, output_format)
        elif args.resource == "pipeline":
            self.show_branch_pipelines(cli, branch_name, args, output_format)
        elif args.resource == "commit":
            self.show_branch_commits(cli, branch_name, args, output_format)
    
    def show_branch_info(self, cli, branch_name, output_format):
        """Show branch information"""
        info = self.get_branch_info(cli, branch_name)
        
        # Get counts of related resources
        try:
            mrs = cli.explorer.get_mrs_for_branch(branch_name, "all")
            mr_counts = {
                "total": len(mrs),
                "opened": len([m for m in mrs if m['state'] == 'opened']),
                "merged": len([m for m in mrs if m['state'] == 'merged']),
                "closed": len([m for m in mrs if m['state'] == 'closed'])
            }
            
            # Get recent pipelines
            pipelines = cli.explorer.project.pipelines.list(
                ref=branch_name,
                per_page=5
            )
            pipeline_count = len(pipelines)
            latest_pipeline = pipelines[0] if pipelines else None
        except:
            mr_counts = {"total": 0, "opened": 0, "merged": 0, "closed": 0}
            pipeline_count = 0
            latest_pipeline = None
        
        if output_format == "json":
            output = {
                "branch": info,
                "merge_requests": mr_counts,
                "pipelines": {
                    "recent_count": pipeline_count,
                    "latest": {
                        "id": latest_pipeline.id,
                        "status": latest_pipeline.status,
                        "created_at": latest_pipeline.created_at
                    } if latest_pipeline else None
                }
            }
            print(json.dumps(output, indent=2))
        else:
            # Friendly output
            print(f"\n{'='*60}")
            print(f"Branch: {branch_name}")
            print(f"{'='*60}\n")
            
            # Branch status
            status_parts = []
            if info["exists_locally"]:
                status_parts.append("✓ Local")
            if info["exists_remote"]:
                status_parts.append("✓ Remote")
            if info.get("protected"):
                status_parts.append("🔒 Protected")
            if info.get("merged"):
                status_parts.append("✅ Merged")
            
            if status_parts:
                print(f"Status: {' | '.join(status_parts)}")
            
            # Last commit
            if info["last_commit"]:
                commit = info["last_commit"]
                print(f"\nLast Commit:")
                print(f"  {commit['sha']} - {commit['message']}")
                print(f"  by {commit['author']} ({commit['age']})")
            
            # Ahead/behind
            if info["ahead_behind"]:
                ab = info["ahead_behind"]
                print(f"\nCompared to {ab['base']}:")
                print(f"  ↑ {ab['ahead']} ahead | ↓ {ab['behind']} behind")
            
            # Related resources
            print(f"\nRelated Resources:")
            print(f"  Merge Requests: {mr_counts['total']} total", end="")
            if mr_counts['opened'] > 0:
                print(f" ({mr_counts['opened']} open)", end="")
            print()
            
            print(f"  Pipelines: {pipeline_count} recent", end="")
            if latest_pipeline:
                status_icon = {
                    "success": "✅",
                    "failed": "❌",
                    "running": "🔄"
                }.get(latest_pipeline.status, "❓")
                print(f" (latest: {status_icon} {latest_pipeline.status})", end="")
            print()
            
            # Quick actions
            print(f"\nQuick Actions:")
            print(f"  gl branch {branch_name} mr         # Show merge requests")
            print(f"  gl branch {branch_name} pipeline   # Show pipelines")
            print(f"  gl branch {branch_name} commit     # Show recent commits")
            
            # URLs
            if info.get("web_url"):
                print(f"\nBRANCH_URL: {info['web_url']}")
    
    def show_branch_mrs(self, cli, branch_name, args, output_format):
        """Show MRs for a branch"""
        mrs = cli.explorer.get_mrs_for_branch(branch_name, args.state)
        
        if not mrs:
            # When using --latest, silently exit with error code (for scripting)
            # Otherwise show a message for interactive use
            if not args.latest:
                print(f"No {args.state} merge requests found for branch '{branch_name}'")
            import sys
            sys.exit(1)  # Exit with error code for scripting
        
        # Handle --latest flag
        if args.latest:
            # Sort by created_at to get the most recent
            mrs = sorted(mrs, key=lambda x: x['created_at'], reverse=True)[:1]
        else:
            # Limit results normally
            mrs = mrs[:args.limit]
        
        if output_format == "json":
            print(json.dumps({"merge_requests": mrs}, indent=2))
        else:
            print(f"\nMerge Requests for branch '{branch_name}' (state: {args.state}):")
            print("-" * 80)
            
            for mr in mrs:
                state_icon = {
                    "opened": "📂",
                    "merged": "✅",
                    "closed": "📕"
                }.get(mr['state'], "❓")
                
                print(f"\n{state_icon} !{mr['iid']}: {mr['title']}")
                print(f"   Author: @{mr['author']}")
                print(f"   Target: {mr['target_branch']}")
                print(f"   Created: {mr['created_at'][:10]}")
                if mr['pipeline_id']:
                    pipeline_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄"
                    }.get(mr['pipeline_status'], "❓")
                    print(f"   Pipeline: #{mr['pipeline_id']} {pipeline_icon} {mr['pipeline_status']}")
                print(f"   MR_URL: {mr['web_url']}")
    
    def show_branch_pipelines(self, cli, branch_name, args, output_format):
        """Show recent pipelines for a branch"""
        try:
            pipelines = cli.explorer.project.pipelines.list(
                ref=branch_name,
                per_page=args.limit
            )
            
            if not pipelines:
                print(f"No pipelines found for branch '{branch_name}'")
                return
            
            if output_format == "json":
                output = {
                    "pipelines": [
                        {
                            "id": p.id,
                            "status": p.status,
                            "source": p.source,
                            "created_at": p.created_at,
                            "user": p.user.get('username') if hasattr(p, 'user') and p.user else None,
                            "web_url": p.web_url
                        }
                        for p in pipelines
                    ]
                }
                print(json.dumps(output, indent=2))
            else:
                print(f"\nRecent Pipelines for branch '{branch_name}':")
                print("-" * 80)
                
                for p in pipelines:
                    status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "pending": "⏳",
                        "canceled": "🚫"
                    }.get(p.status, "❓")
                    
                    user_str = f" by @{p.user['username']}" if hasattr(p, 'user') and p.user else ""
                    created = p.created_at[:19].replace('T', ' ')
                    
                    print(f"\n{status_icon} Pipeline #{p.id} - {p.status}")
                    print(f"   Source: {p.source}{user_str}")
                    print(f"   Created: {created}")
                    print(f"   PIPELINE_URL: {p.web_url}")
                    print(f"   PIPELINE_ID: {p.id}")
        
        except Exception as e:
            print(f"Error fetching pipelines: {e}")
    
    def show_branch_commits(self, cli, branch_name, args, output_format):
        """Show recent commits on branch"""
        try:
            # Get commits from git log
            result = subprocess.run(
                ["git", "log", f"--max-count={args.limit}", 
                 "--format=%H|%s|%an|%ae|%ar", branch_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout:
                print(f"No commits found on branch '{branch_name}'")
                return
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        "sha": parts[0][:8],
                        "message": parts[1],
                        "author": parts[2],
                        "email": parts[3],
                        "age": parts[4]
                    })
            
            if output_format == "json":
                print(json.dumps({"commits": commits}, indent=2))
            else:
                print(f"\nRecent Commits on branch '{branch_name}':")
                print("-" * 80)
                
                for commit in commits:
                    print(f"\n{commit['sha']} - {commit['message'][:60]}")
                    print(f"   by {commit['author']} ({commit['age']})")
        
        except Exception as e:
            print(f"Error fetching commits: {e}")