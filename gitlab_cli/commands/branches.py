"""Branches command handler"""

import sys
import subprocess
import webbrowser
from .base import BaseCommand




class BranchesCommand(BaseCommand):
    """Handle branch-related commands"""

    def add_arguments(self, parser):
        """Add branch-specific arguments to parser"""
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
            "--open", action="store_true", help="Open the MR in web browser (opens latest if multiple)"
        )
        parser.add_argument(
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def handle(self, cli, args, output_format):
        """Handle branch commands"""
        if not args.branch_name:
            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            if result.returncode == 0:
                args.branch_name = result.stdout.strip()
            else:
                self.output_error("Not in a git repository or cannot determine branch")

        if args.open:
            mrs = cli.explorer.get_mrs_for_branch(args.branch_name, args.state)

            if not mrs:
                print(f"No {args.state} MRs found for branch '{args.branch_name}'")
                return

            mr_to_open = mrs[0] if args.latest or len(mrs) == 1 else mrs[0]
            mr_url = mr_to_open['web_url']

            print(f"Opening MR !{mr_to_open['iid']}: {mr_to_open['title']}")
            print(f"MR_URL: {mr_url}")

            try:
                webbrowser.open(mr_url)
                print("Browser opened successfully")
            except Exception as e:
                print(f"Could not open browser: {e}")
                print(f"You can manually open: {mr_url}")
            return

        args.format = output_format
        cli.cmd_branch_mrs(args)