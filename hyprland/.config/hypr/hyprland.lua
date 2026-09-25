-- Hyprland loads this file when it is started without a config, and it prefers
-- it over hyprland.conf. HyDE loads it too, last, as the override layer below.
-- The block keeps the two apart: hyde.lua sets `hyde` on its first line, so it
-- runs only when this file is the entry point and HyDE has not been loaded.
-- Removing it leaves a session with a cursor and nothing else.
if not hyde then
	local share = os.getenv("XDG_DATA_HOME") or (os.getenv("HOME") .. "/.local/share")
	local entry = share .. "/hypr/hyde.lua"
	local handle = io.open(entry, "r")
	if not handle then
		error("HyDE is not installed at " .. entry .. ". Run install.sh -r, or point Hyprland at your own config.")
	end
	handle:close()
	dofile(entry)
end

-- * You can freely edit this file, but make sure to not remove the above line!

-- * All Files Below are yours to modify!

-- !      ░▒▒▒░░░▓▓           ___________

-- !    ░░▒▒▒░░░░░▓▓         //___________/

-- !   ░░▒▒▒░░░░░▓▓      _   _ _     _ _____

-- !   ░░▒▒░░░░░▓▓▓▓▓▓ | | | | |   | |  __/

-- !    ░▒▒░░░░▓▓   ▓▓ | |_| | |_/ /| |___

-- !     ░▒▒░░▓▓   ▓▓    \__  |____/ |____/

-- !      ░▒▓▓   ▓▓  //____/

-- ------------------------------------------------------

-- TODO Please remove this block if you are sure $HYPRLAND_CONFIG is set

-- ? This is only use for fallback

-- -------------------------------------------------------

-- ? Read https://hydeproject.pages.dev/en/configuring/hyprland/ for the full documentation.

-- HyprMod managed settings
require("hyprland-gui")

-- Keyboard layout: English US
hl.config({
	general = {
		layout = "hy3",
	},
	group = {
		groupbar = {
			enabled = false,
		},
	},
	input = {
		kb_layout = "fr",
		numlock_by_default = false,
		follow_mouse = 1,
		mouse_refocus = true,
		sensitivity = 0.5,
		accel_profile = "flat",
		touchpad = {
			natural_scroll = true,
			scroll_factor = 3.0,
			disable_while_typing = true,
		},
	},
})

-- Disable waybar (using Caelestia shell instead)
hyde.config.start.bar = ""

-- Caelestia Shell & cleanup
hl.exec_cmd("hyprctl dispatch exec 'pgrep -x quickshell || caelestia shell -d'")
hl.exec_cmd("hyprctl dispatch exec 'pkill waybar'")
hl.exec_cmd("hyprctl dispatch exec '~/.local/bin/hypr-plugins-boot.sh'")

-- Start awww wallpaper daemon
hl.exec_cmd("hyprctl dispatch exec 'pgrep -x awww-daemon || awww-daemon --format xrgb'")

-- Start HyprPet desktop pet daemon on boot
hl.exec_cmd("hyprctl dispatch exec 'pgrep -f \"python3.*hyprpet.py\" || ~/.local/bin/hyprpet'")

-- ═══════════════════════════════════════════════════════════
--  Custom keybinding overrides (restored from old config)
-- ═══════════════════════════════════════════════════════════
local MOD = hyde.config.modifiers.main

-- Override Super+B: Caelestia toggle (HyDE default is browser)
hl.bind(MOD .. " + B", hl.dsp.exec_cmd("~/.local/bin/caelestia-toggle.sh"),
	{description = "[Caelestia Shell] toggle bar"})

-- Super+W: toggle floating and fit
hl.bind(MOD .. " + W", function()
	-- Toggle floating, then resize+center to "fit"
	hl.dispatch(hl.dsp.window.float({action = "toggle"}))
	hl.dispatch(hl.dsp.window.center())
end,
	{description = "[Window Management] toggle floating and fit"})

-- Super+J: center floating or toggle split
hl.bind(MOD .. " + J", function()
	local w = hl.get_active_window()
	if w and w.floating == true then
		hl.dispatch(hl.dsp.window.center())
	else
		hl.dispatch(hl.dsp.layout("togglesplit"))
	end
end,
	{description = "[Window Management] center floating or toggle split"})

-- Caelestia Shell bindings
hl.bind(MOD .. " + Space", hl.dsp.exec_cmd("caelestia shell drawers toggle launcher"),
	{description = "[Caelestia Shell] toggle launcher"})
hl.bind(MOD .. " + D", hl.dsp.exec_cmd("caelestia shell drawers toggle dashboard"),
	{description = "[Caelestia Shell] toggle dashboard"})
hl.bind(MOD .. " + N", hl.dsp.exec_cmd("caelestia shell drawers toggle sidebar"),
	{description = "[Caelestia Shell] toggle sidebar"})
hl.bind(MOD .. " + H", hl.dsp.exec_cmd("~/.local/bin/caelestia-sidebar-toggle.sh"),
	{description = "[Caelestia Shell] sidebar toggle"})
hl.bind(MOD .. " + ALT + B", hl.dsp.exec_cmd("~/.local/bin/window-blur-toggle.sh"),
	{description = "[Caelestia Shell] window blur toggle"})
hl.bind(MOD .. " + SHIFT + N", hl.dsp.exec_cmd("caelestia shell notifs clear"),
	{description = "[Caelestia Shell] clear notifications"})

-- Emergency restore if Fn+F8 (Num Lock) or Phantom capture leaves keyboard stuck
hl.bind(MOD .. " + SHIFT + K", hl.dsp.exec_cmd("~/.local/bin/fix-keyboard-state.sh"),
	{description = "[Keyboard] emergency keyboard restore (Phantom/NumLock)"})
-- Phantom / Super Sus: toggle chat <-> gameplay (Super+Shift+Y)
hl.bind(MOD .. " + SHIFT + Y", hl.dsp.exec_cmd("~/.local/bin/phantom-toggle"),
	{description = "[Gaming] Super Sus toggle chat / gameplay"})

-- HyprPet desktop pet companion toggle (Super + ^ to start or kill)
hl.bind(MOD .. " + code:34", hl.dsp.exec_cmd("~/.local/bin/hyprpet-toggle"),
	{description = "[HyprPet] toggle desktop pet (start / kill)"})

-- Launcher apps (old keybindings)
local hyde_lib = os.getenv("HOME") .. "/.local/lib/hyde"
hl.bind(MOD .. " + T", hl.dsp.exec_cmd("kitty"),
	{description = "[Launcher|Apps] terminal emulator"})
hl.bind(MOD .. " + ALT + T", hl.dsp.exec_cmd("hyde-shell pypr toggle console"),
	{description = "[Launcher|Apps] dropdown terminal"})
hl.bind(MOD .. " + E", hl.dsp.exec_cmd("dolphin"),
	{description = "[Launcher|Apps] dolphin file explorer"})
hl.bind(MOD .. " + C", hl.dsp.exec_cmd("cursor"),
	{description = "[Launcher|Apps] text editor"})
hl.bind(MOD .. " + SHIFT + C", hl.dsp.exec_cmd("codium"),
	{description = "[Launcher|Apps] VSCodium"})
hl.bind(MOD .. " + SHIFT + W", hl.dsp.exec_cmd(hyde_lib .. "/wallpaper.sh -GS"),
	{description = "[Launcher|Wallpaper] wallpaper selector"})
hl.bind(MOD .. " + SHIFT + I", hl.dsp.exec_cmd(hyde_lib .. "/wallbashtoggle.sh --menu"),
	{description = "[HyDE] wallbash dark/light selector"})
hl.bind(MOD .. " + F", hl.dsp.exec_cmd("firefox"),
	{description = "[Launcher|Apps] web browser"})
hl.bind(MOD .. " + A", hl.dsp.exec_cmd(hyde_lib .. "/rofilaunch.sh d"),
	{description = "[Launcher|Rofi menus] application finder"})
hl.bind(MOD .. " + SHIFT + E", hl.dsp.exec_cmd(hyde_lib .. "/rofilaunch.sh f"),
	{description = "[Launcher|Rofi menus] file finder"})
hl.bind(MOD .. " + slash", hl.dsp.exec_cmd(hyde_lib .. "/keybinds_hint.sh c"),
	{description = "[Launcher|Rofi menus] keybindings hint"})
hl.bind(MOD .. " + comma", hl.dsp.exec_cmd(hyde_lib .. "/emoji-picker.sh"),
	{description = "[Launcher|Rofi menus] emoji picker"})
hl.bind(MOD .. " + period", hl.dsp.exec_cmd(hyde_lib .. "/glyph-picker.sh"),
	{description = "[Launcher|Rofi menus] glyph picker"})
hl.bind(MOD .. " + V", hl.dsp.exec_cmd(hyde_lib .. "/cliphist.sh -c"),
	{description = "[Launcher|Rofi menus] clipboard"})
hl.bind(MOD .. " + SHIFT + V", hl.dsp.exec_cmd(hyde_lib .. "/cliphist.sh"),
	{description = "[Launcher|Rofi menus] clipboard manager"})
hl.bind(MOD .. " + SHIFT + A", hl.dsp.exec_cmd(hyde_lib .. "/rofiselect.sh"),
	{description = "[Launcher|Rofi menus] select rofi launcher"})

-- French keyboard workspace bindings (keycodes)
for i = 1, 10 do
	local code = 9 + i
	hl.bind(MOD .. " + code:" .. code, hl.dsp.focus({workspace = i}),
		{description = "[Workspaces] navigate to workspace " .. i})
	hl.bind(MOD .. " + SHIFT + code:" .. code, hl.dsp.window.move({workspace = i}),
		{description = "[Workspaces] move to workspace " .. i})
end

-- Two separate secret scratchpads (Lua dispatchers, not hyprctl)
-- Super+S = secret   |  Super+R = scratchpad_R
hl.bind(MOD .. " + S", hl.dsp.workspace.toggle_special("secret"),
	{description = "[Workspaces] toggle secret workspace"})
hl.bind(MOD .. " + SHIFT + S", hl.dsp.window.move({workspace = "special:secret"}),
	{description = "[Workspaces] move window to secret workspace"})

hl.bind(MOD .. " + R", hl.dsp.workspace.toggle_special("scratchpad_R"),
	{description = "[Workspaces] toggle second secret workspace"})
hl.bind(MOD .. " + SHIFT + R", hl.dsp.window.move({workspace = "special:scratchpad_R"}),
	{description = "[Workspaces] move window to second secret workspace"})
hl.bind(MOD .. " + ALT + R", hl.dsp.window.move({workspace = "special:scratchpad_R", follow = false}),
	{description = "[Workspaces] move window to second secret (silent)"})

hl.bind(MOD .. " + O", hl.dsp.workspace.toggle_special("scratchpad_O"),
	{description = "[Workspaces] toggle third secret workspace"})
hl.bind(MOD .. " + SHIFT + O", hl.dsp.window.move({workspace = "special:scratchpad_O"}),
	{description = "[Workspaces] move window to third secret workspace"})
hl.bind(MOD .. " + ALT + O", hl.dsp.window.move({workspace = "special:scratchpad_O", follow = false}),
	{description = "[Workspaces] move window to third secret (silent)"})

-- Cursor / I-beam: hl.env (not late hyde.env) + software cursors.
-- hyde.env after finalize() does not export; HW KMS on this AMD iGPU
-- keeps left_ptr and never swaps text/ibeam (hyprwm#6065).
local CURSOR_THEME = "Bibata-Modern-Ice"
local CURSOR_SIZE = "24"
hl.env("XCURSOR_THEME", CURSOR_THEME)
hl.env("XCURSOR_SIZE", CURSOR_SIZE)
hl.env("HYPRCURSOR_THEME", CURSOR_THEME)
hl.env("HYPRCURSOR_SIZE", CURSOR_SIZE)
hyde.env("XCURSOR_THEME", CURSOR_THEME)
hyde.env("XCURSOR_SIZE", CURSOR_SIZE)
hyde.env("HYPRCURSOR_THEME", CURSOR_THEME)
hyde.env("HYPRCURSOR_SIZE", CURSOR_SIZE)
hyde.env.finalize()

hl.config({
	cursor = {
		enable_hyprcursor = true,
		sync_gsettings_theme = true,
		no_hardware_cursors = 1,
		hide_on_key_press = false,
	},
})

hl.exec_cmd("hyprctl setcursor " .. CURSOR_THEME .. " " .. CURSOR_SIZE)
hl.exec_cmd("gsettings set org.gnome.desktop.interface cursor-theme '" .. CURSOR_THEME .. "'")
hl.exec_cmd("gsettings set org.gnome.desktop.interface cursor-size " .. CURSOR_SIZE)


-- Re-apply animations (lua_state loads too early, so force it here)
hyde.config.anim.duration_scale = 6.0
dofile("/home/kutty/.local/state/hyde/lua_state/animations.lua")

-- Gestures: 3-finger swipe for workspace switching
hl.gesture({fingers = 3, direction = "horizontal", action = "workspace"})
hl.gesture({fingers = 3, direction = "vertical", action = "workspace"})

-- Window look from before the HyDE update (loads last so wallbash cannot override it)
hl.config({
	general = {
		gaps_in = 1,
		gaps_out = 8,
		border_size = 0,
		resize_on_border = false,
		col = {
			active_border = {colors = {"rgba(00000000)"}},
			inactive_border = {colors = {"rgba(00000000)"}},
		},
	},
	decoration = {
		rounding = 25,
		active_opacity = 0.95,
		inactive_opacity = 0.75,
		blur = {
			enabled = true,
			size = 5,
			passes = 4,
			ignore_opacity = true,
			new_optimizations = true,
			xray = false,
			noise = 0.0,
			popups = true,
		},
		dim_inactive = true,
		dim_strength = 0.08,
		shadow = {
			enabled = true,
			range = 15,
			scale = 19,
			render_power = 5,
			color = "rgba(40404066)",
			color_inactive = "rgba(60606066)",
		},
	},
	group = {
		col = {
			border_active = {colors = {"rgba(00000000)"}},
			border_inactive = {colors = {"rgba(00000000)"}},
			border_locked_active = {colors = {"rgba(00000000)"}},
			border_locked_inactive = {colors = {"rgba(00000000)"}},
		},
	},
})

-- Plugins (loaded via hyprpm): dynamic-cursors, hyprglass, hymission, hyprcapture
hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")

-- Only apply plugin options when the plugin is loaded (Hyprland wiki pattern).
-- hypr-plugins-boot.sh runs hyprpm reload, then hyprctl reload to apply these.
local function apply_plugin(name, opts)
	if hl.plugin[name] ~= nil then
		hl.config({plugin = {[name] = opts}})
	end
end

apply_plugin("dynamic_cursors", {
	enabled = true,
	mode = "tilt",
	threshold = 1,
	tilt = {
		limit = 3500,
		activation = "negative_quadratic",
		window = 80,
		full = 45,
	},
	stretch = {
		limit = 2500,
		activation = "negative_quadratic",
		window = 80,
	},
	shake = {
		enabled = true,
		threshold = 5.0,
		base = 3.5,
		speed = 4.0,
		influence = 0.0,
		limit = 0.0,
		timeout = 400,
		effects = true,
	},
	hyprcursor = {
		nearest = 1,
		enabled = true,
		resolution = -1,
		fallback = "clientside",
	},
})

-- Dynamic cursor shape rules:
-- 1) Text caret ('text', 'xterm', 'ibeam'): subtle tilt for precise text selection I-beam caret
-- 2) Window dragging ('grab'/'grabbing'): elastic stretch animation
if hl.plugin.dynamic_cursors then
	hl.plugin.dynamic_cursors.shape_rule({
		shape = "text",
		mode = "tilt",
		tilt = { full = 20 },
	})
	hl.plugin.dynamic_cursors.shape_rule({
		shape = "xterm",
		mode = "tilt",
		tilt = { full = 20 },
	})
	hl.plugin.dynamic_cursors.shape_rule({
		shape = "ibeam",
		mode = "tilt",
		tilt = { full = 20 },
	})
	hl.plugin.dynamic_cursors.shape_rule({
		shape = "grab",
		mode = "stretch",
		stretch = { limit = 1800 },
	})
	hl.plugin.dynamic_cursors.shape_rule({
		shape = "grabbing",
		mode = "stretch",
		stretch = { limit = 1800 },
	})
end

apply_plugin("hyprglass", {
	enabled = true,
	refraction_strength = 0.04,
	chromatic_aberration = 0.01,
	brightness = 0.9,
	contrast = 0.9,
	vibrancy = 0.2,
})

apply_plugin("hypr-kinetic-scroll", {
	enabled = 1,
	decel = 0.92,
	min_velocity = 0.5,
	interval_ms = 16,
	delta_multiplier = 1.25,
	disable_in_browser = 1,
	stop_on_target_change = 1,
})

apply_plugin("hymission", {})

-- hy3 (outfoxxed): i3/sway manual tiling. Official Lua API is hl.plugin.hy3.
-- https://github.com/outfoxxed/hy3 — Super+M is hy3:changegroup toggletab, not Hyprland groups.
apply_plugin("hy3", {
	autotile = {
		enable = true,
		ephemeral_groups = true,
	},
	tabs = {
		height = 22,
		padding = 6,
		from_top = true,
		radius = 8,
		border_width = 0,
		render_text = true,
		text_center = true,
		text_height = 10,
		text_padding = 8,
		blur = true,
		opacity = 0.92,
	},
})

local function hy3_bind(fn)
	return function()
		local hy3 = hl.plugin.hy3
		if not hy3 then
			return
		end
		fn(hy3)
	end
end

-- Super+M: toggle tabbed group (hy3:changegroup, toggletab)
-- Super+SHIFT+M is HyDE mute — leave it.
hl.bind(MOD .. " + M", hy3_bind(function(hy3)
	hy3.change_group("toggletab")()
end), {description = "[hy3] toggle tabbed group"})

-- README: replace movefocus / movewindow with hy3 dispatchers
local hy3_dirs = {Left = "l", Right = "r", Up = "u", Down = "d"}
for key, dir in pairs(hy3_dirs) do
	hl.bind(MOD .. " + " .. key, hy3_bind(function(hy3)
		hy3.move_focus(dir)()
	end), {description = "[hy3] focus " .. key:lower()})
	hl.bind(MOD .. " + SHIFT + CONTROL + " .. key, hy3_bind(function(hy3)
		hy3.move_window(dir)()
	end), {description = "[hy3] move window " .. key:lower()})
end

-- Cycle tabs in a hy3 tab group (wraps at the ends)
hl.bind(MOD .. " + ALT + Left", hy3_bind(function(hy3)
	hy3.focus_tab({direction = "l", wrap = true})()
end), {description = "[hy3] previous tab"})
hl.bind(MOD .. " + ALT + Right", hy3_bind(function(hy3)
	hy3.focus_tab({direction = "r", wrap = true})()
end), {description = "[hy3] next tab"})
hl.bind(MOD .. " + CTRL + H", hy3_bind(function(hy3)
	hy3.focus_tab({direction = "l", wrap = true})()
end), {description = "[hy3] previous tab"})
hl.bind(MOD .. " + CTRL + L", hy3_bind(function(hy3)
	hy3.focus_tab({direction = "r", wrap = true})()
end), {description = "[hy3] next tab"})

-- Hymission overview binds (replacing gloview/hyprspace for Super+Tab)
hl.bind(MOD .. " + TAB", function()
	hl.plugin.hymission.toggle()
end, {description = "[Workspaces] hymission overview toggle"})
hl.bind(MOD .. " + ALT + W", function()
	hl.plugin.hymission.toggle()
end, {description = "[Workspaces] hymission overview toggle"})

-- External Monitor Brightness Controls (ddcutil DDC/CI)
hl.bind(MOD .. " + SHIFT + F12", hl.dsp.exec_cmd("ddcutil setvcp 10 + 10"), {description = "[Display] external monitor brightness +10%"})
hl.bind(MOD .. " + SHIFT + F11", hl.dsp.exec_cmd("ddcutil setvcp 10 - 10"), {description = "[Display] external monitor brightness -10%"})


