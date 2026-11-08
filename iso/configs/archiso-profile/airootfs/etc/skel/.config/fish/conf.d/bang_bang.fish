# Native !! and !$ expansion for Fish
function __history_previous_command_run
    switch (commandline -t)
        case "!"
            commandline -t ""
            commandline -i -- $history[1]
        case "*"
            commandline -i !
    end
end

function __history_previous_command_arg
    switch (commandline -t)
        case "!"
            commandline -t ""
            commandline -f history-token-search-backward
        case "*"
            commandline -i '$'
    end
end

if status is-interactive
    bind ! __history_previous_command_run
    bind '$' __history_previous_command_arg
end
