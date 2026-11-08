function fish_right_prompt --description 'Native Tokyo Night right prompt'
    set -l time_color (set_color 565f89)
    set -l reset (set_color normal)
    echo -n "$time_color"(date "+%I:%M %p")"$reset"
end
