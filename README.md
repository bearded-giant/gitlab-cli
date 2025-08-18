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
gl pipelines 123456 --format table
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

### CLI v3: New Intuitive Interface
The new v3 interface makes exploration even easier with ID-based commands:

```bash
# Show summary of a pipeline
gl pipelines 123456

# Show detailed information about a pipeline
gl pipelines detail 123456

# Show failed jobs in a pipeline
gl pipelines 123456 --failed

# Show job details
gl jobs detail 789012

# Show MR details
gl mrs detail 5678
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
The new v3 interface uses intuitive plurals and ID-based exploration:

```bash
gl <area> [id(s)] [options]        # Basic pattern
gl <area> detail <id> [options]    # Detailed view
```

Areas:
- `branches` - Branch operations
- `mrs` - Merge request operations  
- `pipelines` - Pipeline operations
- `jobs` - Job operations
- `config` - Configuration management

### Quick Help
```bash
gl --help                # Show all available commands
gl help                  # Same as --help
gl pipelines --help      # Show pipeline-specific commands
gl jobs --help           # Show job-specific commands
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

### Branch Commands

```bash
# List MRs for current branch (auto-detected)
gl branches

# List MRs for specific branch
gl branches feature-xyz

# Filter by state
gl branches --state all
gl branches --state merged

# Show only latest MR
gl branches --latest
```

### Merge Request Commands

```bash
# Show MR summary
gl mrs 1234

# Show detailed MR information
gl mrs detail 1234

# Show multiple MRs at once
gl mrs 1234,5678,9012

# Show MR with pipeline info
gl mrs 1234 --pipelines

# Show full MR details including description
gl mrs 1234 --full
```

### Pipeline Commands

```bash
# Show pipeline summary
gl pipelines 567890

# Show comprehensive pipeline details
gl pipelines detail 567890

# Show pipeline details with variables
gl pipelines detail 567890 --show-variables

# Retry failed jobs in a pipeline
gl pipelines retry 567890

# Cancel a running pipeline
gl pipelines cancel 567890

# Show multiple pipelines
gl pipelines 567890,567891,567892

# Search for jobs by name pattern
gl pipelines 1090389 --job-search pylint
gl pipelines 1090389 --job-search "integration test"

# Show failed jobs in pipeline
gl pipelines 567890 --failed

# Show running jobs
gl pipelines 567890 --running

# Show all jobs (not just summary)
gl pipelines 567890 --jobs

# Filter by stage
gl pipelines 567890 --stage test
```

### Job Commands

```bash
# Show job summary
gl jobs 123456

# Show comprehensive job details
gl jobs detail 123456

# Show full job logs/trace
gl jobs logs 123456

# Retry a failed job
gl jobs retry 123456

# Play/trigger a manual job
gl jobs play 123456

# Show multiple jobs
gl jobs 123456,123457,123458

# Show job with failure details
gl jobs 123456 --failures
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

## Example Workflows

### Quick Exploration (v3 - Recommended)

```bash
# 1. Find MRs for your current branch
gl branches --latest

# 2. Get detailed MR information
gl mrs detail 5678

# 3. Check the latest pipeline
gl pipelines 987654

# 4. See failed jobs
gl pipelines 987654 --failed

# 5. Get detailed job information
gl jobs detail 111222
```

### Comprehensive Pipeline Investigation

```bash
# 1. Get detailed pipeline overview
gl pipelines detail 987654

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
gl jobs detail 111222

# This shows:
# - Job status and timing
# - Runner information
# - Artifacts
# - Coverage
# - Failure reasons and details
# - Related pipeline status

# 2. Get full job logs with smart failure extraction
gl jobs logs 111222

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
gl pipelines 1090389 --job-search pylint
gl pipelines 1090389 --job-search "integration test"
gl pipelines 1090389 --job-search ruff
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
gl pipelines 987654,987655,987656

# Analyze multiple failed jobs
gl jobs 111222,111223,111224 --failures

# Review multiple MRs
gl mrs 5678,5679,5680
```

### Using Different Output Formats

```bash
# JSON output for scripting
gl pipelines detail 987654 --format json | jq '.stages'
gl jobs 111222,111223,111224 --format json | jq '.jobs[].status'

# Table format with aligned columns
gl pipelines 987654 --format table
gl jobs 111222,111223,111224 --format table
gl mrs 5678,5679 --format table

# Friendly format (default) with colors and icons
gl jobs detail 111222 --format friendly
gl pipelines detail 987654
```

## Features

- **Intuitive exploration**: ID-based commands for easy pipeline/job/MR exploration
- **Detailed views**: New `detail` subcommand shows comprehensive information
- **Pipeline variables**: View pipeline variables with `--show-variables` flag (masked for security)
- **Job logs**: `gl jobs logs <id>` shows full job trace with smart failure extraction
- **Job search**: Search for jobs by name pattern with `--job-search`
- **Pipeline/Job management**: Retry failed pipelines/jobs, cancel running pipelines, play manual jobs
- **Smart failure extraction**: Automatically detects job type (pytest, pylint, mypy, etc.) and extracts relevant failures
- **Color-coded output**: Success (green), Failed (red), Running (yellow)
- **Caching**: Completed pipelines are cached locally for faster access
- **Filtering**: Filter jobs by status or stage
- **Batch processing**: Analyze multiple items at once (pipelines, jobs, MRs)
- **Multiple output formats**: Friendly (default), table, or JSON for scripting
- **Auto-detection**: Automatically detects GitLab project from git remote
- **Global availability**: Install with pipx for use across all projects

## Output Examples

### Table Format

```
gl pipelines 567890 --format table

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

### Pipeline Summary (gl pipelines 567890)
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

### Pipeline Detail (gl pipelines detail 567890)
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

### Job Detail (gl jobs detail 123456)
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

### MR Detail (gl mrs detail 5678)
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