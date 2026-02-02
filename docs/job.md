# Job Commands

Job commands provide exploration, log access, and failure analysis for CI/CD jobs.

## Job Info

```bash
gl job 123456                      # job summary
gl job detail 123456               # comprehensive details
gl job 123456,123457,123458        # multiple jobs
gl job 123456 --failures           # show detailed failure info
```

## Logs

```bash
gl job logs 123456                 # full job logs/trace
gl job tail 123456                 # tail logs in real-time
```

## Actions

```bash
gl job retry 123456                # retry a failed job
gl job play 123456                 # play/trigger a manual job
```

## Smart Failure Extraction

`gl job logs` automatically detects job type and extracts relevant failures:

- **pytest**: test failures and assertions
- **pylint**: linting violations
- **mypy**: type checking errors
- **ruff**: linting errors
- **generic**: last 30 lines before failure

## Output Example

```
============================================================
integration test py parallel 1/100
============================================================

Status:       FAILED
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
  Status:     failed

Failure Details:
  FAILED tests/api/test_checkout.py::test_create_checkout
  FAILED tests/api/test_checkout.py::test_update_checkout

Job URL: https://gitlab.example.com/...
```
