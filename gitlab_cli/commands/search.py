# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Search and filter commands for pipelines and MRs"""

import json
from datetime import datetime, timedelta
from .base import BaseCommand


class SearchCommand(BaseCommand):

    def parse_time_filter(self, time_str: str) -> datetime:
        if not time_str:
            return None
        time_str = time_str.lower().strip()

        if time_str.endswith("m"):  # minutes
            minutes = int(time_str[:-1])
            return datetime.now() - timedelta(minutes=minutes)
        elif time_str.endswith("h"):  # hours
            hours = int(time_str[:-1])
            return datetime.now() - timedelta(hours=hours)
        elif time_str.endswith("d"):  # days
            days = int(time_str[:-1])
            return datetime.now() - timedelta(days=days)
        elif time_str.endswith("w"):  # weeks
            weeks = int(time_str[:-1])
            return datetime.now() - timedelta(weeks=weeks)
        elif "ago" in time_str:  # "2 days ago" format
            parts = time_str.replace("ago", "").strip().split()
            if len(parts) >= 2:
                amount = int(parts[0])
                unit = parts[1].rstrip("s")  # remove plural 's'
                if unit == "minute":
                    return datetime.now() - timedelta(minutes=amount)
                elif unit == "hour":
                    return datetime.now() - timedelta(hours=amount)
                elif unit == "day":
                    return datetime.now() - timedelta(days=amount)
                elif unit == "week":
                    return datetime.now() - timedelta(weeks=amount)
                elif unit == "month":
                    return datetime.now() - timedelta(days=amount * 30)  # approximate

        # Try to parse as ISO date
        try:
            return datetime.fromisoformat(time_str)
        except:
            pass

        # Try common date formats
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(time_str, fmt)
            except:
                continue

        raise ValueError(f"Cannot parse time filter: {time_str}")

    def list_pipelines(self, cli, args, output_format):
        try:

            params = {}

            if hasattr(args, "status") and args.status:
                params["status"] = args.status

            # Ref/branch filter
            if hasattr(args, "ref") and args.ref:
                params["ref"] = args.ref

            # User filter
            if hasattr(args, "user") and args.user:
                # Need to find user ID from username
                users = cli.explorer.project.users.list(username=args.user)
                if users:
                    params["user_id"] = users[0].id
                else:
                    print(f"User '{args.user}' not found")
                    return

            # Source filter - handle --push shortcut
            if hasattr(args, "push") and args.push:
                params["source"] = "push"
            elif hasattr(args, "source") and args.source:
                params["source"] = args.source
            per_page = getattr(args, "limit", 20)
            pipelines = cli.explorer.project.pipelines.list(
                per_page=per_page * 2,  # Get extra to account for filtering
                page=1,
                order_by="id",
                sort="desc",
                **params,
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
                if len(filtered_pipelines) >= per_page:
                    break

            pipelines = filtered_pipelines
            if hasattr(args, "since") and args.since:
                try:
                    since_date = self.parse_time_filter(args.since)
                    pipelines = [
                        p
                        for p in pipelines
                        if datetime.fromisoformat(p.created_at.replace("Z", "+00:00"))
                        >= since_date
                    ]
                except ValueError as e:
                    print(f"Error: {e}")
                    return

            if hasattr(args, "before") and args.before:
                try:
                    before_date = self.parse_time_filter(args.before)
                    pipelines = [
                        p
                        for p in pipelines
                        if datetime.fromisoformat(p.created_at.replace("Z", "+00:00"))
                        <= before_date
                    ]
                except ValueError as e:
                    print(f"Error: {e}")
                    return
            if not pipelines:
                filters = []
                if "status" in params:
                    filters.append(f"status: {params['status']}")
                if "source" in params:
                    if hasattr(args, "push") and args.push:
                        filters.append("push only")
                    else:
                        filters.append(f"source: {params['source']}")
                if "ref" in params:
                    filters.append(f"ref: {params['ref']}")
                if hasattr(args, "user") and args.user:
                    filters.append(f"user: {args.user}")
                if hasattr(args, "since") and args.since:
                    filters.append(f"since: {args.since}")
                if hasattr(args, "before") and args.before:
                    filters.append(f"before: {args.before}")

                filter_msg = f" ({', '.join(filters)})" if filters else ""
                print(f"No pipelines found in project{filter_msg}")
                return

            if output_format == "json":
                output = {
                    "pipelines": [
                        {
                            "id": p.id,
                            "status": p.status,
                            "ref": p.ref,
                            "sha": p.sha[:8],
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
            elif output_format == "table":
                print(f"\nPipelines (showing {len(pipelines)} results)")
                print("=" * 120)
                print(
                    f"{'ID':<10} {'Status':<10} {'Source':<10} {'Branch/Tag':<25} {'User':<15} {'Created':<20}"
                )
                print("-" * 120)

                for p in pipelines:
                    ref_display = p.ref[:22] + "..." if len(p.ref) > 25 else p.ref
                    user_display = (
                        p.user.get("username", "N/A")[:15]
                        if hasattr(p, "user") and p.user
                        else "N/A"
                    )
                    created = p.created_at[:19].replace("T", " ")

                    print(
                        f"{p.id:<10} {p.status:<10} {p.source:<10} {ref_display:<25} {user_display:<15} {created:<20}"
                    )
                print("\nPIPELINE_IDS: " + ",".join(str(p.id) for p in pipelines))
            else:
                # Friendly format
                print(f"\nFound {len(pipelines)} pipelines")
                print("-" * 60)

                for p in pipelines:
                    status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "running": "🔄",
                        "pending": "⏳",
                        "canceled": "🚫",
                        "skipped": "⏭",
                    }.get(p.status, "❓")
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
                    print(f"   Branch: {p.ref}")
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
            print(f"Error listing pipelines: {e}")

    def search_mrs(self, cli, args, output_format):
        try:

            params = {}

            if hasattr(args, "state") and args.state:
                params["state"] = args.state
            else:
                params["state"] = "opened"  # default

            # Author filter
            if hasattr(args, "author") and args.author:
                params["author_username"] = args.author

            # Assignee filter
            if hasattr(args, "assignee") and args.assignee:
                params["assignee_username"] = args.assignee

            # Reviewer filter
            if hasattr(args, "reviewer") and args.reviewer:
                params["reviewer_username"] = args.reviewer

            # Labels filter
            if hasattr(args, "labels") and args.labels:
                params["labels"] = args.labels

            # Search in title/description
            if hasattr(args, "search") and args.search:
                params["search"] = args.search

            # Target branch filter
            if hasattr(args, "target_branch") and args.target_branch:
                params["target_branch"] = args.target_branch

            # Source branch filter
            if hasattr(args, "source_branch") and args.source_branch:
                params["source_branch"] = args.source_branch

            # WIP/Draft filter
            if hasattr(args, "wip") and args.wip:
                params["wip"] = "yes" if args.wip else "no"
            per_page = getattr(args, "limit", 20)
            mrs = cli.explorer.project.mergerequests.list(
                per_page=per_page, page=1, order_by="created_at", sort="desc", **params
            )
            if hasattr(args, "created_after") and args.created_after:
                try:
                    after_date = self.parse_time_filter(args.created_after)
                    # Convert to ISO format for API
                    params["created_after"] = after_date.isoformat()
                    # Re-fetch with date filter
                    mrs = cli.explorer.project.mergerequests.list(
                        per_page=per_page,
                        page=1,
                        order_by="created_at",
                        sort="desc",
                        **params,
                    )
                except ValueError as e:
                    print(f"Error: {e}")
                    return

            if hasattr(args, "updated_after") and args.updated_after:
                try:
                    after_date = self.parse_time_filter(args.updated_after)
                    params["updated_after"] = after_date.isoformat()
                    # Re-fetch with date filter
                    mrs = cli.explorer.project.mergerequests.list(
                        per_page=per_page,
                        page=1,
                        order_by="updated_at",
                        sort="desc",
                        **params,
                    )
                except ValueError as e:
                    print(f"Error: {e}")
                    return
            if not mrs:
                print("No merge requests found matching filters")
                return

            if output_format == "json":
                output = {
                    "merge_requests": [
                        {
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
                            "draft": (
                                mr.draft
                                if hasattr(mr, "draft")
                                else mr.work_in_progress
                            ),
                        }
                        for mr in mrs
                    ]
                }
                print(json.dumps(output, indent=2))
            elif output_format == "table":
                print(f"\nMerge Requests (showing {len(mrs)} results)")
                print("=" * 120)
                print(
                    f"{'MR':<8} {'State':<10} {'Author':<15} {'Title':<40} {'Source → Target':<30}"
                )
                print("-" * 120)

                for mr in mrs:
                    title_display = (
                        mr.title[:37] + "..." if len(mr.title) > 40 else mr.title
                    )
                    branches = f"{mr.source_branch[:13]} → {mr.target_branch[:13]}"

                    print(
                        f"!{mr.iid:<7} {mr.state:<10} {mr.author['username']:<15} {title_display:<40} {branches:<30}"
                    )
                print("\nMR_IIDS: " + ",".join(str(mr.iid) for mr in mrs))
            else:
                # Friendly format
                print(f"\nFound {len(mrs)} merge requests")
                print("-" * 60)

                for mr in mrs:
                    state_icon = {
                        "opened": "📂",
                        "closed": "📕",
                        "merged": "✅",
                        "locked": "🔒",
                    }.get(mr.state, "❓")

                    draft_str = (
                        " 📝 DRAFT"
                        if (hasattr(mr, "draft") and mr.draft)
                        or (hasattr(mr, "work_in_progress") and mr.work_in_progress)
                        else ""
                    )
                    created = mr.created_at[:10]
                    updated = mr.updated_at[:10]

                    print(f"\n{state_icon} MR !{mr.iid}: {mr.title}{draft_str}")
                    print(f"   Author: @{mr.author['username']}")
                    print(f"   Branches: {mr.source_branch} → {mr.target_branch}")
                    print(f"   Created: {created} | Updated: {updated}")
                    print(f"   MR_URL: {mr.web_url}")

        except Exception as e:
            print(f"Error searching MRs: {e}")

