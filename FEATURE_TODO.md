# Feature TODO

## Pipeline Management
- [x] **Pipeline Retry/Cancel Commands** ✅
  - `gl pipelines retry <id>` - Retry failed jobs in pipeline
  - `gl pipelines cancel <id>` - Cancel running pipeline

## Job Management  
- [x] **Job Retry/Play Commands** ✅
  - `gl jobs retry <id>` - Retry a failed job
  - `gl jobs play <id>` - Play/trigger a manual job

## Pipeline Details
- [ ] **Pipeline Variables View**
  - `gl pipelines detail <id> --show-variables` - Show pipeline variables that were set
  - Include both predefined and user-defined variables

## Job Dependencies
- [ ] **Job Dependencies/Needs Visualization**
  - Show which jobs a job depends on ("needs")
  - Show which jobs depend on this job
  - Add to `gl jobs detail <id>` output

## Artifacts
- [ ] **Artifact Management**
  - `gl jobs artifacts <id>` - List artifacts for a job
  - `gl jobs artifacts <id> --download` - Download all artifacts
  - `gl jobs artifacts <id> --download-path <path>` - Download to specific location
  - `gl jobs artifacts <id> --download <name>` - Download specific artifact

## Pipeline Visualization
- [ ] **Pipeline Graph/DAG View (Text-based)**
  - ASCII representation of pipeline stages and job dependencies
  - Example:
    ```
    build → test → deploy
      ├─ build-app    ├─ unit-tests     ├─ deploy-prod
      └─ build-docs   ├─ integration     └─ cleanup
                      └─ lint
    ```
  - `gl pipelines graph <id>` or `gl pipelines detail <id> --graph`

## Time-based Features
- [ ] **Time-based Pipeline Filtering**
  - `gl pipelines --since "2 days ago"` - Recent pipelines
  - `gl pipelines --date 2024-01-15` - Pipelines from specific date
  - `gl pipelines --last 10` - Last N pipelines

## Pipeline Comparison
- [ ] **Compare Pipelines**
  - `gl pipelines compare <id1> <id2>` - Compare two pipelines
  - Show differences in:
    - Job statuses
    - Durations
    - Failed jobs
    - Variables

## Advanced Job Information
- [ ] **Job Resource Metrics**
  - Extract CPU/Memory usage from job logs if available
  - Show in `gl jobs detail <id>` when metrics exist

- [ ] **Schedule Information**
  - Show if pipeline was triggered by schedule
  - Display schedule name and next run time
  - Add to `gl pipelines detail <id>`

## Quality of Life Improvements
- [ ] **Interactive Mode**
  - `gl interactive` - Interactive pipeline/job browser
  - Navigate with arrow keys
  - Quick actions (retry, cancel, view logs)

- [ ] **Watch Mode**
  - `gl pipelines watch <id>` - Auto-refresh pipeline status
  - `gl jobs watch <id>` - Auto-refresh job status
  - Update the existing watch_pipeline.sh script to use new CLI

- [ ] **Pipeline Templates**
  - Save commonly used command combinations
  - `gl pipelines <id> --save-as check-failures`
  - `gl run check-failures <id>`

## Performance
- [ ] **Parallel API Calls**
  - When fetching multiple items, use concurrent requests
  - Especially useful for batch operations

- [ ] **Better Caching Strategy**
  - Cache job logs for completed jobs
  - Cache pipeline details for completed pipelines
  - Add cache management commands (`gl cache clear`, `gl cache stats`)

## Integration Features
- [ ] **Export Formats**
  - CSV export for pipeline/job data
  - Markdown reports for sharing
  - `--format csv`, `--format markdown`

- [ ] **Webhooks/Notifications**
  - `gl pipelines <id> --notify-on-complete`
  - Send notifications to Slack/Discord/Email when pipeline completes

## Notes
Priority should be on:
1. Retry/Cancel commands (most immediately useful)
2. Artifact handling
3. Pipeline graph visualization
4. Time-based filtering

These features would bring the CLI closer to feature parity with the GitLab UI while maintaining the power of command-line automation.