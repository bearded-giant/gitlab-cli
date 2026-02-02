# Configuration

## Environment Variables

```bash
export GITLAB_URL=https://gitlab.example.com
export GITLAB_TOKEN=your_personal_access_token
```

Create access tokens at GitLab > Settings > Access Tokens.

## Auto-Detection

The tool automatically detects the GitLab project from your git remote URL:

```bash
cd /path/to/your/gitlab/repo
gl branch    # just works
```

Works with:
- Standard projects: `group/project`
- Nested groups: `myorg/team/service`
- Monorepos: `myorg/monolith`

## Manual Project Override

```bash
export GITLAB_PROJECT=group/project

# or via config
gl config set --project group/project
```

## Config Commands

```bash
gl config show                              # view current config
gl config set --gitlab-url https://gitlab.example.com
gl config set --project group/project       # rarely needed with auto-detection
gl config set --default-format json         # set default output format
gl config set --diff-view split             # set default diff view
```

## Output Formats

All commands support `--format`:
- `friendly` - human-readable with colors and icons (default)
- `table` - tabular with aligned columns
- `json` - JSON for scripting
- `csv` - CSV (search only)

```bash
gl config set --default-format table    # set default
gl pipeline 123456 --format json        # override per command
```

## Config Locations

- Config file: `~/.config/gitlab-cli/config.json`
- Cache database: `~/.cache/gitlab-cli/pipelines_cache.db`
- Search results: `~/.cache/gitlab-cli/`

## Cache Management

```bash
gl cache info                              # cache behavior info
gl cache stats                             # statistics
gl cache stats --detailed                  # breakdown by status, largest items

gl cache list                              # list cached pipelines
gl cache list --limit 50 --sort size       # 50 items sorted by size
gl cache list --sort id                    # sort by pipeline ID

gl cache clear --all                       # clear everything (with confirmation)
gl cache clear --pipeline 123456           # clear specific pipeline
gl cache clear --older-than 7              # clear older than 7 days
gl cache clear --all --force               # clear without confirmation
```
