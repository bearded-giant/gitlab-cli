#!/usr/bin/env python3
"""Test the stage URL functionality"""

# Simulate the stage URL logic
def generate_stage_url(branch_name):
    return f"https://{branch_name}.stage.rechargeapps.net/config"

# Test cases
test_branches = [
    "feature-auth-improvements",
    "bugfix-payment-flow",
    "main",
    "develop"
]

print("Testing stage URL generation:")
print("=" * 50)

for branch in test_branches:
    stage_url = generate_stage_url(branch)
    print(f"Branch: {branch}")
    print(f"STAGE_URL: {stage_url}")
    print()

print("Command usage:")
print("gl branch --stage-url                    # Current branch")
print("gl branch feature-name --stage-url       # Specific branch")