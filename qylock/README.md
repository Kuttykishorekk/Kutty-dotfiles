# qylock (Quickshell lockscreen)

Portable backup of the active qylock setup used with Hyprland + HyDE + Caelestia.

## Active theme
See `.config/qylock/theme` (currently `clockwork/orbital`).

## Restore (manual)
```bash
# From kutty-dotfiles root
cp -a qylock/.config/qylock ~/.config/
cp -a qylock/.config/uwsm/env.d/20-qylock.sh ~/.config/uwsm/env.d/
cp -a qylock/.config/uwsm/env-hyprland.d/20-qylock.sh ~/.config/uwsm/env-hyprland.d/
mkdir -p ~/.local/bin ~/.local/share
cp -a qylock/.local/bin/qylock ~/.local/bin/
chmod +x ~/.local/bin/qylock
rsync -a qylock/.local/share/quickshell-lockscreen/ ~/.local/share/quickshell-lockscreen/
# Optional: merge hyde lockscreen preference
# cp qylock/.config/hyde/config.toml ~/.config/hyde/config.toml
```

Extra themes: clone https://github.com/Darkkal44/qylock and point
`~/.local/share/quickshell-lockscreen/themes_link` at its `themes/` directory.
