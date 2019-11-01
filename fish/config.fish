alias cl="xclip -in -sel clip"
alias rl="readlink -f"

#peco
function fish_user_key_bindings
    bind \cr peco_select_history
end

# color 
set fish_color_command '#A0DDFF'
set fish_color_param '#FFAA55'
set fish_color_autosuggestion '#999999'

# vim 
fish_vi_key_bindings
function fish_mode_prompt
end

# autojump
begin
    set --local AUTOJUMP_PATH $HOME/.autojump/share/autojump/autojump.fish
    if test -e $AUTOJUMP_PATH
        source $AUTOJUMP_PATH
    end
end
