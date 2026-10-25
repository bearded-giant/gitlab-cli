#!/usr/bin/env python3

# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Test script for CLI v3 commands"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gitlab_cli.cli_v3 import GitLabCLIv3

cli = GitLabCLIv3()

# (argv, expected parsed attributes)
test_commands = [
    (["job", "123456"], {"area": "job", "action": "123456"}),
    (["job", "123456,789012"], {"area": "job", "action": "123456,789012"}),
    (["job", "detail", "123456"], {"area": "job", "action": "detail", "job_id": "123456"}),
    (["job", "123456", "--failures"], {"area": "job", "action": "123456", "failures": True}),
    (["pipeline", "567890"], {"area": "pipeline", "action": "567890"}),
    (["pipeline", "567890,567891"], {"area": "pipeline", "action": "567890,567891"}),
    (["pipeline", "detail", "567890"], {"area": "pipeline", "action": "detail", "pipeline_id": "567890"}),
    (["pipeline", "567890", "--failed"], {"area": "pipeline", "action": "567890", "failed": True}),
    (["mr", "5678"], {"area": "mr", "mr_id": "5678"}),
    (["mr", "5678", "diff"], {"area": "mr", "mr_id": "5678", "resource": "diff"}),
    (["merge-request", "5678", "discussion"], {"mr_id": "5678", "resource": "discussion"}),
    (["branch", "feature-x", "mr", "--format", "json"], {"area": "branch", "branch_or_resource": "feature-x", "resource": "mr", "format": "json"}),
]

print("Testing command parsing...\n")
failed = 0
for cmd, expected in test_commands:
    try:
        args = cli.create_parser().parse_args(cmd)
        wrong = {k: getattr(args, k, None) for k, v in expected.items() if getattr(args, k, None) != v}
    except SystemExit:
        wrong = {"parse": "argparse rejected it"}
    if wrong:
        failed += 1
        print(f"✗ {' '.join(cmd)}: {wrong}")
    else:
        print(f"✓ {' '.join(cmd)}")

if failed:
    print(f"\n{failed} command format(s) failed")
    sys.exit(1)
print("\nAll command formats parse correctly!")
