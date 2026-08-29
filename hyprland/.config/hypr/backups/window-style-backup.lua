-- Backup of custom window styling — taken 2026-08-19
-- Paste this block at the END of hyprland.lua to restore window look

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
		dim_strength = 0.20,
		shadow = {
			enabled = true,
			range = 10,
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
