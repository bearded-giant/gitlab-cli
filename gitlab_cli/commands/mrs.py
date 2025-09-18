# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Merge Requests command handler"""

import json
from .base import BaseCommand


class MRsCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            nargs="?",
            help='MR ID(s) or action: <id>, <id,id,...>, or "detail"',
        )
        parser.add_argument("mr_id", nargs="?", help='MR ID (when using "detail")')
        parser.add_argument(
            "--pipelines", action="store_true", help="Show pipeline information"
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Show full information including description",
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def handle(self, cli, args, output_format, action=None, mr_id=None):
        if action == "detail" and mr_id:
            self.handle_detail(cli, mr_id, args, output_format)
        elif action:
            ids = self.parse_ids(action)
            self.handle_list(cli, ids, args, output_format)

    def handle_list(self, cli, ids, args, output_format):
        all_mrs = []

        for mr_id in ids:
            if output_format == "json":
                self.show_mr_json(cli, mr_id, args)
            elif output_format == "table":

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
            self.display_table(all_mrs)

    def display_table(self, mrs):
        print("\nMerge Requests")
        print("-" * 120)
        print(
            f"{'MR':<8} {'State':<10} {'Author':<15} {'Target':<20} {'Created':<12} {'Title':<50}"
        )
        print("-" * 120)
        for mr_info in mrs:
            title = (
                mr_info["title"][:47] + "..."
                if len(mr_info["title"]) > 50
                else mr_info["title"]
            )
            print(
                f"!{mr_info['iid']:<7} {mr_info['state']:<10} {mr_info['author']:<15} "
                f"{mr_info['target']:<20} {mr_info['created']:<12} {title:<50}"
            )
        print("-" * 120)

    def show_mr_summary(self, cli, mr_id, args, output_format):
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)

            status_color = {
                "opened": "\033[92m",  # Green
                "merged": "\033[94m",  # Blue
                "closed": "\033[91m",  # Red
            }.get(mr.state, "")

            print(f"\nMR !{mr.iid}: {mr.title}")
            print(
                f"Status: {status_color}{mr.state.upper()}\033[0m | "
                f"Author: {mr.author['username']} | Target: {mr.target_branch}"
            )
            print(f"Created: {mr.created_at[:10]} | Updated: {mr.updated_at[:10]}")

            # Pipeline status if available
            if hasattr(mr, "head_pipeline") and mr.head_pipeline:
                p_status = mr.head_pipeline.get("status", "unknown")
                p_color = {
                    "success": "\033[92m",
                    "failed": "\033[91m",
                    "running": "\033[93m",
                }.get(p_status, "")
                print(
                    f"Pipeline: {p_color} {p_status}\033[0m (ID: {mr.head_pipeline.get('id')})"
                )

            if args.pipelines:

                pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
                if pipelines:
                    print("\nRecent Pipelines:")
                    for p in pipelines:
                        status_icon = {
                            "success": "[SUCCESS]",
                            "failed": "[FAILED]",
                            "running": "[RUNNING]",
                        }.get(p["status"], "[PENDING]")
                        print(
                            f"  {status_icon} {p['id']} - {p['status']} ({p['created_at'][:16]})"
                        )

            if args.full and mr.description:
                print(f"\nDescription:\n{mr.description[:500]}...")

        except Exception as e:
            print(f"Error fetching MR {mr_id}: {e}")

    def show_mr_json(self, cli, mr_id, args):
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

    def handle_detail(self, cli, mr_id, args, output_format):
        try:
            mr = cli.explorer.project.mergerequests.get(mr_id)

            if output_format == "json":
                self.show_detail_json(cli, mr, mr_id)
            else:
                self.show_detail_friendly(cli, mr, mr_id)

        except Exception as e:
            self.output_error(f"Error fetching MR {mr_id} details: {e}", output_format)

    def show_detail_json(self, cli, mr, mr_id):
        output = {
            "id": mr.id,
            "iid": mr.iid,
            "title": mr.title,
            "description": mr.description,
            "state": mr.state,
            "created_at": mr.created_at,
            "updated_at": mr.updated_at,
            "merged_at": getattr(mr, "merged_at", None),
            "closed_at": getattr(mr, "closed_at", None),
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "author": {
                "username": mr.author["username"],
                "name": mr.author["name"],
            },
            "assignee": getattr(mr, "assignee", None),
            "assignees": getattr(mr, "assignees", []),
            "reviewers": getattr(mr, "reviewers", []),
            "merge_user": getattr(mr, "merge_user", None),
            "merge_status": getattr(mr, "merge_status", None),
            "draft": getattr(mr, "draft", False),
            "work_in_progress": getattr(mr, "work_in_progress", False),
            "merge_when_pipeline_succeeds": getattr(
                mr, "merge_when_pipeline_succeeds", False
            ),
            "has_conflicts": getattr(mr, "has_conflicts", False),
            "blocking_discussions_resolved": getattr(
                mr, "blocking_discussions_resolved", True
            ),
            "approvals_before_merge": getattr(mr, "approvals_before_merge", None),
            "reference": mr.reference,
            "web_url": mr.web_url,
            "labels": mr.labels,
            "milestone": getattr(mr, "milestone", None),
            "head_pipeline": getattr(mr, "head_pipeline", None),
            "diff_stats": {
                "additions": getattr(mr, "additions", 0),
                "deletions": getattr(mr, "deletions", 0),
                "total": getattr(mr, "additions", 0) + getattr(mr, "deletions", 0),
            },
        }
        pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
        if pipelines:
            output["recent_pipelines"] = pipelines

        print(json.dumps(output, indent=2))

    def show_detail_friendly(self, cli, mr, mr_id):
        status_color = {
            "opened": "\033[92m",  # Green
            "merged": "\033[94m",  # Blue
            "closed": "\033[91m",  # Red
        }.get(mr.state, "")

        print(f"\n{'='*60}")
        print(f"MR !{mr.iid}: {mr.title}")
        print(f"{'='*60}\n")

        print(f"Status:       {status_color}{mr.state.upper()}\033[0m")
        if getattr(mr, "draft", False):
            print(f"              DRAFT")

        print(f"Author:       {mr.author['name']} (@{mr.author['username']})")

        if getattr(mr, "assignees", None):
            assignee_names = [f"@{a['username']}" for a in mr.assignees]
            print(f"Assignees:    {', '.join(assignee_names)}")

        if getattr(mr, "reviewers", None):
            reviewer_names = [f"@{r['username']}" for r in mr.reviewers]
            print(f"Reviewers:    {', '.join(reviewer_names)}")

        print(f"\nBranches:")
        print(f"  Source:     {mr.source_branch}")
        print(f"  Target:     {mr.target_branch}")

        print(f"\nTiming:")
        print(f"  Created:    {mr.created_at}")
        print(f"  Updated:    {mr.updated_at}")

        if getattr(mr, "merged_at", None):
            print(f"  Merged:     {mr.merged_at}")
            if getattr(mr, "merge_user", None):
                print(f"  Merged by:  @{mr.merge_user['username']}")
        elif getattr(mr, "closed_at", None):
            print(f"  Closed:     {mr.closed_at}")

        # Merge status for open MRs
        if mr.state == "opened":
            print(f"\nMerge Status:")
            if getattr(mr, "has_conflicts", False):
                print(f"  Has conflicts")
            if getattr(mr, "work_in_progress", False):
                print(f"  Work in progress")
            if getattr(mr, "merge_when_pipeline_succeeds", False):
                print(f"  Set to merge when pipeline succeeds")
            if hasattr(mr, "blocking_discussions_resolved"):
                if mr.blocking_discussions_resolved:
                    print(f"  All discussions resolved")
                else:
                    print(f"  Unresolved discussions")

        # Diff stats
        if hasattr(mr, "additions") or hasattr(mr, "deletions"):
            additions = getattr(mr, "additions", 0)
            deletions = getattr(mr, "deletions", 0)
            print(f"\nChanges:")
            print(f"  Additions:  +{additions}")
            print(f"  Deletions:  -{deletions}")
            print(f"  Total:      {additions + deletions} lines")

        # Pipeline status
        if getattr(mr, "head_pipeline", None):
            p = mr.head_pipeline
            p_status = p.get("status", "unknown")
            p_color = {
                "success": "\033[92m",
                "failed": "\033[91m",
                "running": "\033[93m",
            }.get(p_status, "")
            print(f"\nCurrent Pipeline:")
            print(f"  {p_color} {p_status}\033[0m (ID: {p.get('id')})")
            print(f"  SHA: {p.get('sha', '')[:8]}")

        # Recent pipelines
        pipelines = cli.explorer.get_pipelines_for_mr(mr_id)[:5]
        if pipelines:
            print(f"\nRecent Pipelines:")
            for p in pipelines:
                status_icon = {
                    "success": "[SUCCESS]",
                    "failed": "[FAILED]",
                    "running": "[RUNNING]",
                }.get(p["status"], "[PENDING]")
                print(
                    f"  {status_icon} {p['id']} - {p['status']} ({p['created_at'][:16]})"
                )

        # Labels and milestone
        if mr.labels:
            print(f"\nLabels: {', '.join(mr.labels)}")

        if getattr(mr, "milestone", None):
            print(f"Milestone: {mr.milestone['title']}")

        # Description preview
        if mr.description:
            print(f"\nDescription (preview):")
            desc_lines = mr.description.split("\n")[:5]
            for line in desc_lines:
                print(f"  {line[:80]}")
            if len(mr.description.split("\n")) > 5:
                print(f"  ... (truncated)")

        print(f"\nMR_URL: {mr.web_url}")

