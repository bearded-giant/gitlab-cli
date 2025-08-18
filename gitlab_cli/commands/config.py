"""Configuration command handler"""

from .base import BaseCommand


class ConfigCommand(BaseCommand):
    """Handle configuration commands"""

    def add_arguments(self, subparsers):
        """Add config-specific arguments to parser"""
        parser = subparsers.add_parser(
            "config",
            help="Configuration management",
            description="View and update GitLab CLI configuration",
        )

        # Add subparsers for show/set
        config_subparsers = parser.add_subparsers(dest="action", help="Config action")

        # config show
        config_subparsers.add_parser("show", help="Show current configuration")

        # config set
        set_parser = config_subparsers.add_parser("set", help="Set configuration values")
        set_parser.add_argument("--gitlab-url", help="GitLab server URL")
        set_parser.add_argument("--project", help="GitLab project path")
        set_parser.add_argument(
            "--default-format",
            choices=["friendly", "table", "json"],
            help="Default output format",
        )

    def handle(self, config, args):
        """Handle configuration commands"""
        if not hasattr(args, "action") or not args.action:
            # Default to show
            args.action = "show"

        if args.action == "show":
            self.show_config(config)
        elif args.action == "set":
            self.set_config(config, args)

    def show_config(self, config):
        """Display current configuration"""
        print(f"GitLab URL:     {config.gitlab_url or 'Not set'}")
        print(f"Project:        {config.project_path or 'Not set (auto-detected)'}")
        print(f"Token:          {'Set' if config.gitlab_token else 'Not set'}")
        print(f"Default format: {config.default_format}")
        print(f"Cache dir:      {config.cache_dir}")

    def set_config(self, config, args):
        """Update configuration values"""
        update = {}
        if hasattr(args, "gitlab_url") and args.gitlab_url:
            update["gitlab_url"] = args.gitlab_url
        if hasattr(args, "project") and args.project:
            update["project_path"] = args.project
        if hasattr(args, "default_format") and args.default_format:
            update["default_format"] = args.default_format

        if update:
            config.save_config(**update)
            print("Configuration saved")
        else:
            print("No configuration values provided")