# name: creeonix
# ---------------
# Based on crearance. Display the following bits on the left:
# - Virtualenv name (if applicable, see https://github.com/adambrenecki/virtualfish)
# - Current directory name
# - Git branch and dirty state (if inside a git repo)

function _git_branch_name
  echo (command git symbolic-ref HEAD ^/dev/null | sed -e 's|^refs/heads/||')
end

function _git_is_dirty
  echo (command git status -s --ignore-submodules=dirty ^/dev/null)
end

function fish_prompt
  set -l last_status $status

  set -l cyan (set_color cyan)
  set -l yellow (set_color yellow)
  set -l red (set_color red)
  set -l blue (set_color blue)
  set -l green (set_color green)
  set -l normal (set_color normal)
  set -l gray (set_color 999)

  set -l cwd $blue(pwd | sed "s:^$HOME:~:")

  # Output the prompt, left to right

  # Add a newline before new prompts
  #echo -e ''

  # Display [venvname] if in a virtualenv
  if set -q VIRTUAL_ENV
      echo -n -s (set_color -b cyan black) '[' (basename "$VIRTUAL_ENV") ']' $normal ' '
  end

  # Terminate with a nice prompt char
  echo -e ''
  # Display current time
  echo -e -s $gray '[' $green (whoami) '@' (hostname) $gray'] ' $normal
  # Print pwd or full path
  echo -n $cwd $normal

  # Show git branch and status
  if [ (_git_branch_name) ]
    set -l git_branch (_git_branch_name)

    if [ (_git_is_dirty) ]
      set git_info $red '(' $git_branch ')' $normal
    else
      set git_info $green '(' $git_branch ')' $normal
    end
    echo -n -s ' · ' $git_info $normal
  end

  set -l prompt_color $red
  if test $last_status = 0
    set prompt_color $normal
  end

  echo -e ''
  # vim
#    if test -z (string match -ri '^no|false|0$' $tomita_vi_mode)
#    printf '['
#    switch $fish_bind_mode
#      case default
#        set_color --bold red
#        printf 'N'
#      case insert
#        set_color --bold green
#        printf 'I'
#      case visual
#        set_color --bold magenta
#        printf 'N'
#    end
#    set_color normal
#    printf '] '
#  end

  # fish icon
  echo -e -n -s $prompt_color '⋊  ' $normal
end
