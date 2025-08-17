#!/usr/bin/env python3

from gitlab_cli.config import Config

config = Config()
print(f"Detected project: {config.project_path}")
print(f"GitLab URL: {config.gitlab_url}")
print(f"GitLab Token: {'Set' if config.gitlab_token else 'Not set'}")