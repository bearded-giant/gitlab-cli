# GitLab CLI Tab Completion

Tab completion for the `gl` command to make it easier to work with branches, MRs, pipelines, and jobs.

## Features

- **Branch name completion**: `gl branch fea<TAB>` completes to `feature-xyz`
- **Command completion**: `gl bra<TAB>` completes to `gl branch`
- **Resource completion**: `gl branch <name> pi<TAB>` completes to `pipeline`
- **Flag completion**: `gl --for<TAB>` completes to `--format`
- **Value completion**: `gl --format <TAB>` shows `friendly table json`

## Installation

### Quick Install

```bash
cd completion
./install.sh
```

Then reload your shell:
```bash
# For bash
source ~/.bashrc

# For zsh
source ~/.zshrc
```

### Manual Installation

#### Bash

1. Copy the completion script:
```bash
# macOS with Homebrew
cp gl_completion.bash /usr/local/etc/bash_completion.d/gl

# Or to user directory
mkdir -p ~/.local/share/bash-completion/completions
cp gl_completion.bash ~/.local/share/bash-completion/completions/gl
```

2. Add to your `.bashrc`:
```bash
# Source the completion
[ -f ~/.local/share/bash-completion/completions/gl ] && source ~/.local/share/bash-completion/completions/gl
```

#### ZSH

1. Copy the completion script:
```bash
mkdir -p ~/.zsh/completions
cp gl_completion.zsh ~/.zsh/completions/_gl
```

2. Add to your `.zshrc`:
```bash
# Add to fpath
fpath=(~/.zsh/completions $fpath)
autoload -Uz compinit && compinit
```

## Usage Examples

### Branch Completion

```bash
# Complete branch names
gl branch fea<TAB>
# Expands to: gl branch feature-multi-product-sub-overviews

# Complete with options
gl branch --o<TAB>
# Expands to: gl branch --open
```

### Command Completion

```bash
# Complete commands
gl pip<TAB>
# Expands to: gl pipeline

# Complete subcommands
gl pipeline ret<TAB>
# Expands to: gl pipeline retry
```

### Resource Completion

```bash
# Complete MR resources
gl mr 449 pip<TAB>
# Expands to: gl mr 449 pipeline

# Complete branch resources
gl branch main pip<TAB>
# Expands to: gl branch main pipeline
```

### Flag Completion

```bash
# Complete flags
gl pipeline --fol<TAB>
# Expands to: gl pipeline --follow

# Complete flag values
gl --format <TAB>
# Shows: friendly  table  json

gl --status <TAB>
# Shows: success failed running pending canceled skipped manual created
```

## Supported Completions

### Commands
- `branch` - with git branch name completion
- `mr` - merge request operations
- `pipeline` - pipeline operations
- `job` - job operations
- `config` - configuration management
- `cache` - cache management

### Branch Resources
- `mr` - show MRs for branch
- `pipeline` - show pipelines for branch
- `commit` - show commits for branch
- `info` - show branch info

### MR Resources
- `diff` - show MR diff
- `pipeline` - show MR pipelines
- `commit` - show MR commits
- `discussion` - show MR discussions
- `approve` - approve MR
- `info` - show MR info

### Pipeline Actions
- `list` - list pipelines
- `detail` - show pipeline details
- `graph` - show pipeline graph
- `retry` - retry failed jobs
- `rerun` - create new pipeline
- `cancel` - cancel pipeline
- `--follow` - follow pipeline progress

### Common Flags
- `--format` - output format (friendly/table/json)
- `--state` - filter by state (opened/merged/closed/all)
- `--status` - filter by status
- `--limit` - limit number of results
- `--open` - open in browser
- `--create-mr` - create merge request
- `--follow` - follow progress
- `--latest` - show latest only

## Troubleshooting

### Completions not working

1. Make sure the completion script is sourced:
```bash
# Check if loaded (bash)
complete -p gl

# Check if loaded (zsh)
print -l $_comps[gl]
```

2. Reload your shell configuration:
```bash
exec $SHELL
```

3. For ZSH, rebuild completion cache:
```bash
rm -f ~/.zcompdump
compinit
```

### Branch names not completing

Branch name completion only works when you're in a git repository. The completion script uses `git branch` to get the list of branches.

## Customization

You can modify the completion scripts to add custom completions:

- **Bash**: Edit `gl_completion.bash` and update the `_gl_complete` function
- **ZSH**: Edit `gl_completion.zsh` and update the `_gl` function

For example, to add custom MR IDs:
```bash
# In bash completion
local common_mrs="449 450 451"
COMPREPLY=($(compgen -W "$common_mrs" -- "$cur"))
```