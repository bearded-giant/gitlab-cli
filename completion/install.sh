#!/usr/bin/env bash
# Install tab completion for gl (GitLab CLI)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing GitLab CLI tab completion..."

# Detect shell
if [ -n "$BASH_VERSION" ]; then
    SHELL_TYPE="bash"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_TYPE="zsh"
else
    echo "Unsupported shell. Only bash and zsh are supported."
    exit 1
fi

echo "Detected shell: $SHELL_TYPE"

# Install for Bash
if [ "$SHELL_TYPE" = "bash" ]; then
    # Check for bash-completion
    if [ -d "/usr/local/etc/bash_completion.d" ]; then
        # macOS with Homebrew
        COMPLETION_DIR="/usr/local/etc/bash_completion.d"
    elif [ -d "/opt/homebrew/etc/bash_completion.d" ]; then
        # macOS with Homebrew on Apple Silicon
        COMPLETION_DIR="/opt/homebrew/etc/bash_completion.d"
    elif [ -d "/etc/bash_completion.d" ]; then
        # Linux
        COMPLETION_DIR="/etc/bash_completion.d"
    else
        # User directory fallback
        COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
        mkdir -p "$COMPLETION_DIR"
    fi
    
    echo "Installing to: $COMPLETION_DIR/gl"
    cp "$SCRIPT_DIR/gl_completion.bash" "$COMPLETION_DIR/gl"
    
    # Add to bashrc if not already there
    if ! grep -q "gl_completion.bash" "$HOME/.bashrc" 2>/dev/null; then
        echo "" >> "$HOME/.bashrc"
        echo "# GitLab CLI completion" >> "$HOME/.bashrc"
        echo "[ -f $COMPLETION_DIR/gl ] && source $COMPLETION_DIR/gl" >> "$HOME/.bashrc"
    fi
    
    echo "✓ Bash completion installed"
    echo "  Reload your shell: source ~/.bashrc"
fi

# Install for ZSH
if [ "$SHELL_TYPE" = "zsh" ]; then
    # ZSH uses fpath for completions
    COMPLETION_DIR="$HOME/.zsh/completions"
    mkdir -p "$COMPLETION_DIR"
    
    echo "Installing to: $COMPLETION_DIR/_gl"
    cp "$SCRIPT_DIR/gl_completion.zsh" "$COMPLETION_DIR/_gl"
    
    # Add to zshrc if not already there
    if ! grep -q "fpath.*gl" "$HOME/.zshrc" 2>/dev/null; then
        echo "" >> "$HOME/.zshrc"
        echo "# GitLab CLI completion" >> "$HOME/.zshrc"
        echo "fpath=(~/.zsh/completions \$fpath)" >> "$HOME/.zshrc"
        echo "autoload -Uz compinit && compinit" >> "$HOME/.zshrc"
    fi
    
    echo "✓ ZSH completion installed"
    echo "  Reload your shell: source ~/.zshrc"
fi

echo ""
echo "Installation complete! Tab completion will be available after reloading your shell."
echo ""
echo "Examples:"
echo "  gl bra<TAB>           # Completes to 'gl branch'"
echo "  gl branch fea<TAB>    # Completes branch names starting with 'fea'"
echo "  gl branch --<TAB>     # Shows available flags"
echo "  gl pipeline --st<TAB> # Completes to '--status'"