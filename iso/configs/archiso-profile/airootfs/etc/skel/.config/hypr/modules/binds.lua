local mainMod = "SUPER"

-- Core App Binds
hl.bind(mainMod .. " + RETURN", hl.dsp.exec_cmd("kitty"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd("thunar"))
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd("quickshell ipc call welcome toggle"))
hl.bind(mainMod .. " + C", hl.dsp.window.close())
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd("discord"))

-- App Launcher / Menu (Scriptless Native Quickshell IPC Call)
hl.bind("SUPER + Super_L", hl.dsp.exec_cmd("quickshell ipc call drawer toggle"), { release = true })
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd("quickshell ipc call drawer toggle"))

-- System Management
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd("notify-send 'Quickshell' 'Active!'"))
hl.bind(mainMod .. " + SHIFT + R", hl.dsp.exec_cmd("sh -c 'hyprctl reload && notify-send \"Hyprland\" \"Reloaded!\"'"))
hl.bind(mainMod .. " + SHIFT + I", hl.dsp.exec_cmd("/usr/local/bin/launch-calamares"))

-- Quickshell Menus
hl.bind(mainMod .. " + K", hl.dsp.exec_cmd("quickshell ipc call keybinds toggle"))
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd("quickshell ipc call powermenu toggle"))
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("quickshell ipc call notifications toggle"))
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("quickshell ipc call media toggle"))
hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("quickshell ipc call clipboard toggle"))
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("quickshell ipc call calendar toggle"))
hl.bind(mainMod .. " + I", hl.dsp.exec_cmd("quickshell ipc call controlcenter toggle"))

-- Window Management
hl.bind(mainMod .. " + V", hl.dsp.exec_cmd("hyprctl dispatch togglefloating"))
hl.bind(mainMod .. " + P", hl.dsp.exec_cmd("hyprctl dispatch pseudo"))
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))
hl.bind(mainMod .. " + TAB", hl.dsp.focus({ monitor = "+1" }))

-- Move focus
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

for i = 1, 10 do
    local key = i % 10
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i}))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.exec_cmd("hyprctl dispatch movetoworkspace special:magic"))

-- Mouse Window Interactions
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })
hl.bind("mouse:274", hl.dsp.window.drag(), { mouse = true })

-- Native Quickshell Volume Controls
hl.bind(mainMod .. " + equal", hl.dsp.exec_cmd("quickshell ipc call volume up"), { repeating = true })
hl.bind(mainMod .. " + minus", hl.dsp.exec_cmd("quickshell ipc call volume down"), { repeating = true })
hl.bind(mainMod .. " + BackSpace", hl.dsp.exec_cmd("quickshell ipc call volume mute"))
