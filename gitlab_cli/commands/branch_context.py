# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Branch context commands - show branch info and related resources"""


import subprocess
import json
import webbrowser
import urllib.parse
from datetime import datetime
from typing import Optional
from .base import BaseCommand


class BranchCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "branch_or_resource",
            nargs="?",
            help="Branch name or resource type (mr, pipeline, commit). Defaults to current branch info.",
        )

        parser.add_argument(
            "resource",
            nargs="?",
            choices=["mr", "pipeline", "commit", "info", "approvals", "mr-approvals"],
            help="Resource to show for branch (when branch name is specified)",
        )

        parser.add_argument(
            "--create-mr", action="store_true", help="Create a new MR from this branch"
        )
        parser.add_argument(
            "--open", action="store_true", help="Open the branch in web browser"
        )
        parser.add_argument(
            "--open-mr", action="store_true", help="Open the MR in web browser"
        )

        parser.add_argument(
            "--state",
            choices=["opened", "merged", "closed", "all"],
            default="opened",
            help="Filter by state (for MRs)",
        )
        parser.add_argument(
            "--latest", action="store_true", help="Show only the latest/most recent MR"
        )
        parser.add_argument(
            "--push",
            action="store_true",
            help="Show only push pipelines (exclude merge_request_event, etc.)",
        )
        parser.add_argument(
            "--source",
            choices=[
                "push",
                "web",
                "trigger",
                "schedule",
                "api",
                "external",
                "pipeline",
                "chat",
                "merge_request_event",
            ],
            help="Filter pipelines by source type",
        )
        parser.add_argument(
            "--status",
            choices=[
                "success",
                "failed",
                "running",
                "pending",
                "canceled",
                "skipped",
                "manual",
                "created",
            ],
            help="Filter pipelines by status",
        )
        parser.add_argument(
            "--passed",
            action="store_true",
            help="Show only passed/successful pipelines (shortcut for --status success)",
        )
        parser.add_argument(
            "--failed",
            action="store_true",
            help="Show only failed pipelines (shortcut for --status failed)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Limit number of results (default: 10)",
        )
        parser.add_argument(
            "--stage-url",
            action="store_true",
            help="Show stage environment URL for the branch",
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def get_current_branch(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except:
            return None

    def get_branch_info(self, cli, branch_name: str) -> dict:
        info = {
            "name": branch_name,
            "exists_locally": False,
            "exists_remote": False,
            "last_commit": None,
            "ahead_behind": None,
            "age": None,
            "author": None,
        }
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                capture_output=True,
                text=True,
            )
            info["exists_locally"] = result.returncode == 0
        except:
            pass
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%an|%ae|%ar", branch_name],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                parts = result.stdout.strip().split("|")
                if len(parts) >= 5:
                    info["last_commit"] = {
                        "sha": parts[0][:8],
                        "message": parts[1][:60],
                        "author": parts[2],
                        "email": parts[3],
                        "age": parts[4],
                    }
                    info["age"] = parts[4]
                    info["author"] = parts[2]
        except:
            pass
        try:
            # Try to find the main branch
            for main_branch in ["main", "master"]:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", f"origin/{main_branch}"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:

                    result = subprocess.run(
                        [
                            "git",
                            "rev-list",
                            "--left-right",
                            "--count",
                            f"origin/{main_branch}...{branch_name}",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if result.stdout:
                        behind, ahead = result.stdout.strip().split("\t")
                        info["ahead_behind"] = {
                            "ahead": int(ahead),
                            "behind": int(behind),
                            "base": main_branch,
                        }
                    break
        except:
            pass
        try:
            branches = cli.explorer.project.branches.list(search=branch_name)
            for branch in branches:
                if branch.name == branch_name:
                    info["exists_remote"] = True
                    info["protected"] = branch.protected
                    info["merged"] = branch.merged
                    info["web_url"] = (
                        f"{cli.explorer.project.web_url}/-/tree/{branch_name}"
                    )
                    if hasattr(branch, "commit"):
                        info["remote_commit"] = branch.commit["id"][:8]
                    break
        except:
            pass

        return info

    def handle(self, cli, args, output_format):

        branch_name = None
        resource = None
        resource_keywords = [
            "mr",
            "mrs",
            "merge-request",
            "merge-requests",
            "mr-approvals",
            "approvals",
            "pipeline",
            "pipelines",
            "commit",
            "commits",
            "info",
        ]

        if (
            args.branch_or_resource
            and args.branch_or_resource.lower() in resource_keywords
        ):
            resource = args.branch_or_resource.lower()
            if resource in ["mrs", "merge-requests"]:
                resource = "mr"
            elif resource in ["pipelines"]:
                resource = "pipeline"
            elif resource in ["commits"]:
                resource = "commit"

            branch_name = self.get_current_branch()
            if not branch_name:
                print("Error: Not in a git repository or cannot determine branch")
                return
        elif args.branch_or_resource:
            branch_name = args.branch_or_resource
            resource = args.resource
        else:
            branch_name = self.get_current_branch()
            if not branch_name:
                print("Error: Not in a git repository or cannot determine branch")
                return
        if args.create_mr:
            self.create_mr_for_branch(cli, branch_name, args, output_format)
            return
        if args.open:
            self.open_branch_in_browser(cli, branch_name)
            return
        if args.open_mr:
            self.open_mr_in_browser(cli, branch_name)
            return
        if args.stage_url:
            stage_url = f"https://{branch_name}.stage.rechargeapps.net/config"
            print(f"STAGE_URL: {stage_url}")
            return

        # If --latest flag is used without specifying 'mr' resource, show latest MR
        if args.latest and not resource:
            resource = "mr"

        # If no resource specified, show branch info
        if not resource or resource == "info":
            self.show_branch_info(cli, branch_name, output_format)
        elif resource == "mr":
            self.show_branch_mrs(cli, branch_name, args, output_format)
        elif resource in ["mr-approvals", "approvals"]:
            self.show_branch_mr_approvals(cli, branch_name, args, output_format)
        elif resource == "pipeline":
            self.show_branch_pipelines(cli, branch_name, args, output_format)
        elif resource == "commit":
            self.show_branch_commits(cli, branch_name, args, output_format)

    def show_branch_info(self, cli, branch_name, output_format):
        info = self.get_branch_info(cli, branch_name)
        try:
            mrs = cli.explorer.get_mrs_for_branch(branch_name, "all")
            mr_counts = {
                "total": len(mrs),
                "opened": len([m for m in mrs if m["state"] == "opened"]),
                "merged": len([m for m in mrs if m["state"] == "merged"]),
                "closed": len([m for m in mrs if m["state"] == "closed"]),
            }
            pipelines = cli.explorer.project.pipelines.list(ref=branch_name, per_page=5)
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
                    "latest": (
                        {
                            "id": latest_pipeline.id,
                            "status": latest_pipeline.status,
                            "created_at": latest_pipeline.created_at,
                        }
                        if latest_pipeline
                        else None
                    ),
                },
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
                status_parts.append("Merged")

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
            if mr_counts["opened"] > 0:
                print(f" ({mr_counts['opened']} open)", end="")
            print()

            print(f"  Pipelines: {pipeline_count} recent", end="")
            if latest_pipeline:
                status_icon = {
                    "success": "[SUCCESS]",
                    "failed": "[FAILED]",
                    "running": "[RUNNING]",
                }.get(latest_pipeline.status, "[UNKNOWN]")
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
        mrs = cli.explorer.get_mrs_for_branch(branch_name, args.state)

        if not mrs:
            # When using --latest, silently exit with error code (for scripting)
            # Otherwise show a message for interactive use
            if not args.latest:
                print(
                    f"No {args.state} merge requests found for branch '{branch_name}'"
                )
            import sys

            sys.exit(1)  # Exit with error code for scripting
        if args.latest:

            mrs = sorted(mrs, key=lambda x: x["created_at"], reverse=True)[:1]
        else:
            # Limit results normally
            mrs = mrs[: args.limit]

        if output_format == "json":
            print(json.dumps({"merge_requests": mrs}, indent=2))
        else:
            print(f"\nMerge Requests for branch '{branch_name}' (state: {args.state}):")
            print("-" * 80)

            for mr in mrs:
                print(f"\n!{mr['iid']}: {mr['title']}")
                print(f"   State: {mr['state']}")
                print(f"   Author: @{mr['author']}")
                print(f"   Target: {mr['target_branch']}")
                print(f"   Created: {mr['created_at'][:10]}")
                if mr["pipeline_id"]:
                    print(f"   Pipeline: #{mr['pipeline_id']} {mr['pipeline_status']}")
                print(f"   MR_ID: {mr['iid']}")
                print(f"   MR_URL: {mr['web_url']}")

    def show_branch_mr_approvals(self, cli, branch_name, args, output_format):
        mrs = cli.explorer.get_mrs_for_branch(branch_name, "opened")
        if not mrs:
            print(f"No open merge requests found for branch '{branch_name}'")
            return

        mr_data = mrs[0]
        mr_id = mr_data["iid"]

        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)
            approvals = mr.approvals.get()

            approved_by = []
            if hasattr(approvals, "approved_by") and approvals.approved_by:
                approved_by = [u["user"]["username"] for u in approvals.approved_by]

            approval_rules = []
            try:
                rules = mr.approval_rules.list()
                for rule in rules:
                    rule_data = {
                        "name": rule.name,
                        "approvals_required": rule.approvals_required,
                        "approved_by": [u["username"] for u in getattr(rule, "approved_by", [])],
                        "eligible_approvers": [u["username"] for u in getattr(rule, "eligible_approvers", [])],
                    }
                    approval_rules.append(rule_data)
            except:
                pass

            if output_format == "json":
                output = {
                    "mr_iid": mr.iid,
                    "title": mr.title,
                    "approved": approvals.approved,
                    "approvals_required": approvals.approvals_required,
                    "approvals_left": approvals.approvals_left,
                    "approved_by": approved_by,
                    "approval_rules": approval_rules,
                }
                print(json.dumps(output, indent=2))
            else:
                print(f"\nApprovals for MR !{mr.iid}: {mr.title}")
                print("-" * 80)

                status = "Approved" if approvals.approved else f"{approvals.approvals_left} more needed"
                print(f"\nStatus: {status}")
                print(f"Required: {approvals.approvals_required}")

                if approved_by:
                    print(f"Approved by: {', '.join(['@' + u for u in approved_by])}")
                else:
                    print("Approved by: (none)")

                if approval_rules:
                    print(f"\nApproval Rules:")
                    for rule in approval_rules:
                        rule_approved = len(rule["approved_by"])
                        rule_status = f"{rule_approved}/{rule['approvals_required']}"
                        print(f"  {rule['name']}: {rule_status}")
                        if rule["approved_by"]:
                            print(f"    Approved: {', '.join(['@' + u for u in rule['approved_by']])}")
                        if rule["eligible_approvers"]:
                            print(f"    Eligible: {', '.join(['@' + u for u in rule['eligible_approvers'][:5]])}")
                            if len(rule["eligible_approvers"]) > 5:
                                print(f"              ... and {len(rule['eligible_approvers']) - 5} more")

                print(f"\nMR_URL: {mr.web_url}")

        except Exception as e:
            print(f"Error fetching approvals: {e}")

    def show_branch_pipelines(self, cli, branch_name, args, output_format):
        try:

            list_params = {
                "ref": branch_name,
                "order_by": "id",
                "sort": "desc",
                "per_page": args.limit * 2,  # Get extra to account for filtering
            }
            if args.push:
                list_params["source"] = "push"
            elif hasattr(args, "source") and args.source:
                list_params["source"] = args.source
            status_filter = None
            if hasattr(args, "passed") and args.passed:
                status_filter = "success"
            elif hasattr(args, "failed") and args.failed:
                status_filter = "failed"
            elif hasattr(args, "status") and args.status:
                status_filter = args.status

            if status_filter:
                list_params["status"] = status_filter

            pipelines = cli.explorer.project.pipelines.list(
                **list_params, get_all=False
            )
            filtered_pipelines = []
            for p in pipelines:
                # Skip pipelines created by GitLab Security Policy Bot
                if hasattr(p, "user") and p.user:
                    username = p.user.get("username", "")
                    name = p.user.get("name", "")
                    if (
                        "security-policy-bot" in username.lower()
                        or "security policy bot" in name.lower()
                    ):
                        continue
                filtered_pipelines.append(p)

                # Stop when we have enough
                if len(filtered_pipelines) >= args.limit:
                    break

            pipelines = filtered_pipelines

            if not pipelines:
                filters = []
                if args.push:
                    filters.append("push only")
                elif hasattr(args, "source") and args.source:
                    filters.append(f"source: {args.source}")
                if hasattr(args, "passed") and args.passed:
                    filters.append("passed only")
                elif hasattr(args, "failed") and args.failed:
                    filters.append("failed only")
                elif hasattr(args, "status") and args.status:
                    filters.append(f"status: {args.status}")

                filter_msg = f" ({', '.join(filters)})" if filters else ""
                print(f"No pipelines found for branch '{branch_name}'{filter_msg}")
                return

            if output_format == "json":
                output = {
                    "pipelines": [
                        {
                            "id": p.id,
                            "status": p.status,
                            "source": p.source,
                            "created_at": p.created_at,
                            "user": (
                                p.user.get("username")
                                if hasattr(p, "user") and p.user
                                else None
                            ),
                            "web_url": p.web_url,
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
                        "success": "[SUCCESS]",
                        "failed": "[FAILED]",
                        "running": "[RUNNING]",
                        "pending": "[PENDING]",
                        "canceled": "[CANCELED]",
                    }.get(p.status, "[UNKNOWN]")
                    user_str = ""
                    if hasattr(p, "user") and p.user:
                        username = p.user.get("username", "unknown")
                        name = p.user.get("name", "")
                        if name and name != username:
                            user_str = f"@{username} ({name})"
                        else:
                            user_str = f"@{username}"

                    created = p.created_at[:19].replace("T", " ")

                    print(f"\n{status_icon} Pipeline #{p.id} - {p.status}")
                    print(f"   Source: {p.source}")
                    print(
                        f"   Created by: {user_str}"
                        if user_str
                        else "   Created by: Unknown"
                    )
                    print(f"   Created at: {created}")
                    print(f"   PIPELINE_URL: {p.web_url}")
                    print(f"   PIPELINE_ID: {p.id}")

        except Exception as e:
            print(f"Error fetching pipelines: {e}")

    def show_branch_commits(self, cli, branch_name, args, output_format):
        try:

            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"--max-count={args.limit}",
                    "--format=%H|%s|%an|%ae|%ar",
                    branch_name,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if not result.stdout:
                print(f"No commits found on branch '{branch_name}'")
                return

            commits = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 5:
                    commits.append(
                        {
                            "sha": parts[0][:8],
                            "message": parts[1],
                            "author": parts[2],
                            "email": parts[3],
                            "age": parts[4],
                        }
                    )

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

    def create_mr_for_branch(self, cli, branch_name, args, output_format):
        import urllib.parse
        import webbrowser

        gitlab_url = cli.config.gitlab_url
        project_path = cli.config.project_path

        if not gitlab_url or not project_path:
            print("Error: GitLab URL or project path not configured")
            return
        # URL format: https://gitlab.example.com/group/project/-/merge_requests/new?merge_request[source_branch]=branch-name
        base_url = f"{gitlab_url}/{project_path}/-/merge_requests/new"
        params = {"merge_request[source_branch]": branch_name}
        # Don't set target branch - let GitLab use the repo's default
        query_string = urllib.parse.urlencode(params)
        full_url = f"{base_url}?{query_string}"

        if output_format == "json":
            print(
                json.dumps(
                    {"action": "create_mr", "branch": branch_name, "url": full_url},
                    indent=2,
                )
            )
        else:
            print(f"\nCreate MR for branch '{branch_name}':")
            print("-" * 80)
            print(f"\nMR_CREATE_URL: {full_url}")

            # Open the URL in the default browser
            try:
                webbrowser.open(full_url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}")

    def open_branch_in_browser(self, cli, branch_name):
        try:

            project = cli.explorer.project
            project_url = project.web_url

            # URL encode the branch name for safety
            encoded_branch = urllib.parse.quote(branch_name, safe="")

            # Construct the branch URL
            branch_url = f"{project_url}/-/tree/{encoded_branch}"

            print(f"Opening branch '{branch_name}' in browser...")
            print(f"URL: {branch_url}")

            # Open the URL in the default browser
            try:
                webbrowser.open(branch_url)
                print("Browser opened successfully")
            except Exception as e:
                print(f"Could not open browser: {e}")
                print(f"You can manually open: {branch_url}")

        except Exception as e:
            print(f"Error opening branch in browser: {e}")

    def open_mr_in_browser(self, cli, branch_name):
        try:

            mrs = cli.explorer.get_mrs_for_branch(branch_name, "opened")

            if not mrs:
                print(f"No open MRs found for branch '{branch_name}'")
                print("Tip: Use 'gl branch --create-mr' to create one")
                return

            # Open the first/latest MR
            mr = mrs[0]
            mr_url = mr["web_url"]
            print(f"Opening MR !{mr['iid']}: {mr['title']}")
            print(f"MR_URL: {mr_url}")

            try:
                webbrowser.open(mr_url)
                print("Browser opened successfully")
            except Exception as e:
                print(f"Could not open browser: {e}")
                print(f"You can manually open: {mr_url}")

        except Exception as e:
            print(f"Error opening MR in browser: {e}")

