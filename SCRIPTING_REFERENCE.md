# GitLab CLI Scripting Reference & Tips

Complete reference for scripting with the GitLab CLI, including greppable outputs, one-liners, and automation patterns.

## Table of Contents
- [Greppable Output Format](#greppable-output-format)
- [Command Reference](#command-reference)
- [Quick One-Liners](#quick-one-liners)
- [Common Scripting Patterns](#common-scripting-patterns)
- [Advanced Grep/Awk Patterns](#advanced-grepawk-patterns)
- [Workflow Automation](#workflow-automation)
- [Shell Aliases](#shell-aliases)
- [JSON Processing with jq](#json-processing-with-jq)
- [Pro Tips](#pro-tips)

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

# Create MR from current branch
gl branch --create-mr
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

# Follow pipeline progress (auto-refreshes)
gl pipeline 12345 --follow

# Pipeline actions
gl pipeline retry 12345      # Retry failed jobs
gl pipeline rerun 12345      # Create new pipeline for same commit
gl pipeline cancel 12345     # Cancel running pipeline

# List pipelines with filters
gl pipeline list --status failed
gl pipeline list --limit 10
```

### Job Commands

```bash
# Get job info
gl job 67890
# Outputs: JOB_ID: 67890
#          JOB_URL: https://gitlab.example.com/.../jobs/67890

# Job actions
gl job tail 67890           # Tail job logs in real-time
gl job logs 67890           # Show full job logs
gl job retry 67890          # Retry failed job
gl job play 67890           # Play manual job
```

## Quick One-Liners

### Follow Latest Pipeline
```bash
# Follow the latest pipeline for current branch
gl pipeline $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}') --follow
```

### Retry Failed Pipeline
```bash
# Retry the latest failed pipeline for current branch
gl pipeline retry $(gl branch pipeline --status failed --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
```

### Get Second Pipeline (for dual-pipeline projects)
```bash
# Get the SECOND pipeline (older one, often the main pipeline)
gl pipeline $(gl branch pipeline --limit 2 | grep PIPELINE_ID: | tail -1 | awk '{print $2}')

# Alternative using sed
gl pipeline $(gl branch pipeline --limit 2 | grep PIPELINE_ID: | sed -n '2p' | awk '{print $2}')

# Using awk directly
gl pipeline $(gl branch pipeline --limit 2 | grep PIPELINE_ID: | awk 'NR==2 {print $2}')
```

### MR Quick Actions
```bash
# Get the latest MR for current branch and show its pipelines
gl mr $(gl branch mr --latest | grep MR_ID: | awk '{print $2}') pipeline

# Open the latest MR in browser (using the URL)
open $(gl branch mr --latest | grep MR_URL: | awk '{print $2}')

# Check if current branch has any open MRs
gl branch mr --state opened | grep -q MR_ID: && echo "Has open MR" || echo "No open MR"
```

### Pipeline Status Checks
```bash
# Check if latest pipeline passed
gl branch pipeline --limit 1 | grep -q "success" && echo "✓ Passed" || echo "✗ Failed"

# Get status of latest pipeline
gl branch pipeline --limit 1 | grep "Status:" | awk '{print $2}'

# Count failed jobs in latest pipeline
gl pipeline $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}') --failed | grep -c "failed"
```

## Common Scripting Patterns

### The Pipeline Chain
```bash
# Branch → MR → Pipeline → Jobs
MR_ID=$(gl branch mr | grep MR_ID: | head -1 | awk '{print $2}')
PIPELINE_ID=$(gl mr $MR_ID pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
gl pipeline $PIPELINE_ID --jobs

# One-liner version
gl pipeline $(gl mr $(gl branch mr | grep MR_ID: | head -1 | awk '{print $2}') pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}') --jobs
```

### Extract Multiple Values
```bash
# Get both ID and URL in one pass
eval $(gl branch mr --latest | awk '/MR_ID:/ {print "MR_ID="$2} /MR_URL:/ {print "MR_URL="$2}')
echo "MR $MR_ID is at $MR_URL"

# Get pipeline ID and status together
eval $(gl branch pipeline --limit 1 | awk '/PIPELINE_ID:/ {print "PID="$2} /Status:/ {print "STATUS="$2}')
echo "Pipeline $PID is $STATUS"
```

### Finding and Fixing Failures
```bash
# Get the first failed job from latest pipeline
FAILED_JOB=$(gl pipeline $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}') --failed --format json | jq -r '.jobs[0].id')

# Show logs for that failed job
gl job logs $FAILED_JOB

# Retry the failed job
gl job retry $FAILED_JOB
```

### Conditional Actions
```bash
# Retry if failed, otherwise show status
PIPELINE_ID=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
STATUS=$(gl pipeline $PIPELINE_ID --format json | jq -r .status)
if [ "$STATUS" = "failed" ]; then
  gl pipeline retry $PIPELINE_ID
else
  echo "Pipeline is $STATUS"
fi
```

## Advanced Grep/Awk Patterns

### Multi-line Extraction
```bash
# Get MR ID and Pipeline ID in one command
gl branch mr --latest | awk '/MR_ID:|PIPELINE_ID:/ {print $2}'

# Get all IDs from output
gl branch mr | grep -E '(MR_ID|PIPELINE_ID):' | awk '{print $2}'

# Extract with labels
gl branch mr | awk '/MR_ID:/ {print "mr="$2} /PIPELINE_ID:/ {print "pipeline="$2}'
```

### Filtering and Counting
```bash
# Count pipelines by status
gl branch pipeline --limit 10 | grep "Status:" | awk '{print $2}' | sort | uniq -c

# Get only successful pipeline IDs
gl branch pipeline --limit 5 | awk '/Status: success/ {getline; if (/PIPELINE_ID:/) print $2}'

# Find pipelines with specific user
gl pipeline list --limit 20 --format json | jq -r '.pipelines[] | select(.user.username=="myuser") | .id'
```

### Complex Parsing
```bash
# Extract job IDs from specific stage
gl pipeline $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}') --format json | \
  jq -r '.jobs[] | select(.stage=="test") | .id'

# Get failed test names
gl pipeline $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}') --format json | \
  jq -r '.jobs[] | select(.status=="failed" and (.name | contains("test"))) | .name'
```

## Workflow Automation

### Monitor Pipeline Until Complete
```bash
#!/bin/bash
# Wait for pipeline to complete
PIPELINE_ID=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
while true; do
  STATUS=$(gl pipeline $PIPELINE_ID --format json | jq -r .status)
  if [[ "$STATUS" =~ ^(success|failed|canceled)$ ]]; then
    echo "Pipeline completed: $STATUS"
    break
  fi
  echo "Still running... (status: $STATUS)"
  sleep 10
done
```

### Auto-retry Failed Pipelines
```bash
#!/bin/bash
# Auto-retry failed pipelines up to 3 times
PIPELINE_ID=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  STATUS=$(gl pipeline $PIPELINE_ID --format json | jq -r .status)
  
  if [ "$STATUS" = "success" ]; then
    echo "Pipeline succeeded!"
    exit 0
  elif [ "$STATUS" = "failed" ]; then
    echo "Pipeline failed, retrying... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
    gl pipeline retry $PIPELINE_ID
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 30
  else
    echo "Pipeline is $STATUS, waiting..."
    sleep 30
  fi
done

echo "Pipeline failed after $MAX_RETRIES retries"
exit 1
```

### Pre-push Check
```bash
#!/bin/bash
# Check if pipeline will pass before pushing
echo "Checking pipeline status..."
PIPELINE_ID=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
STATUS=$(gl pipeline $PIPELINE_ID --format json | jq -r .status)

if [ "$STATUS" = "success" ]; then
  echo "✓ Pipeline passed, safe to push"
  git push
else
  echo "✗ Pipeline status: $STATUS"
  echo "Fix issues before pushing"
  exit 1
fi
```

### Daily Status Report
```bash
#!/bin/bash
# Generate daily status report
echo "=== GitLab Daily Status Report ==="
echo "Date: $(date)"
echo ""

# Check all your active branches
for branch in $(git branch -r | grep origin | grep -v HEAD | sed 's/origin\///' | head -5); do
  echo "Branch: $branch"
  git checkout $branch 2>/dev/null
  
  # Get MR status
  MR_COUNT=$(gl branch mr --state opened 2>/dev/null | grep -c MR_ID: || echo "0")
  echo "  Open MRs: $MR_COUNT"
  
  # Get latest pipeline status
  PIPELINE_STATUS=$(gl branch pipeline --limit 1 2>/dev/null | grep "Status:" | awk '{print $2}' || echo "none")
  echo "  Latest Pipeline: $PIPELINE_STATUS"
  
  echo ""
done
```

## Shell Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick aliases
alias glb='gl branch'
alias glm='gl mr'
alias glp='gl pipeline'
alias glj='gl job'

# Complex aliases
alias gl-follow='gl pipeline $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk "{print \$2}") --follow'
alias gl-retry='gl pipeline retry $(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk "{print \$2}")'
alias gl-open='gl branch --open'
alias gl-mr-open='open $(gl branch mr --latest | grep MR_URL: | awk "{print \$2}")'

# Function for following the main (older) pipeline
gl-follow-main() {
  gl pipeline $(gl branch pipeline --limit 2 | grep PIPELINE_ID: | tail -1 | awk '{print $2}') --follow
}

# Function to tail the first running job
gl-tail-running() {
  local pid=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
  local job_id=$(gl pipeline $pid --running --format json | jq -r '.jobs[0].id')
  if [ "$job_id" != "null" ]; then
    gl job tail $job_id
  else
    echo "No running jobs"
  fi
}

# Function to get all failed job logs
gl-show-failures() {
  local pid=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
  for job_id in $(gl pipeline $pid --failed --format json | jq -r '.jobs[].id'); do
    echo "=== Job $job_id ==="
    gl job logs $job_id | tail -20
    echo ""
  done
}
```

## JSON Processing with jq

### Basic Queries
```bash
# Get MR ID with jq
gl branch mr --format json | jq -r '.merge_requests[0].iid'

# Get pipeline IDs with jq
gl mr 449 pipeline --format json | jq -r '.pipelines[].id'

# Get all failed job names
gl pipeline 12345 --format json | jq -r '.jobs[] | select(.status=="failed") | .name'
```

### Advanced jq Patterns
```bash
# Get pipeline duration in minutes
gl pipeline 12345 --format json | jq '.duration / 60 | floor'

# Count jobs by status
gl pipeline 12345 --format json | \
  jq '.jobs | group_by(.status) | map({status: .[0].status, count: length})'

# Get jobs from specific stage
gl pipeline 12345 --format json | \
  jq -r '.jobs[] | select(.stage=="test") | "\(.id): \(.name)"'

# Find long-running jobs (>10 minutes)
gl pipeline 12345 --format json | \
  jq -r '.jobs[] | select(.duration > 600) | "\(.name): \(.duration/60|floor) minutes"'
```

## Pro Tips

### 1. Performance Optimization
```bash
# Cache common IDs in variables to reduce API calls
export CURRENT_MR=$(gl branch mr --latest | grep MR_ID: | awk '{print $2}')
export CURRENT_PIPELINE=$(gl branch pipeline --limit 1 | grep PIPELINE_ID: | awk '{print $2}')
```

### 2. Use watch for Monitoring
```bash
# Auto-refresh with highlighted changes
watch -n 5 -d "gl pipeline $PIPELINE_ID"

# Monitor multiple pipelines
watch -n 10 "gl branch pipeline --limit 3"
```

### 3. Git Hook Integration
```bash
# In .git/hooks/pre-push
#!/bin/bash
gl branch pipeline --limit 1 | grep -q "Status: success" || {
  echo "Pipeline not passing, push aborted"
  exit 1
}
```

### 4. Process Substitution for Comparisons
```bash
# Compare pipelines between MRs
diff <(gl mr 449 pipeline --limit 5 | grep PIPELINE_ID:) \
     <(gl mr 450 pipeline --limit 5 | grep PIPELINE_ID:)
```

### 5. Tee for Logging
```bash
# Save output while viewing
gl pipeline $ID --jobs | tee pipeline_$(date +%Y%m%d_%H%M%S).log
```

### 6. Silent Checks with Exit Codes
```bash
# Deploy only if pipeline passed
gl branch pipeline --limit 1 | grep -q "success" && ./deploy.sh || echo "Pipeline not successful"
```

### 7. Parallel Processing
```bash
# Check multiple pipelines in parallel
for id in 12345 12346 12347; do
  gl pipeline $id --format json | jq -r '.status' &
done
wait
```

### 8. Tab Completion
```bash
# Install tab completion for faster typing
cd /path/to/gitlab-cli/completion
./install.sh
source ~/.bashrc  # or ~/.zshrc
```

## Debugging

```bash
# Show what's actually being extracted (reveals hidden characters)
gl branch mr | grep -E '(MR_ID|PIPELINE_ID):' | cat -A

# Debug pipeline issues with pretty printing
gl pipeline $ID --format json | jq . | less

# Time commands to find bottlenecks
time gl pipeline $ID --jobs

# Verbose mode for more details
gl --verbose pipeline $ID

# Check exit codes
gl branch pipeline --limit 1 | grep -q "success"
echo $?  # 0 if found, 1 if not
```

## Quick Reference Table

| Task | Command |
|------|---------|
| Follow latest pipeline | `gl pipeline $(gl branch pipeline --limit 1 \| grep PIPELINE_ID: \| awk '{print $2}') --follow` |
| Retry failed pipeline | `gl pipeline retry $(gl branch pipeline --status failed --limit 1 \| grep PIPELINE_ID: \| awk '{print $2}')` |
| Get second pipeline | `gl branch pipeline --limit 2 \| grep PIPELINE_ID: \| tail -1 \| awk '{print $2}'` |
| Open branch in browser | `gl branch --open` |
| Open MR in browser | `open $(gl branch mr --latest \| grep MR_URL: \| awk '{print $2}')` |
| Check if pipeline passed | `gl branch pipeline --limit 1 \| grep -q "success" && echo "✓" \|\| echo "✗"` |
| Get failed job IDs | `gl pipeline $ID --failed --format json \| jq -r '.jobs[].id'` |
| Tail running job | `gl job tail $(gl pipeline $ID --running --format json \| jq -r '.jobs[0].id')` |

## Notes

1. All IDs are numeric only (no prefix symbols like ! or #)
2. Pipeline and job lists are always sorted newest-first
3. Use `--limit N` to restrict results to most recent N items
4. Add `| head -1` to get only the first/latest result
5. The greppable format is consistent: `<TYPE>_ID:` followed by space and the ID
6. Use `--format json` with `jq` for complex queries - more reliable than grep/awk for structured data