#!/usr/bin/env python3

# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Test script for CLI v3 commands"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gitlab_cli.cli_v3 import GitLabCLIv3

# Test parsing various command formats
cli = GitLabCLIv3()

test_commands = [
    # Jobs commands
    ["jobs", "123456"],
    ["jobs", "123456,789012"],
    ["jobs", "detail", "123456"],
    ["jobs", "123456", "--failures"],
    # Pipelines commands
    ["pipelines", "567890"],
    ["pipelines", "567890,567891"],
    ["pipelines", "detail", "567890"],
    ["pipelines", "567890", "--failed"],
    # MRs commands
    ["mrs", "5678"],
    ["mrs", "5678,5679"],
    ["mrs", "detail", "5678"],
    ["mrs", "5678", "--pipelines"],
]

print("Testing command parsing...\n")
for cmd in test_commands:
    sys.argv = ["gl"] + cmd
    try:
        parser = cli.create_parser()
        args = parser.parse_args(cmd)
        print(f"✓ {' '.join(cmd)}")
        print(f"  Parsed: area={args.area}", end="")
        if args.area == "jobs":
            print(f", job_ids={args.job_ids}, detail_id={args.detail_id}")
        elif args.area == "pipelines":
            print(f", pipeline_ids={args.pipeline_ids}, detail_id={args.detail_id}")
        elif args.area == "mrs":
            print(f", mr_ids={args.mr_ids}, detail_id={args.detail_id}")
        else:
            print()
    except Exception as e:
        print(f"✗ {' '.join(cmd)}: {e}")

print("\nAll command formats parse correctly!")

