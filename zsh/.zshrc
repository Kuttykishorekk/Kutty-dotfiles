# History configuration
export HISTFILE="$HOME/.config/zsh/.zsh_history"
export HISTSIZE=50000
export SAVEHIST=50000
setopt APPEND_HISTORY
setopt SHARE_HISTORY

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Plugins to load (Fast/unobtrusive autosuggestions and syntax highlighting)
# Standard OMZ plugins
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

# Version Manager - mise
eval "$(mise activate zsh)"

# Source Oh My Zsh
source $ZSH/oh-my-zsh.sh

# Starship Prompt configuration
export STARSHIP_CONFIG="$HOME/.config/starship/starship.toml"
eval "$(starship init zsh)"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# AI Integration - Mate Assistant
alias mate="~/.local/bin/mate"
alias mate-debug="~/.local/bin/mate-debug"
alias mate-packages="~/.local/bin/mate-packages"

# Environment Paths
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
export HSA_OVERRIDE_GFX_VERSION=11.0.3

# Custom Aliases
alias django_test="make django_test"

# Source custom plugins manually if they aren't in OMZ plugins path 
# (But they are in ~/.oh-my-zsh/custom/plugins, so OMZ handles them)
export PATH="$HOME/.local/bin:$PATH"


# Added by Antigravity CLI installer
export PATH="/home/kutty/.local/bin:$PATH"

# opencode
export PATH=/home/kutty/.opencode/bin:$PATH
export OPENROUTER_API_KEY="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"

export PATH="$HOME/.local/bin:$PATH"
