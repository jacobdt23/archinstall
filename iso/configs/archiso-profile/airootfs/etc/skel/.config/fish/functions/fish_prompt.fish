function fish_prompt --description 'Native Tokyo Night two-line prompt'
    set -l last_status $status

    # Colors (Tokyo Night palette)
    set -l user_color (set_color 7aa2f7 --bold)
    set -l host_color (set_color bb9af7 --bold)
    set -l at_color (set_color 565f89)
    set -l path_color (set_color 7dcfff)
    set -l reset (set_color normal)

    set -l user_host "$user_color$USER$at_color@$host_color"(prompt_hostname)"$reset"
    set -l pwd_str "$path_color"(prompt_pwd)"$reset"

    # Git status styling
    set -g __fish_git_prompt_showdirtystate 1
    set -g __fish_git_prompt_showuntrackedfiles 1
    set -g __fish_git_prompt_showstashstate 1
    set -g __fish_git_prompt_color_branch 9ece6a --bold
    set -g __fish_git_prompt_color_dirtystate f7768e
    set -g __fish_git_prompt_color_stagedstate e0af68
    set -g __fish_git_prompt_color_untrackedfiles 7aa2f7
    set -g __fish_git_prompt_char_dirtystate " ✗"
    set -g __fish_git_prompt_char_stagedstate " +"
    set -g __fish_git_prompt_char_untrackedfiles " …"
    set -g __fish_git_prompt_char_stashstate " ⚑"

    set -l vcs (fish_vcs_prompt)

    # Line 2 prompt symbol (green on success, red on error)
    set -l arrow_color (set_color 9ece6a --bold)
    if test $last_status -ne 0
        set arrow_color (set_color f7768e --bold)
    end

    echo -e "\n$user_host  $pwd_str$vcs"
    echo -n "$arrow_color❯$reset "
end
