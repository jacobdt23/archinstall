return {
  -- Tokyonight theme matching Hyprland (Standalone) & Orbit Suite
  {
    "folke/tokyonight.nvim",
    opts = {
      style = "night",
      transparent = false,
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "tokyonight-night",
    },
  },
  -- Ensure Hyprlang, Lua, Python, Bash, CSS, JSON treesitter parsers are installed
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      vim.list_extend(opts.ensure_installed, {
        "hyprlang",
        "lua",
        "python",
        "bash",
        "css",
        "json",
        "markdown",
        "toml",
      })
    end,
  },
}
