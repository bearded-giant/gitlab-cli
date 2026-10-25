#!/usr/bin/env python3
import os
import time
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gitlab_cli.config import Config
from gitlab_cli.cli import GitLabExplorer

# live check: needs a completed pipeline in GITLAB_PROJECT (or the git-detected project)
pipeline_id = os.environ.get("GL_TEST_PIPELINE_ID")
if not pipeline_id:
    print("SKIP: set GL_TEST_PIPELINE_ID to a completed pipeline id in GITLAB_PROJECT")
    sys.exit(0)
pipeline_id = int(pipeline_id)

config = Config()
explorer = GitLabExplorer(config)

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
assert elapsed < 0.5, "second call should hit the cache"

# Force API call
start = time.time()
data = explorer.get_pipeline_details(pipeline_id, use_cache=False)
elapsed = time.time() - start
print(f"Forced API call: {elapsed:.2f}s")
