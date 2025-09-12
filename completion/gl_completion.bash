#!/usr/bin/env bash
# Bash completion script for gl (GitLab CLI)

_gl_complete() {
    local cur prev words cword
    # Manual initialization for compatibility
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    words=("${COMP_WORDS[@]}")
    cword=$COMP_CWORD

    local commands="branch mr pipeline job config cache"
    
    # First level command
    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    # Handle branch name completion
    if [[ ${words[1]} == "branch" ]]; then
        # If we're at position 2 (after 'branch'), complete with branch names
        if [[ $cword -eq 2 ]]; then
            # Get git branches if we're in a git repo
            if git rev-parse --git-dir > /dev/null 2>&1; then
                local branches=$(git branch --format='%(refname:short)' 2>/dev/null)
                # Also add resource keywords
                local resources="mr pipeline commit info --open --create-mr"
                local all_options="$branches $resources"
                COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
            else
                # Not in git repo, just show resource options
                local resources="mr pipeline commit info --open --create-mr"
                COMPREPLY=($(compgen -W "$resources" -- "$cur"))
            fi
        elif [[ $cword -eq 3 ]]; then
            # After branch name, show resource options
            local resources="mr pipeline commit info"
            COMPREPLY=($(compgen -W "$resources" -- "$cur"))
        fi
        return
    fi

    # Handle MR ID completion  
    if [[ ${words[1]} == "mr" ]]; then
        if [[ $cword -eq 2 ]]; then
            # Could complete with MR IDs if we cache them
            local resources="search detail --help"
            # Try to get recent MR IDs from cache or recent commands
            COMPREPLY=($(compgen -W "$resources" -- "$cur"))
        elif [[ $cword -eq 3 ]]; then
            local resources="diff pipeline commit discussion approve info"
            COMPREPLY=($(compgen -W "$resources" -- "$cur"))
        fi
        return
    fi

    # Handle pipeline completion
    if [[ ${words[1]} == "pipeline" ]]; then
        if [[ $cword -eq 2 ]]; then
            local actions="list detail graph retry rerun cancel --follow --help"
            COMPREPLY=($(compgen -W "$actions" -- "$cur"))
        fi
        return
    fi

    # Handle job completion
    if [[ ${words[1]} == "job" ]]; then
        if [[ $cword -eq 2 ]]; then
            local actions="detail logs tail retry play --help"
            COMPREPLY=($(compgen -W "$actions" -- "$cur"))
        fi
        return
    fi

    # Handle flags
    case "$prev" in
        --format)
            COMPREPLY=($(compgen -W "friendly table json" -- "$cur"))
            return
            ;;
        --state)
            COMPREPLY=($(compgen -W "opened merged closed all" -- "$cur"))
            return
            ;;
        --status)
            COMPREPLY=($(compgen -W "success failed running pending canceled skipped manual created" -- "$cur"))
            return
            ;;
        --source)
            COMPREPLY=($(compgen -W "push web trigger schedule api external pipeline chat merge_request_event" -- "$cur"))
            return
            ;;
    esac

    # Generic flag completion
    if [[ "$cur" == -* ]]; then
        local flags="--help --verbose --format --limit --state --status --source --open --create-mr --follow --latest --push --passed --failed"
        COMPREPLY=($(compgen -W "$flags" -- "$cur"))
        return
    fi
}

# Register the completion function
complete -F _gl_complete gl