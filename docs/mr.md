# Merge Request Commands

MR commands provide contextual exploration of merge requests and their resources.

## MR Info

```bash
gl mr 1234                          # MR summary with quick actions
gl mr 1234 info                     # same as above (explicit)
gl mr detail 1234                   # detailed MR information
gl mr 1234,5678,9012                # multiple MRs at once
```

## Diff Commands

```bash
gl mr 1234 diff                     # diff using config default view
gl mr 1234 diff --view unified      # traditional git diff
gl mr 1234 diff --view inline       # inline diff with line numbers
gl mr 1234 diff --view split        # side-by-side diff
gl mr 1234 diff --stats             # statistics only
gl mr 1234 diff --name-only         # changed file names only
gl mr 1234 diff --file path/to/file # diff for specific file
gl mr 1234 diff --no-color          # disable color output
```

### Diff View Configuration

```bash
gl config set --diff-view split     # set split as default
gl config set --diff-view inline    # set inline as default
gl config set --diff-view unified   # set unified as default
gl config show                      # shows current diff_view setting
```

## MR Resources

```bash
gl mr 1234 pipeline                 # pipelines for MR
gl mr 1234 commit                   # commits in MR
gl mr 1234 discussion               # discussions/comments
```

## Search MRs

```bash
gl mr search                        # list all open MRs
gl mr search --author johndoe       # by author
gl mr search --assignee janedoe     # by assignee
gl mr search --reviewer bobsmith    # by reviewer
gl mr search --state merged         # merged MRs
gl mr search --state all            # all states
gl mr search --labels "bug,critical" # by labels
gl mr search --search "fix login"   # search title and description
gl mr search --target-branch main   # targeting main
gl mr search --wip                  # only drafts
gl mr search --created-after 3d     # created in last 3 days
gl mr search --updated-after "2 hours ago"
```

## Output Example

```
============================================================
MR !5678: Add checkout validation improvements
============================================================

Status:       OPENED
              DRAFT
Author:       Jane Smith (@jsmith)
Assignees:    @jdoe, @mike
Reviewers:    @alice, @bob

Branches:
  Source:     feature/checkout-validation
  Target:     main

Merge Status:
  All discussions resolved
  Has conflicts

Changes:
  Additions:  +245
  Deletions:  -89
  Total:      334 lines

Current Pipeline:
  failed (ID: 567890)

Labels: backend, checkout, needs-review
Milestone: Sprint 45

MR URL: https://gitlab.example.com/...
```
