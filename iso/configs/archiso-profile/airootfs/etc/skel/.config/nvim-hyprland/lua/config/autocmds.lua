-- Detect Hyprland config files automatically
vim.filetype.add({
  pattern = {
    [".*/hypr.*%.conf"] = "hyprlang",
  },
})
