# Pipeline Commands

Pipeline commands provide exploration, filtering, and management of CI/CD pipelines.

## List Pipelines

```bash
gl pipeline list                           # recent pipelines across all branches
gl pipeline list --failed                  # only failed
gl pipeline list --passed                  # only successful
gl pipeline list --push                    # only push pipelines
gl pipeline list --status running          # specific status
gl pipeline list --limit 5                 # limit results
```

### Combined Filters

```bash
gl pipeline list --failed --push           # failed push pipelines
gl pipeline list --failed --limit 2        # two most recent failed
gl pipeline list --push --passed           # successful push pipelines
gl pipeline list --source web --failed     # failed pipelines from web UI
```

### Time-Based Filters

```bash
gl pipeline list --since 2d                # last 2 days
gl pipeline list --since "3 hours ago"     # last 3 hours
gl pipeline list --before 1w               # older than 1 week
gl pipeline list --failed --since 1w       # failed in last week
```

### User and Branch Filters

```bash
gl pipeline list --user johndoe            # by user
gl pipeline list --ref main                # by branch
gl pipeline list --ref main --failed       # failed on main
```

## Pipeline Info

```bash
gl pipeline 567890                         # summary
gl pipeline detail 567890                  # comprehensive details
gl pipeline detail 567890 --show-variables # include pipeline variables
gl pipeline graph 567890                   # graph visualization
gl pipeline 567890,567891,567892           # multiple pipelines
```

## Pipeline Actions

```bash
gl pipeline retry 567890                   # retry failed jobs
gl pipeline rerun 567890                   # create NEW pipeline for same commit
gl pipeline cancel 567890                  # cancel running pipeline
```

`retry` retries only failed jobs. `rerun` creates a completely new pipeline.

## Job Filtering Within Pipelines

```bash
gl pipeline 567890 --failed                # failed jobs
gl pipeline 567890 --running               # running jobs
gl pipeline 567890 --jobs                  # all jobs
gl pipeline 567890 --stage test            # filter by stage
gl pipeline 1090389 --job-search pylint    # search by job name
gl pipeline 1090389 --job-search "integration test"
```

## Pipeline Watching

```bash
gl pipeline 567890 --follow                # follow pipeline progress, auto-tail running jobs
```

## Notes

- GitLab Security Policy Bot pipelines are automatically filtered out
- All pipeline listings show the user who created each pipeline

## Output Examples

### Summary
```
Pipeline 567890: FAILED
Created: 2024-01-15T10:30 | Duration: 45m32s
Jobs: 142 total | 5 failed | 130 success | 2 running | 2 skipped

Failed Jobs:
  123456 - py311 integration test parallel 1/100 (test)
  123457 - py311 integration test parallel 15/100 (test)
  ... and 3 more
```

### Detail
```
============================================================
Pipeline #567890
============================================================

Status:       FAILED
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
  Failed:     5
  Success:    130
  Running:    2
  Skipped:    2
  Pending:    3

Stages:
  build: 10 jobs
  test: 100 jobs
      123456 - py311 integration test parallel 1/100
      123457 - py311 integration test parallel 15/100
  deploy: 32 jobs

Pipeline URL: https://gitlab.example.com/...
```
