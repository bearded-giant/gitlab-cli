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

After installation, the tool is available as `gitlab-cli` or `gl` (short alias):

```bash
# Get MRs for current branch
gitlab-cli branch $(git branch --show-current)

# Or use the short alias
gl branch $(git branch --show-current)

# Get pipeline status
gl status 123456 --detailed
```

## Command Structure

GitLab CLI follows a consistent pattern: `gl <area> <action> [options]`

### Quick Help
```bash
gl --help                # Show all areas
gl branch --help         # Show branch commands
gl mr --help            # Show MR commands
gl pipeline --help      # Show pipeline commands
gl job --help           # Show job commands
gl config --help        # Show config commands
```

## Commands

### Branch Commands

```bash
# List MRs for current branch
gl branch list

# List MRs for specific branch
gl branch list feature-xyz

# Filter by state
gl branch list --state all
gl branch list --state merged

# Show only latest MR
gl branch list --latest
```

### Merge Request Commands

```bash
# Show detailed MR information
gl mr show 1234

# Show MR with recent pipelines
gl mr show 1234 --pipelines

# List all pipelines for an MR
gl mr pipelines 1234

# Show only latest pipeline
gl mr pipelines 1234 --latest
```

### Pipeline Commands

```bash
# Show pipeline status summary
gl pipeline status 567890

# Show detailed stage-by-stage view
gl pipeline status 567890 --detailed

# List all jobs in a pipeline
gl pipeline jobs 567890

# Filter jobs by status
gl pipeline jobs 567890 --status failed

# Filter jobs by stage
gl pipeline jobs 567890 --stage test

# Sort jobs
gl pipeline jobs 567890 --sort duration
```

### Job Commands

```bash
# Show job details and failures
gl job show 123456

# Show verbose failure information
gl job show 123456 --verbose

# Batch analyze multiple failed jobs
gl job batch 123456 123457 123458
```

### Configuration Commands

```bash
# Show current configuration
gl config show

# Set GitLab URL
gl config set --gitlab-url https://gitlab.example.com

# Set project (rarely needed with auto-detection)
gl config set --project group/project
```

## Example Workflows

### Starting from Current Git Branch

```bash
# 1. Find MRs for your current branch
gl branch list --latest

# 2. Show MR details (using MR ID from step 1)
gl mr show 5678

# 3. Get pipelines for the MR
gl mr pipelines 5678 --latest

# 4. Check pipeline status (using pipeline ID from step 3)
gl pipeline status 987654

# 5. If there are failures, get details
gl pipeline jobs 987654 --status failed
gl job show 111222 --verbose
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

### Direct Pipeline Investigation

```bash
# 1. Show all pipelines for an MR
gl mr pipelines 5678

# 2. Check status of a specific pipeline
gl pipeline status 987654

# 3. List failed jobs in that pipeline
gl pipeline jobs 987654 --status failed

# 4. Get details on specific failed job
gl job show 111222 --verbose

# 5. Or check multiple failed jobs at once
gl job batch 111222 111223 111224
```

## Features

- **Color-coded output**: Success (green), Failed (red), Running (yellow)
- **Caching**: Completed pipelines are cached locally for faster access
- **Filtering**: Filter jobs by status or stage
- **Sorting**: Sort jobs by duration, name, or creation time
- **Batch processing**: Analyze multiple failed jobs at once
- **Detailed failure extraction**: Automatically extracts test failures, stderr, and error messages

## Output Examples

### Pipeline Status
```
Pipeline 567890 Job Summary:
----------------------------------------
Total Jobs:    142
  ✅ Success:  130
  ❌ Failed:   5
  🔄 Running:  2
  ⏸  Pending:  3
  ⏭  Skipped:  2
  🚫 Canceled: 0
  👤 Manual:   0

Failed Jobs:
------------------------------------------------------------
ID           Stage           Name                                     Duration
------------------------------------------------------------
123456       test            py311 integration test parallel 1/100   5m32s
123457       test            py311 integration test parallel 15/100  4m18s
```

### Job Failures (Condensed)
```
Job 123456: py311 integration test parallel 1/100
Status: failed | Stage: test
Duration: 5m32s
URL: https://gitlab.rechargeapps.net/...

📋 Test Failures:
  • FAILED tests/api/test_checkout.py::test_create_checkout
  • FAILED tests/api/test_checkout.py::test_update_checkout
```