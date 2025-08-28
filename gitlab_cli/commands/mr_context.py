"""MR context commands - show MR info and related resources with diff support"""

import json
import re
from typing import List, Dict, Any
from .base import BaseCommand


class MRContextCommand(BaseCommand):
    """Handle MR context commands with rich diff support"""
    
    def add_arguments(self, parser):
        """Add MR-specific arguments to parser"""
        parser.add_argument(
            "mr_id",
            help="MR ID or IID"
        )
        
        # Subcommands for MR context
        parser.add_argument(
            "resource",
            nargs="?",
            choices=["diff", "pipeline", "commit", "discussion", "approve", "info"],
            help="Resource to show for MR (diff, pipeline, commit, discussion, approve, info)"
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
        
        # Other options
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Limit number of results (default: 20)"
        )
        parser.add_argument(
            "--format",
            choices=["friendly", "table", "json"],
            help="Output format"
        )
    
    def get_diff_view_preference(self, cli, args):
        """Get diff view preference from args or config"""
        if args.view:
            return args.view
        
        # Check config for default diff view
        config_view = getattr(cli.config, 'diff_view', 'unified')
        if not config_view:
            config_view = 'unified'
        return config_view
    
    def handle(self, cli, args, output_format):
        """Handle MR commands"""
        mr_id = args.mr_id
        
        # If no resource specified, show MR info
        if not args.resource or args.resource == "info":
            self.show_mr_info(cli, mr_id, output_format)
        elif args.resource == "diff":
            self.show_mr_diff(cli, mr_id, args, output_format)
        elif args.resource == "pipeline":
            self.show_mr_pipelines(cli, mr_id, args, output_format)
        elif args.resource == "commit":
            self.show_mr_commits(cli, mr_id, args, output_format)
        elif args.resource == "discussion":
            self.show_mr_discussions(cli, mr_id, args, output_format)
        elif args.resource == "approve":
            self.handle_mr_approval(cli, mr_id, args, output_format)
    
    def show_mr_info(self, cli, mr_id, output_format):
        """Show comprehensive MR information"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            
            # Get additional details
            changes = mr.changes()
            approvals = None
            try:
                approvals = mr.approvals.get()
            except:
                pass
            
            if output_format == "json":
                output = {
                    "id": mr.id,
                    "iid": mr.iid,
                    "title": mr.title,
                    "state": mr.state,
                    "author": mr.author,
                    "source_branch": mr.source_branch,
                    "target_branch": mr.target_branch,
                    "created_at": mr.created_at,
                    "updated_at": mr.updated_at,
                    "merge_status": mr.merge_status if hasattr(mr, 'merge_status') else None,
                    "has_conflicts": mr.has_conflicts if hasattr(mr, 'has_conflicts') else None,
                    "changes_count": len(changes.get('changes', [])),
                    "additions": sum(c.get('added_lines', 0) for c in changes.get('changes', [])),
                    "deletions": sum(c.get('removed_lines', 0) for c in changes.get('changes', [])),
                    "web_url": mr.web_url
                }
                if approvals:
                    output["approvals"] = {
                        "approved": approvals.approved,
                        "approvals_required": approvals.approvals_required,
                        "approvals_left": approvals.approvals_left
                    }
                print(json.dumps(output, indent=2))
            else:
                # Friendly output
                print(f"\n{'='*80}")
                print(f"MR !{mr.iid}: {mr.title}")
                print(f"{'='*80}\n")
                
                # Status
                state_icon = {
                    "opened": "📂",
                    "merged": "✅",
                    "closed": "📕"
                }.get(mr.state, "❓")
                print(f"Status: {state_icon} {mr.state.upper()}")
                
                if mr.draft if hasattr(mr, 'draft') else mr.work_in_progress:
                    print("        📝 DRAFT")
                
                # Author and assignees
                print(f"Author: @{mr.author['username']} ({mr.author['name']})")
                if hasattr(mr, 'assignees') and mr.assignees:
                    assignees = ", ".join([f"@{a['username']}" for a in mr.assignees])
                    print(f"Assignees: {assignees}")
                
                # Branches
                print(f"\nBranches: {mr.source_branch} → {mr.target_branch}")
                
                # Merge status
                if mr.state == "opened":
                    merge_status = getattr(mr, 'merge_status', 'unknown')
                    if merge_status == 'can_be_merged':
                        print("Merge Status: ✅ Can be merged")
                    elif merge_status == 'cannot_be_merged':
                        print("Merge Status: ❌ Has conflicts")
                    else:
                        print(f"Merge Status: {merge_status}")
                
                # Approvals
                if approvals:
                    if approvals.approved:
                        print(f"Approvals: ✅ Approved ({approvals.approvals_required} required)")
                    else:
                        print(f"Approvals: ⏳ {approvals.approvals_left} more needed ({approvals.approvals_required} required)")
                
                # Changes summary
                changes_list = changes.get('changes', [])
                additions = sum(c.get('added_lines', 0) for c in changes_list)
                deletions = sum(c.get('removed_lines', 0) for c in changes_list)
                print(f"\nChanges: {len(changes_list)} files (+{additions} -{deletions})")
                
                # Recent pipeline
                if hasattr(mr, 'head_pipeline') and mr.head_pipeline:
                    p = mr.head_pipeline
                    status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄"
                    }.get(p['status'], "❓")
                    print(f"\nLatest Pipeline: {status_icon} {p['status']} (#{p['id']})")
                
                # Quick actions
                print(f"\nQuick Actions:")
                print(f"  gl mr {mr.iid} diff         # Show diff")
                print(f"  gl mr {mr.iid} pipeline     # Show pipelines")
                print(f"  gl mr {mr.iid} commit       # Show commits")
                print(f"  gl mr {mr.iid} discussion   # Show discussions")
                
                # URL
                print(f"\nMR_URL: {mr.web_url}")
                
        except Exception as e:
            print(f"Error fetching MR {mr_id}: {e}")
    
    def show_mr_diff(self, cli, mr_id, args, output_format):
        """Show MR diff with various view modes"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            changes = mr.changes()
            
            if args.name_only:
                # Just show file names
                for change in changes.get('changes', []):
                    print(change['new_path'])
                return
            
            if args.stats:
                # Show statistics
                self.show_diff_stats(changes)
                return
            
            # Get view preference
            view_mode = self.get_diff_view_preference(cli, args)
            
            # Filter by file if specified
            changes_list = changes.get('changes', [])
            if args.file:
                changes_list = [c for c in changes_list if args.file in c['new_path']]
                if not changes_list:
                    print(f"No changes found for file: {args.file}")
                    return
            
            # Display diffs based on view mode
            for change in changes_list:
                if view_mode == "split":
                    self.show_split_diff(change, args)
                elif view_mode == "inline":
                    self.show_inline_diff(change, args)
                else:  # unified
                    self.show_unified_diff(change, args)
                
                print()  # Blank line between files
                
        except Exception as e:
            print(f"Error fetching diff for MR {mr_id}: {e}")
    
    def show_diff_stats(self, changes):
        """Show diff statistics"""
        changes_list = changes.get('changes', [])
        total_additions = 0
        total_deletions = 0
        
        print(f"\n{'='*80}")
        print("Diff Statistics")
        print(f"{'='*80}\n")
        
        for change in changes_list:
            additions = change.get('added_lines', 0)
            deletions = change.get('removed_lines', 0)
            total_additions += additions
            total_deletions += deletions
            
            # Create visual bar
            max_width = 50
            total_changes = additions + deletions
            if total_changes > 0:
                add_width = int((additions / total_changes) * max_width)
                del_width = max_width - add_width
                bar = "+" * add_width + "-" * del_width
            else:
                bar = ""
            
            file_name = change['new_path']
            if len(file_name) > 40:
                file_name = "..." + file_name[-37:]
            
            print(f"{file_name:40} | {additions:4}+ {deletions:4}- |{bar}")
        
        print(f"\n{len(changes_list)} files changed, {total_additions} insertions(+), {total_deletions} deletions(-)")
    
    def show_unified_diff(self, change, args):
        """Show unified diff view (traditional git diff)"""
        file_path = change['new_path']
        old_path = change['old_path']
        
        if not args.no_color:
            print(f"\033[1m--- {old_path}\033[0m")
            print(f"\033[1m+++ {file_path}\033[0m")
        else:
            print(f"--- {old_path}")
            print(f"+++ {file_path}")
        
        diff = change.get('diff', '')
        if not diff:
            print("(No changes or binary file)")
            return
        
        lines = diff.split('\n')
        for line in lines:
            if line.startswith('@@'):
                if not args.no_color:
                    print(f"\033[36m{line}\033[0m")  # Cyan for hunks
                else:
                    print(line)
            elif line.startswith('+'):
                if not args.no_color:
                    print(f"\033[32m{line}\033[0m")  # Green for additions
                else:
                    print(line)
            elif line.startswith('-'):
                if not args.no_color:
                    print(f"\033[31m{line}\033[0m")  # Red for deletions
                else:
                    print(line)
            else:
                print(line)
    
    def show_inline_diff(self, change, args):
        """Show inline diff view with changes highlighted in context"""
        file_path = change['new_path']
        
        print(f"\n{'='*80}")
        print(f"File: {file_path}")
        print(f"{'='*80}")
        
        diff = change.get('diff', '')
        if not diff:
            print("(No changes or binary file)")
            return
        
        lines = diff.split('\n')
        current_line_old = 0
        current_line_new = 0
        
        for line in lines:
            if line.startswith('@@'):
                # Parse hunk header
                match = re.match(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
                if match:
                    current_line_old = int(match.group(1))
                    current_line_new = int(match.group(2))
                
                if not args.no_color:
                    print(f"\n\033[36m{line}\033[0m")
                else:
                    print(f"\n{line}")
            elif line.startswith('-'):
                if not args.no_color:
                    print(f"{current_line_old:4} \033[31m- {line[1:]}\033[0m")
                else:
                    print(f"{current_line_old:4} - {line[1:]}")
                current_line_old += 1
            elif line.startswith('+'):
                if not args.no_color:
                    print(f"{current_line_new:4} \033[32m+ {line[1:]}\033[0m")
                else:
                    print(f"{current_line_new:4} + {line[1:]}")
                current_line_new += 1
            else:
                # Context line
                print(f"{current_line_new:4}   {line[1:] if line else ''}")
                current_line_old += 1
                current_line_new += 1
    
    def show_split_diff(self, change, args):
        """Show side-by-side diff view"""
        file_path = change['new_path']
        
        print(f"\n{'='*80}")
        print(f"File: {file_path}")
        print(f"{'='*80}")
        print(f"{'OLD':<39} | {'NEW':<39}")
        print("-" * 79)
        
        diff = change.get('diff', '')
        if not diff:
            print("(No changes or binary file)")
            return
        
        # Parse diff into old and new sections
        lines = diff.split('\n')
        old_lines = []
        new_lines = []
        
        for line in lines:
            if line.startswith('@@'):
                # Sync point - show hunk header
                if old_lines or new_lines:
                    self._print_split_lines(old_lines, new_lines, args)
                    old_lines = []
                    new_lines = []
                print(f"\n{line}")
            elif line.startswith('-'):
                old_lines.append(line[1:])
            elif line.startswith('+'):
                new_lines.append(line[1:])
            else:
                # Context line - add to both
                if old_lines or new_lines:
                    self._print_split_lines(old_lines, new_lines, args)
                    old_lines = []
                    new_lines = []
                # Print context line
                content = line[1:] if line else ''
                if len(content) > 38:
                    content = content[:35] + "..."
                print(f"{content:<39} | {content:<39}")
        
        # Print any remaining lines
        if old_lines or new_lines:
            self._print_split_lines(old_lines, new_lines, args)
    
    def _print_split_lines(self, old_lines, new_lines, args):
        """Helper to print side-by-side diff lines"""
        max_len = max(len(old_lines), len(new_lines))
        
        for i in range(max_len):
            old_line = old_lines[i] if i < len(old_lines) else ""
            new_line = new_lines[i] if i < len(new_lines) else ""
            
            # Truncate long lines
            if len(old_line) > 38:
                old_line = old_line[:35] + "..."
            if len(new_line) > 38:
                new_line = new_line[:35] + "..."
            
            if not args.no_color:
                if i < len(old_lines):
                    old_display = f"\033[31m{old_line:<39}\033[0m"
                else:
                    old_display = " " * 39
                
                if i < len(new_lines):
                    new_display = f"\033[32m{new_line:<39}\033[0m"
                else:
                    new_display = " " * 39
                
                print(f"{old_display} | {new_display}")
            else:
                print(f"{old_line:<39} | {new_line:<39}")
    
    def show_mr_pipelines(self, cli, mr_id, args, output_format):
        """Show pipelines for MR"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            pipelines = mr.pipelines()
            
            if not pipelines:
                print(f"No pipelines found for MR !{mr.iid}")
                return
            
            # Limit results
            pipelines = pipelines[:args.limit]
            
            if output_format == "json":
                print(json.dumps({"pipelines": pipelines}, indent=2))
            else:
                print(f"\nPipelines for MR !{mr.iid}:")
                print("-" * 80)
                
                for p in pipelines:
                    status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "pending": "⏳"
                    }.get(p['status'], "❓")
                    
                    created = p['created_at'][:19].replace('T', ' ')
                    
                    print(f"\n{status_icon} Pipeline #{p['id']} - {p['status']}")
                    print(f"   SHA: {p['sha'][:8]}")
                    print(f"   Created: {created}")
                    print(f"   PIPELINE_ID: {p['id']}")
                    print(f"   PIPELINE_URL: {p['web_url']}")
                    
        except Exception as e:
            print(f"Error fetching pipelines for MR {mr_id}: {e}")
    
    def show_mr_commits(self, cli, mr_id, args, output_format):
        """Show commits in MR"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            commits = mr.commits()
            
            if not commits:
                print(f"No commits found for MR !{mr.iid}")
                return
            
            # Limit results
            commits = commits[:args.limit]
            
            if output_format == "json":
                output = {
                    "commits": [
                        {
                            "id": c.id[:8],
                            "message": c.message,
                            "author_name": c.author_name,
                            "author_email": c.author_email,
                            "created_at": c.created_at
                        }
                        for c in commits
                    ]
                }
                print(json.dumps(output, indent=2))
            else:
                print(f"\nCommits in MR !{mr.iid}:")
                print("-" * 80)
                
                for c in commits:
                    message_first_line = c.message.split('\n')[0][:60]
                    print(f"\n{c.id[:8]} - {message_first_line}")
                    print(f"   by {c.author_name} <{c.author_email}>")
                    print(f"   at {c.created_at[:19]}")
                    
        except Exception as e:
            print(f"Error fetching commits for MR {mr_id}: {e}")
    
    def show_mr_discussions(self, cli, mr_id, args, output_format):
        """Show discussions/comments on MR"""
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            discussions = mr.discussions.list(all=True)
            
            if not discussions:
                print(f"No discussions found for MR !{mr.iid}")
                return
            
            if output_format == "json":
                output = {
                    "discussions": [
                        {
                            "id": d.id,
                            "notes": [
                                {
                                    "author": n['author']['username'],
                                    "body": n['body'],
                                    "created_at": n['created_at']
                                }
                                for n in d.notes
                            ]
                        }
                        for d in discussions
                    ]
                }
                print(json.dumps(output, indent=2))
            else:
                print(f"\nDiscussions in MR !{mr.iid}:")
                print("-" * 80)
                
                for d in discussions:
                    for note in d.notes:
                        author = note['author']['username']
                        created = note['created_at'][:19].replace('T', ' ')
                        body = note['body']
                        
                        print(f"\n@{author} ({created}):")
                        for line in body.split('\n'):
                            print(f"  {line}")
                            
        except Exception as e:
            print(f"Error fetching discussions for MR {mr_id}: {e}")
    
    def handle_mr_approval(self, cli, mr_id, args, output_format):
        """Handle MR approval actions"""
        # This would handle approve/unapprove actions
        print(f"Approval handling for MR {mr_id} - to be implemented")