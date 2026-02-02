# Scripting and Automation

## Greppable Prefixes

All commands output greppable prefixes for easy scripting:

```bash
# open branch in browser
open $(gl branch | grep "^BRANCH_URL:" | cut -d' ' -f2)

# open latest MR
open $(gl branch --latest | grep "^LATEST_MR_URL:" | cut -d' ' -f2)

# open specific pipeline
open $(gl pipeline detail 123456 | grep "^PIPELINE_URL:" | cut -d' ' -f2)

# get pipeline ID for latest MR
PIPELINE_ID=$(gl branch --latest | grep "^LATEST_PIPELINE_ID:" | cut -d' ' -f2)
gl pipeline detail $PIPELINE_ID

# open failed job from a pipeline
JOB_ID=$(gl pipeline 123456 --failed | head -n 20 | grep "^[0-9]" | head -1)
open $(gl job detail $JOB_ID | grep "^JOB_URL:" | cut -d' ' -f2)
```

## Shell Functions

```bash
# add to .bashrc/.zshrc
open_mr() {
    local url=$(gl branch --latest | grep "^MR_URL:" | cut -d' ' -f2)
    if [ -n "$url" ]; then
        open "$url"
    else
        echo "No MR to open"
    fi
}
```

## JSON Scripting

```bash
# extract stages
gl pipeline detail 987654 --format json | jq '.stages'

# get job statuses
gl job 111222,111223,111224 --format json | jq '.jobs[].status'

# check if pipeline succeeded
gl pipeline 567890 --format json | jq -r '.status' | grep -q "success"

# list all failed job IDs
gl pipeline 567890 --format json | jq -r '.jobs[] | select(.status == "failed") | .id'

# export MR diff to file
gl mr 1234 diff --no-color > mr_1234_changes.diff
```

## Batch Operations

```bash
gl pipeline 987654,987655,987656           # multiple pipelines
gl job 111222,111223,111224 --failures     # multiple jobs with failures
gl mr 5678,5679,5680                       # multiple MRs
```

## Output Formats

```bash
# JSON for scripting
gl pipeline detail 987654 --format json | jq '.stages'

# table for terminals
gl pipeline 987654 --format table

# friendly (default) with colors
gl pipeline detail 987654
```
