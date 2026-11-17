#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Omarchy PATH, environment, shell prompt, and aliases
if [ -r /usr/share/omarchy/default/bash/env-bootstrap ]; then
  . /usr/share/omarchy/default/bash/env-bootstrap
fi

if [ -r /usr/share/omarchy/default/bash/rc ]; then
  . /usr/share/omarchy/default/bash/rc
fi

[[ ":$PATH:" != *":$HOME/.local/bin:"* ]] && export PATH="$PATH:$HOME/.local/bin"
