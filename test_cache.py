#!/usr/bin/env python3
import time
import sys
sys.path.insert(0, '/Users/bryan/dev/python/gitlab-tools/gitlab-cli')

from gitlab_cli.config import Config
from gitlab_cli.cli import GitLabExplorer

# Test cache performance
config = Config()
explorer = GitLabExplorer(config)

pipeline_id = 1090389

print(f"Testing pipeline {pipeline_id} cache performance...")

# First call - should check cache
start = time.time()
data = explorer.get_pipeline_details(pipeline_id)
elapsed = time.time() - start
print(f"First call: {elapsed:.2f}s - {'Found in cache' if elapsed < 0.5 else 'Fetched from API'}")

# Second call - definitely should use cache
start = time.time()
data = explorer.get_pipeline_details(pipeline_id)
elapsed = time.time() - start
print(f"Second call: {elapsed:.2f}s - {'Found in cache' if elapsed < 0.5 else 'Fetched from API'}")

# Force API call
start = time.time()
data = explorer.get_pipeline_details(pipeline_id, use_cache=False)
elapsed = time.time() - start
print(f"Forced API call: {elapsed:.2f}s")