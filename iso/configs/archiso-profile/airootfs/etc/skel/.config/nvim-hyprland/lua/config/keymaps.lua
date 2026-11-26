-- Keymaps loaded on VeryLazy
local map = vim.keymap.set
map("n", "<C-s>", "<cmd>w<cr>", { desc = "Save File" })
map("i", "<C-s>", "<esc><cmd>w<cr>a", { desc = "Save File" })
map("n", "<leader>fh", "<cmd>e ~/.config/hypr-standalone/hyprland.conf<cr>", { desc = "Edit Hyprland Config" })
