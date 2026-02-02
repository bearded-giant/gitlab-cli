# Branch Commands

Branch commands provide contextual exploration of branches and their related resources (MRs, pipelines, commits, approvals).

## Branch Info

```bash
gl branch                           # current branch info
gl branch feature-xyz               # specific branch info
```

## Branch Resources

```bash
# pipelines
gl branch pipeline                  # pipelines for current branch (newest first)
gl branch feature-xyz pipeline      # pipelines for specific branch
gl branch pipeline --push           # only push pipelines (excludes merge_request_event)
gl branch pipeline --failed         # only failed pipelines
gl branch pipeline --passed         # only successful pipelines
gl branch pipeline --status running # specific status
gl branch pipeline --source web     # pipelines from web UI
gl branch pipeline --limit 5        # limit results

# merge requests
gl branch mr                        # MRs for current branch
gl branch feature-xyz mr            # MRs for specific branch
gl branch mr --state all            # all MRs (opened, merged, closed)
gl branch mr --limit 5              # limit results

# commits
gl branch commits                   # commits for current branch
gl branch feature-xyz commit        # commits for specific branch
```

## MR Operations

```bash
gl branch --create-mr               # open browser to create MR from current branch
gl branch --latest                  # show only the most recent MR
gl branch --open                    # open branch in browser
gl branch --open-mr                 # open the MR in browser
```

## MR Approvals

View approval status for the open MR on a branch.

```bash
gl branch approvals                 # approval status for current branch's MR
gl branch feature-xyz approvals     # approval status for specific branch's MR
gl branch approvals --format json   # JSON output
```

Output includes:
- approval status (approved or how many more needed)
- required approvals count
- who has approved
- approval rules with per-rule status
- eligible approvers per rule

## Notes

- GitLab Security Policy Bot pipelines are automatically filtered out from all pipeline listings
- `approvals` and `mr-approvals` are aliases for the same command
