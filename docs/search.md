# Code Search

Search code across all projects in a GitLab group. Requires advanced search (Elasticsearch) enabled on the instance.

## Usage

```bash
gl search code <term> --group <group> [options]
```

## Options

| Flag | Short | Description |
|---|---|---|
| `--group` | `-g` | group path (required) |
| `--extension` | `-x` | filter by file extension (e.g., py, rb) |
| `--exclude` | `-e` | exclude projects matching substring (repeatable) |
| `--files-only` | | output unique file paths only (no snippets) |
| `--comments` | | include comment lines (excluded by default) |
| `--out` | `-o` | output directory (default: ~/.cache/gitlab-cli/) |
| `--format` | | friendly, json, or csv |

## Examples

```bash
# basic search
gl search code redis --group myorg

# python files only
gl search code redis --group myorg -x py

# exclude a project
gl search code redis --group myorg -e legacy-monolith

# exclude multiple projects
gl search code redis --group myorg -e legacy-monolith -e old-service

# unique files only, no snippets
gl search code redis --group myorg -e legacy-monolith --files-only

# csv for duckdb / spreadsheet analysis
gl search code redis --group myorg --format csv

# json output
gl search code redis --group myorg --format json
```

## GitLab Query Syntax

Filters are embedded in the search term:

```bash
gl search code "redis filename:*.py" --group myorg
gl search code "import redis filename:requirements*.txt" --group myorg
gl search code "redis path:src/" --group myorg
gl search code "redis extension:py" --group myorg    # same as -x py
```

## Output Formats

### Friendly (default)
```
myorg/payments/src/cache/client.py:42
    connection = Redis(host=REDIS_HOST, port=6379)

myorg/core-api/lib/session_store.py:118
    redis.set(f"session_{user_id}", data)

Found 47 results across 12 projects
```

### CSV
```csv
project,file,line,ref,snippet
myorg/payments,src/cache/client.py,42,main,"connection = Redis(host=REDIS_HOST, port=6379)"
```

### Files Only
```
myorg/core-api/lib/session_store.py
myorg/payments/src/cache/client.py

2 files across 2 projects
```

## Result Files

Results are saved to timestamped files:
- `~/.cache/gitlab-cli/search-redis-20260201-1931.txt`
- `~/.cache/gitlab-cli/search-redis-20260201-1931.csv`

A symlink always points to the most recent:
- `last_search.txt` (friendly/files-only)
- `last_search.csv` (csv format)

## Post-Search Filtering

```bash
# exclude a project from saved results
rg -v legacy-monolith ~/.cache/gitlab-cli/last_search.txt

# only python files
rg '\.py:' ~/.cache/gitlab-cli/last_search.txt

# only a specific subgroup
rg 'myorg/platform' ~/.cache/gitlab-cli/last_search.txt

# combine filters
rg -v legacy-monolith ~/.cache/gitlab-cli/last_search.txt | rg '\.py:'

# just file paths from friendly output
rg -v '^ ' ~/.cache/gitlab-cli/last_search.txt | rg -v '^$'

# count results per project
rg -v '^ ' ~/.cache/gitlab-cli/last_search.txt | rg -v '^$' | sed 's|/[^/]*/[^/]*$||' | sort | uniq -c | sort -rn
```

## DuckDB Analysis

```bash
# query csv directly
duckdb -c "SELECT project, count(*) as hits FROM '~/.cache/gitlab-cli/last_search.csv' GROUP BY project ORDER BY hits DESC"

# exclude and filter
duckdb -c "SELECT * FROM '~/.cache/gitlab-cli/last_search.csv' WHERE project NOT LIKE '%legacy-monolith%'"
```

## Notes

- comments are excluded by default (lines starting with #, //, /*, --, etc.)
- use `--comments` to include them
- snippets are truncated to 5 lines, 200 chars per line to reduce bloat from minified files
- the `--exclude` flag filters before output; post-search rg works on saved files
