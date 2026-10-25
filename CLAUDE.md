# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a GitLab CLI tool (`gl`) for exploring pipelines, jobs, and merge requests. It's designed for both interactive exploration and scripting, with modular command architecture and intelligent caching.

## Development Commands

### Install for Development
```bash
# Install in development mode with pipx (recommended - globally available)
pipx install -e .

# Install in virtual environment (for development)
pip install -e .
```

### Testing
```bash
# Run basic CLI parsing tests
python test_cli_v3.py

# Test cache functionality
python test_cache.py

# Test git detection
python test_git_detection.py
```

### Running the CLI
```bash
# Main entry point
gl <command> [options]

# Verbose mode (shows caching, timing details)
gl --verbose <command>

# Alternative entry points
gitlab-cli <command>  # Full name
python -m gitlab_cli.cli_v3  # Module execution
```

## Code Architecture

### Core Structure
- **Main CLI Router**: `gitlab_cli/cli_v3.py` - Entry point that routes commands to specialized handlers
- **Command Handlers**: `gitlab_cli/commands/` - Modular command implementations following consistent patterns
- **GitLab Explorer**: `gitlab_cli/cli.py:GitLabExplorer` - Handles GitLab API interactions and caching
- **Configuration**: `gitlab_cli/config.py:Config` - Manages environment variables, config files, and git remote detection

### Command Handler Pattern
All command handlers in `gitlab_cli/commands/` follow this structure:
1. Inherit from `BaseCommand` for common functionality (ID parsing, JSON output, error handling)
2. Implement `handle()` method for main logic
3. Support multiple output formats: friendly (default), table, json
4. Use greppable prefixes for scripting (e.g., `PIPELINE_URL:`, `MR_ID:`)

### Key Features Implementation

**Caching System** (`gitlab_cli/cli.py:GitLabExplorer`):
- SQLite database at `~/.cache/gitlab-cli/pipelines_cache.db`
- Only caches completed pipelines (success, failed, canceled, skipped)
- Cache management via `CacheCommand` class

**Git Project Detection** (`gitlab_cli/config.py:Config._detect_project_from_git`):
- Automatically extracts project path from git remote URL
- Supports SSH and HTTPS formats
- Handles nested groups (e.g., `engineering/foo/bar`)

**Output Formatting**:
- Format hierarchy: CLI flag > config file > default ('friendly')
- All commands support `--format` flag
- JSON output includes all data for scripting

**Failure Extraction** (`gitlab_cli/cli.py:GitLabExplorer.extract_failures_from_trace`):
- Intelligent job type detection (pytest, pylint, mypy, ruff)
- Type-specific failure extraction patterns
- Fallback to generic extraction for unknown job types

### Adding New Commands

1. Create new command class in `gitlab_cli/commands/`:
```python
from .base import BaseCommand

class NewCommand(BaseCommand):
    def add_arguments(self, parser):
        # Add command-specific arguments
        pass
    
    def handle(self, cli, args, output_format):
        # Implement command logic
        # Use cli.explorer for GitLab API calls
        # Support output_format: friendly, table, json
        pass
```

2. Register in `gitlab_cli/commands/__init__.py`

3. Add routing in `gitlab_cli/cli_v3.py:GitLabCLIv3.route_command()`

### API Patterns

**GitLab API Access**:
```python
# Get project object
cli.explorer.project

# Get pipeline
pipeline = cli.explorer.project.pipelines.get(pipeline_id)

# Get jobs for pipeline
jobs = pipeline.jobs.list(all=True)

# Get MR
mr = cli.explorer.project.mergerequests.get(mr_id)
```

**Caching Pattern**:
```python
# Check cache first
data = cli.explorer.get_pipeline_from_cache(pipeline_id)
if not data:
    # Fetch from API
    data = cli.explorer.get_pipeline_details(pipeline_id)
```

## Important Conventions

### Output Format Rules
- Friendly format: Use colors, icons, human-readable formatting
- Table format: Fixed-width columns, no colors, suitable for terminals
- JSON format: Complete data structure for scripting

### Greppable Output
Always include greppable prefixes in friendly output for scripting:
```python
print(f"PIPELINE_URL: {pipeline.web_url}")
print(f"PIPELINE_ID: {pipeline.id}")
```

### Error Handling
- Use `BaseCommand.output_error()` for consistent error formatting
- Exit with status 1 on errors
- Provide helpful error messages with context

### Performance Considerations
- Cache completed pipelines to reduce API calls
- Use `all=True` when fetching lists from GitLab API
- Show cache location and timing in verbose mode

## Configuration Locations
- Config file: `~/.config/gitlab-cli/config.json`
- Cache database: `~/.cache/gitlab-cli/pipelines_cache.db`
- Environment variables: `GITLAB_URL`, `GITLAB_TOKEN`, `GITLAB_PROJECT`

## Common Development Tasks

### Adding Pipeline Actions
Pipeline actions (retry, cancel) follow this pattern in `pipelines.py`:
1. Get pipeline object
2. Call action method
3. Return formatted result based on output_format

### Extending Job Failure Detection
Add new job type detection in `cli.py:extract_failures_from_trace()`:
1. Check job name pattern
2. Create extraction method for that job type
3. Return structured failure data

### Adding Search/Filter Functionality
See `search.py:SearchCommand` for pattern - use GitLab API list parameters and format results consistently.