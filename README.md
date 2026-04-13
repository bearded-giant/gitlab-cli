# GitLab CLI Explorer

A command-line tool for exploring GitLab pipelines, jobs, merge requests, and code search. Designed for interactive exploration and scripting.

## Installation

Install with pipx (global `gl` on your PATH):

```bash
brew install pipx           # macOS
pipx ensurepath
git clone <repo-url>
cd gitlab-cli
make install                # pipx install -e .
```

Other make targets:

| Target | Action |
|---|---|
| `make install` | pipx editable install |
| `make reinstall` | pipx uninstall + install (refresh entry points) |
| `make upgrade` | `pipx upgrade gitlab-cli-explorer` |
| `make uninstall` | remove the pipx install |
| `make dev` | `pip install -e .` (for a venv, not global) |
| `make build` | build sdist + wheel |
| `make test` | run manual test scripts |
| `make completions` | install bash/zsh completions |
| `make clean` | clear build artifacts and `__pycache__` |

`make help` prints the same list.

## Configuration

```bash
export GITLAB_URL=https://gitlab.example.com
export GITLAB_TOKEN=your_personal_access_token
```

The tool auto-detects your GitLab project from git remote URL. See [docs/config.md](docs/config.md) for full configuration options.

## Quick Start

```bash
gl branch                              # current branch info
gl branch pipeline                     # pipelines for current branch
gl branch approvals                    # MR approval status
gl mr 1234                             # MR summary
gl mr 1234 diff --view split           # side-by-side diff
gl pipeline 567890                     # pipeline summary
gl pipeline list --failed --push       # failed push pipelines
gl job logs 123456                     # job logs with failure extraction
gl search code redis -g myorg -x py    # search code across a group
```

## Commands

| Area | Description | Docs |
|---|---|---|
| `gl branch` | branch info, MRs, pipelines, approvals | [docs/branch.md](docs/branch.md) |
| `gl mr` | merge requests, diffs, discussions, search | [docs/mr.md](docs/mr.md) |
| `gl pipeline` | pipeline listing, details, actions, job filtering | [docs/pipeline.md](docs/pipeline.md) |
| `gl job` | job details, logs, failure analysis, retry/play | [docs/job.md](docs/job.md) |
| `gl search code` | code search across group projects | [docs/search.md](docs/search.md) |
| `gl config` | configuration and cache management | [docs/config.md](docs/config.md) |

Scripting examples, greppable prefixes, and batch operations: [docs/scripting.md](docs/scripting.md)

## Output Formats

All commands support `--format`:
- `friendly` - human-readable with colors (default)
- `table` - aligned columns
- `json` - for scripting
- `csv` - search only

## Features

- **Contextual exploration** - branch/MR/pipeline context with related resources
- **MR approvals** - approval status, rules, and who approved
- **Diff views** - unified, inline, or split side-by-side
- **Pipeline management** - retry, rerun, cancel, follow
- **Smart failure extraction** - auto-detects pytest, pylint, mypy, ruff failures
- **Group code search** - search across all projects with exclude, comment filtering, csv/files-only output
- **Transparent caching** - completed pipelines cached locally
- **Auto-detection** - project detected from git remote
- **Greppable output** - prefixed lines for shell scripting
- **Batch processing** - multiple pipelines, jobs, or MRs at once
