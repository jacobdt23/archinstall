fish_add_path -a $HOME/.local/bin
set -gx OMARCHY_PATH /usr/share/omarchy

if status is-interactive
    set -g fish_greeting ""
    set -g fish_prompt_pwd_dir_length 0

    alias v="nvim"
    alias gs="git status"
    alias ll="ls -lah"

    if type -q fastfetch
        fastfetch
    end
end
