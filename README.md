# Kutty's Dotfiles 🚀

A portable configuration repository for **Hyprland**, **Caelestia**, and **QuickShell** desktop environments on Arch Linux. Easily restore your entire setup on any new machine.

## 📋 Contents

- **Hyprland** - Wayland compositor configuration
- **Caelestia** - Desktop environment configs
- **QuickShell** - GUI framework configurations
- **qylock** - Quickshell session lock (Clockwork theme + HyDE/hypridle wiring)

## 🚀 Quick Start

### On a Fresh Arch Install

Copy and paste this one-liner to restore everything:

```bash
git clone <repo-url> ~/kutty-dotfiles && cd ~/kutty-dotfiles && bash restore.sh
```

Or use the restore script directly:

```bash
bash restore.sh
```

### Manual Installation

```bash
# 1. Clone this repository
git clone <repo-url> ~/kutty-dotfiles
cd ~/kutty-dotfiles

# 2. Run the installer (handles Stow installation + symlink setup)
bash install.sh

# 3. Restart your session or source your shell config
exec $SHELL
```

## 📁 Repository Structure

```
kutty-dotfiles/
├── install.sh              # Main installation script
├── restore.sh              # Quick restore on new machines
├── README.md              # This file
├── .gitignore            # Files to exclude from git
├── hyprland/             # Hyprland configs
│   └── .config/hypr/     # Stow directory - will symlink to ~/.config/hypr
├── caelestia/            # Caelestia configs
│   └── .config/caelestia/
├── quickshell/           # QuickShell / Caelestia shell configs
│   └── .config/quickshell/
└── qylock/               # Session lock (qylock + clockwork theme)
    ├── .config/qylock/
    ├── .config/uwsm/
    ├── .local/bin/qylock
    └── .local/share/quickshell-lockscreen/
```

## 🔧 How It Works

This repository uses **GNU Stow** to manage symlinks. Each top-level directory (`hyprland/`, `caelestia/`, `quickshell/`) contains a `.config/` structure that mirrors your home directory.

When you run `install.sh`:
1. GNU Stow is installed (if needed)
2. Existing configs are backed up to `~/.config.backup-TIMESTAMP`
3. Symlinks are created from your home directory to the dotfiles repo

**Result:** Your configs stay in one place (the repo) and are accessible where the system expects them.

## 📝 Usage

### Update Your Configs

If you modify a config file in `~/.config/`, changes are automatically reflected in the repo (thanks to symlinks).

To push changes:
```bash
cd ~/kutty-dotfiles
git add .
git commit -m "Update Hyprland keybindings"
git push
```

### Pull Latest Changes on Another Machine

```bash
cd ~/kutty-dotfiles
git pull
stow -R hyprland caelestia quickshell  # Refresh symlinks
```

### Unstow All Configs

To remove all symlinks and revert to original file structure:

```bash
cd ~/kutty-dotfiles
stow -D hyprland caelestia quickshell
```

This leaves your files untouched; it only removes the symlinks.

## 🔒 Sensitive Data

This repository does **NOT** include:
- API keys or tokens
- Passwords or credentials
- Machine-specific local configs
- Secrets

If your configs reference external secret files, create them manually on each machine or use a separate secrets manager.

### Adding a Template for Secrets

If a config file contains a template for secrets, it will be named `*.example`:
```bash
# Example template (copy and fill in locally)
cp ~/.config/mysoftware/secrets.example ~/.config/mysoftware/secrets.conf
# Edit and add your actual secrets
nano ~/.config/mysoftware/secrets.conf
```

## 🛠️ Prerequisites

- **Arch Linux** (or compatible distro)
- **Git**
- **GNU Stow** (auto-installed by `install.sh`)

## 📦 System Backups

Before running `install.sh`, the installer automatically backs up your existing configs:

```
~/.config.backup-20260520_105843/
├── hypr/
├── caelestia/
└── quickshell/
```

If something goes wrong, you can restore from this backup.

## 🐛 Troubleshooting

### Symlinks not created?
- Run `stow -v hyprland` to see verbose output
- Check for permission issues: `ls -la ~/.config/`
- Ensure config directories don't already exist as symlinks

### Conflicts when stowing?
- The installer backs up existing configs
- Remove conflicting files: `rm -rf ~/.config/hypr`
- Run `bash install.sh` again

### How do I update a config?
- Edit the file in `~/.config/` (which is a symlink to the repo)
- Commit and push from the `kutty-dotfiles` directory
- On other machines, just `git pull` and restart your session

## 🚀 For New Machines

1. Fresh Arch install
2. Install git: `sudo pacman -S git`
3. Run: `bash restore.sh`
4. Done! 🎉

## 📚 Resources

- [GNU Stow Documentation](https://www.gnu.org/software/stow/)
- [Hyprland Documentation](https://wiki.hyprland.org/)
- [Dotfiles Best Practices](https://chezmoi.io/user-guide/best-practices/)

## 📝 License

This is a personal configuration repository. Feel free to use as reference or inspiration for your own dotfiles.

---

**Last Updated:** May 2026  
**Maintainer:** Kutty
