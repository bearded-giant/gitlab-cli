# GitLab CLI Explorer

A command-line tool for exploring GitLab pipeline and job statuses, designed for interactive exploration and scripting.

## Installation

### Method 1: Install with pipx (Recommended - Available Everywhere)
```bash
# Install pipx if you don't have it
brew install pipx  # macOS with Homebrew
# or
python3 -m pip install --user pipx

pipx ensurepath  # Add pipx binaries to PATH

# Install gitlab-cli globally
git clone <repo-url>
cd gitlab-cli
pipx install -e .
```

This makes `gitlab-cli` and `gl` available in all directories and projects, regardless of virtual environment.

### Method 2: Install from source (for development)
```bash
# Clone and install in your virtual environment
git clone <repo-url>
cd gitlab-cli
pip install -e .
```

Note: With Method 2, the tool is only available when the virtual environment is activated.

### Method 3: Install directly from git
```bash
pipx install git+https://github.com/yourusername/gitlab-cli.git
# or in a virtual environment:
pip install git+https://github.com/yourusername/gitlab-cli.git
```

## Configuration

### Required Environment Variables
```bash
export GITLAB_URL=https://gitlab.example.com  # Your GitLab instance URL
export GITLAB_TOKEN=your_personal_access_token  # Create at GitLab > Settings > Access Tokens
```

### Default Output Format
You can set a default output format (friendly, table, or json) that will be used when not specified:
```bash
# Set default format via config
gl config set --default-format json

# Override per command
gl pipeline 123456 --format table
```

### Auto-Detection of Project
The tool automatically detects the GitLab project from your git remote URL. No need to set `GITLAB_PROJECT` manually!

```bash
# Just cd into any GitLab repository and run commands
cd /path/to/your/gitlab/repo
gl branch $(git branch --show-current)
```

The auto-detection works with:
- Standard projects: `group/project`
- Nested groups: `engineering/foo/bar`
- Monorepos: `engineering/monolith`

### Manual Project Override (Optional)
```bash
# Only needed if auto-detection doesn't work or you want to query a different project
export GITLAB_PROJECT=group/project

# Or set via config file
gitlab-cli config --project group/project
```

### Config File
```bash
# View current configuration
gitlab-cli config --show

# Set GitLab URL (persisted to config file)
gitlab-cli config --gitlab-url https://gitlab.example.com
```

Configuration is stored in `~/.config/gitlab-cli/config.json`
Cache is stored in `~/.cache/gitlab-cli/`

## Quick Start

After installation, the tool is available as `gitlab-cli` or `gl` (short alias).

### CLI v3: New Contextual Interface
The new v3 interface provides fluid, contextual discovery of resources:

```bash
# Branch context - explore branch and related resources
gl branch                          # Show current branch info
gl branch feature-xyz              # Show specific branch info  
gl branch feature-xyz mr           # Show MRs for branch
gl branch feature-xyz pipeline     # Show pipelines for branch
gl branch feature-xyz commit       # Show commits on branch

# MR context - explore MR and related resources
gl mr 1234                         # Show MR info
gl mr 1234 diff                    # Show MR diff
gl mr 1234 diff --view split      # Show side-by-side diff
gl mr 1234 pipeline                # Show MR pipelines
gl mr 1234 commit                  # Show MR commits
gl mr 1234 discussion              # Show MR discussions

# Pipeline and job exploration
gl pipeline 567890                 # Show pipeline summary
gl pipeline detail 567890          # Show detailed pipeline info
gl job 123456                      # Show job summary
gl job logs 123456                 # Show job logs
```

### Traditional Commands (v2)
```bash
# Get MRs for current branch
gl branch list

# Get pipeline status
gl pipeline status 123456 --detailed
```

## Command Structure

### CLI v3 (New - Recommended)
The new v3 interface provides contextual, discoverable commands:

```bash
gl <area> [resource] [subcommand] [options]    # Contextual pattern
gl <area> <id> [options]                       # Direct ID access
```

Areas:
- `branch` - Branch context and related resources
- `mr` - Merge request context and related resources (alias: `merge-request`)
- `pipeline` - Pipeline operations and job exploration
- `job` - Job operations and log access
- `config` - Configuration management
- `cache` - Cache management

### Quick Help
```bash
gl --help                # Show all available commands
gl help                  # Same as --help
gl pipeline --help      # Show pipeline-specific commands
gl job --help           # Show job-specific commands
```

### Output Formats
All commands support multiple output formats:
- `--format friendly` - Human-readable with colors and icons (default)
- `--format table` - Tabular format with aligned columns
- `--format json` - JSON output for scripting

The default format can be set in config:
```bash
gl config set --default-format table
```

Format inheritance:
- If `--format` is not specified, the format from config is used
- If no default is configured, `friendly` format is used

## Commands

### Branch Commands (Contextual)

```bash
# Show current branch information
gl branch                           # Shows branch info, MR count, pipeline status

# Show specific branch information  
gl branch feature-xyz               # Shows feature-xyz branch info

# Explore branch resources
gl branch feature-xyz mr            # List MRs for branch
gl branch feature-xyz mr --state all     # All MRs (opened, merged, closed)
gl branch feature-xyz pipeline      # Recent pipelines for branch
gl branch feature-xyz commit        # Recent commits on branch

# Filter options
gl branch feature-xyz mr --limit 5  # Limit results
gl branch main pipeline --limit 10  # Show last 10 pipelines
```

### Merge Request Commands (Contextual)

```bash
# Show MR information and explore resources
gl mr 1234                          # Show MR summary with quick actions
gl mr 1234 info                     # Same as above (explicit)

# MR Diff Commands - Multiple View Modes
gl mr 1234 diff                     # Show diff (uses config default view)
gl mr 1234 diff --view unified      # Traditional git diff
gl mr 1234 diff --view inline       # Inline diff with line numbers
gl mr 1234 diff --view split        # Side-by-side diff
gl mr 1234 diff --stats             # Show only statistics
gl mr 1234 diff --name-only         # List changed files only
gl mr 1234 diff --file path/to/file # Show diff for specific file
gl mr 1234 diff --no-color          # Disable color output

# Explore MR resources
gl mr 1234 pipeline                 # Show pipelines for MR
gl mr 1234 commit                   # Show commits in MR
gl mr 1234 discussion               # Show discussions/comments

# Search MRs with filters
gl mr search                        # List all open MRs
gl mr search --author johndoe       # MRs by specific author
gl mr search --assignee janedoe     # MRs assigned to janedoe
gl mr search --reviewer bobsmith    # MRs with bobsmith as reviewer
gl mr search --state merged         # Show merged MRs
gl mr search --state all            # Show all MRs
gl mr search --labels "bug,critical" # MRs with specific labels
gl mr search --search "fix login"   # Search in title and description
gl mr search --target-branch main   # MRs targeting main branch
gl mr search --wip                  # Only WIP/Draft MRs
gl mr search --created-after 3d     # MRs created in last 3 days
gl mr search --updated-after "2 hours ago" # Recently updated MRs

# Legacy commands (still supported)
gl mr detail 1234                   # Detailed MR information
gl mr 1234,5678,9012                # Show multiple MRs at once
```

### Diff View Configuration

```bash
# Set default diff view mode in config
gl config set --diff-view split     # Set split as default
gl config set --diff-view inline    # Set inline as default
gl config set --diff-view unified   # Set unified as default

# View current configuration
gl config show                      # Shows current diff_view setting
```

### Pipeline Commands

```bash
# List pipelines with filters
gl pipeline list                           # List recent pipelines
gl pipeline list --since 2d                # Pipelines from last 2 days
gl pipeline list --since "3 hours ago"     # Pipelines from last 3 hours
gl pipeline list --before 1w               # Pipelines older than 1 week
gl pipeline list --user johndoe            # Pipelines by specific user
gl pipeline list --ref main                # Pipelines for main branch
gl pipeline list --source schedule         # Scheduled pipelines
gl pipeline list --status failed           # Failed pipelines only
gl pipeline list --since 2d --status failed --user johndoe  # Combine filters

# Show pipeline summary
gl pipeline 567890

# Show comprehensive pipeline details
gl pipeline detail 567890

# Show pipeline details with variables
gl pipeline detail 567890 --show-variables

# Show pipeline graph visualization (stages, jobs, test durations)
gl pipeline graph 567890

# Retry failed jobs in a pipeline
gl pipeline retry 567890

# Cancel a running pipeline
gl pipeline cancel 567890

# Show multiple pipelines
gl pipeline 567890,567891,567892

# Search for jobs by name pattern
gl pipeline 1090389 --job-search pylint
gl pipeline 1090389 --job-search "integration test"

# Show failed jobs in pipeline
gl pipeline 567890 --failed

# Show running jobs
gl pipeline 567890 --running

# Show all jobs (not just summary)
gl pipeline 567890 --jobs

# Filter by stage
gl pipeline 567890 --stage test
```

### Job Commands

```bash
# Show job summary
gl job 123456

# Show comprehensive job details
gl job detail 123456

# Show full job logs/trace
gl job logs 123456

# Retry a failed job
gl job retry 123456

# Play/trigger a manual job
gl job play 123456

# Show multiple jobs
gl job 123456,123457,123458

# Show job with failure details
gl job 123456 --failures
```

### Configuration Commands

```bash
# Show current configuration
gl config show

# Set GitLab URL
gl config set --gitlab-url https://gitlab.example.com

# Set project (rarely needed with auto-detection)
gl config set --project group/project

# Set default output format
gl config set --default-format json
```

### Cache Management Commands

```bash
# Show cache information and behavior
gl cache info

# Show cache statistics
gl cache stats
gl cache stats --detailed  # Include breakdown by status and largest cached items

# List cached pipelines
gl cache list
gl cache list --limit 50 --sort size  # Show 50 items sorted by size
gl cache list --sort id                # Sort by pipeline ID

# Clear cache
gl cache clear --all                   # Clear entire cache (with confirmation)
gl cache clear --pipeline 123456       # Clear specific pipeline
gl cache clear --older-than 7          # Clear pipelines older than 7 days
gl cache clear --all --force           # Clear all without confirmation
```

## Example Workflows

### Quick Exploration (v3 - Recommended)

```bash
# 1. Check your current branch status
gl branch

# 2. See MRs for your branch (use branch name explicitly)
gl branch auth-logging mr

# 3. Quick access to MR URL
open $(gl branch auth-logging mr | grep "^MR_URL:" | cut -d' ' -f2)

# 4. Check an MR and its diff
gl mr 5678
gl mr 5678 diff --view split

# 5. Check the latest pipeline
gl pipeline 987654

# 6. See failed jobs
gl pipeline 987654 --failed

# 7. Get job logs
gl job logs 111222
```

### Useful Scripting Examples

```bash
# Open branch URL in browser
open $(gl branch | grep "^BRANCH_URL:" | cut -d' ' -f2)

# Get MR URL for quick access
gl mr 1234 | grep "^MR_URL:" | cut -d' ' -f2

# Get pipeline URL
gl pipeline 567890 | grep "^PIPELINE_URL:" | cut -d' ' -f2

# Check if pipeline succeeded
gl pipeline 567890 --format json | jq -r '.status' | grep -q "success"

# List all failed job IDs
gl pipeline 567890 --format json | jq -r '.jobs[] | select(.status == "failed") | .id'

# Export MR diff to file
gl mr 1234 diff --no-color > mr_1234_changes.diff
```

### Comprehensive Pipeline Investigation

```bash
# 1. Get detailed pipeline overview
gl pipeline detail 987654

# This shows:
# - Full timing information (created, started, finished, queued duration)
# - Pipeline source and trigger
# - Commit details
# - Job statistics by status
# - Stage-by-stage breakdown
# - Failed job listings
```

### Job Failure Analysis

```bash
# 1. Get comprehensive job details
gl job detail 111222

# This shows:
# - Job status and timing
# - Runner information
# - Artifacts
# - Coverage
# - Failure reasons and details
# - Related pipeline status

# 2. Get full job logs with smart failure extraction
gl job logs 111222

# This shows:
# - Smart failure extraction based on job type:
#   - pytest: test failures and assertions
#   - pylint: linting violations
#   - mypy: type checking errors
#   - generic: last 30 lines before failure
# - Full job trace/logs
```

### Finding Specific Jobs

```bash
# Search for jobs by name in a pipeline
gl pipeline 1090389 --job-search pylint
gl pipeline 1090389 --job-search "integration test"
gl pipeline 1090389 --job-search ruff
```

### Automated Pipeline Watching

```bash
# Watch pipeline for current branch (auto-refreshes every 30 seconds)
./watch_pipeline.sh

# Watch with custom refresh interval (10 seconds)
./watch_pipeline.sh 10
```

This will:
1. Find the latest MR for your current git branch
2. Get the latest pipeline for that MR
3. Continuously monitor the pipeline status
4. Show failed job details automatically
5. Stop when pipeline completes

Note: The watch script needs updating to use `gl` instead of direct Python script.

### Batch Operations

```bash
# Check multiple pipelines at once
gl pipeline 987654,987655,987656

# Analyze multiple failed jobs
gl job 111222,111223,111224 --failures

# Review multiple MRs
gl mr 5678,5679,5680
```

### Using Different Output Formats

```bash
# JSON output for scripting
gl pipeline detail 987654 --format json | jq '.stages'
gl job 111222,111223,111224 --format json | jq '.jobs[].status'

# Table format with aligned columns
gl pipeline 987654 --format table
gl job 111222,111223,111224 --format table
gl mr 5678,5679 --format table

# Friendly format (default) with colors and icons
gl job detail 111222 --format friendly
gl pipeline detail 987654
```

### Scriptable Output with Greppable Prefixes

All commands output greppable prefixes (like `BRANCH_URL:`, `MR_ID:`, `PIPELINE_URL:`) for easy scripting:

```bash
# Open branch in browser
open $(gl branch | grep "^BRANCH_URL:" | cut -d' ' -f2)

# Open latest MR
open $(gl branch --latest | grep "^LATEST_MR_URL:" | cut -d' ' -f2)

# Open specific pipeline
open $(gl pipeline detail 123456 | grep "^PIPELINE_URL:" | cut -d' ' -f2)

# Open failed job from a pipeline
JOB_ID=$(gl pipeline 123456 --failed | head -n 20 | grep "^[0-9]" | head -1)
open $(gl job detail $JOB_ID | grep "^JOB_URL:" | cut -d' ' -f2)

# Get pipeline ID for latest MR
PIPELINE_ID=$(gl branch --latest | grep "^LATEST_PIPELINE_ID:" | cut -d' ' -f2)
gl pipeline detail $PIPELINE_ID
```

## Features

- **Intuitive exploration**: ID-based commands for easy pipeline/job/MR exploration
- **Detailed views**: New `detail` subcommand shows comprehensive information
- **Pipeline variables**: View pipeline variables with `--show-variables` flag (masked for security)
- **Job logs**: `gl job logs <id>` shows full job trace with smart failure extraction
- **Job tailing**: `gl job tail <id>` follows job logs in real-time as they're generated
- **Job dependencies**: View job dependencies (needs/needed_by) in job detail view
- **Job search**: Search for jobs by name pattern with `--job-search`
- **Pipeline/Job management**: Retry failed pipelines/jobs, cancel running pipelines, play manual jobs
- **Smart failure extraction**: Automatically detects job type (pytest, pylint, mypy, etc.) and extracts relevant failures
- **Color-coded output**: Success (green), Failed (red), Running (yellow)
- **Transparent caching**: Completed pipelines are cached locally for faster access
  - Full cache management with `gl cache` commands
  - View cache statistics and contents
  - Clear cache selectively or completely
- **Filtering**: Filter jobs by status or stage
- **Batch processing**: Analyze multiple items at once (pipelines, jobs, MRs)
- **Multiple output formats**: Friendly (default), table, or JSON for scripting
- **Auto-detection**: Automatically detects GitLab project from git remote
- **Global availability**: Install with pipx for use across all projects

## Output Examples

### Table Format

```
gl pipeline 567890 --format table

Pipeline 567890 Summary
------------------------------------------------------------
Status          FAILED
Created         2024-01-15T10:30
Duration        45m32s
------------------------------------------------------------
Job Status      Count
------------------------------------------------------------
Total                142
Success              130
Failed                 5
Running                2
Skipped                2
------------------------------------------------------------

Failed Jobs:
--------------------------------------------------------------------------------
ID           Stage           Name
--------------------------------------------------------------------------------
123456       test            py311 integration test parallel 1/100
123457       test            py311 integration test parallel 15/100
```

### Pipeline Summary (gl pipeline 567890)
```
Pipeline 567890: ❌ FAILED
Created: 2024-01-15T10:30 | Duration: 45m32s
Jobs: 142 total | ❌ 5 failed | ✅ 130 success | 🔄 2 running | ⏭ 2 skipped

Failed Jobs:
  ❌ 123456 - py311 integration test parallel 1/100 (test)
  ❌ 123457 - py311 integration test parallel 15/100 (test)
  ... and 3 more

💡 Use --failed to see all failed jobs
```

### Pipeline Detail (gl pipeline detail 567890)
```
============================================================
Pipeline #567890
============================================================

Status:       ❌ FAILED
Source:       push
Branch/Tag:   main
Started by:   John Doe (@jdoe)

Timing:
  Created:    2024-01-15T10:30:45Z
  Started:    2024-01-15T10:31:02Z  
  Finished:   2024-01-15T11:16:34Z
  Duration:   45m32s
  Queued:     17s

Commit:
  SHA:        abc123de
  Message:    Fix checkout flow validation
  Author:     Jane Smith

Job Statistics:
  Total:      142 jobs
  Failed:     ❌ 5
  Success:    ✅ 130
  Running:    🔄 2
  Skipped:    ⏭ 2
  Pending:    ⏸ 3

Stages:
  ✅ build: 10 jobs
  ❌ test: 100 jobs
      ❌ 123456 - py311 integration test parallel 1/100
      ❌ 123457 - py311 integration test parallel 15/100
  🔄 deploy: 32 jobs

Pipeline URL: https://gitlab.example.com/...
```

### Job Detail (gl job detail 123456)
```
============================================================
integration test py parallel 1/100
============================================================

Status:       ❌ FAILED
Failure:      script_failure
Stage:        test
Job ID:       123456
Started by:   Mike (@mike)

Timing:
  Created:    2024-01-15T10:45:00Z
  Started:    2024-01-15T10:45:30Z
  Finished:   2024-01-15T10:51:02Z
  Duration:   5m32s
  Queued:     30s

Runner:
  ID:         #1689
  Name:       runner-km1ekr-ci
  Type:       Shared

Source:
  Branch/Tag: main
  Commit:     abc123de

Pipeline:
  ID:         #567890
  Status:     ❌ failed

Failure Details:
  FAILED tests/api/test_checkout.py::test_create_checkout
  FAILED tests/api/test_checkout.py::test_update_checkout

Job URL: https://gitlab.example.com/...
```

### MR Detail (gl mr detail 5678)
```
============================================================
MR !5678: Add checkout validation improvements
============================================================

Status:       OPENED
              📝 DRAFT
Author:       Jane Smith (@jsmith)
Assignees:    @jdoe, @mike
Reviewers:    @alice, @bob

Branches:
  Source:     feature/checkout-validation
  Target:     main

Timing:
  Created:    2024-01-14T15:30:00Z
  Updated:    2024-01-15T11:20:00Z

Merge Status:
  ✅ All discussions resolved
  ❌ Has conflicts

Changes:
  Additions:  +245
  Deletions:  -89
  Total:      334 lines

Current Pipeline:
  ❌ failed (ID: 567890)
  SHA: abc123de

Recent Pipelines:
  ❌ 567890 - failed (2024-01-15T10:30)
  ✅ 567889 - success (2024-01-14T16:45)
  ✅ 567888 - success (2024-01-14T15:35)

Labels: backend, checkout, needs-review
Milestone: Sprint 45

MR URL: https://gitlab.example.com/...
```