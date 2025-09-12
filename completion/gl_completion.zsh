#compdef gl
# ZSH completion script for gl (GitLab CLI)

_gl() {
    local context state line
    typeset -A opt_args

    # Main commands
    local -a commands
    commands=(
        'branch:Show branch information and related resources'
        'mr:Show MR information and related resources'
        'pipeline:Show pipeline information and jobs'
        'job:Show job information and logs'
        'config:Manage configuration'
        'cache:Manage cache'
    )

    # First argument - main command
    if (( CURRENT == 2 )); then
        _describe 'command' commands
        return
    fi

    # Handle subcommands based on the main command
    case "${words[2]}" in
        branch)
            if (( CURRENT == 3 )); then
                # Complete with git branch names and options
                local -a branches options
                if git rev-parse --git-dir > /dev/null 2>&1; then
                    branches=(${(f)"$(git branch --format='%(refname:short)' 2>/dev/null)"})
                fi
                options=(
                    '--open:Open branch in browser'
                    '--create-mr:Create merge request'
                    'mr:Show merge requests'
                    'pipeline:Show pipelines'
                    'commit:Show commits'
                    'info:Show branch info'
                )
                _alternative \
                    'branches:branch name:compadd -a branches' \
                    'options:option:compadd -a options'
            elif (( CURRENT == 4 )); then
                # After branch name, show resources
                local -a resources
                resources=(mr pipeline commit info)
                _describe 'resource' resources
            fi
            ;;
            
        mr)
            if (( CURRENT == 3 )); then
                # MR ID or actions
                local -a actions
                actions=(
                    'search:Search MRs'
                    'detail:Show detailed MR info'
                )
                _describe 'action' actions
                _message 'MR ID'
            elif (( CURRENT == 4 )); then
                # MR resources
                local -a resources
                resources=(
                    'diff:Show MR diff'
                    'pipeline:Show MR pipelines'
                    'commit:Show MR commits'
                    'discussion:Show MR discussions'
                    'approve:Approve MR'
                    'info:Show MR info'
                )
                _describe 'resource' resources
            fi
            ;;
            
        pipeline)
            if (( CURRENT == 3 )); then
                local -a actions
                actions=(
                    'list:List pipelines'
                    'detail:Show pipeline details'
                    'graph:Show pipeline graph'
                    'retry:Retry failed jobs'
                    'rerun:Create new pipeline'
                    'cancel:Cancel pipeline'
                    '--follow:Follow pipeline progress'
                )
                _describe 'action' actions
                _message 'pipeline ID'
            fi
            ;;
            
        job)
            if (( CURRENT == 3 )); then
                local -a actions
                actions=(
                    'detail:Show job details'
                    'logs:Show job logs'
                    'tail:Tail job logs'
                    'retry:Retry job'
                    'play:Play manual job'
                )
                _describe 'action' actions
                _message 'job ID'
            fi
            ;;
    esac

    # Global options
    _arguments \
        '--help[Show help]' \
        '--verbose[Verbose output]' \
        '--format[Output format]:format:(friendly table json)' \
        '--limit[Limit results]:number:' \
        '--state[Filter by state]:state:(opened merged closed all)' \
        '--status[Filter by status]:status:(success failed running pending canceled skipped manual created)' \
        '--source[Filter by source]:source:(push web trigger schedule api external pipeline chat merge_request_event)' \
        '--open[Open in browser]' \
        '--create-mr[Create merge request]' \
        '--follow[Follow progress]' \
        '--latest[Show latest only]' \
        '--push[Push pipelines only]' \
        '--passed[Passed pipelines only]' \
        '--failed[Failed items only]'
}

_gl "$@"