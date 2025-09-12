# GitLab CLI Scripting Reference

Quick reference for grepping IDs and URLs from various commands for scripting.

## Greppable Output Format

All commands output standardized greppable lines:
- `<TYPE>_ID: <number>` - The numeric ID 
- `<TYPE>_URL: <url>` - The full GitLab URL

## Command Reference

### Branch Commands

```bash
# Get MR ID for current branch
gl branch mr
# Outputs: MR_ID: 449
#          MR_URL: https://gitlab.example.com/.../merge_requests/449

# Extract MR ID
gl branch mr | grep MR_ID: | awk '{print $2}'

# Get pipelines for branch
gl branch pipeline
# Outputs: PIPELINE_ID: 12345
#          PIPELINE_URL: https://gitlab.example.com/.../pipelines/12345

# Open branch in browser
gl branch --open                    # Opens current branch
gl branch feature-xyz --open        # Opens specific branch
```

### MR Commands

```bash
# Get MR info
gl mr 449
# Outputs: MR_URL: https://gitlab.example.com/.../merge_requests/449

# Get pipelines for MR
gl mr 449 pipeline
# Outputs: PIPELINE_ID: 12345
#          PIPELINE_URL: https://gitlab.example.com/.../pipelines/12345

# Limit to most recent 3 pipelines
gl mr 449 pipeline --limit 3
```

### Pipeline Commands

```bash
# Get pipeline info
gl pipeline 12345
# Outputs: PIPELINE_ID: 12345
#          PIPELINE_URL: https://gitlab.example.com/.../pipelines/12345

# List pipelines
gl pipeline list
# Outputs: PIPELINE_ID: 12345 (for each pipeline)
#          PIPELINE_URL: https://gitlab.example.com/.../pipelines/12345
```

### Job Commands

```bash
# Get job info
gl job 67890
# Outputs: JOB_ID: 67890
#          JOB_URL: https://gitlab.example.com/.../jobs/67890

# Tail job logs in real-time
gl job tail 67890
```

### Following Pipeline Progress

```bash
# Follow a pipeline's progress (auto-refreshes every 5 seconds)
gl pipeline 12345 --follow

# This will:
# - Show all stages and jobs with their status
# - Display recent output from running jobs
# - Auto-refresh until pipeline completes
# - Exit when pipeline finishes (success/failed/canceled)
```

### Search Commands

```bash
# Search for pipelines
gl pipeline search --status failed
# Outputs: PIPELINE_ID: 12345
#          PIPELINE_URL: https://gitlab.example.com/.../pipelines/12345

# Search for MRs
gl mr search --state opened
# Outputs: MR_URL: https://gitlab.example.com/.../merge_requests/449
```

## Common Scripting Patterns

### Get latest pipeline ID for current branch's MR
```bash
MR_ID=$(gl branch mr | grep MR_ID: | head -1 | awk '{print $2}')
PIPELINE_ID=$(gl mr $MR_ID pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
```

### Get all failed pipeline IDs for a branch
```bash
gl branch pipeline --status failed | grep PIPELINE_ID: | awk '{print $2}'
```

### Check status of MR's latest pipeline
```bash
MR_ID=$(gl branch mr | grep MR_ID: | head -1 | awk '{print $2}')
PIPELINE_ID=$(gl mr $MR_ID pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
gl pipeline $PIPELINE_ID
```

### Get all job IDs from a pipeline
```bash
gl pipeline 12345 detail | grep "JOB_ID:" | awk '{print $2}'
```

## Tips

1. All IDs are numeric only (no prefix symbols like ! or #)
2. Use `--format json` for structured data parsing with `jq`
3. Use `--limit N` to restrict results to most recent N items
4. Pipeline and job lists are always sorted newest-first
5. Add `| head -1` to get only the first/latest result
6. The greppable format is consistent: `<TYPE>_ID:` followed by space and the ID

## JSON Output Alternative

For more complex scripting, use JSON output:
```bash
# Get MR ID with jq
gl branch mr --format json | jq -r '.merge_requests[0].iid'

# Get pipeline IDs with jq
gl mr 449 pipeline --format json | jq -r '.pipelines[].id'
```