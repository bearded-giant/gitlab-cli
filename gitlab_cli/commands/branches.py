"""Branches command handler"""

import sys
import subprocess
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
            "--format", choices=["friendly", "table", "json"], help="Output format"
        )

    def handle(self, cli, args, output_format):
        """Handle branch commands"""
        # Get current branch if not specified
        if not args.branch_name:
            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            if result.returncode == 0:
                args.branch_name = result.stdout.strip()
            else:
                self.output_error("Not in a git repository or cannot determine branch")

        # Use existing command
        args.format = output_format
        cli.cmd_branch_mrs(args)