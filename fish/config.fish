alias cl="xclip -in -sel clip"
alias rl="readlink -f"
alias lf="find (pwd) -name"

# color 
set fish_color_command '#A0DDFF'
set fish_color_param '#FFAA55'
set fish_color_autosuggestion '#999999'

# vim 
# fish_vi_key_bindings
# function fish_mode_prompt
# end

# key_bindings
fish_default_key_bindings

# autojump
begin
    set --local AUTOJUMP_PATH $HOME/.autojump/share/autojump/autojump.fish
    if test -e $AUTOJUMP_PATH
        source $AUTOJUMP_PATH
    end
end

# fzf
set -gx FZF_LEGACY_KEYBINDINGS 0
set -gx FZF_CTRL_T_OPTS "--preview 'bat --color=always --style=header,grid --line-range :200 {}'"
set -gx FZF_DEFAULT_OPTS "--height 80% --reverse --border"
set -gx FZF_ALT_C_OPTS   "--preview 'tree -F -C {} | head -200'"
# set -gx FZF_CTRL_T_OPTS "--preview 'bat --color \"always\" {}' --height 90%"


# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/fumihiro.kubota/google-cloud-sdk/path.fish.inc' ]; . '/Users/fumihiro.kubota/google-cloud-sdk/path.fish.inc'; end
