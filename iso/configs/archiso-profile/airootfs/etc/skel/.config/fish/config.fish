fish_add_path -a $HOME/.local/bin

if status is-interactive
    set -g fish_greeting ""
    set -g fish_prompt_pwd_dir_length 0
    set -gx EDITOR orbit-nvim-cli
    set -gx VISUAL orbit-nvim-cli
    alias gs="git status"
    alias ll="ls -lah"

    if type -q fastfetch
        fastfetch
    end
    if type -q starship
        starship init fish | source
    end
end
