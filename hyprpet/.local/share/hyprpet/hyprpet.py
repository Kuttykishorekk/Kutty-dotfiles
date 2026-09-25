#!/usr/bin/env python3
"""
HyprPet - Modern Dynamic Desktop Companion for Hyprland (Wayland).
Featuring:
- Genshin Impact (Hu Tao, Klee, Ayaka, Venti) & Marvel (Spider-Man).
- Pixel-Perfect Dynamic Window Clinging:
  - Exact character hand-grip alignment against window borders (right or left).
  - Dynamic active window tracking (Hyprland IPC).
  - Rich climbing behaviors: climbing up, wall sliding, peeking inside, corner hanging, resting.
  - Interactive drag-to-snap and momentum toss.
- Presence profiles (focus / calm / lively): soft opacity, quieter idle, modern shadow polish.
- 100% Wayland Layer-Shell click-through transparency.
"""

import sys
import os
import time
import math
import random
import json
import subprocess
import socket
from collections import deque
from PIL import Image

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell
import cairo

# ----------------------------------------------------------------------
# Character Definitions & Dialogue
# ----------------------------------------------------------------------
CHARACTERS = {
    "hutao": {
        "name": "Hu Tao",
        "series": "Genshin Impact",
        "format": "genshin",
        "particle": "butterfly",
        "default_scale": 0.68,
        "climb_raw_facing": "LEFT",
        "hand_offset": 36.0,
        "feet_offset": 64.0,
        "hang_feet_offset": 64.0,
        "taunts": [
            "Yahoo! Hu Tao's here! Director of the Wangsheng Funeral Parlor! 👻",
            "Balmy breeze, butterflies fluttering... what a nice window! 🦋",
            "Aiya! What are you coding today? Looks interesting! ✨",
            "Clinging to your window frame! Don't mind me! 👻",
            "One client, two clients, three clients! Teehee~ ⚰️",
            "Sun's out, gotta go out! When rain comes, stay inside and code! ☔",
            "Need a spectral buddy to help find bugs? 🐞",
        ],
    },
    "klee": {
        "name": "Klee",
        "series": "Genshin Impact",
        "format": "genshin",
        "particle": "clover",
        "default_scale": 0.68,
        "climb_raw_facing": "LEFT",
        "hand_offset": 47.0,
        "feet_offset": 64.0,
        "hang_feet_offset": 64.0,
        "taunts": [
            "Spark Knight Klee, reporting for duty! 💣",
            "Fish blasting was banned by Master Jean... so I'm climbing windows! 🐟",
            "Dodoco is my best friend! Look! 🐰",
            "Yay! High places on windows are the best for throwing sparky treasures! ✨",
            "Boom boom bakudan! Everything's looking good! 💥",
            "No solitary confinement today! Woohoo! 🎈",
        ],
    },
    "ayaka": {
        "name": "Kamisato Ayaka",
        "series": "Genshin Impact",
        "format": "genshin",
        "particle": "sakura",
        "default_scale": 0.68,
        "climb_raw_facing": "LEFT",
        "hand_offset": 31.0,
        "feet_offset": 64.0,
        "hang_feet_offset": 64.0,
        "taunts": [
            "A pleasure to accompany you today. Shirasagi Himegimi at your service. 🌸",
            "The frost dances gracefully upon your windows... ❄️",
            "May your work flourish like the blossoms of Inazuma. ✨",
            "A tranquil moment amidst the bustling screen. 🍵",
        ],
    },
    "venti": {
        "name": "Venti",
        "series": "Genshin Impact",
        "format": "genshin",
        "particle": "feather",
        "default_scale": 0.68,
        "climb_raw_facing": "LEFT",
        "hand_offset": 47.0,
        "feet_offset": 64.0,
        "hang_feet_offset": 64.0,
        "taunts": [
            "Yahoo! The wind brought me to your desktop! 🍃",
            "Shall I compose a ballad about this awesome code? 🎶",
            "Climbing windows is breezy and fun! Ehe~ ✨",
            "May the wind guide your keystrokes! 🪶",
        ],
    },
    "spiderman": {
        "name": "Spider-Man",
        "series": "Marvel Comics",
        "format": "shimeji",
        "particle": "web",
        "default_scale": 0.68,
        "climb_raw_facing": "LEFT",
        "hand_offset": 44.0,
        "feet_offset": 64.0,
        "hang_feet_offset": 36.0,
        "taunts": [
            "Friendly neighborhood Spider-Man on window-climbing duty! 🕷️",
            "With great power comes great coding! 💻",
            "Just clinging to your window ledge... great view from here! 🏙️",
            "Thwip! Nice setup you got here! ✨",
            "Spidey senses tingling... no bugs detected! 🐞",
            "Doing my daily window workout! 🧗",
        ],
    },
}

CONFIG_FILE = os.path.expanduser("~/.local/share/hyprpet/config.json")

# Presence profiles: modern companion that stays out of the way by default.
# focus  = almost ambient edge buddy
# calm   = polished default (dynamic but not noisy)
# lively = classic playful shimeji energy
PRESENCE_PROFILES = {
    "focus": {
        "label": "Focus — minimal",
        "idle_alpha": 0.88,
        "active_alpha": 0.98,
        "pet_scale": 0.70,
        "cling_scale": 0.70,
        "free_scale": 0.70,
        "particle_mul": 0.12,
        "burst_cap": 1,
        "rest_bias": 0.55,
        "cling_duration": (18.0, 30.0),
        "wall_rest": (5.0, 10.0),
        "idle_think": (10.0, 18.0),
        "sit_time": (14.0, 26.0),
        "leap_chance": 0.08,
        "auto_taunt": False,
        "taunt_cooldown": 90.0,
        "hang_particle": 0.006,
        "climb_particle": 0.012,
        "slide_particle": 0.01,
        "sway": 1.2,
        "max_particles": 4,
    },
    "calm": {
        "label": "Calm — modern default",
        "idle_alpha": 0.94,
        "active_alpha": 1.0,
        "pet_scale": 0.78,
        "cling_scale": 0.78,
        "free_scale": 0.78,
        "particle_mul": 0.28,
        "burst_cap": 2,
        "rest_bias": 0.38,
        "cling_duration": (14.0, 24.0),
        "wall_rest": (3.5, 7.0),
        "idle_think": (6.0, 11.0),
        "sit_time": (9.0, 16.0),
        "leap_chance": 0.18,
        "auto_taunt": True,
        "taunt_cooldown": 48.0,
        "hang_particle": 0.012,
        "climb_particle": 0.025,
        "slide_particle": 0.02,
        "sway": 1.8,
        "max_particles": 8,
    },
    "lively": {
        "label": "Lively — playful",
        "idle_alpha": 1.0,
        "active_alpha": 1.0,
        "pet_scale": 0.85,
        "cling_scale": 0.85,
        "free_scale": 0.85,
        "particle_mul": 1.0,
        "burst_cap": 4,
        "rest_bias": 0.22,
        "cling_duration": (9.0, 16.0),
        "wall_rest": (2.5, 5.0),
        "idle_think": (2.0, 4.0),
        "sit_time": (4.5, 8.0),
        "leap_chance": 0.70,
        "auto_taunt": True,
        "taunt_cooldown": 14.0,
        "hang_particle": 0.04,
        "climb_particle": 0.08,
        "slide_particle": 0.07,
        "sway": 2.2,
        "max_particles": 12,
    },
}

# Force-throw gate (shimeji-style): only hard flings dismiss the pet
FORCE_THROW_SPEED = 920.0
FORCE_THROW_SPEED_HARD = 1400.0
FORCE_THROW_TRAVEL = 260.0
AWAY_DURATION_SOFT = (28.0, 45.0)
AWAY_DURATION_HARD = (45.0, 75.0)

# ----------------------------------------------------------------------
# Particle System
# ----------------------------------------------------------------------
class Particle:
    __slots__ = (
        "x", "y", "ptype", "text", "alpha_mul", "vx", "vy", "life", "decay",
        "alpha", "angle", "rot_speed", "alive",
    )

    def __init__(self):
        self.alive = False
        self.reset(0.0, 0.0, "sparkle", "", 1.0)

    def reset(self, x, y, ptype="sparkle", text="", alpha_mul=1.0):
        self.x = x
        self.y = y
        self.ptype = ptype
        self.text = text
        self.alpha_mul = max(0.15, min(1.0, alpha_mul))
        if ptype == "spark":
            self.vx = random.uniform(-45, 45)
            self.vy = random.uniform(-40, 15)
            self.decay = 3.2
        elif ptype == "bubble":
            self.vx = 0.0
            self.vy = -16.0
            self.decay = 0.28
        else:
            self.vx = random.uniform(-18, 18)
            self.vy = (
                random.uniform(-28, -10)
                if ptype in ["sparkle", "butterfly", "clover", "sakura", "feather", "web"]
                else -16.0
            )
            self.decay = 1.15 if ptype in ["butterfly", "clover", "sakura", "feather", "web"] else 1.85
        self.life = 1.0
        self.alpha = 1.0
        self.angle = random.uniform(0, math.pi * 2)
        self.rot_speed = random.uniform(-2.2, 2.2)
        self.alive = True
        return self

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.rot_speed * dt
        self.life -= self.decay * dt
        if self.ptype == "bubble":
            self.alpha = max(0.0, min(1.0, self.life * 1.35)) * self.alpha_mul
        else:
            self.alpha = max(0.0, self.life) * self.alpha_mul
        self.alive = self.life > 0
        return self.alive

    def draw(self, cr):
        if self.alpha <= 0:
            return
        cr.save()
        if self.ptype == "spark":
            cr.translate(self.x, self.y)
            cr.rotate(self.angle)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            # Golden outer glint
            cr.set_source_rgba(1.0, 0.76, 0.22, 0.95 * self.alpha)
            cr.set_line_width(1.6 * self.alpha)
            cr.move_to(-3.5 * self.alpha, 0)
            cr.line_to(3.5 * self.alpha, 0)
            cr.stroke()
            # Hot white core
            cr.set_source_rgba(1.0, 1.0, 0.95, 1.0 * self.alpha)
            cr.set_line_width(0.8 * self.alpha)
            cr.move_to(-1.8 * self.alpha, 0)
            cr.line_to(1.8 * self.alpha, 0)
            cr.stroke()
        elif self.ptype == "sparkle" or self.ptype == "web":
            cr.set_source_rgba(1.0, 0.88, 0.45, 0.55 * self.alpha)
            cr.arc(self.x, self.y, 2.0 * self.alpha, 0, 2 * math.pi)
            cr.fill()
        elif self.ptype == "butterfly":
            cr.translate(self.x, self.y)
            cr.rotate(self.angle)
            wing = math.sin(self.life * 14.0) * 0.55 + 0.85
            cr.set_source_rgba(1.0, 0.48, 0.22, 0.55 * self.alpha)
            cr.scale(wing, 1.0)
            cr.arc(-4, 0, 3.4, 0, 2 * math.pi)
            cr.fill()
            cr.arc(4, 0, 3.4, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgba(1.0, 0.92, 0.45, 0.65 * self.alpha)
            cr.arc(0, 0, 1.6, 0, 2 * math.pi)
            cr.fill()
        elif self.ptype == "clover":
            cr.translate(self.x, self.y)
            cr.rotate(self.angle)
            cr.set_source_rgba(0.25, 0.85, 0.38, 0.55 * self.alpha)
            for a in [0, math.pi/2, math.pi, math.pi * 1.5]:
                cx = math.cos(a) * 3.2
                cy = math.sin(a) * 3.2
                cr.arc(cx, cy, 2.6, 0, 2 * math.pi)
                cr.fill()
            cr.set_source_rgba(1.0, 0.88, 0.35, 0.55 * self.alpha)
            cr.arc(0, 0, 1.6, 0, 2 * math.pi)
            cr.fill()
        elif self.ptype == "sakura":
            cr.translate(self.x, self.y)
            cr.rotate(self.angle)
            cr.set_source_rgba(1.0, 0.74, 0.86, 0.50 * self.alpha)
            cr.scale(1.0, 1.45)
            cr.arc(0, 0, 3.2, 0, 2 * math.pi)
            cr.fill()
        elif self.ptype == "feather":
            cr.translate(self.x, self.y)
            cr.set_source_rgba(0.30, 0.90, 0.82, 0.55 * self.alpha)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(12)
            cr.move_to(0, 0)
            cr.show_text("♪")
        elif self.ptype == "bubble":
            # Soft floating caption — no chrome, short-lived, low visual weight
            cr.translate(self.x, self.y)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(12)
            extents = cr.text_extents(self.text)
            tx = -extents.width * 0.5
            ty = -10.0

            cr.set_source_rgba(0.0, 0.0, 0.0, 0.45 * self.alpha)
            for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                cr.move_to(tx + ox, ty + oy)
                cr.show_text(self.text)

            cr.set_source_rgba(1.0, 1.0, 1.0, 0.82 * self.alpha)
            cr.move_to(tx, ty)
            cr.show_text(self.text)
        cr.restore()

# ----------------------------------------------------------------------
# Main HyprPet Window Class
# ----------------------------------------------------------------------
class HyprPet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        # Layer Shell Setup — must be true fullscreen (zero margins) or the pet
        # draws past the surface and becomes invisible (seen: xywh 10,10,1108,732).
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "hyprpet")
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        for edge in (
            GtkLayerShell.Edge.TOP,
            GtkLayerShell.Edge.BOTTOM,
            GtkLayerShell.Edge.LEFT,
            GtkLayerShell.Edge.RIGHT,
        ):
            GtkLayerShell.set_margin(self, edge, 0)
        try:
            GtkLayerShell.set_exclusive_zone(self, -1)
        except Exception:
            pass
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        # RGBA Transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)

        # Event Masks
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("size-allocate", self.on_size_allocate)

        # Screen Dimensions — drawing space follows GTK allocation; Hyprland
        # geometry is mapped into this space via coord_off_* (layer insets).
        self.screen_width = 1128
        self.screen_height = 752
        self.coord_off_x = 0.0
        self.coord_off_y = 0.0
        self.hypr_screen_width = 1128.0
        self.hypr_screen_height = 752.0

        # Active Character Selection
        self.current_char = "hutao"
        self.presence_mode = "calm"
        self.draw_alpha = 0.96
        self.presence_boost = 0.0
        self.last_interaction = time.time()
        self.user_scale = None  # optional override from menu / IPC
        self.load_config()

        # Dynamic Hyprland Layout Metrics (Borders, Gaps, Rounding)
        self.hypr_border_size = 0.0
        self.hypr_rounding = 25.0
        self.hypr_shadow_range = 15.0
        self.hypr_glow = 0.0  # unused for cling — pets track window border, not shadow glow
        self.hypr_border_outset = 0.0  # general:border_size outward reach
        self.hypr_gap_top = 8.0
        self.hypr_gap_right = 8.0
        self.hypr_gap_bottom = 8.0
        self.hypr_gap_left = 8.0
        self.hypr_socket2 = None
        self.hypr_screen_width = 0.0
        self.hypr_screen_height = 0.0
        self.update_hyprland_layout_metrics()
        self.sync_screen_from_hypr()
        self.connect_hyprland_socket2()

        # Cache of loaded surfaces & auto-rigged limb geometries
        self.character_surfaces = {}
        self.sprite_rig_data = {}
        self.load_all_characters()

        # Physics Constants
        self.gravity = 1450.0
        self.restitution = 0.35
        self.air_drag = 0.992
        self.ground_friction = 0.86

        # State Machine & Dynamic Window Clinging Attributes
        self.state = "CLINGING"
        self.state_timer = 0.0
        self.anim_tick = 0.0
        self.cling_wall_x = float(self.screen_width)
        self.cling_side = "RIGHT"
        self.cling_min_y = 60.0
        self.cling_max_y = float(self.screen_height) - 12.0
        self.cling_mode = "WALL_REST"
        self.cling_mode_timer = 0.0
        self.cling_duration = 22.0
        self.cling_target_window = None
        self.cling_target_address = None
        self.cling_border_type = "SCREEN_RIGHT"
        self.cling_orbit = 1  # +1 clockwise around window, -1 counter-clockwise
        self.top_mode = "AUTO"  # LEDGE | CROUCH | UNDER — picked from live headroom
        self._top_mode_smooth = "LEDGE"
        # Modern ceiling cling / soft dangle
        self.hang_theta = 0.0
        self.hang_omega = 0.0
        self.hang_phase = random.uniform(0.0, math.pi * 2)
        self.hang_style = "crawl"  # prefer crawl; dangle only as completed phrase
        self.hang_style_timer = 0.0
        self.hang_anchor_x = 0.0
        self.hang_anchor_y = 0.0
        # Continuous motion controller — finish phrases before switching
        self.gait_phase = 0.0          # 0..1 stride cycle
        self.gait_cadence = 7.2        # strides per second (scaled by speed)
        self.move_speed = 0.0          # smoothed signed speed along edge
        self.move_speed_target = 0.0
        self.motion_name = "idle"
        self.motion_t = 0.0
        self.motion_dur = 0.0
        self.motion_lock = False       # True while a phrase must complete
        self.pending_intent = None     # queued next action after unlock
        self.edge_progress = 0.0       # 0..1 along current edge
        self._top_mode_committed = "LEDGE"

        # Smooth corner arc (outer path around Hyprland rounding)
        self.corner_t = 0.0
        self.corner_duration = 0.55
        self.corner_cx = 0.0
        self.corner_cy = 0.0
        self.corner_radius = 40.0
        self.corner_ang0 = 0.0
        self.corner_ang1 = 0.0
        self.corner_from = "RIGHT"
        self.corner_to = "TOP"
        self.corner_win = None
        self.corner_phase = "plant"  # plant | reach | pull | settle
        self.grip_catch_x = 0.0
        self.grip_catch_y = 0.0
        self.grip_reach_x = 0.0
        self.grip_reach_y = 0.0
        self.grip_reach_t = 0.0  # 0=at body, 1=locked on next edge
        self.corner_struggle = 0.0
        self.no_cling_timer = 0.0

        # Spider-Man Web Swinging
        self.web_active = False
        self.web_anchor_x = 0.0
        self.web_anchor_y = 0.0
        self.web_length = 0.0
        self.web_stiffness = 9.0
        self.web_duration = 0.0
        self.web_hand_x = 0.0
        self.web_hand_y = 0.0
        self.web_strands = 9
        self.web_phase = 0.0
        self.web_opacity = 0.0
        self.web_fade_speed = 2.2  # slower dissolve so the last swing stays readable
        self.crawl_web_points = []
        self._web_seed = random.random() * 1000.0
        self.web_swings_left = 0
        self.web_swing_index = 0
        self.web_ghosts = []  # fading previous strands (modern multi-swing look)
        self.web_tension = 0.0

        # Away / Break / Shoo Mechanics
        self.away_timer = 0.0
        self.away_duration = 45.0

        # Spatial Coordinates & Starting Habitat
        # Strictly Screen Borders & Window Borders (Never bottom of screen)
        self.base_render_scale = self.user_scale if self.user_scale else CHARACTERS[self.current_char]["default_scale"]
        prof0 = self.profile()
        self.render_scale = self.base_render_scale * float(prof0.get("pet_scale", prof0.get("cling_scale", 0.78)))
        rig = self.get_current_rig()
        half_w = rig["width"] * self.render_scale * 0.5
        self.x = float(self.screen_width) - half_w - 4.0
        self.y = self.screen_height * 0.40
        self.vx = 0.0
        self.vy = 0.0
        self.target_x = self.x
        # USER RULE: Outside borders face inward toward the window to stick/grip.
        self.facing = 1.0
        self.facing_scale = self.facing
        self.body_angle = 0.0
        self.target_body_angle = 0.0
        self.step_bob_y = 0.0

        # Soft-Body Spring Dynamics
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_vy = 0.0
        self.spring_k = 220.0
        self.spring_d = 14.0

        # Mouse Dragging
        self.is_dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        self.mouse_history = deque(maxlen=10)
        self.drag_origin_x = 0.0
        self.drag_origin_y = 0.0
        self.last_mouse_x = self.x
        self.last_mouse_y = self.y
        self._force_fling = False
        self._last_taunt_at = 0.0
        self._shape_dirty = True
        self._last_shape_key = None
        self._frame_tick_id = 0
        self._last_frame_us = 0
        self._idle_frame_accum = 0.0

        # Windows & Borders
        self.particles = []
        self._particle_pool = []
        self.platforms = []
        self.vertical_borders = []
        self.active_window = None
        self.last_platform_update = 0.0
        self.cling_border_type = "WIN_RIGHT"
        self.hang_on_screen = False

        # VSync-aligned game loop (GTK FrameClock) — falls back to 60Hz timeout
        self.last_time = time.time()
        self.connect("realize", self._on_realize_frame_clock)

        self.start_ipc_server()

        self.realize()
        self.update_input_shape()
        self.show_all()

    def _on_realize_frame_clock(self, *_args):
        if self._frame_tick_id:
            return
        try:
            self._frame_tick_id = self.add_tick_callback(self.on_frame_tick)
            print("[HyprPet] FrameClock tick (vsync) armed", flush=True)
        except Exception as e:
            print(f"[HyprPet] FrameClock unavailable ({e}); using 16ms timeout", flush=True)
            GLib.timeout_add(16, self.tick)

    def on_frame_tick(self, widget, frame_clock):
        """Compositor-synced update — smoother than fixed GLib timeout."""
        now_us = frame_clock.get_frame_time()
        if self._last_frame_us <= 0:
            self._last_frame_us = now_us
        dt = min(0.05, max(0.001, (now_us - self._last_frame_us) / 1_000_000.0))
        self._last_frame_us = now_us
        self.last_time = time.time()
        return self._tick_dt(dt)

    def bottom_pad(self):
        """Dynamic dock clearance matching Hyprland layout metrics with zero arbitrary air gap."""
        return float(getattr(self, "hypr_gap_bottom", 0.0))

    # ------------------------------------------------------------------
    # Presence / calm helpers
    # ------------------------------------------------------------------
    def profile(self):
        return PRESENCE_PROFILES.get(self.presence_mode, PRESENCE_PROFILES["calm"])

    def note_interaction(self, boost=1.0):
        self.last_interaction = time.time()
        self.presence_boost = max(self.presence_boost, min(1.0, boost))

    def emit(self, count, x, y, ptype="sparkle", text=""):
        """Spawn particles from a reuse pool (no alloc churn / hard RAM cap)."""
        prof = self.profile()
        cap = int(prof.get("max_particles", 8))
        if ptype == "bubble":
            # One speech bubble max
            self.particles = [p for p in self.particles if p.ptype != "bubble"]
            p = self._particle_pool.pop() if self._particle_pool else Particle()
            self.particles.append(p.reset(x, y, ptype, text, 0.9))
            return
        if random.random() > prof["particle_mul"] and count > 0:
            if random.random() > 0.35:
                return
            count = 1
        n = max(0, min(int(count), int(prof["burst_cap"])))
        if n <= 0 and prof["particle_mul"] > 0.5:
            n = 1
        room = max(0, cap - len(self.particles))
        n = min(n, room)
        for _ in range(n):
            p = self._particle_pool.pop() if self._particle_pool else Particle()
            self.particles.append(p.reset(
                x + random.uniform(-8, 8),
                y + random.uniform(-6, 6),
                ptype,
                text,
                0.55 + 0.35 * prof["particle_mul"],
            ))

    def _recycle_particles(self, dt):
        alive = []
        for p in self.particles:
            if p.update(dt):
                alive.append(p)
            elif len(self._particle_pool) < 24:
                p.alive = False
                self._particle_pool.append(p)
        self.particles = alive

    def set_presence(self, mode):
        if mode not in PRESENCE_PROFILES:
            return
        self.presence_mode = mode
        self.note_interaction(0.6)
        self.save_config()
        label = PRESENCE_PROFILES[mode]["label"]
        self.speak(f"{label}")

    def update_presence_visuals(self, dt):
        prof = self.profile()
        idle_for = time.time() - self.last_interaction
        self.presence_boost = max(0.0, self.presence_boost - dt * 0.35)

        active_states = {"DRAGGING", "FALLING", "SWINGING", "CORNER_ARC", "DANCE", "WAVE_HANDS", "SPECIAL"}
        if self.state in active_states or self.is_dragging or self.presence_boost > 0.15:
            target = prof["active_alpha"]
        elif idle_for > 40.0 and self.state in ("CLINGING", "SITTING", "WINDOW_TOP_HANG", "IDLE"):
            # Stay bright — only a tiny ease-off after long idle
            target = max(0.82, prof["idle_alpha"] * 0.92)
        else:
            target = prof["idle_alpha"] if self.state in ("CLINGING", "SITTING", "WINDOW_TOP_HANG", "IDLE", "AWAY") else prof["active_alpha"]

        # Blend toward target smoothly (modern, not snappy)
        self.draw_alpha += (target - self.draw_alpha) * min(1.0, dt * 3.0)

    def estimate_sprite_half_w(self):
        """Approximate visible half-width of the current sprite (logical px)."""
        try:
            bounds = self.get_rendered_bounds()
            return max(12.0, abs(bounds.get("width", 40.0)) * 0.5)
        except Exception:
            return max(12.0, 55.0 * float(self.render_scale))

    def compute_outward_cling_x(self, wall_x, side, is_screen, rounding_offset_x=0.0, glass_x=None):
        """Flush-stick to the live window border using per-frame grip reach.

        Uses solid hand/foot alpha (not faint fringe). Dig-in scales with
        render_scale so resize / scale changes stay glued with no hardcoded gap.
        """
        screen_w = float(self.screen_width)
        border = float(glass_x) if glass_x is not None else float(wall_x)
        bounds = self.get_rendered_bounds()
        rs = max(0.2, float(self.render_scale))
        grip_bite = max(1.2, 2.0 * rs)

        if side == "RIGHT":
            # Window is to pet's left. The leftmost hands (rel_grip_left, negative) touch the border.
            contact = float(bounds["rel_grip_left"])
            if is_screen:
                r_edge = float(bounds["rel_grip_right"])
                return max(24.0, screen_w - r_edge - grip_bite)
            # x + contact = border - grip_bite  ->  x = border - contact - grip_bite
            desired = border - contact - grip_bite + rounding_offset_x
            return min(screen_w - 2.0, desired)

        # Window is to pet's right (side == "LEFT"). The rightmost hands (rel_grip_right, positive) touch the border.
        contact = float(bounds["rel_grip_right"])
        if is_screen:
            l_edge = float(bounds["rel_grip_left"])
            return min(screen_w - 24.0, -l_edge + grip_bite)
        # x + contact = border + grip_bite  ->  x = border - contact + grip_bite
        desired = border - contact + grip_bite + rounding_offset_x
        return max(2.0, desired)

    def canonical_scale(self):
        """One coherent pet size for climb / run / slide / ledge / floor."""
        prof = self.profile()
        mul = float(prof.get("pet_scale", prof.get("cling_scale", 0.78)))
        return float(self.base_render_scale) * mul

    def emergency_scale_cap(self):
        """Only shrink when a gap would truly clip the pet — else None (full size)."""
        if self.state not in ("CLINGING", "CORNER_ARC", "WINDOW_TOP_HANG"):
            return None
        # Side outer gaps — maintain full canonical scale (no shrinking on sides)
        if self.state == "CLINGING" and self.cling_side in ("LEFT", "RIGHT"):
            return None
        # Top headroom — prefer UNDER pose over shrink; only mild cap for CROUCH
        if (self.state == "CLINGING" and self.cling_side == "TOP") or self.state == "WINDOW_TOP_HANG":
            mode = getattr(self, "top_mode", "LEDGE")
            if mode == "UNDER":
                return None  # hang under at full size
            win = self.cling_target_window
            if not win:
                return None
            headroom = self.measure_top_headroom(win)
            need_h = 95.0 * self.canonical_scale() / max(0.4, self.base_render_scale)
            if mode == "LEDGE" and headroom >= need_h * 0.9:
                return None
            if mode == "CROUCH":
                # Slight shrink only if still needed after crouch pose
                return max(floor, min(self.canonical_scale(), (headroom * 0.95) / 70.0))
            return None
        return None

    def fit_cling_scale_to_gap(self, side, glass, is_screen):
        """Compat no-op — coherent scale is driven by update_coherent_scale()."""
        return

    def fit_top_scale_to_headroom(self, headroom, mode):
        """Compat no-op — pose adapts; size stays coherent."""
        return

    def update_coherent_scale(self, dt):
        """Keep one size across all behaviors; rare emergency shrink only."""
        target = self.canonical_scale()
        cap = self.emergency_scale_cap()
        if cap is not None:
            target = min(target, float(cap))
        # Smooth but decisive — no cling/free bounce
        self.render_scale += (target - self.render_scale) * min(1.0, dt * 6.0)

    def begin_motion(self, name, duration, lock=True):
        """Start a motion phrase that should finish before the next big change."""
        self.motion_name = name
        self.motion_t = 0.0
        self.motion_dur = max(0.12, float(duration))
        self.motion_lock = bool(lock)

    def queue_intent(self, intent):
        """Queue an intent; runs only when the current phrase unlocks."""
        self.pending_intent = intent

    def motion_busy(self):
        return bool(self.motion_lock and self.motion_t < self.motion_dur)

    def tick_motion(self, dt):
        if self.motion_dur <= 0:
            self.motion_lock = False
            return
        self.motion_t += dt
        if self.motion_t >= self.motion_dur:
            self.motion_lock = False
            self.motion_name = "idle"
            intent = self.pending_intent
            self.pending_intent = None
            if intent:
                self._dispatch_intent(intent)

    def _dispatch_intent(self, intent):
        kind = intent.get("type")
        win = intent.get("win") or self.cling_target_window
        if kind == "corner" and win:
            self.transition_orbit_corner(win, intent.get("to_side", "LEFT"))
        elif kind == "hang_style":
            self.hang_style = intent.get("style", "crawl")
            self.hang_style_timer = 0.0
            self.begin_motion("hang_" + self.hang_style, intent.get("dur", 2.8), lock=True)
        elif kind == "top_mode":
            self._top_mode_committed = intent.get("mode", self.top_mode)
            self.top_mode = self._top_mode_committed
            self.begin_motion("mode_" + self.top_mode, 0.45, lock=True)

    def smooth_move_speed(self, dt, target, accel=140.0, decel=180.0):
        """Accelerate / brake toward target speed (no instant cuts)."""
        self.move_speed_target = float(target)
        cur = float(self.move_speed)
        if abs(target) < abs(cur) or (target * cur < 0):
            rate = decel
        else:
            rate = accel
        if cur < target:
            cur = min(target, cur + rate * dt)
        elif cur > target:
            cur = max(target, cur - rate * dt)
        self.move_speed = cur
        return cur

    def advance_gait(self, dt, speed):
        """Advance continuous biomechanical stride phase; returns (phase, plant 0..1, stride_mul, weight_roll)."""
        # Dynamic cadence scaling with velocity (slower deliberate reach, athletic push)
        cadence = self.gait_cadence * (0.60 + 0.40 * min(1.0, abs(speed) / 65.0))
        self.gait_phase = (self.gait_phase + dt * cadence) % 1.0
        # Smooth raised-cosine plant curve with contact cushioning
        plant = 0.5 - 0.5 * math.cos(self.gait_phase * math.pi * 2.0)
        # Biomechanical pull-and-coast velocity curve (push mid-stride, cushion at plant)
        stride_mul = 0.75 + 0.32 * math.sin(self.gait_phase * math.pi)
        # Alternating left/right weight-transfer roll (IK torso tilt)
        weight_roll = math.sin(self.gait_phase * math.pi * 2.0) * 0.052
        return self.gait_phase, plant, stride_mul, weight_roll

    def edge_end_factor(self, pos, start, end, travel, slow_dist=80.0):
        """Ultra-smooth quintic smootherstep brake factor approaching corner apex (no abrupt stops)."""
        if travel > 0:
            remain = end - pos
        else:
            remain = pos - start
        if remain >= slow_dist:
            return 1.0
        if remain <= 6.0:
            return 0.0
        # Quintic polynomial: 6t^5 - 15t^4 + 10t^3 (zero 1st & 2nd derivative at ends)
        t = max(0.0, min(1.0, remain / slow_dist))
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    def request_corner(self, win, to_side):
        """Approach-complete then turn or arc — never yank mid-stride."""
        if self.motion_busy() and self.motion_name.startswith("corner"):
            return
        # If mid-stride, finish current stride first (~remaining phase)
        remain = (1.0 - self.gait_phase) / max(0.5, self.gait_cadence)
        if abs(self.move_speed) > 12.0 and remain > 0.08:
            self.begin_motion("finish_stride", remain + 0.12, lock=True)
            self.queue_intent({"type": "corner", "win": win, "to_side": to_side})
            self.move_speed_target = 0.0
            return
        self.begin_motion("corner_" + to_side, 0.55, lock=True)
        self.transition_orbit_corner(win, to_side)

    def commit_top_mode(self, desired):
        """Change top pose only between strides (no mid-crawl pop)."""
        committed = getattr(self, "_top_mode_committed", desired)
        if desired == committed:
            self.top_mode = committed
            return committed
        if self.motion_busy():
            self.queue_intent({"type": "top_mode", "mode": desired})
            self.top_mode = committed
            return committed
        # Wait for near plant (gait_phase near 0 or 0.5)
        if 0.12 < (self.gait_phase % 0.5) < 0.38:
            self.top_mode = committed
            return committed
        self._top_mode_committed = desired
        self.top_mode = desired
        self.begin_motion("mode_" + desired, 0.4, lock=True)
        return desired

    def step_border_crawl(self, dt, axis, travel, target_speed, grip_pos, grip_axis_value):
        """Modern biomechanical border crawl along an axis ('x' or 'y') with hand-over-hand weight shift.

        grip_axis_value: the constant coordinate to spring toward (wall x or rail y).
        Returns plant for squash.
        """
        brake = 1.0
        # Caller may set move_speed_target already; apply smooth acceleration
        spd = self.smooth_move_speed(dt, travel * abs(target_speed) * brake, accel=130.0, decel=170.0)
        phase, plant, stride_mul, weight_roll = self.advance_gait(dt, spd)
        vel = spd * stride_mul

        if axis == "x":
            self.vx = vel
            self.vy = 0.0
            self.x += self.vx * dt
            # Spring grip to rail/sill Y with second-order smooth damping
            err = grip_axis_value - self.y
            self.vy = err * 36.0
            self.y += err * min(1.0, dt * 30.0)
        else:
            self.vy = vel
            self.vx = 0.0
            self.y += self.vy * dt
            err = grip_axis_value - self.x
            self.x += err * min(1.0, dt * 30.0)

        self.facing = 1.0 if travel > 0 else -1.0
        if axis == "y":
            # Vertical walls: facing is toward window
            pass
        else:
            self.facing_scale = self.facing

        # Biomechanical torso dynamics: directional lean + weight-shift roll + muscle effort
        if abs(spd) > 3.0:
            lean = max(-0.16, min(0.16, -travel * 0.06 + weight_roll + (plant - 0.5) * 0.04))
            self.target_body_angle += (lean - self.target_body_angle) * min(1.0, dt * 12.0)
            if axis == "x":
                # For horizontal rail/sill walking: soles stay firmly planted with 0 gap
                self.step_bob_y = 0.0
            else:
                self.step_bob_y = plant * 1.45 * self.render_scale
            # Muscle contraction squash during pull phase
            self.scale_y += ((1.0 - 0.055 * plant) - self.scale_y) * min(1.0, dt * 16.0)
            self.scale_x += ((1.0 + 0.040 * plant) - self.scale_x) * min(1.0, dt * 16.0)
        else:
            # Idle micro-breathing & living presence when pausing / stopped on window border
            breath = math.sin(self.anim_tick * 2.2) * 0.022
            self.target_body_angle += (0.0 - self.target_body_angle) * min(1.0, dt * 6.0)
            self.step_bob_y += (0.0 - self.step_bob_y) * min(1.0, dt * 8.0)
            self.scale_y += ((1.0 + breath) - self.scale_y) * min(1.0, dt * 6.0)
            self.scale_x += ((1.0 - breath * 0.6) - self.scale_x) * min(1.0, dt * 6.0)

        return plant

    def step_modern_underhang(self, dt, win, edge, travel):
        """Ceiling crawl under chrome — continuous horizontal crawl along rail using hands/feet, zero webs."""
        self.hang_style = "crawl"
        self.hang_style_timer += dt

        self.hang_anchor_x = self.x + travel * 4.0
        self.hang_anchor_y = float(edge)
        rest_y = self.compute_hang_y(edge)

        target = 48.0 * (1.05 if self.presence_mode == "lively" else 0.92)
        # Brake near ends
        brake = self.edge_end_factor(self.x, win["x1"] + 36.0, win["x2"] - 36.0, travel, slow_dist=80.0)
        spd = self.smooth_move_speed(dt, travel * target * max(0.15, brake))
        phase, plant, stride_mul, _ = self.advance_gait(dt, spd)
        self.vx = spd * stride_mul
        self.x += self.vx * dt
        target_y = rest_y
        self.y += (target_y - self.y) * min(1.0, dt * 35.0)
        self.hang_omega = 0.0
        self.hang_theta = 0.0
        self.target_body_angle = 0.0
        self.step_bob_y = 0.0
        self.scale_y += ((1.0 - 0.02 * plant) - self.scale_y) * min(1.0, dt * 14.0)
        self.scale_x += ((1.0 + 0.02 * plant) - self.scale_x) * min(1.0, dt * 14.0)

        self.facing = travel
        self.facing_scale = travel
        self.web_hand_x = self.x
        self.web_hand_y = float(edge)
        return True


    def draw_ceiling_hitch(self, cr, alpha=1.0):
        """Ultra HD top window attachment:
        - Spider-Man inverted web dangle: 7-layer procedural silk tether with piriform anchor plaque
        - Genshin / Hand-hang mode: Anatomically articulated character hands firmly clamping the top rail
        """
        edge_y = float(getattr(self, "hang_anchor_y", self.y - 30.0))
        rs = self.render_scale
        cformat = CHARACTERS[self.current_char].get("format", "genshin")

        if cformat == "shimeji":
            # Direct physical hand/foot grip on the window top rail — zero webs on top
            return

        # Physical Hand-Grips clutching the window's top rail
        cr.save()
        cr.set_antialias(cairo.ANTIALIAS_BEST)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        char_key = self.current_char
        palettes = {
            "spiderman": {
                "sleeve": (0.85, 0.12, 0.12),
                "sleeve_dark": (0.50, 0.06, 0.06),
                "cuff": (0.12, 0.12, 0.14),
                "glove": (0.85, 0.12, 0.12),
                "knuckle": (1.0, 0.40, 0.40),
            },
            "hutao": {
                "sleeve": (0.18, 0.14, 0.16),
                "sleeve_dark": (0.10, 0.08, 0.10),
                "cuff": (0.85, 0.65, 0.20),
                "glove": (0.95, 0.82, 0.75),
                "knuckle": (1.0, 0.92, 0.88),
            },
            "klee": {
                "sleeve": (0.82, 0.18, 0.16),
                "sleeve_dark": (0.52, 0.10, 0.08),
                "cuff": (0.96, 0.96, 0.96),
                "glove": (0.96, 0.86, 0.72),
                "knuckle": (1.0, 0.95, 0.85),
            },
            "ayaka": {
                "sleeve": (0.15, 0.20, 0.45),
                "sleeve_dark": (0.08, 0.12, 0.28),
                "cuff": (0.85, 0.75, 0.40),
                "glove": (0.75, 0.82, 0.95),
                "knuckle": (0.95, 0.98, 1.0),
            },
            "venti": {
                "sleeve": (0.92, 0.92, 0.90),
                "sleeve_dark": (0.68, 0.70, 0.68),
                "cuff": (0.18, 0.60, 0.45),
                "glove": (0.88, 0.78, 0.65),
                "knuckle": (0.98, 0.92, 0.82),
            },
        }
        pal = palettes.get(char_key, palettes["spiderman"])

        # Rotated shoulders
        cos_b = math.cos(self.body_angle)
        sin_b = math.sin(self.body_angle)
        def rot_offset(ox, oy):
            return ox * cos_b - oy * sin_b, ox * sin_b + oy * cos_b

        sh_l_ox, sh_l_oy = rot_offset(-7.0 * rs, -4.0 * rs)
        sh_r_ox, sh_r_oy = rot_offset(7.0 * rs, -4.0 * rs)
        sh_lx = self.x + sh_l_ox
        sh_ly = self.y - self.step_bob_y + sh_l_oy
        sh_rx = self.x + sh_r_ox
        sh_ry = self.y - self.step_bob_y + sh_r_oy

        # Hand grip points on the top rail
        step_phase = math.sin(self.anim_tick * 5.0) if getattr(self, "hang_style", "dangle") == "crawl" else 0.0
        hlx = self.x - 7.5 * rs - step_phase * (2.0 * rs)
        hly = edge_y
        hrx = self.x + 7.5 * rs + step_phase * (2.0 * rs)
        hry = edge_y

        arm_w = 2.2 * rs
        arm_outline = 3.2 * rs
        cuff_w = 2.6 * rs
        palm_r = 1.9 * rs
        knuckle_r = 0.80 * rs
        shadow_r = 2.0 * rs

        for (sx, sy, hx, hy) in [(sh_lx, sh_ly, hlx, hly), (sh_rx, sh_ry, hrx, hry)]:
            # Wrist at 78% of arm length
            wx = sx + (hx - sx) * 0.78
            wy = sy + (hy - sy) * 0.78

            # Arm shadow/outline
            cr.set_source_rgba(pal["sleeve_dark"][0], pal["sleeve_dark"][1], pal["sleeve_dark"][2], 0.80 * alpha)
            cr.set_line_width(arm_outline)
            cr.move_to(sx, sy)
            cr.line_to(wx, wy)
            cr.stroke()

            # Sleeve fill
            cr.set_source_rgba(pal["sleeve"][0], pal["sleeve"][1], pal["sleeve"][2], 0.95 * alpha)
            cr.set_line_width(arm_w)
            cr.move_to(sx, sy)
            cr.line_to(wx, wy)
            cr.stroke()

            # Cuff ring
            cr.set_source_rgba(pal["cuff"][0], pal["cuff"][1], pal["cuff"][2], 0.95 * alpha)
            cr.set_line_width(cuff_w)
            cr.move_to(wx - 2.0 * rs, wy)
            cr.line_to(wx + 2.0 * rs, wy)
            cr.stroke()

            # Glove palm
            cr.set_source_rgba(pal["glove"][0], pal["glove"][1], pal["glove"][2], 0.95 * alpha)
            cr.arc(hx, hy, palm_r, 0, 2 * math.pi)
            cr.fill()

            # Contact shadow cast on window rail
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.30 * alpha)
            cr.arc(hx, hy + 0.8 * rs, shadow_r, 0, 2 * math.pi)
            cr.fill()

            # 4 finger knuckles clamped over the top window border lip
            for k in [-1.5, -0.5, 0.5, 1.5]:
                kx = hx + k * (1.05 * rs)
                ky = hy - 0.8 * rs
                cr.set_source_rgba(pal["glove"][0] * 0.88, pal["glove"][1] * 0.88, pal["glove"][2] * 0.88, 0.95 * alpha)
                cr.arc(kx, ky, knuckle_r, 0, 2 * math.pi)
                cr.fill()
                cr.set_source_rgba(pal["knuckle"][0], pal["knuckle"][1], pal["knuckle"][2], 0.90 * alpha)
                cr.arc(kx - 0.2 * rs, ky - 0.2 * rs, 0.45 * rs, 0, 2 * math.pi)
                cr.fill()

        cr.restore()

    def screen_ceiling_y(self):
        """Top of usable layer space (Hyprland gap / bezel)."""
        return max(0.0, float(getattr(self, "hypr_gap_top", 0.0)))

    def measure_top_headroom(self, win):
        """Pixels available ABOVE the window top rail before the screen clips."""
        if not win:
            return 999.0
        edge = float(self.window_border_edge(win, "TOP"))
        ceiling = self.screen_ceiling_y()
        # Also respect layer surface top (0 in layer-local coords)
        ceiling = max(ceiling, 2.0)
        return max(0.0, edge - ceiling)

    def estimate_upright_height(self):
        """Approx full standing height in logical px (head→feet)."""
        try:
            b = self.get_rendered_bounds()
            return max(36.0, abs(float(b.get("rel_grip_bottom", 55))) + abs(float(b.get("rel_grip_top", -40))))
        except Exception:
            return 90.0 * float(self.render_scale)

    def resolve_top_mode(self, win):
        """Top edge mode — always outwards to the window border."""
        headroom = self.measure_top_headroom(win)
        mode = "OUTWARD"
        self._top_mode_smooth = mode
        self.top_mode = mode
        return mode, headroom

    def window_border_edge(self, win, side):
        """Exact Hyprland window border edge (geometry + border_size), not shadow glow."""
        outset = float(getattr(self, "hypr_border_outset", 0.0))
        if side == "RIGHT":
            return float(win["x2"]) + outset
        if side == "LEFT":
            return float(win["x1"]) - outset
        if side == "TOP":
            return float(win["y_top"]) - outset
        if side == "BOTTOM":
            # For bottom sill (inward inside window border), align with the physical inner sill
            return float(win["y_bot"])
        return float(win["y_bot"])

    def hang_foot_reach(self):
        """Stable hang grip (most extended feet) — no frame-key recursion / no bounce."""
        c_rigs = getattr(self, "sprite_rig_data", {}).get(self.current_char, {})
        fmt = CHARACTERS[self.current_char].get("format", "genshin")
        keys = ("shime15", "shime16", "shime17", "drag2", "drag1")
        reaches = []
        for k in keys:
            rig = c_rigs.get(k)
            if not rig:
                continue
            if fmt == "genshin":
                # π hang: feet were bottom
                reaches.append(-abs(float(rig["bottom_reach"])) * float(self.render_scale))
            else:
                # Native upside-down: feet near image top
                reaches.append(float(rig["top_reach"]) * float(self.render_scale))
        if not reaches:
            return -40.0 * float(self.render_scale)
        return min(reaches)  # most negative = furthest toward the border

    def hang_contact_reach(self):
        return self.hang_foot_reach()

    def compute_top_outward_crawl_y(self, border_top):
        """Flush hands and feet to top border rail from above (body outwards above window)."""
        rs = max(0.2, float(self.render_scale))
        dig = max(1.0, 1.8 * rs)
        # With horizontal rail crawl (69.0 deg / -69.0 deg), both hands and feet reach +18.0 * rs below sprite center
        # y + 18.0 * rs = border_top + dig  =>  y = border_top - 18.0 * rs + dig
        return float(border_top) - 18.0 * rs + dig

    def compute_hang_y(self, border_top):
        """Flush hang feet/hands to the live top border (outwards above window)."""
        fmt = CHARACTERS[self.current_char].get("format", "genshin")
        rs = max(0.2, float(self.render_scale))
        if fmt == "genshin":
            dig = max(0.6, 1.2 * rs)
            return float(border_top) + 48.0 * rs - dig
        else:
            return self.compute_top_outward_crawl_y(border_top)

    def compute_bottom_cling_y(self, border_bot, is_sitting=False):
        """INSIDE the window — feet/base planted firmly on the bottom inner sill (strictly inward)."""
        rs = max(0.2, float(self.render_scale))
        fmt = CHARACTERS[self.current_char].get("format", "genshin")
        if is_sitting:
            seat_reach = (60.0 if fmt == "genshin" else 62.0) * rs
            return float(border_bot) - seat_reach
        else:
            foot_reach = self.upright_foot_reach()
            return float(border_bot) - foot_reach

    def compute_top_crawl_y(self, border_top):
        """Outside top rail while crawling (same flush as hang)."""
        return self.compute_hang_y(border_top)

    def upright_foot_reach(self):
        """Stable foot reach for standing — never calls get_current_frame_key (no recursion)."""
        c_rigs = getattr(self, "sprite_rig_data", {}).get(self.current_char, {})
        for key in ("shime1", "id1_1", "walk1", "shime5", "shime11", "climb1"):
            rig = c_rigs.get(key)
            if rig and "bottom_reach" in rig:
                return abs(float(rig["bottom_reach"])) * float(self.render_scale)
        return 63.0 * float(self.render_scale)

    def compute_stand_y(self, ground_edge):
        """Flush feet to a horizontal ground/window edge with sub-pixel contact."""
        contact = self.upright_foot_reach()
        rs = max(0.2, float(self.render_scale))
        dig = max(1.0, 1.8 * rs)  # solid contact: soles firmly kiss border line with 0 air gap
        # y + contact = ground + dig  (feet firmly on edge from above)
        return float(ground_edge) - contact + dig

    def compute_top_rail_y(self, border_top, is_sitting=False):
        """Dynamic sub-pixel top rail alignment:
        - Sitting/perching: base sits flush on the border with zero air gap
        - Standing/walking: soles of feet firmly kiss the border line with zero gap
        """
        rs = max(0.2, float(self.render_scale))
        dig = max(1.0, 1.8 * rs)
        fmt = CHARACTERS[self.current_char].get("format", "genshin")
        if is_sitting:
            seat_reach = (60.0 if fmt == "genshin" else 64.0) * rs
            return float(border_top) - seat_reach + dig
        else:
            foot_reach = self.upright_foot_reach()
            return float(border_top) - foot_reach + dig

    def compute_ledge_sit_y(self, ground_edge):
        """Backwards-compatible seated position on window top border."""
        return self.compute_top_rail_y(ground_edge, is_sitting=True)

    def floor_y_for(self, feet_offset=None):
        """Pet center Y when standing on the ground or bottom window sill."""
        if getattr(self, "platforms", None):
            for p in self.platforms:
                if p.get("address") in ("floor", "screen"):
                    continue
                if p["x1"] - 20.0 <= self.x <= p["x2"] + 20.0:
                    return self.compute_bottom_cling_y(p["y_bot"])
        if getattr(self, "active_window", None):
            aw = self.active_window
            if aw["x1"] - 20.0 <= self.x <= aw["x2"] + 20.0:
                return self.compute_bottom_cling_y(aw["y_bot"])
        return self.compute_bottom_cling_y(float(self.screen_height) - self.bottom_pad())

    def get_screen_floor(self):
        if getattr(self, "active_window", None):
            aw = self.active_window
            return {
                "address": aw.get("address", "floor"),
                "x1": aw["x1"],
                "x2": aw["x2"],
                "y_top": aw["y_bot"],
                "y_bot": aw["y_bot"],
                "title": aw.get("title", ""),
                "class": aw.get("class", ""),
            }
        ground = float(self.screen_height) - self.bottom_pad()
        return {
            "address": "floor",
            "x1": 24.0,
            "x2": float(self.screen_width) - 24.0,
            "y_top": ground,  # walkable surface edge
            "y_bot": float(self.screen_height),
            "title": "desktop-floor",
            "class": "floor",
        }

    def resolve_hang_border_y(self, win=None):
        """Live top rail: window top border, or screen top bezel."""
        if win and win.get("address") not in (None, "screen", "floor"):
            return self.window_border_edge(win, "TOP")
        if getattr(self, "hang_on_screen", False) or (win and win.get("address") == "screen"):
            return float(getattr(self, "hypr_gap_top", 8.0))
        if win:
            return float(win.get("y_top", 0.0))
        return float(getattr(self, "hypr_gap_top", 8.0))

    def sync_screen_from_hypr(self):
        """Map Hyprland logical geometry into GTK layer-local drawing space."""
        try:
            mons = self.hypr_ipc_query("monitors")
            if not mons:
                mons = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"], stderr=subprocess.DEVNULL).decode())
            mon = next((m for m in mons if m.get("focused")), mons[0] if mons else None)
            if not mon:
                return
            scale = float(mon.get("scale") or 1.0) or 1.0
            logical_w = float(mon["width"]) / scale
            logical_h = float(mon["height"]) / scale
            self.hypr_screen_width = logical_w
            self.hypr_screen_height = logical_h

            off_x, off_y = 0.0, 0.0
            try:
                layers = self.hypr_ipc_query("layers")
                if not layers:
                    layers = json.loads(subprocess.check_output(["hyprctl", "layers", "-j"], stderr=subprocess.DEVNULL).decode())
                my_pid = os.getpid()
                found = False
                for _mon, payload in layers.items():
                    for _z, arr in (payload.get("levels") or {}).items():
                        for layer in arr:
                            ns = layer.get("namespace", "")
                            if layer.get("pid") == my_pid or ns == "hyprpet":
                                off_x = float(layer.get("x", 0) or 0)
                                off_y = float(layer.get("y", 0) or 0)
                                lw = float(layer.get("w", 0) or 0)
                                lh = float(layer.get("h", 0) or 0)
                                if lw > 200:
                                    self.screen_width = lw
                                if lh > 200:
                                    self.screen_height = lh
                                found = True
                                break
                        if found:
                            break
                    if found:
                        break
                if not found:
                    # Surface smaller than monitor → assume inset margins
                    if float(self.screen_width) < logical_w - 1.0:
                        off_x = (logical_w - float(self.screen_width)) * 0.5
                    if float(self.screen_height) < logical_h - 1.0:
                        off_y = (logical_h - float(self.screen_height)) * 0.5
            except Exception:
                if float(self.screen_width) < logical_w - 1.0:
                    off_x = (logical_w - float(self.screen_width)) * 0.5
                if float(self.screen_height) < logical_h - 1.0:
                    off_y = (logical_h - float(self.screen_height)) * 0.5

            self.coord_off_x = off_x
            self.coord_off_y = off_y
        except Exception:
            pass

    def hypr_to_local_x(self, x):
        return float(x) - float(getattr(self, "coord_off_x", 0.0))

    def hypr_to_local_y(self, y):
        return float(y) - float(getattr(self, "coord_off_y", 0.0))

    def on_size_allocate(self, widget, allocation):
        if allocation.width > 200 and allocation.height > 200:
            # Drawing space = real GTK surface (never overwrite with larger hypr size)
            self.screen_width = float(allocation.width)
            self.screen_height = float(allocation.height)
            self.sync_screen_from_hypr()
            print(
                f"[HyprPet] surface={self.screen_width:.0f}x{self.screen_height:.0f} "
                f"off=({self.coord_off_x:.1f},{self.coord_off_y:.1f}) "
                f"hypr={self.hypr_screen_width:.0f}x{self.hypr_screen_height:.0f}",
                flush=True,
            )

    # ------------------------------------------------------------------
    # Configuration & IPC
    # ------------------------------------------------------------------
    def start_ipc_server(self):
        sock_path = "/tmp/hyprpet.sock"
        try:
            if os.path.exists(sock_path):
                os.remove(sock_path)
            self.ipc_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.ipc_sock.bind(sock_path)
            self.ipc_sock.setblocking(False)
            channel = GLib.IOChannel(self.ipc_sock.fileno())
            GLib.io_add_watch(channel, GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN, self.on_ipc_data)
        except Exception:
            pass

    def on_ipc_data(self, channel, cond):
        try:
            data, _ = self.ipc_sock.recvfrom(1024)
            cmd = data.decode().strip()
            self.handle_ipc_cmd(cmd)
        except Exception:
            pass
        return True

    def handle_ipc_cmd(self, cmd):
        parts = cmd.split()
        if not parts:
            return
        action = parts[0].lower()
        print(f"[IPC received] cmd='{cmd}' (current state={self.state}, x={self.x:.1f}, y={self.y:.1f})", flush=True)
        if action in ["screen_left", "cling_screen_left"]:
            self.cling_to_screen_border("LEFT")
        elif action in ["screen_right", "cling_screen_right"]:
            self.cling_to_screen_border("RIGHT")
        elif action in ["screen_top", "hang_screen_top"]:
            self.hang_on_screen_top()
        elif action in ["cling_right", "win_right"]:
            self.cling_to_active_window("RIGHT")
        elif action in ["cling_left", "win_left"]:
            self.cling_to_active_window("LEFT")
        elif action in ["hang", "win_hang"]:
            self.hang_upside_down_on_active_window()
        elif action in ["perch", "win_perch"]:
            self.perch_on_active_window()
        elif action in ["walk", "floor"]:
            self.start_walking()
        elif action == "dance":
            self.trigger_dance()
        elif action == "wave":
            self.trigger_wave()
        elif action == "taunt":
            self.trigger_taunt()
        elif action in ["away", "throw", "shoo", "dismiss"]:
            dur = float(parts[1]) if len(parts) > 1 else 45.0
            self.dismiss_pet(duration=dur)
        elif action in ["come_back", "return", "summon"]:
            self.return_from_away()
        elif action in ["char", "character"] and len(parts) > 1:
            self.switch_character(parts[1])
        elif action == "scale" and len(parts) > 1:
            self.set_scale(float(parts[1]))
        elif action in ["presence", "mode"] and len(parts) > 1:
            self.set_presence(parts[1].lower())
        elif action == "calm":
            self.set_presence("calm")
        elif action == "focus":
            self.set_presence("focus")
        elif action == "lively":
            self.set_presence("lively")
        self.note_interaction(0.85)
        print(f"[IPC executed] state={self.state}, x={self.x:.1f}, y={self.y:.1f}, char={self.current_char}, presence={self.presence_mode}", flush=True)

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    c = cfg.get("character", "hutao")
                    if c in CHARACTERS:
                        self.current_char = c
                    p = cfg.get("presence", "calm")
                    if p in PRESENCE_PROFILES:
                        self.presence_mode = p
                    if "scale" in cfg:
                        try:
                            self.user_scale = float(cfg["scale"])
                        except (TypeError, ValueError):
                            self.user_scale = None
        except Exception:
            self.current_char = "hutao"
            self.presence_mode = "calm"

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            payload = {
                "character": self.current_char,
                "presence": self.presence_mode,
            }
            if self.user_scale is not None:
                payload["scale"] = self.user_scale
            with open(CONFIG_FILE, "w") as f:
                json.dump(payload, f)
        except Exception:
            pass

    def hypr_ipc_query(self, cmd):
        """Zero-latency (<0.1ms) query over Hyprland's UNIX IPC socket with fallback."""
        his = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if not his:
            return None
        xdg_rt = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        sock_paths = [
            f"{xdg_rt}/hypr/{his}/.socket.sock",
            f"/tmp/hypr/{his}/.socket.sock",
        ]
        sock_path = None
        for sp in sock_paths:
            if os.path.exists(sp):
                sock_path = sp
                break
        if not sock_path:
            return None

        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(0.05)
            s.connect(sock_path)
            req = f"j/{cmd}" if not cmd.startswith("j/") else cmd
            s.sendall(req.encode("utf-8"))
            chunks = []
            while True:
                data = s.recv(8192)
                if not data:
                    break
                chunks.append(data)
            s.close()
            raw = b"".join(chunks).decode("utf-8", errors="ignore")
            if not raw or raw == "unknown request":
                return None
            return json.loads(raw)
        except Exception:
            return None

    def update_hyprland_layout_metrics(self):
        try:
            bs = self.hypr_ipc_query("getoption general:border_size")
            if not bs:
                bs = json.loads(subprocess.check_output(["hyprctl", "getoption", "general:border_size", "-j"], stderr=subprocess.DEVNULL).decode())
            self.hypr_border_size = float(bs.get("int", 0))
        except Exception:
            self.hypr_border_size = 0.0

        try:
            rd = self.hypr_ipc_query("getoption decoration:rounding")
            if not rd:
                rd = json.loads(subprocess.check_output(["hyprctl", "getoption", "decoration:rounding", "-j"], stderr=subprocess.DEVNULL).decode())
            self.hypr_rounding = float(rd.get("int", 25))
        except Exception:
            self.hypr_rounding = 25.0

        try:
            sh = self.hypr_ipc_query("getoption decoration:shadow:range")
            if not sh:
                sh = json.loads(subprocess.check_output(["hyprctl", "getoption", "decoration:shadow:range", "-j"], stderr=subprocess.DEVNULL).decode())
            self.hypr_shadow_range = float(sh.get("int", 15))
        except Exception:
            self.hypr_shadow_range = 15.0

        # Window border rail = geometry + border_size (not shadow glow)
        self.hypr_border_outset = max(0.0, self.hypr_border_size)
        self.hypr_glow = 0.0

        try:
            go = self.hypr_ipc_query("getoption general:gaps_out")
            if not go:
                go = json.loads(subprocess.check_output(["hyprctl", "getoption", "general:gaps_out", "-j"], stderr=subprocess.DEVNULL).decode())
            css = go.get("css", "8 8 8 8").split()
            self.hypr_gap_top = float(css[0])
            self.hypr_gap_right = float(css[1]) if len(css) > 1 else self.hypr_gap_top
            self.hypr_gap_bottom = float(css[2]) if len(css) > 2 else self.hypr_gap_top
            self.hypr_gap_left = float(css[3]) if len(css) > 3 else self.hypr_gap_top
        except Exception:
            self.hypr_gap_top = self.hypr_gap_right = self.hypr_gap_bottom = self.hypr_gap_left = 8.0

    def connect_hyprland_socket2(self):
        his = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if not his:
            return
        xdg_rt = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        sock_paths = [
            f"{xdg_rt}/hypr/{his}/.socket2.sock",
            f"/tmp/hypr/{his}/.socket2.sock",
        ]
        for sp in sock_paths:
            if os.path.exists(sp):
                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect(sp)
                    s.setblocking(False)
                    channel = GLib.IOChannel(s.fileno())
                    GLib.io_add_watch(channel, GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN, self.on_hyprland_event)
                    self.hypr_socket2 = s
                    print(f"[HyprPet] Connected to Hyprland socket2: {sp}", flush=True)
                    break
                except Exception as e:
                    print(f"[HyprPet] Socket2 connection error: {e}", flush=True)

    def on_hyprland_event(self, channel, cond):
        try:
            data = self.hypr_socket2.recv(2048).decode(errors="ignore")
            if not data:
                return True
            events = [
                "activewindow", "movewindow", "resizewindow", "openwindow", "closewindow",
                "workspace", "fullscreen", "changefloatingmode", "focusedmon",
                "configreloaded", "monitoradded", "monitorremoved",
            ]
            if any(ev in data for ev in events):
                self.refresh_platforms(force=True)
                # Flag so next cling tick snaps if geometry shifted
                self._hypr_geom_dirty = True
        except Exception:
            pass
        return True

    def load_all_characters(self):
        base_dir = os.path.expanduser("~/.local/share/hyprpet")
        self.sprite_rig_data = {}
        for cid in CHARACTERS.keys():
            self.character_surfaces[cid] = {}
            self.sprite_rig_data[cid] = {}
            cdir = os.path.join(base_dir, cid)
            if not os.path.exists(cdir):
                continue
            for fn in os.listdir(cdir):
                if fn.endswith(".png"):
                    k = os.path.splitext(fn)[0]
                    fp = os.path.join(cdir, fn)
                    try:
                        self.character_surfaces[cid][k] = cairo.ImageSurface.create_from_png(fp)
                        with Image.open(fp) as im:
                            rgba = im.convert("RGBA")
                            bbox = rgba.getbbox()
                            if bbox:
                                min_x, min_y, max_x, max_y = bbox
                                grip_l, grip_r, grip_t, grip_b = self._measure_sprite_grip(rgba)
                                self.sprite_rig_data[cid][k] = {
                                    "width": float(max_x - min_x),
                                    "height": float(max_y - min_y),
                                    "left_reach": float(min_x - 64),
                                    "right_reach": float(max_x - 64),
                                    "grip_left_reach": float(grip_l - 64),
                                    "grip_right_reach": float(grip_r - 64),
                                    "top_reach": float(min_y - 64),
                                    "bottom_reach": float(max_y - 64),
                                    "grip_top_reach": float(grip_t - 64),
                                    "grip_bottom_reach": float(grip_b - 64),
                                }
                    except Exception:
                        pass

    @staticmethod
    def _measure_sprite_grip(rgba_img):
        """Solid hand/foot contact (ignore faint alpha fringe) — L/R + top/bottom."""
        px = rgba_img.load()
        w, h = rgba_img.size
        # Mid + lower body: hands and planted feet that should kiss the wall
        y0, y1 = int(h * 0.28), int(h * 0.98)

        def col_mass(x):
            m = 0
            for y in range(y0, y1):
                a = px[x, y][3]
                if a >= 96:
                    m += a
            return m

        masses = [col_mass(x) for x in range(w)]
        total = sum(masses) or 1
        cum = 0
        grip_l = 0
        for x, m in enumerate(masses):
            cum += m
            if cum >= total * 0.004 and m > 0:
                grip_l = x
                break
        cum = 0
        grip_r = w - 1
        for x in range(w - 1, -1, -1):
            cum += masses[x]
            if cum >= total * 0.004 and masses[x] > 0:
                grip_r = x
                break

        # Solid head / foot rows (for bottom sill + top ledge flush)
        x0, x1 = int(w * 0.18), int(w * 0.82)

        def row_mass(y):
            m = 0
            for x in range(x0, x1):
                a = px[x, y][3]
                if a >= 110:
                    m += a
            return m

        row_masses = [row_mass(y) for y in range(h)]
        rtotal = sum(row_masses) or 1
        cum = 0
        grip_t = 0
        for y, m in enumerate(row_masses):
            cum += m
            if cum >= rtotal * 0.015 and m > 0:
                grip_t = y
                break
        cum = 0
        grip_b = h - 1
        for y in range(h - 1, -1, -1):
            cum += row_masses[y]
            if cum >= rtotal * 0.015 and row_masses[y] > 0:
                grip_b = y
                break
        return grip_l, grip_r, grip_t, grip_b

    def get_current_rig(self):
        c_rigs = getattr(self, "sprite_rig_data", {}).get(self.current_char, {})
        frame_key = self.get_current_frame_key()
        rig = c_rigs.get(frame_key)
        if not rig:
            return {
                "width": 64.0,
                "height": 110.0,
                "left_reach": -25.0,
                "right_reach": 25.0,
                "grip_left_reach": -22.0,
                "grip_right_reach": 22.0,
                "top_reach": -55.0,
                "bottom_reach": 55.0,
                "grip_top_reach": -48.0,
                "grip_bottom_reach": 55.0,
            }
        return rig

    def get_rendered_bounds(self):
        rig = self.get_current_rig()
        raw_left = rig["left_reach"]
        raw_right = rig["right_reach"]
        raw_grip_l = rig.get("grip_left_reach", raw_left)
        raw_grip_r = rig.get("grip_right_reach", raw_right)
        raw_top = rig["top_reach"]
        raw_bottom = rig["bottom_reach"]
        raw_grip_t = rig.get("grip_top_reach", raw_top)
        raw_grip_b = rig.get("grip_bottom_reach", raw_bottom)

        raw_facing = CHARACTERS[self.current_char].get("climb_raw_facing", "LEFT")
        fmt = CHARACTERS[self.current_char].get("format", "genshin")

        if self.state == "CLINGING":
            if self.cling_side == "RIGHT":
                cling_sx = 1.0 if raw_facing == "LEFT" else -1.0
            else:
                cling_sx = -1.0 if raw_facing == "LEFT" else 1.0
            sx = cling_sx * self.render_scale
            sy = self.render_scale
        elif self.state == "WINDOW_TOP_HANG":
            # Stable hang measure — no squash; facing flip only
            turn_sx = -self.facing_scale
            if abs(turn_sx) < 0.08:
                turn_sx = -0.08 if self.facing_scale >= 0 else 0.08
            sx = turn_sx * self.render_scale
            sy = self.render_scale
        else:
            turn_sx = -self.facing_scale
            sx = turn_sx * getattr(self, "scale_x", 1.0) * self.render_scale
            sy = getattr(self, "scale_y", 1.0) * self.render_scale

        if sx >= 0:
            rel_left = raw_left * sx
            rel_right = raw_right * sx
            rel_grip_left = raw_grip_l * sx
            rel_grip_right = raw_grip_r * sx
        else:
            rel_left = raw_right * sx
            rel_right = raw_left * sx
            rel_grip_left = raw_grip_r * sx
            rel_grip_right = raw_grip_l * sx

        rel_top = raw_top * sy
        rel_bottom = raw_bottom * sy
        hang_contact = rel_top

        # Solid head/foot (ignore transparent fringe) — critical for sill flush
        abs_sy = abs(sy) if sy else 1.0
        sign_sy = 1.0 if sy >= 0 else -1.0
        rel_grip_top = float(raw_grip_t) * abs_sy * sign_sy
        rel_grip_bottom = float(raw_grip_b) * abs_sy * sign_sy

        return {
            "rel_left": rel_left,
            "rel_right": rel_right,
            "rel_grip_left": rel_grip_left,
            "rel_grip_right": rel_grip_right,
            "rel_top": rel_top,
            "rel_bottom": rel_bottom,
            "rel_grip_top": rel_grip_top,
            "rel_grip_bottom": rel_grip_bottom,
            "hang_contact": hang_contact,
            "width": rel_right - rel_left,
            "height": rel_bottom - rel_top,
        }

    def get_surface(self, key):
        c_dict = self.character_surfaces.get(self.current_char, {})
        if key in c_dict:
            return c_dict[key]
        for fb in ["id1_1", "shime1", "walk1"]:
            if fb in c_dict:
                return c_dict[fb]
        return None

    # ------------------------------------------------------------------
    # Input Region Clipping
    # ------------------------------------------------------------------
    def update_input_shape(self):
        gdk_win = self.get_window()
        if not gdk_win:
            return

        try:
            if self.state == "AWAY":
                # 100% click-through everywhere while companion is away on a break
                region = cairo.Region()
                gdk_win.input_shape_combine_region(region, 0, 0)
                return

            box_w = int(128 * self.render_scale) + 20
            box_h = int(128 * self.render_scale) + 20
            rx = int(self.x - box_w * 0.5)
            ry = int(self.y - box_h * 0.5)
            screen_w = int(max(1, self.screen_width))
            screen_h = int(max(1, self.screen_height))

            if self.web_active and self.state == "SWINGING":
                min_x = int(min(rx, self.web_anchor_x - 16))
                max_x = int(max(rx + box_w, self.web_anchor_x + 16))
                min_y = int(min(ry, self.web_anchor_y - 16))
                max_y = int(max(ry + box_h, self.y + box_h * 0.5))
                x0 = int(max(0, min_x))
                y0 = int(max(0, min_y))
                rw = int(max(20, min(screen_w - x0, max_x - min_x)))
                rh = int(max(20, min(screen_h - y0, max_y - min_y)))
                rect = cairo.RectangleInt(x0, y0, rw, rh)
            else:
                rx = int(max(0, min(rx, max(0, screen_w - box_w))))
                ry = int(max(0, min(ry, max(0, screen_h - box_h))))
                rect = cairo.RectangleInt(rx, ry, int(box_w), int(box_h))

            region = cairo.Region(rect)
            gdk_win.input_shape_combine_region(region, 0, 0)
        except Exception:
            # Never let input-shape math crash the companion
            pass

    # ------------------------------------------------------------------
    # Dynamic Hyprland Window & Border Detection
    # ------------------------------------------------------------------
    def refresh_platforms(self, force=False):
        now = time.time()
        if not force and (now - self.last_platform_update < 0.02):
            return
        self.last_platform_update = now
        self.sync_screen_from_hypr()
        self.update_hyprland_layout_metrics()

        borders = []
        try:
            # Active window info via zero-latency IPC socket
            aw = self.hypr_ipc_query("activewindow")
            if aw is None:
                aw_raw = subprocess.check_output(["hyprctl", "activewindow", "-j"], stderr=subprocess.DEVNULL).decode()
                aw = json.loads(aw_raw)
            if aw and aw.get("mapped") and not aw.get("hidden") and aw.get("address"):
                ax, ay = aw["at"]
                aw_w, aw_h = aw["size"]
                self.active_window = {
                    "address": aw.get("address"),
                    "x1": self.hypr_to_local_x(float(ax)),
                    "x2": self.hypr_to_local_x(float(ax + aw_w)),
                    "y_top": self.hypr_to_local_y(float(ay)),
                    "y_bot": self.hypr_to_local_y(float(ay + aw_h)),
                    "title": aw.get("title", ""),
                    "class": aw.get("class", ""),
                }
            else:
                self.active_window = None

            # All visible clients via zero-latency IPC socket
            clients = self.hypr_ipc_query("clients")
            if clients is None:
                clients_raw = subprocess.check_output(["hyprctl", "clients", "-j"], stderr=subprocess.DEVNULL).decode()
                clients = json.loads(clients_raw)

            active_ws_data = self.hypr_ipc_query("activeworkspace")
            if active_ws_data is None:
                ws_raw = subprocess.check_output(["hyprctl", "activeworkspace", "-j"], stderr=subprocess.DEVNULL).decode()
                active_ws_data = json.loads(ws_raw)
            active_ws = active_ws_data.get("id", 1)

            # Check if a special workspace is currently open on the monitor
            mons = self.hypr_ipc_query("monitors")
            if mons is None:
                mon_raw = subprocess.check_output(["hyprctl", "monitors", "-j"], stderr=subprocess.DEVNULL).decode()
                mons = json.loads(mon_raw)
            special_ws_id = mons[0].get("specialWorkspace", {}).get("id", 0) if mons else 0

            plats = []
            for c in clients:
                if c.get("mapped") and not c.get("hidden"):
                    c_ws = c.get("workspace", {}).get("id")
                    # Window is visible if on active workspace or open special workspace
                    if c_ws == active_ws or (special_ws_id != 0 and c_ws == special_ws_id):
                        x, y = c["at"]
                        w, h = c["size"]
                        if w > 60 and h > 60:
                            x1 = self.hypr_to_local_x(float(x))
                            x2 = self.hypr_to_local_x(float(x + w))
                            y1 = self.hypr_to_local_y(float(y))
                            y2 = self.hypr_to_local_y(float(y + h))
                            win_info = {
                                "address": c.get("address"),
                                "x1": x1,
                                "x2": x2,
                                "y_top": y1,
                                "y_bot": y2,
                                "title": c.get("title", ""),
                                "class": c.get("class", ""),
                            }
                            plats.append(win_info)
                            border_out = float(getattr(self, "hypr_border_outset", 0.0))
                            y2_cap = min(float(self.screen_height) - self.bottom_pad(), y2)
                            borders.append({
                                "type": "WIN_LEFT",
                                "x": x1 - border_out,
                                "y1": y1,
                                "y2": y2_cap,
                                "side": "LEFT",
                                "win": win_info,
                            })
                            borders.append({
                                "type": "WIN_RIGHT",
                                "x": x2 + border_out,
                                "y1": y1,
                                "y2": y2_cap,
                                "side": "RIGHT",
                                "win": win_info,
                            })

            # Screen outer borders — full height down to a small dock pad (bottom roam OK)
            y_bot = float(self.screen_height) - self.bottom_pad()
            borders.append({"type": "SCREEN_LEFT", "x": 0.0, "y1": 60.0, "y2": y_bot, "side": "LEFT", "win": None})
            borders.append({"type": "SCREEN_RIGHT", "x": float(self.screen_width), "y1": 60.0, "y2": y_bot, "side": "RIGHT", "win": None})

            self.platforms = plats
            self.vertical_borders = borders

            # Real-time dynamic cling target address update & smooth follow-through delta
            prev_win = self.cling_target_window
            if self.cling_target_address and self.cling_target_address not in ("screen", "floor"):
                found_win = None
                for p in plats:
                    if p.get("address") == self.cling_target_address:
                        found_win = p
                        break
                if found_win:
                    if prev_win and prev_win.get("address") == found_win["address"]:
                        dx = found_win["x1"] - prev_win["x1"]
                        dy = found_win["y_top"] - prev_win["y_top"]
                        if (dx != 0.0 or dy != 0.0) and self.state in ("CLINGING", "WINDOW_TOP_HANG", "CORNER_ARC", "SITTING"):
                            self.x += dx
                            self.y += dy
                    self.cling_target_window = found_win
                elif self.active_window:
                    self.cling_target_window = self.active_window
            elif self.active_window and not self.cling_target_window:
                self.cling_target_window = self.active_window

        except Exception:
            pass

    def get_current_platform(self):
        # 1. Check all windows: top ledge and bottom inner sill
        for p in self.platforms:
            if p.get("address") in ("floor", "screen"):
                continue
            if p["x1"] - 25 <= self.x <= p["x2"] + 25:
                # Top ledge
                edge_top = self.window_border_edge(p, "TOP")
                stand_top = self.compute_stand_y(edge_top)
                if abs(self.y - stand_top) < 28.0:
                    return {**p, "active_edge": "TOP", "edge_y": edge_top}
                
                # Bottom inner sill (inside window)
                edge_bot = float(p["y_bot"])
                stand_bot = self.compute_bottom_cling_y(edge_bot)
                if abs(self.y - stand_bot) < 42.0 or (self.cling_side == "BOTTOM" and p.get("address") == self.cling_target_address):
                    return {**p, "active_edge": "BOTTOM", "edge_y": edge_bot}

        # 2. Window under pet if pet is near the bottom
        for p in self.platforms:
            if p.get("address") in ("floor", "screen"):
                continue
            if p["x1"] - 25 <= self.x <= p["x2"] + 25:
                edge_bot = float(p["y_bot"])
                stand_bot = self.compute_bottom_cling_y(edge_bot)
                if self.y >= stand_bot - 45.0:
                    return {**p, "active_edge": "BOTTOM", "edge_y": edge_bot}

        # 3. Explicit cling target address
        if self.cling_target_address and self.cling_target_address not in ("floor", "screen"):
            for p in self.platforms:
                if p.get("address") == self.cling_target_address:
                    if self.cling_side == "BOTTOM":
                        return {**p, "active_edge": "BOTTOM", "edge_y": float(p["y_bot"])}
                    return {**p, "active_edge": "TOP", "edge_y": self.window_border_edge(p, "TOP")}

        # 4. Desktop floor fallback
        floor = self.get_screen_floor()
        return {**floor, "active_edge": "FLOOR", "edge_y": floor["y_top"]}

    # ------------------------------------------------------------------
    # Physics & Dynamic Clinging Engine
    # ------------------------------------------------------------------
    def tick(self):
        now = time.time()
        dt = min(0.05, max(0.001, now - self.last_time))
        self.last_time = now
        return self._tick_dt(dt)

    def _tick_dt(self, dt):
        # Adaptive cadence: calm wall-rest burns fewer platform polls
        quiet_cling = (
            self.state == "CLINGING"
            and self.cling_mode == "WALL_REST"
            and not self.is_dragging
            and self.presence_mode != "lively"
        )

        if self.state != "AWAY" and not quiet_cling:
            self.refresh_platforms()
        elif quiet_cling and (time.time() - self.last_platform_update) > 0.45:
            self.refresh_platforms()

        self.state_timer += dt
        self.anim_tick += dt
        if getattr(self, "no_cling_timer", 0.0) > 0.0:
            self.no_cling_timer = max(0.0, self.no_cling_timer - dt)
        self.update_presence_visuals(dt)
        self._recycle_particles(dt)

        # Dissolve silk after swings (no leftover rope on the desktop)
        if not self.web_active and self.web_opacity > 0.0:
            self.web_opacity = max(0.0, self.web_opacity - dt * max(2.0, self.web_fade_speed))
            if self.web_opacity <= 0.01:
                self.web_opacity = 0.0
                self.crawl_web_points = []
        elif self.web_active:
            self.web_opacity = 1.0
            self.web_phase += dt * 3.5

        # Ghost strands fade even outside SWINGING
        if self.web_ghosts and self.state != "SWINGING":
            alive = []
            for g in self.web_ghosts:
                g["a"] -= dt * 1.1
                if g["a"] > 0.04:
                    alive.append(g)
            self.web_ghosts = alive

        # One coherent size for climb / run / slide / ledge / swing / floor
        self.update_coherent_scale(dt)
        self.tick_motion(dt)

        cdata = CHARACTERS[self.current_char]
        hand_offset = cdata["hand_offset"] * self.render_scale
        feet_offset = cdata.get("feet_offset", 63.0) * self.render_scale
        hang_offset = cdata.get("hang_feet_offset", 63.0) * self.render_scale
        raw_facing = cdata.get("climb_raw_facing", "LEFT")

        floor_y = self.floor_y_for(feet_offset)
        ceil_y = feet_offset + 8.0

        # Smooth real-time turning scale interpolation (3D perspective flip effect)
        self.facing_scale += (self.facing - self.facing_scale) * min(1.0, dt * 16.0)

        # Smooth real-time body rotation interpolation
        self.body_angle += (self.target_body_angle - self.body_angle) * min(1.0, dt * 14.0)

        # --------------------------------------------------------------
        # State Machine Execution
        # --------------------------------------------------------------
        if self.state == "AWAY":
            self.away_timer += dt
            if self.away_timer >= self.away_duration:
                self.return_from_away()
            # Rare redraw while invisible — keeps compositor quiet
            if int(self.away_timer * 2) != int((self.away_timer - dt) * 2):
                self.queue_draw()
            return True

        elif self.is_dragging:
            self.state = "DRAGGING"
            self.web_active = False
            self.step_bob_y = 0.0
            target_x = self.last_mouse_x - self.drag_offset_x
            target_y = self.last_mouse_y - self.drag_offset_y

            self.vx = (target_x - self.x) * 24.0
            self.vy = (target_y - self.y) * 24.0
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Dynamic swing angle based on mouse drag velocity
            self.target_body_angle = max(-0.45, min(0.45, self.vx * 0.0006))

            spd = math.hypot(self.vx, self.vy)
            target_sy = min(1.32, 1.0 + spd * 0.0003)
            self.scale_y += (target_sy - self.scale_y) * 0.3
            self.scale_x = 1.0 / math.sqrt(max(0.5, self.scale_y))
            if abs(self.vx) > 30:
                self.facing = 1.0 if self.vx > 0 else -1.0

        elif self.state == "WINDOW_TOP_HANG":
            self.step_bob_y = 0.0
            now_hang = time.time()
            if getattr(self, "_hypr_geom_dirty", False) or (now_hang - float(getattr(self, "_cling_geom_poll", 0.0))) >= 0.05:
                self.refresh_platforms(force=True)
                self._cling_geom_poll = now_hang
                self._hypr_geom_dirty = False
                if self.cling_target_address and self.cling_target_address not in ("screen", "floor"):
                    for p in self.platforms:
                        if p.get("address") == self.cling_target_address:
                            self.cling_target_window = p
                            break

            target_win = self.cling_target_window
            if self.hang_on_screen:
                border_now = self.resolve_hang_border_y(None)
                mode, _hr = "LEDGE", 999.0
            else:
                if not target_win or target_win.get("address") in ("floor",):
                    target_win = self.active_window or (self.platforms[0] if self.platforms else None)
                    self.cling_target_window = target_win
                if target_win:
                    border_now = self.window_border_edge(target_win, "TOP")
                    mode, _hr = self.resolve_top_mode(target_win)
                else:
                    border_now = self.resolve_hang_border_y(None)
                    mode, _hr = "LEDGE", 999.0

            # Agile outward crawl along the top border rail
            self.hang_style = "crawl"
            travel = self.facing if abs(self.facing) > 0.1 else 1.0
            target_y = self.compute_top_outward_crawl_y(border_now)
            target = 48.0 * (1.05 if self.presence_mode == "lively" else 0.92)
            spd = self.smooth_move_speed(dt, travel * target)
            phase, plant, stride_mul, _ = self.advance_gait(dt, spd)
            self.vx = spd * stride_mul
            self.x += self.vx * dt
            self.y += (target_y - self.y) * min(1.0, dt * 35.0)
            self.hang_omega = 0.0
            self.hang_theta = 0.0
            self.target_body_angle = 0.0
            self.step_bob_y = 0.0
            self.scale_y += ((1.0 - 0.02 * plant) - self.scale_y) * min(1.0, dt * 14.0)
            self.scale_x += ((1.0 + 0.02 * plant) - self.scale_x) * min(1.0, dt * 14.0)
            if target_win and not self.hang_on_screen:
                self.x = max(target_win["x1"] + 36.0, min(target_win["x2"] - 36.0, self.x))
            else:
                self.x = max(48.0, min(self.screen_width - 48.0, self.x))
            self.step_bob_y = 0.0

            self._last_hang_border = border_now
            if random.random() < self.profile()["hang_particle"] * 0.5:
                self.emit(1, self.x + random.uniform(-8, 8), self.y, "sparkle")
            if self.web_active or self.web_opacity > 0.05:
                self.release_web(fade=True)

            hang_lo, hang_hi = (7.0, 14.0) if self.presence_mode == "lively" else (10.0, 18.0)
            if self.state_timer > random.uniform(hang_lo, hang_hi):
                self.state_timer = 0.0
                if not self.hang_on_screen and target_win and random.random() < 0.7:
                    self.y = self.compute_top_rail_y(self.window_border_edge(target_win, "TOP"), is_sitting=True)
                    self.state = "SITTING"
                    self.trigger_squash(0.2)
                elif self.hang_on_screen:
                    side = "LEFT" if self.x < self.screen_width * 0.5 else "RIGHT"
                    self.cling_to_screen_border(side, mode="WALL_SLIDE")
                elif target_win and random.random() < 0.55:
                    # Resume ledge run around the window
                    self.cling_orbit = 1 if random.random() < 0.5 else -1
                    border = {
                        "type": "WIN_TOP",
                        "x": (target_win["x1"] + target_win["x2"]) * 0.5,
                        "y1": target_win["y_top"],
                        "y2": target_win["y_bot"],
                        "side": "TOP",
                        "win": target_win,
                    }
                    self.start_clinging(border)
                    self.cling_mode = "TOP_CRAWL"
                else:
                    self.state = "FALLING"
                    self.vy = random.uniform(40, 100)
                    self.vx = random.uniform(-60, 60)
                    self.trigger_squash(0.16)

        elif self.state == "CORNER_ARC":
            # Real spider corner: plant one hand → reach the other → pull around → settle
            self.step_modern_corner(dt)


        elif self.state == "CLINGING":
            self.step_bob_y = 0.0
            self.target_body_angle = 0.0  # Flush to edge
            # Kill leftover squash/stretch so grip math matches the drawn sprite
            self.scale_x += (1.0 - self.scale_x) * min(1.0, dt * 14.0)
            self.scale_y += (1.0 - self.scale_y) * min(1.0, dt * 14.0)

            # Hyprland has no continuous resize IPC — poll live geometry while clinging
            now_cling = time.time()
            last_poll = float(getattr(self, "_cling_geom_poll", 0.0))
            if getattr(self, "_hypr_geom_dirty", False) or (now_cling - last_poll) >= 0.05:
                self.refresh_platforms(force=True)
                self._cling_geom_poll = now_cling
                self._hypr_geom_dirty = False

            is_screen = getattr(self, "cling_border_type", "").startswith("SCREEN")
            target_win = None
            side = self.cling_side

            if is_screen and side in ("LEFT", "RIGHT"):
                self.cling_min_y = 60.0
                self.cling_max_y = float(self.screen_height) - self.bottom_pad() - 8.0
                self.cling_wall_x = 0.0 if side == "LEFT" else float(self.screen_width)
            else:
                target_win = self.cling_target_window or self.active_window or (self.platforms[0] if self.platforms else None)
                if target_win and target_win.get("address") not in ("floor",):
                    self.cling_min_y = target_win["y_top"]
                    self.cling_max_y = min(float(self.screen_height) - self.bottom_pad() - 8.0, target_win["y_bot"])
                    if side in ("LEFT", "RIGHT"):
                        self.cling_wall_x = self.window_border_edge(target_win, side)
                        self.fit_cling_scale_to_gap(side, self.cling_wall_x, False)

            # --- Horizontal edges: TOP ledge-run / BOTTOM sill crawl ---
            if side == "TOP" and target_win:
                edge = self.window_border_edge(target_win, "TOP")
                desired_mode, headroom = self.resolve_top_mode(target_win)
                mode = self.commit_top_mode(desired_mode)
                travel = -1.0 if self.cling_orbit > 0 else 1.0
                x0, x1 = target_win["x1"] + 36.0, target_win["x2"] - 36.0
                brake = self.edge_end_factor(self.x, x0, x1, travel, slow_dist=88.0)
                # If an intent is waiting, keep braking
                if self.pending_intent and self.pending_intent.get("type") == "corner":
                    brake = min(brake, 0.2)

                is_sit = abs(getattr(self, "move_speed", 0.0)) <= 3.0 and brake < 0.35
                if is_sit:
                    target_y = self.compute_top_rail_y(edge, is_sitting=True)
                else:
                    target_y = self.compute_top_outward_crawl_y(edge)
                base_spd = 58.0 * (1.08 if self.presence_mode == "lively" else 0.95) * brake
                self.step_border_crawl(dt, "x", travel, base_spd, self.x, target_y)

                self.x = max(x0 - 4.0, min(x1 + 4.0, self.x))
                # Corner only when nearly stopped at the end (complete approach)
                if travel < 0 and self.x <= x0 + 6.0 and abs(self.move_speed) < 18.0:
                    self.release_web(fade=True)
                    self.request_corner(target_win, "LEFT")
                    return True
                if travel > 0 and self.x >= x1 - 6.0 and abs(self.move_speed) < 18.0:
                    self.release_web(fade=True)
                    self.request_corner(target_win, "RIGHT")
                    return True
                # Keep requesting brake+queue when close but still moving
                if travel < 0 and self.x <= x0 + 40.0 and not (self.pending_intent and self.pending_intent.get("type") == "corner"):
                    if brake < 0.45:
                        self.request_corner(target_win, "LEFT")
                if travel > 0 and self.x >= x1 - 40.0 and not (self.pending_intent and self.pending_intent.get("type") == "corner"):
                    if brake < 0.45:
                        self.request_corner(target_win, "RIGHT")
                self.draw_alpha = max(self.draw_alpha, 0.97)
                self.cling_mode_timer += dt
            elif side == "BOTTOM" and target_win:
                edge = self.window_border_edge(target_win, "BOTTOM")
                is_sit = abs(getattr(self, "move_speed", 0.0)) <= 3.0
                target_y = self.compute_bottom_cling_y(edge, is_sitting=is_sit)
                travel = 1.0 if self.cling_orbit > 0 else -1.0
                self.facing = 1.0 if travel > 0 else -1.0
                self.facing_scale = self.facing
                x0, x1 = target_win["x1"] + 44.0, target_win["x2"] - 44.0
                brake = self.edge_end_factor(self.x, x0, x1, travel, slow_dist=88.0)
                if self.pending_intent and self.pending_intent.get("type") == "corner":
                    brake = min(brake, 0.2)
                base_spd = 56.0 * (1.08 if self.presence_mode == "lively" else 1.0) * brake
                self.step_border_crawl(dt, "x", travel, base_spd, self.x, target_y)
                self.x = max(x0 - 4.0, min(x1 + 4.0, self.x))
                if travel > 0 and self.x >= x1 - 6.0 and abs(self.move_speed) < 18.0:
                    self.request_corner(target_win, "RIGHT")
                    return True
                if travel < 0 and self.x <= x0 + 6.0 and abs(self.move_speed) < 18.0:
                    self.request_corner(target_win, "LEFT")
                    return True
                if travel > 0 and self.x >= x1 - 36.0 and brake < 0.45:
                    self.request_corner(target_win, "RIGHT")
                    return True
                if travel < 0 and self.x <= x0 + 36.0 and brake < 0.45:
                    self.request_corner(target_win, "LEFT")
                    return True
                self.draw_alpha = max(self.draw_alpha, 0.97)
                self.cling_mode_timer += dt
            elif side in ("LEFT", "RIGHT"):
                sway = math.sin(self.anim_tick * 2.0) * 0.2 * self.profile()["sway"]
                if side == "RIGHT":
                    sway = abs(sway) * 0.04
                    self.facing = -1.0
                    self.facing_scale = -1.0
                else:
                    sway = -abs(sway) * 0.04
                    self.facing = 1.0
                    self.facing_scale = 1.0

                glass_x = self.window_border_edge(target_win, side) if target_win else self.cling_wall_x
                rounding_offset_x = 0.0
                if not is_screen and target_win and self.hypr_rounding > 0:
                    R = float(self.hypr_rounding)
                    # Top rounding — hug the curve near header
                    if self.y < (self.cling_min_y + R):
                        dy = (self.cling_min_y + R) - self.y
                        if 0 < dy <= R:
                            arc_dx = R - math.sqrt(max(0.0, R * R - dy * dy))
                            rounding_offset_x = -arc_dx if side == "RIGHT" else arc_dx
                    # Bottom rounding — same physics near sill
                    elif self.y > (self.cling_max_y - R):
                        dy = self.y - (self.cling_max_y - R)
                        if 0 < dy <= R:
                            arc_dx = R - math.sqrt(max(0.0, R * R - dy * dy))
                            rounding_offset_x = -arc_dx if side == "RIGHT" else arc_dx

                target_x = self.compute_outward_cling_x(
                    self.cling_wall_x, side, is_screen, rounding_offset_x, glass_x=glass_x,
                ) + sway

                border_now = float(glass_x)
                resized = abs(border_now - float(getattr(self, "_last_cling_border", border_now))) > 0.35
                self._last_cling_border = border_now
                if resized or abs(target_x - self.x) > 10.0:
                    self.x = target_x
                else:
                    self.x += (target_x - self.x) * min(1.0, dt * 40.0)
                self.vx = 0.0
                self.cling_mode_timer += dt
                self.draw_alpha = max(self.draw_alpha, 0.96)

                y_lo = self.cling_min_y + 42.0
                y_hi = self.cling_max_y - 28.0
                if CHARACTERS[self.current_char]["format"] == "shimeji":
                    inward_lean = math.radians(15.0) if side == "RIGHT" else math.radians(-15.0)
                else:
                    inward_lean = -0.04 if side == "RIGHT" else 0.04

                if self.cling_mode == "ORBIT":
                    self.cling_mode = "CLIMB_UP"
                    self.cling_mode_timer = 0.0
                    self.begin_motion("climb", 1.2, lock=False)

                if self.cling_mode == "CLIMB_UP":
                    travel_y = -1.0  # up
                    brake = self.edge_end_factor(self.y, y_lo, y_hi, travel_y, slow_dist=70.0)
                    if self.pending_intent and self.pending_intent.get("type") == "corner":
                        brake = min(brake, 0.2)
                    base = 48.0 * (1.08 if self.presence_mode == "lively" else 0.95) * brake
                    spd = self.smooth_move_speed(dt, travel_y * base, accel=100.0, decel=140.0)
                    phase, plant, smul, w_roll = self.advance_gait(dt, spd)
                    self.vy = spd * smul
                    self.y += self.vy * dt
                    self.step_bob_y = plant * 1.25 * self.render_scale
                    self.target_body_angle = inward_lean + w_roll * 0.70 + (plant - 0.5) * 0.03
                    self.scale_y += ((1.0 - 0.05 * plant) - self.scale_y) * min(1.0, dt * 14.0)
                    self.scale_x += ((1.0 + 0.035 * plant) - self.scale_x) * min(1.0, dt * 14.0)
                    if random.random() < self.profile()["climb_particle"] * 0.6:
                        self.emit(1, self.cling_wall_x, self.y, cdata["particle"])
                    if self.y <= y_lo + 4.0 and abs(self.move_speed) < 16.0:
                        if target_win and not is_screen:
                            self.cling_orbit = 1 if side == "RIGHT" else -1
                            self.request_corner(target_win, "TOP")
                            return True
                        if is_screen and random.random() < 0.35:
                            self.hang_on_screen_top()
                            return True
                        # Reverse only after completing climb phrase
                        if not self.motion_busy():
                            self.cling_mode = "WALL_SLIDE"
                            self.cling_mode_timer = 0.0
                            self.begin_motion("slide", 1.4, lock=False)
                    elif self.y <= y_lo + 36.0 and brake < 0.45 and target_win and not is_screen:
                        self.cling_orbit = 1 if side == "RIGHT" else -1
                        self.request_corner(target_win, "TOP")

                elif self.cling_mode == "WALL_SLIDE":
                    travel_y = 1.0  # down
                    brake = self.edge_end_factor(self.y, y_lo, y_hi, travel_y, slow_dist=70.0)
                    if self.pending_intent and self.pending_intent.get("type") == "corner":
                        brake = min(brake, 0.2)
                    base = 42.0 * brake
                    spd = self.smooth_move_speed(dt, travel_y * base, accel=90.0, decel=130.0)
                    phase, plant, smul, _ = self.advance_gait(dt, spd)
                    self.vy = spd * smul
                    self.y += self.vy * dt
                    self.step_bob_y = plant * 0.7 * self.render_scale
                    self.target_body_angle = inward_lean
                    self.scale_y += ((1.0 - 0.03 * plant) - self.scale_y) * min(1.0, dt * 12.0)
                    self.scale_x += ((1.0 + 0.025 * plant) - self.scale_x) * min(1.0, dt * 12.0)
                    if random.random() < self.profile()["slide_particle"] * 0.5:
                        self.emit(1, self.cling_wall_x, self.y, "sparkle")
                    if self.y >= y_hi - 4.0 and abs(self.move_speed) < 16.0:
                        self.y = min(self.y, y_hi)
                        if target_win and not is_screen:
                            self.cling_orbit = -1 if side == "LEFT" else 1
                            self.request_corner(target_win, "BOTTOM")
                            return True
                        if not self.motion_busy():
                            self.cling_mode = "CLIMB_UP" if random.random() < 0.65 else "WALL_REST"
                            self.cling_mode_timer = 0.0
                            self.begin_motion(self.cling_mode.lower(), 1.0, lock=False)
                            self.trigger_squash(-0.1)
                    elif self.y >= y_hi - 36.0 and brake < 0.45 and target_win and not is_screen:
                        self.cling_orbit = -1 if side == "LEFT" else 1
                        self.request_corner(target_win, "BOTTOM")
                        return True

                else:  # WALL_REST — breathe, then resume only when unlocked
                    self.move_speed = self.smooth_move_speed(dt, 0.0, accel=80.0, decel=120.0)
                    self.vy = self.move_speed
                    self.step_bob_y = 0.0
                    self.target_body_angle = inward_lean + math.sin(self.anim_tick * 1.5) * 0.02
                    breath = 0.5 + 0.5 * math.sin(self.anim_tick * 2.0)
                    self.scale_y += ((0.97 + 0.03 * breath) - self.scale_y) * min(1.0, dt * 8.0)
                    rest_lo, rest_hi = self.profile()["wall_rest"]
                    if (not self.motion_busy()) and self.cling_mode_timer > random.uniform(rest_lo, rest_hi):
                        if random.random() < self.profile()["rest_bias"] * 0.45:
                            self.cling_mode_timer = 0.0
                            self.begin_motion("rest", 1.2, lock=True)
                        elif target_win and not is_screen and random.random() < 0.35:
                            self.request_corner(target_win, self.orbit_next_side(side))
                            return True
                        else:
                            self.cling_mode = random.choice(["WALL_SLIDE", "CLIMB_UP", "CLIMB_UP"])
                            self.cling_mode_timer = 0.0
                            self.begin_motion(self.cling_mode.lower(), 1.2, lock=False)

                self.y = max(y_lo - 2.0, min(y_hi + 2.0, self.y))

                # Long-duration orbit: only when unlocked (never mid-climb cut)
                if self.state_timer > self.cling_duration and not self.motion_busy():
                    if target_win and not is_screen and random.random() < 0.5:
                        self.request_corner(target_win, self.orbit_next_side(side))
                        self.state_timer = 0.0
                        lo, hi = self.profile()["cling_duration"]
                        self.cling_duration = random.uniform(lo, hi)
                    elif random.random() < self.profile()["leap_chance"] * 0.7:
                        self.state = "FALLING"
                        self.state_timer = 0.0
                        push_dir = 1.0 if side == "RIGHT" else -1.0
                        self.vx = push_dir * random.uniform(140, 220)
                        self.vy = -random.uniform(100, 170)
                        self.facing = push_dir
                        self.trigger_squash(0.16)
                        self.emit(2, self.x, self.y, CHARACTERS[self.current_char]["particle"])
                    else:
                        lo, hi = self.profile()["cling_duration"]
                        self.cling_duration = random.uniform(lo, hi)
                        self.state_timer = 0.0
                        self.cling_mode = random.choice(["CLIMB_UP", "WALL_SLIDE"])
                        self.cling_mode_timer = 0.0
                        self.begin_motion(self.cling_mode.lower(), 1.0, lock=False)
            # end LEFT/RIGHT

        elif self.state == "SWINGING":
            # Real Spidey swing: constrained pendulum (web = fixed-length rope)
            self.step_bob_y = 0.0
            self.web_phase += dt * 4.0
            self.web_opacity = 1.0
            ax, ay = self.web_anchor_x, self.web_anchor_y
            rest = max(40.0, float(self.web_length))

            self.vy += self.gravity * 0.95 * dt
            self.vx *= math.pow(0.999, dt * 60)
            self.vy *= math.pow(0.999, dt * 60)

            self.x += self.vx * dt
            self.y += self.vy * dt
            dx = self.x - ax
            dy = self.y - ay
            dist = math.hypot(dx, dy)
            if dist > 0.001:
                ux, uy = dx / dist, dy / dist
                if dist > rest * 1.01:
                    self.x = ax + ux * rest
                    self.y = ay + uy * rest
                    v_rad = self.vx * ux + self.vy * uy
                    if v_rad > 0.0:
                        self.vx -= ux * v_rad
                        self.vy -= uy * v_rad
                elif dist < rest * 0.90:
                    pull = (rest - dist) * 22.0
                    self.vx += ux * pull * dt
                    self.vy += uy * pull * dt
                else:
                    v_rad = self.vx * ux + self.vy * uy
                    self.vx -= ux * v_rad * 0.9
                    self.vy -= uy * v_rad * 0.9

            dx = self.x - ax
            dy = self.y - ay
            dist = math.hypot(dx, dy) or 1.0
            self.web_tension = max(0.0, min(1.5, (dist / rest) - 0.92) * 6.0)
            self.web_hand_x = self.x
            self.web_hand_y = self.y - 10.0 * self.render_scale

            self.facing = 1.0 if self.vx >= 0 else -1.0
            self.facing_scale = self.facing
            ang = math.atan2(dx, max(1.0, dy))
            self.target_body_angle = max(-0.55, min(0.55, -ang * 0.28 + self.vx * 0.0007))

            self.web_duration += dt
            win = self.cling_target_window
            swing_ang = math.atan2(dx, max(1.0, dy))
            at_apex = self.web_duration > 0.9 and self.vy < -18.0 and abs(swing_ang) > 0.32
            past_mid = self.web_duration > 1.4 and (
                (self.cling_orbit > 0 and self.x > ax - 8.0) or
                (self.cling_orbit < 0 and self.x < ax + 8.0)
            )
            time_up = self.web_duration > 2.8

            if win and (at_apex or past_mid or time_up):
                if self.web_swings_left > 1:
                    self._push_web_ghost()
                    self.web_swings_left -= 1
                    self.web_swing_index += 1
                    keep_vx, keep_vy = self.vx * 0.7, self.vy * 0.3
                    self._begin_next_web_swing(win)
                    self.vx = keep_vx + self.vx * 0.4
                    self.vy = min(keep_vy, self.vy)
                else:
                    # Land back onto top crawl at CURRENT x — keep walking the circuit
                    self.web_swings_left = 0
                    self._push_web_ghost()
                    self.release_web(fade=True)
                    edge = self.window_border_edge(win, "TOP")
                    self.x = max(win["x1"] + 40.0, min(win["x2"] - 40.0, self.x))
                    self.y = self.compute_stand_y(edge)
                    self.vx = 0.0
                    self.vy = 0.0
                    border = {
                        "type": "WIN_TOP",
                        "x": (win["x1"] + win["x2"]) * 0.5,
                        "y1": win["y_top"],
                        "y2": win["y_bot"],
                        "side": "TOP",
                        "win": win,
                    }
                    self.start_clinging(border)
                    self.cling_mode = "TOP_CRAWL"
                    self.cling_mode_timer = 0.4
            elif not win and self.web_duration > 3.5:
                self.release_web(fade=True)
                self.state = "FALLING"
                self.state_timer = 0.0

            if self.web_ghosts:
                alive = []
                for g in self.web_ghosts:
                    g["a"] -= dt * 0.65
                    if g["a"] > 0.04:
                        alive.append(g)
                self.web_ghosts = alive[:6]

        elif self.state == "FALLING":
            self.step_bob_y = 0.0
            self.vy += self.gravity * dt
            self.vx *= math.pow(self.air_drag, dt * 60)

            # Dynamic airborne velocity-aligned rotation & squash/stretch
            speed = math.hypot(self.vx, self.vy)
            target_tilt = math.atan2(self.vy, self.vx * self.facing) * 0.22 if abs(self.vx) > 30 else (self.vx * 0.0006)
            self.target_body_angle = max(-0.55, min(0.55, target_tilt))
            target_sy = min(1.35, 1.0 + speed * 0.00035)
            self.scale_y += (target_sy - self.scale_y) * 0.25
            self.scale_x = 1.0 / math.sqrt(max(0.4, self.scale_y))

            prev_y = self.y
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Screen edge bouncing during fall / throw (never disappears)
            if self.x < 20.0:
                self.x = 20.0
                self.vx = abs(self.vx) * 0.55
                self.emit(1, self.x, self.y, CHARACTERS[self.current_char]["particle"])
            elif self.x > self.screen_width - 20.0:
                self.x = self.screen_width - 20.0
                self.vx = -abs(self.vx) * 0.55
                self.emit(1, self.x, self.y, CHARACTERS[self.current_char]["particle"])
            if self.y < 20.0:
                self.y = 20.0
                self.vy = abs(self.vy) * 0.50

            # Mid-air catch vertical borders:
            if getattr(self, "no_cling_timer", 0.0) <= 0.0:
                for b in self.vertical_borders:
                    bx = b["x"]
                    if abs(self.x - bx) < (hand_offset + 16.0) and (b["y1"] - 10 <= self.y <= b["y2"] - 20):
                        if random.random() < 0.65:
                            self.start_clinging(b)
                            return True

                # Window Top Catching upside down / perch:
                if self.vy > 80.0:
                    for p in self.platforms:
                        edge = self.window_border_edge(p, "TOP")
                        if p["x1"] + 25 <= self.x <= p["x2"] - 25:
                            if prev_y <= edge + 22 and self.y >= edge - 22:
                                if random.random() < 0.5:
                                    self.start_window_top_hang(p)
                                else:
                                    self.y = self.compute_stand_y(edge)
                                    self.handle_landing(dt)
                                    self.state = "SITTING"
                                    self.cling_target_window = p
                                    self.cling_target_address = p.get("address")
                                    self.state_timer = 0.0
                                break

                # Check window top landing (feet flush to border)
                if self.state == "FALLING":
                    for p in self.platforms:
                        edge = self.window_border_edge(p, "TOP")
                        stand = self.compute_stand_y(edge)
                        if p["x1"] - 15 <= self.x <= p["x2"] + 15:
                            if prev_y <= stand + 18 and self.y >= stand - 12 and self.vy >= 0:
                                self.y = stand
                                self.handle_landing(dt)
                                self.state = "SITTING"
                                self.cling_target_window = p
                                self.cling_target_address = p.get("address")
                                self.state_timer = 0.0
                                break

                # Check window bottom inner sill landing (inside window)
                if self.state == "FALLING":
                    for p in self.platforms:
                        if p.get("address") in ("floor", "screen"):
                            continue
                        edge_bot = float(p["y_bot"])
                        stand_bot = self.compute_bottom_cling_y(edge_bot)
                        if p["x1"] - 15 <= self.x <= p["x2"] + 15:
                            if prev_y <= stand_bot + 22 and self.y >= stand_bot - 14 and self.vy >= 0:
                                self.y = stand_bot
                                self.handle_landing(dt)
                                self.state = "SITTING"
                                self.cling_target_window = p
                                self.cling_target_address = p.get("address")
                                self.cling_side = "BOTTOM"
                                self.state_timer = 0.0
                                break

            # Land on the desktop floor — feet flush to bottom edge
            floor_stand = self.floor_y_for()
            if self.state == "FALLING" and self.y >= floor_stand - 2.0 and self.vy >= 0:
                self.y = floor_stand
                self.handle_landing(dt)
                self._force_fling = False
                self.state = "SITTING"
                floor = self.get_screen_floor()
                self.cling_target_window = floor
                self.cling_target_address = "floor"
                self.state_timer = 0.0
                self.emit(1, self.x, self.y, CHARACTERS[self.current_char]["particle"])
                return True

        elif self.state in ["IDLE", "WALKING", "SITTING", "DANCE", "WAVE_HANDS", "SPECIAL", "KNOCKOUT"]:
            curr_plat = self.get_current_platform()

            if not curr_plat:
                # Prefer settling on the floor over forced fall
                if abs(self.y - floor_y) < 28.0 or self.y >= floor_y - 8.0:
                    floor = self.get_screen_floor()
                    curr_plat = {**floor, "active_edge": "FLOOR", "edge_y": floor["y_top"]}
                    self.cling_target_window = curr_plat
                    self.cling_target_address = "floor"
                    self.y = floor_y
                else:
                    self.state = "FALLING"
                    self.vy = max(self.vy, 40.0)
                    return True

            is_sit = self.state in ("SITTING", "DANCE", "SPECIAL") or abs(getattr(self, "vx", 0.0)) <= 3.0
            edge_type = curr_plat.get("active_edge", "TOP")
            edge_y = curr_plat.get("edge_y", curr_plat.get("y_top", 0.0))

            if edge_type == "BOTTOM":
                target_plat_y = self.compute_bottom_cling_y(edge_y, is_sitting=is_sit)
            else:
                target_plat_y = self.compute_top_rail_y(edge_y, is_sitting=is_sit) if is_sit else self.compute_stand_y(edge_y)

            if self.state == "WALKING" and curr_plat:
                stride_cycle = math.sin(self.anim_tick * 15.0)
                self.step_bob_y = 0.0  # Zero air gap: soles stay planted flush to platform surface
                self.target_body_angle = self.facing * 0.08 + stride_cycle * 0.035
                self.x += self.vx * dt
                self.y = target_plat_y

                if self.x <= curr_plat["x1"] + 22.0:
                    self.facing = 1.0
                    self.target_x = curr_plat["x2"] - 35.0
                    if curr_plat.get("address") != "floor" and edge_type == "TOP" and random.random() < 0.4:
                        self.start_window_top_hang(curr_plat)
                elif self.x >= curr_plat["x2"] - 22.0:
                    self.facing = -1.0
                    self.target_x = curr_plat["x1"] + 35.0
                    if curr_plat.get("address") != "floor" and edge_type == "TOP" and random.random() < 0.4:
                        self.start_window_top_hang(curr_plat)

                # Check vertical borders to cling to while walking
                for b in self.vertical_borders:
                    bx = b["x"]
                    if abs(self.x - bx) < (hand_offset + 14.0) and (b["y1"] - 10 <= self.y <= b["y2"] + 10):
                        if random.random() < 0.65:
                            self.start_clinging(b)
                            break

                self.update_ground_ai(dt)

            elif self.state == "IDLE":
                self.vx = 0.0
                self.vy = 0.0
                self.step_bob_y = 0.0
                self.target_body_angle = math.sin(self.anim_tick * 2.0) * 0.02
                self.y = target_plat_y
                self.x = max(curr_plat["x1"] + 25.0, min(curr_plat["x2"] - 25.0, self.x))
                self.update_ground_ai(dt)

            elif self.state == "SITTING":
                self.vx = 0.0
                self.vy = 0.0
                self.step_bob_y = 0.0
                self.target_body_angle = 0.0
                self.y = target_plat_y
                self.x = max(curr_plat["x1"] + 25.0, min(curr_plat["x2"] - 25.0, self.x))
                self.update_ground_ai(dt)

            elif self.state == "DANCE":
                self.vx = 0.0
                self.vy = 0.0
                self.step_bob_y = abs(math.sin(self.anim_tick * 10.0)) * 2.5 * self.render_scale
                self.target_body_angle = math.sin(self.anim_tick * 6.0) * 0.07
                self.y = target_plat_y
                self.x = max(curr_plat["x1"] + 25.0, min(curr_plat["x2"] - 25.0, self.x))
                self.update_ground_ai(dt)

            elif self.state == "WAVE_HANDS":
                self.vx = 0.0
                self.vy = 0.0
                self.step_bob_y = 0.0
                self.target_body_angle = 0.0
                self.y = target_plat_y
                self.x = max(curr_plat["x1"] + 25.0, min(curr_plat["x2"] - 25.0, self.x))
                self.update_ground_ai(dt)

            elif self.state == "SPECIAL":
                self.vx = 0.0
                self.vy = 0.0
                self.step_bob_y = 0.0
                self.target_body_angle = math.sin(self.anim_tick * 4.0) * 0.06
                self.y = target_plat_y
                if random.random() < 0.04 * self.profile()["particle_mul"]:
                    p_type = CHARACTERS[self.current_char]["particle"]
                    self.emit(1, self.x + random.uniform(-20, 20), self.y - 20, p_type)
                if self.state_timer > 5.5:
                    self.state = "IDLE"
                    self.state_timer = 0.0

            elif self.state == "KNOCKOUT":
                self.vx *= 0.85
                self.step_bob_y = 0.0
                self.target_body_angle = 0.0
                self.y = target_plat_y
                if self.state_timer > 3.0:
                    self.state = "IDLE"
                    self.state_timer = 0.0

        # Spring squash & stretch recovery
        if self.state != "CLINGING" and self.state != "WINDOW_TOP_HANG" and self.state != "SWINGING":
            diff = self.scale_y - 1.0
            accel = -self.spring_k * diff - self.spring_d * self.scale_vy
            self.scale_vy += accel * dt
            self.scale_y += self.scale_vy * dt
            self.scale_y = max(0.55, min(1.6, self.scale_y))
            self.scale_x = 1.0 / math.sqrt(max(0.4, self.scale_y))
        else:
            self.scale_x = 1.0
            self.scale_y = 1.0
            self.scale_vy = 0.0

        # Cheap input-shape updates only when pose/size moved
        shape_key = (int(self.x), int(self.y), int(self.render_scale * 100), self.state)
        if shape_key != self._last_shape_key:
            self._last_shape_key = shape_key
            self.update_input_shape()
        self.queue_draw()
        return True

    def start_window_top_hang(self, win=None):
        self.state = "WINDOW_TOP_HANG"
        self.cling_side = "TOP"
        self.state_timer = 0.0
        self.cling_target_window = win
        self.cling_target_address = win.get("address") if win else None
        # Only explicit screen bezel hang — near-top tiled windows still use window top
        self.hang_on_screen = bool(win is None or (win and win.get("address") == "screen"))
        self.vx = 0.0
        self.vy = 0.0
        self.step_bob_y = 0.0
        self.target_body_angle = 0.0
        self.body_angle = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.scale_vy = 0.0
        # Keep coherent size (no snap to a different scale)
        self.render_scale = self.canonical_scale()

        border_y = self.resolve_hang_border_y(None if self.hang_on_screen else win)
        self.y = self.compute_top_outward_crawl_y(border_y)
        self._last_hang_border = border_y
        if win and not self.hang_on_screen:
            self.x = max(win["x1"] + 40.0, min(win["x2"] - 40.0, self.x))
        else:
            self.x = max(48.0, min(self.screen_width - 48.0, self.x))

        self.draw_alpha = 1.0
        cdata = CHARACTERS[self.current_char]
        # Hang without leftover silk — webs only exist during active swings
        self.release_web(fade=False)
        self.emit(2, self.x, self.y, cdata["particle"])
        print(
            f"[HyprPet] hang top border={border_y:.1f} -> y={self.y:.1f} "
            f"screen={self.hang_on_screen} addr={self.cling_target_address}",
            flush=True,
        )

    def start_clinging(self, border):
        self.state = "CLINGING"
        self.state_timer = 0.0
        self.move_speed = 0.0
        self.move_speed_target = 0.0
        self.pending_intent = None
        self.motion_lock = False
        self.gait_phase = random.random()
        self.cling_wall_x = border["x"]
        self.cling_side = border["side"]
        self.cling_border_type = border.get("type", "WIN_" + self.cling_side)
        self.cling_min_y = border["y1"]
        self.cling_max_y = border["y2"]
        lo, hi = self.profile()["cling_duration"]
        self.cling_duration = random.uniform(lo, hi)
        if random.random() < self.profile()["rest_bias"]:
            self.cling_mode = "WALL_REST"
        else:
            self.cling_mode = random.choice(["CLIMB_UP", "CLIMB_UP", "WALL_SLIDE", "ORBIT"])
        self.cling_mode_timer = 0.0
        self.cling_target_window = border.get("win")
        self.cling_target_address = border.get("win", {}).get("address") if border.get("win") else None
        self.vx = 0.0
        self.vy = 0.0
        if border.get("side") in ("LEFT", "RIGHT") and CHARACTERS[self.current_char]["format"] == "shimeji":
            init_lean = math.radians(15.0) if border.get("side") == "RIGHT" else math.radians(-15.0)
            self.target_body_angle = init_lean
            self.body_angle = init_lean
        else:
            self.target_body_angle = 0.0
            self.body_angle = 0.0
        self.render_scale = self.canonical_scale()
        self.crawl_web_points = []

        cdata = CHARACTERS[self.current_char]
        is_screen = self.cling_border_type.startswith("SCREEN")
        side = self.cling_side

        if side == "RIGHT":
            self.facing = -1.0
            self.facing_scale = -1.0
        elif side == "LEFT":
            self.facing = 1.0
            self.facing_scale = 1.0
        elif side == "TOP":
            # Match crawl travel: +orbit from RIGHT crawls left
            self.facing = -1.0 if self.cling_orbit > 0 else 1.0
            self.facing_scale = self.facing
        else:  # BOTTOM
            self.facing = 1.0 if self.cling_orbit > 0 else -1.0
            self.facing_scale = self.facing

        glass = None
        if self.cling_target_window and side in ("LEFT", "RIGHT"):
            glass = self.window_border_edge(self.cling_target_window, side)
            self.fit_cling_scale_to_gap(side, glass, is_screen)
            self.x = self.compute_outward_cling_x(self.cling_wall_x, side, is_screen, glass_x=glass)
        elif self.cling_target_window and side == "TOP":
            edge = self.window_border_edge(self.cling_target_window, "TOP")
            self.y = self.compute_top_outward_crawl_y(edge)
            self.x = max(self.cling_target_window["x1"] + 36.0, min(self.cling_target_window["x2"] - 36.0, self.x))
        elif self.cling_target_window and side == "BOTTOM":
            self.y = self.compute_bottom_cling_y(self.window_border_edge(self.cling_target_window, "BOTTOM"))
            self.x = max(self.cling_target_window["x1"] + 36.0, min(self.cling_target_window["x2"] - 36.0, self.x))
        elif side in ("LEFT", "RIGHT"):
            self.x = self.compute_outward_cling_x(self.cling_wall_x, side, is_screen, glass_x=glass)

        if side in ("LEFT", "RIGHT"):
            # Smoothly bound Y within the window wall span without popping to the center
            self.y = max(self.cling_min_y + 18.0, min(self.cling_max_y - 18.0, self.y))

        self.trigger_squash(0.14)
        self.emit(2, self.x, self.y, cdata["particle"])

    def orbit_next_side(self, current):
        """Clockwise / counter-clockwise window perimeter."""
        order = ["RIGHT", "TOP", "LEFT", "BOTTOM"]
        if current not in order:
            return "RIGHT"
        i = order.index(current)
        return order[(i + int(self.cling_orbit)) % 4]

    def _corner_geometry(self, win, from_side, to_side):
        """Outer quarter-circle around a Hyprland-rounded window corner."""
        if not win:
            return None
        R = max(12.0, float(getattr(self, "hypr_rounding", 25.0)))
        border_size = max(1.0, float(getattr(self, "hypr_border_size", 2.0)))
        R_eff = R + border_size
        rs = max(0.2, float(self.render_scale))
        # Hands grip the corner rail at R_eff; body center rides at R_eff + standoff
        bounds = self.get_rendered_bounds()
        standoff = max(18.0 * rs, abs(float(bounds.get("rel_grip_left", -22.0 * rs))))
        radius = R_eff + standoff
        x1, x2 = float(win["x1"]), float(win["x2"])
        yt, yb = float(win["y_top"]), float(win["y_bot"])
        pair = (from_side, to_side)

        # Corner centers are inset by R_eff; angles use screen coords (+y down)
        table = {
            ("RIGHT", "TOP"):    dict(cx=x2 - R_eff, cy=yt + R_eff, a0=0.0,            a1=-math.pi * 0.5),
            ("TOP", "RIGHT"):    dict(cx=x2 - R_eff, cy=yt + R_eff, a0=-math.pi * 0.5, a1=0.0),
            ("TOP", "LEFT"):     dict(cx=x1 + R_eff, cy=yt + R_eff, a0=-math.pi * 0.5, a1=-math.pi),
            ("LEFT", "TOP"):     dict(cx=x1 + R_eff, cy=yt + R_eff, a0=-math.pi,        a1=-math.pi * 0.5),
            ("LEFT", "BOTTOM"):  dict(cx=x1 + R_eff, cy=yb - R_eff, a0=math.pi,         a1=math.pi * 0.5),
            ("BOTTOM", "LEFT"):  dict(cx=x1 + R_eff, cy=yb - R_eff, a0=math.pi * 0.5,   a1=math.pi),
            ("BOTTOM", "RIGHT"): dict(cx=x2 - R_eff, cy=yb - R_eff, a0=math.pi * 0.5,   a1=0.0),
            ("RIGHT", "BOTTOM"): dict(cx=x2 - R_eff, cy=yb - R_eff, a0=0.0,            a1=math.pi * 0.5),
        }
        spec = table.get(pair)
        if not spec:
            return None
        spec = dict(spec)
        spec["radius"] = radius
        spec["R"] = R_eff

        is_bottom = (from_side == "BOTTOM" or to_side == "BOTTOM")
        spec["is_bottom"] = is_bottom

        if is_bottom:
            rs = max(0.2, float(self.render_scale))
            edge_bot = self.window_border_edge(win, "BOTTOM")
            stand_y = self.compute_bottom_cling_y(edge_bot)
            wall_left = self.window_border_edge(win, "LEFT")
            wall_right = self.window_border_edge(win, "RIGHT")
            x_on_left = self.compute_outward_cling_x(wall_left, "LEFT", False, glass_x=wall_left)
            x_on_right = self.compute_outward_cling_x(wall_right, "RIGHT", False, glass_x=wall_right)
            sill_x_left = x1 + 44.0 * rs
            sill_x_right = x2 - 44.0 * rs
            rail_bot_y = edge_bot

            if pair == ("LEFT", "BOTTOM"):
                spec["start_x"] = x_on_left
                spec["start_y"] = yb - R_eff - 6.0 * rs
                spec["dest_x"] = sill_x_left
                spec["dest_y"] = stand_y
                spec["ctrl_x"] = x_on_left + (sill_x_left - x_on_left) * 0.25
                spec["ctrl_y"] = yb - 2.0 * rs
                spec["rail_start_x"] = x1 - border_size
                spec["rail_start_y"] = yb - R_eff - 6.0 * rs
                spec["rail_apex_x"] = x1 + border_size * 0.5
                spec["rail_apex_y"] = yb - border_size * 0.5
                spec["rail_dest_x"] = sill_x_left
                spec["rail_dest_y"] = rail_bot_y
            elif pair == ("BOTTOM", "LEFT"):
                spec["start_x"] = sill_x_left
                spec["start_y"] = stand_y
                spec["dest_x"] = x_on_left
                spec["dest_y"] = yb - R_eff - 10.0 * rs
                spec["ctrl_x"] = x_on_left + (sill_x_left - x_on_left) * 0.25
                spec["ctrl_y"] = yb - 2.0 * rs
                spec["rail_start_x"] = sill_x_left
                spec["rail_start_y"] = rail_bot_y
                spec["rail_apex_x"] = x1 + border_size * 0.5
                spec["rail_apex_y"] = yb - border_size * 0.5
                spec["rail_dest_x"] = x1 - border_size
                spec["rail_dest_y"] = yb - R_eff - 10.0 * rs
            elif pair == ("RIGHT", "BOTTOM"):
                spec["start_x"] = x_on_right
                spec["start_y"] = yb - R_eff - 6.0 * rs
                spec["dest_x"] = sill_x_right
                spec["dest_y"] = stand_y
                spec["ctrl_x"] = x_on_right + (sill_x_right - x_on_right) * 0.25
                spec["ctrl_y"] = yb - 2.0 * rs
                spec["rail_start_x"] = x2 + border_size
                spec["rail_start_y"] = yb - R_eff - 6.0 * rs
                spec["rail_apex_x"] = x2 - border_size * 0.5
                spec["rail_apex_y"] = yb - border_size * 0.5
                spec["rail_dest_x"] = sill_x_right
                spec["rail_dest_y"] = rail_bot_y
            elif pair == ("BOTTOM", "RIGHT"):
                spec["start_x"] = sill_x_right
                spec["start_y"] = stand_y
                spec["dest_x"] = x_on_right
                spec["dest_y"] = yb - R_eff - 10.0 * rs
                spec["ctrl_x"] = x_on_right + (sill_x_right - x_on_right) * 0.25
                spec["ctrl_y"] = yb - 2.0 * rs
                spec["rail_start_x"] = sill_x_right
                spec["rail_start_y"] = rail_bot_y
                spec["rail_apex_x"] = x2 - border_size * 0.5
                spec["rail_apex_y"] = yb - border_size * 0.5
                spec["rail_dest_x"] = x2 + border_size
                spec["rail_dest_y"] = yb - R_eff - 10.0 * rs
        return spec

    def trigger_bottom_corner_leap(self, win, corner="BOTTOM_RIGHT"):
        """Athletic parkour leap from bottom window corners down to the desktop floor:
        - Symmetric physics for both bottom-left and bottom-right corners
        - Anticipation crouch / spring
        - Dynamic parabolic launch arc directed outward and downward toward the floor
        - Rotational body lean aligning with trajectory velocity vector
        - Seamless desktop floor landing with impact squash and particles
        """
        is_left = ("LEFT" in str(corner).upper())
        push_dir = -1.0 if is_left else 1.0

        if win and win.get("address") not in ("floor", "screen", None):
            x1 = float(win["x1"])
            x2 = float(win["x2"])
            yb = float(win["y_bot"])
            if is_left:
                self.x = min(self.x, x1 + 8.0)
            else:
                self.x = max(self.x, x2 - 8.0)
            self.y = min(self.y, yb - 2.0)

        floor_stand = self.floor_y_for()
        dist_to_floor = max(10.0, floor_stand - self.y)

        # Release any clinging or webs
        self.release_web(fade=False)
        self.motion_lock = False
        self.pending_intent = None
        self.cling_target_window = None
        self.cling_target_address = None

        # Anticipation crouch & explosive spring off the corner ledge
        self.trigger_squash(-0.24)

        # Trajectory physics: outward push + upward pop into parabolic gravity arc
        if dist_to_floor < 45.0:
            # Short hop if window is already close to desktop floor
            self.vx = push_dir * random.uniform(120.0, 160.0)
            self.vy = -random.uniform(70.0, 110.0)
        else:
            # Athletic parkour leap
            self.vx = push_dir * random.uniform(150.0, 205.0)
            self.vy = -random.uniform(105.0, 155.0)

        self.facing = push_dir
        self.facing_scale = push_dir
        self.target_body_angle = push_dir * 0.28
        self.body_angle = push_dir * 0.18

        # Grace period so pet does not immediately catch the wall it just leapt from
        self.no_cling_timer = 0.70

        # State transition
        self.state = "FALLING"
        self.state_timer = 0.0

        # Kinetic push-off particles & dust
        char_p = CHARACTERS[self.current_char].get("particle", "sparkle")
        self.emit(3, self.x, self.y, char_p)
        self.emit(2, self.x, self.y, "sparkle")

    def start_corner_arc(self, win, from_side, to_side):
        """Begin an athletic, biomechanically real corner climb with physical hand grips (no webs)."""
        meta = self._corner_geometry(win, from_side, to_side)
        if not meta:
            self._apply_edge_cling(win, to_side)
            return

        self.corner_win = win
        self.corner_from = from_side
        self.corner_to = to_side
        self.corner_cx = float(meta["cx"])
        self.corner_cy = float(meta["cy"])
        self.corner_radius = float(meta["radius"])
        self.corner_R_eff = float(meta["R"])
        self.corner_ang0 = float(meta["a0"])
        self.corner_ang1 = float(meta["a1"])
        self.corner_t = 0.0
        self.corner_phase = "plant"
        self.grip_reach_t = 0.0
        self.corner_struggle = 0.0
        self.corner_slip_drop = 0.0
        self.corner_hand_slip_offset = 0.0
        self.corner_catch_pulse = 0.0

        self.corner_is_bottom = bool(meta.get("is_bottom", False))
        if self.corner_is_bottom:
            self.corner_start_x = float(meta["start_x"])
            self.corner_start_y = float(meta["start_y"])
            self.corner_dest_x = float(meta["dest_x"])
            self.corner_dest_y = float(meta["dest_y"])
            self.corner_ctrl_x = float(meta["ctrl_x"])
            self.corner_ctrl_y = float(meta["ctrl_y"])
            self.corner_rail_start_x = float(meta["rail_start_x"])
            self.corner_rail_start_y = float(meta["rail_start_y"])
            self.corner_rail_apex_x = float(meta["rail_apex_x"])
            self.corner_rail_apex_y = float(meta["rail_apex_y"])
            self.corner_rail_dest_x = float(meta["rail_dest_x"])
            self.corner_rail_dest_y = float(meta["rail_dest_y"])

            # Agile, springy duration for bottom corner transitions (0.48s - 0.58s)
            self.corner_duration = 0.44 if self.presence_mode == "lively" else 0.54
            self.x = self.corner_start_x
            self.y = self.corner_start_y
            self.grip_anchor_x = self.corner_rail_start_x
            self.grip_anchor_y = self.corner_rail_start_y
            self.grip_reach_x = self.grip_anchor_x
            self.grip_reach_y = self.grip_anchor_y
            self.grip_reach_target_x = self.grip_reach_x
            self.grip_reach_target_y = self.grip_reach_y
        else:
            # Dynamic agile corner duration (0.42s - 0.54s)
            self.corner_duration = 0.42 if self.presence_mode == "lively" else 0.52

            # Start on the incoming edge just before the curve begins
            self.x = self.corner_cx + math.cos(self.corner_ang0) * self.corner_radius
            self.y = self.corner_cy + math.sin(self.corner_ang0) * self.corner_radius

            # Anchor hand clamped on incoming rail curve
            self.grip_anchor_x = self.corner_cx + math.cos(self.corner_ang0) * self.corner_R_eff
            self.grip_anchor_y = self.corner_cy + math.sin(self.corner_ang0) * self.corner_R_eff

            dang = self.corner_ang1 - self.corner_ang0
            init_reach_ang = self.corner_ang0 + dang * 0.15
            self.grip_reach_x = self.corner_cx + math.cos(init_reach_ang) * self.corner_R_eff
            self.grip_reach_y = self.corner_cy + math.sin(init_reach_ang) * self.corner_R_eff
            self.grip_reach_target_x = self.grip_reach_x
            self.grip_reach_target_y = self.grip_reach_y

        self.grip_catch_x = self.grip_anchor_x
        self.grip_catch_y = self.grip_anchor_y
        self._corner_apex_emitted = False

        self.vx = 0.0
        self.vy = 0.0
        self.move_speed = 0.0
        self.state = "CORNER_ARC"
        self.state_timer = 0.0
        self.cling_target_window = win
        self.cling_target_address = win.get("address")
        self.cling_side = from_side
        self.release_web(fade=False)  # Clean transition, zero stray web
        self.begin_motion("corner_struggle", self.corner_duration, lock=True)
        self.trigger_squash(0.06)
        self.emit(1, self.grip_anchor_x, self.grip_anchor_y, CHARACTERS[self.current_char]["particle"])

    def step_modern_corner(self, dt):
        """Dynamic physics hand-climbing arc across window corners with natural anatomical reach."""
        win = self.corner_win or self.cling_target_window
        if win and win.get("address") not in ("floor", None):
            meta = self._corner_geometry(win, self.corner_from, self.corner_to)
            if meta:
                self.corner_cx = float(meta["cx"])
                self.corner_cy = float(meta["cy"])
                self.corner_radius = float(meta["radius"])
                self.corner_R_eff = float(meta["R"])
                self.corner_ang0 = float(meta["a0"])
                self.corner_ang1 = float(meta["a1"])

        dur = max(0.35, getattr(self, "corner_duration", 0.48))
        self.corner_t += dt / dur
        u = max(0.0, min(1.0, self.corner_t))
        dang = self.corner_ang1 - self.corner_ang0
        rs = self.render_scale

        # Smooth cubic ease-in-out progress along the arc
        e = u * u * (3.0 - 2.0 * u)

        # Set animated climbing phases for sprite frame alternation
        if u < 0.25:
            self.corner_phase = "plant"
        elif u < 0.60:
            self.corner_phase = "reach"
        elif u < 0.85:
            self.corner_phase = "pull"
        else:
            self.corner_phase = "settle"

        # Biomechanical muscular effort squash & stretch during the pull-up phase
        if 0.20 <= u <= 0.80:
            pull_effort = math.sin((u - 0.20) / 0.60 * math.pi)
            self.scale_y += ((1.0 - 0.065 * pull_effort) - self.scale_y) * min(1.0, dt * 18.0)
            self.scale_x += ((1.0 + 0.045 * pull_effort) - self.scale_x) * min(1.0, dt * 18.0)
        else:
            self.scale_y += (1.0 - self.scale_y) * min(1.0, dt * 14.0)
            self.scale_x += (1.0 - self.scale_x) * min(1.0, dt * 14.0)

        is_bottom = getattr(self, "corner_is_bottom", False)
        if is_bottom:
            omt = 1.0 - e
            bx = (omt * omt) * self.corner_start_x + (2.0 * omt * e) * self.corner_ctrl_x + (e * e) * self.corner_dest_x
            by = (omt * omt) * self.corner_start_y + (2.0 * omt * e) * self.corner_ctrl_y + (e * e) * self.corner_dest_y
            prev_x, prev_y = self.x, self.y
            self.x = bx
            self.y = by
            self.vx = (self.x - prev_x) / max(dt, 1e-4)
            self.vy = (self.y - prev_y) / max(dt, 1e-4)

            self.grip_catch_x = self.x
            self.grip_catch_y = self.y

            # Smooth body lean along tangent
            de = min(1.0, e + 0.02)
            omte = 1.0 - de
            nx = (omte * omte) * self.corner_start_x + (2.0 * omte * de) * self.corner_ctrl_x + (de * de) * self.corner_dest_x
            ny = (omte * omte) * self.corner_start_y + (2.0 * omte * de) * self.corner_ctrl_y + (de * de) * self.corner_dest_y
            tx, ty = nx - bx, ny - by
            lean = math.atan2(ty, abs(tx) + 1e-4) * 0.35
            self.target_body_angle = lean
            self.body_angle += (self.target_body_angle - self.body_angle) * min(1.0, dt * 16.0)
        else:
            ang = self.corner_ang0 + dang * e
            r = self.corner_radius
            prev_x, prev_y = self.x, self.y
            self.x = self.corner_cx + math.cos(ang) * r
            self.y = self.corner_cy + math.sin(ang) * r
            self.vx = (self.x - prev_x) / max(dt, 1e-4)
            self.vy = (self.y - prev_y) / max(dt, 1e-4)

            # Update live contact point on physical curved rail for ambient contact shadow
            self.grip_catch_x = self.corner_cx + math.cos(ang) * self.corner_R_eff
            self.grip_catch_y = self.corner_cy + math.sin(ang) * self.corner_R_eff

            # Emit a subtle themed particle puff as the pet crests the apex
            if u >= 0.48 and not getattr(self, "_corner_apex_emitted", False):
                self._corner_apex_emitted = True
                self.emit(1, self.grip_catch_x, self.grip_catch_y, CHARACTERS[self.current_char]["particle"])

            # Smooth body rotation matching the corner arc tangent
            from_side = getattr(self, "corner_from", "LEFT")
            to_side = getattr(self, "corner_to", "TOP")
            
            if from_side == "LEFT" and to_side == "TOP":
                turn_rad = math.radians(90.0)
                self.target_body_angle = e * turn_rad
            elif from_side == "TOP" and to_side == "LEFT":
                turn_rad = math.radians(-90.0)
                self.target_body_angle = (1.0 - e) * turn_rad
            elif from_side == "RIGHT" and to_side == "TOP":
                turn_rad = math.radians(-90.0)
                self.target_body_angle = e * turn_rad
            elif from_side == "TOP" and to_side == "RIGHT":
                turn_rad = math.radians(90.0)
                self.target_body_angle = (1.0 - e) * turn_rad
            else:
                self.target_body_angle = dang * e

            self.body_angle += (self.target_body_angle - self.body_angle) * min(1.0, dt * 18.0)

        self.step_bob_y = 0.0
        self.draw_alpha = max(self.draw_alpha, 0.98)

        if self.corner_t >= 1.0:
            self.target_body_angle = 0.0
            self.body_angle = 0.0
            self._finish_corner_arc()



    def _finish_corner_arc(self):
        """Settle onto the destination edge after the arc completes."""
        win = self.corner_win or self.cling_target_window
        to_side = self.corner_to
        self.move_speed = 0.0
        self.move_speed_target = 0.0
        self.pending_intent = None
        self.begin_motion("post_corner", 0.35, lock=True)
        # Land exactly on arc end
        if getattr(self, "corner_is_bottom", False):
            self.x = self.corner_dest_x
            self.y = self.corner_dest_y
        else:
            self.x = self.corner_cx + math.cos(self.corner_ang1) * self.corner_radius
            self.y = self.corner_cy + math.sin(self.corner_ang1) * self.corner_radius
        self.corner_slip_drop = 0.0
        self.vx *= 0.2
        self.vy *= 0.2
        self.trigger_squash(-0.08)
        self._apply_edge_cling(win, to_side)

    def _apply_edge_cling(self, win, to_side):
        """Attach to an edge after a corner (or fallback) — no teleport jumps."""
        if not win or win.get("address") in ("screen", "floor", None):
            if to_side in ("LEFT", "RIGHT"):
                self.cling_to_screen_border(to_side, mode="CLIMB_UP")
            else:
                self.hang_on_screen_top()
            return

        if to_side == "TOP":
            border = {
                "type": "WIN_TOP",
                "x": (win["x1"] + win["x2"]) * 0.5,
                "y1": win["y_top"],
                "y2": win["y_bot"],
                "side": "TOP",
                "win": win,
            }
            # Keep current x (from arc); only clamp into the header
            self.x = max(win["x1"] + 36.0, min(win["x2"] - 36.0, self.x))
            self.start_clinging(border)
            self.cling_mode = "TOP_CRAWL"
            self.cling_mode_timer = 0.0
            self.release_web(fade=False)
        elif to_side == "BOTTOM":
            border = {
                "type": "WIN_BOTTOM",
                "x": (win["x1"] + win["x2"]) * 0.5,
                "y1": win["y_top"],
                "y2": win["y_bot"],
                "side": "BOTTOM",
                "win": win,
            }
            # Inside sill — keep x near the corner we entered from
            self.x = max(win["x1"] + 44.0, min(win["x2"] - 44.0, self.x))
            self.y = self.compute_bottom_cling_y(self.window_border_edge(win, "BOTTOM"))
            self.start_clinging(border)
            self.cling_mode = "BOTTOM_CRAWL"
            self.cling_mode_timer = 0.0
        else:
            wall = self.window_border_edge(win, to_side)
            border = {
                "type": f"WIN_{to_side}",
                "x": wall,
                "y1": win["y_top"],
                "y2": win["y_bot"],
                "side": to_side,
                "win": win,
            }
            # Keep arc Y; clamp into the wall span
            self.y = max(win["y_top"] + 40.0, min(win["y_bot"] - 28.0, self.y))
            self.start_clinging(border)
            if self.corner_from == "BOTTOM" or (to_side == "RIGHT" and self.cling_orbit > 0) or (to_side == "LEFT" and self.cling_orbit < 0):
                self.cling_mode = "CLIMB_UP"
            else:
                self.cling_mode = "WALL_SLIDE"
            self.cling_mode_timer = 0.0

    def transition_orbit_corner(self, win, to_side):
        """Move from one outer edge to the next via corner-arc physics."""
        if not win or win.get("address") in ("screen", "floor", None):
            if to_side in ("LEFT", "RIGHT"):
                self.cling_to_screen_border(to_side, mode="CLIMB_UP")
            else:
                self.hang_on_screen_top()
            return
        from_side = self.cling_side if self.cling_side in ("LEFT", "RIGHT", "TOP", "BOTTOM") else "RIGHT"
        if self.state == "CORNER_ARC" and self.corner_to == to_side:
            return
        self.start_corner_arc(win, from_side, to_side)

    def start_sill_corner(self, win, from_side, to_side):
        """Hop between an outside wall and the inside bottom sill."""
        edge = self.window_border_edge(win, "BOTTOM")
        stand = self.compute_bottom_cling_y(edge)
        if to_side == "BOTTOM":
            # Coming from LEFT/RIGHT outside → step inward onto the sill
            if from_side == "LEFT" or self.x < (win["x1"] + win["x2"]) * 0.5:
                self.x = win["x1"] + 52.0
            else:
                self.x = win["x2"] - 52.0
            self.y = stand
            self.vx = 0.0
            self.vy = 0.0
            self.trigger_squash(0.12)
            self._apply_edge_cling(win, "BOTTOM")
            return
        # Leaving sill → outside wall near bottom
        if to_side == "LEFT":
            self.x = win["x1"] + 44.0
            self.y = stand
        else:
            self.x = win["x2"] - 44.0
            self.y = stand
        # Brief outward hop onto the wall
        self.trigger_squash(0.1)
        self._apply_edge_cling(win, to_side)
        # Pin near bottom of the wall for climb-up
        self.y = min(self.y, win["y_bot"] - 36.0)
        self.y = max(self.y, win["y_bot"] - 90.0)
        self.cling_mode = "CLIMB_UP"
        self.cling_mode_timer = 0.0

    def release_web(self, fade=True):
        """Dissolve silk after a swing — no rope left hanging on the desktop."""
        self.web_active = False
        self.crawl_web_points = []
        if fade and self.web_opacity > 0.02:
            self.web_fade_speed = 2.4
        else:
            self.web_opacity = 0.0
            self.web_hand_x = self.x
            self.web_hand_y = self.y
            self.web_ghosts = []

    def _push_web_ghost(self):
        """Keep a fading afterimage of the last strand (multi-swing readability)."""
        self.web_ghosts.append({
            "x0": float(self.web_hand_x or self.x),
            "y0": float(self.web_hand_y or self.y),
            "x1": float(self.web_anchor_x),
            "y1": float(self.web_anchor_y),
            "a": 0.55,
            "seed": float(self._web_seed),
        })
        if len(self.web_ghosts) > 5:
            self.web_ghosts = self.web_ghosts[-5:]

    def attach_crawl_web(self, ax, ay):
        """Begin / refresh an active swing strand (only while swinging)."""
        self.web_active = True
        self.web_opacity = 1.0
        self.web_fade_speed = 0.0
        self.web_anchor_x = float(ax)
        self.web_anchor_y = float(ay)
        self.web_hand_x = self.x
        self.web_hand_y = self.y - 18.0 * self.render_scale
        self.web_length = max(36.0, math.hypot(self.x - ax, self.y - ay))
        self.web_duration = 0.0
        self._web_seed = random.random() * 1000.0

    def start_top_web_traverse(self, win):
        """Natural crawl along the top rail — zero webs."""
        if not win:
            return
        self.cling_target_window = win
        self.cling_target_address = win.get("address")
        self.cling_side = "TOP"
        self.cling_mode = "TOP_CRAWL"
        self.cling_mode_timer = 0.0

    def start_short_web_hop(self, win):
        """One short Spidey hop along the top from the CURRENT spot — no teleport."""
        if not win:
            return
        self.cling_target_window = win
        self.cling_target_address = win.get("address")
        self.cling_side = "TOP"
        self.web_swings_left = 1
        self.web_swing_index = 0
        self.web_ghosts = []
        travel = -1.0 if self.cling_orbit > 0 else 1.0  # match TOP crawl direction
        edge = self.window_border_edge(win, "TOP")
        # Stay where we are — just drop a little to swing
        self.x = max(win["x1"] + 48.0, min(win["x2"] - 48.0, self.x))
        # Anchor ahead in travel direction
        ahead = random.uniform(70.0, 110.0)
        ax = self.x + travel * ahead
        ax = max(win["x1"] + 36.0, min(win["x2"] - 36.0, ax))
        ay = edge
        rope = random.uniform(55.0, 78.0)
        self.y = ay + rope * 0.85
        self.y = min(self.y, win["y_bot"] - 48.0)
        self.y = max(self.y, ay + 42.0)

        self.web_active = True
        self.web_opacity = 1.0
        self.web_fade_speed = 0.0
        self.web_anchor_x = ax
        self.web_anchor_y = ay
        self.web_length = math.hypot(self.x - ax, self.y - ay)
        self.web_stiffness = 0.0
        self.web_tension = 0.25
        self.web_duration = 0.0
        self.web_phase = random.uniform(0.0, math.pi)
        self._web_seed = random.random() * 1000.0
        self.vx = travel * random.uniform(50.0, 75.0)
        self.vy = random.uniform(-8.0, 18.0)
        self.state = "SWINGING"
        self.state_timer = 0.0
        self.facing = travel
        self.facing_scale = travel
        self.web_hand_x = self.x
        self.web_hand_y = self.y - 10.0 * self.render_scale
        self.emit(2, ax, ay, "web")

    def _begin_next_web_swing(self, win):
        """Chain another short hop from current position (same direction)."""
        self.start_short_web_hop(win)

    def draw_realistic_web(self, cr, x0, y0, x1, y1, alpha=1.0):
        """Photorealistic Spider-Man Web Silk:
        1. Catenary sag physics with aerodynamic flutter & damped harmonic string vibration.
        2. Volumetric Mie-scattering glow halo.
        3. Double-helical braided micro-fibrils (authentic spun-silk rope texture).
        4. High-tensile translucent silk core.
        5. Sharp crystalline specular hairline highlight.
        6. Micro-viscid pearlescent glue droplets & glints with dynamic shimmer.
        7. Piriform silk attachment plaque (branching anchor web disc).
        8. Spinneret wrist emitter flare.
        """
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 4.0 or alpha < 0.02:
            return

        # Unit vectors: along line (ux, uy) and normal (nx, ny)
        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux

        tension = float(getattr(self, "web_tension", 0.35))
        tension = max(0.08, min(2.0, tension))

        # True catenary sag in gravity direction (+Y), cushioned by tension
        sag_amp = min(18.0, dist * 0.082) * max(0.12, 1.0 - tension * 0.65)
        # Aerodynamic flutter transverse to line
        flutter = math.sin(self.anim_tick * 3.5 + float(getattr(self, "web_phase", 0.0))) * (1.1 * max(0.15, 1.0 - tension * 0.55))
        # High-frequency damped harmonic guitar-string vibration
        web_dur = float(getattr(self, "web_duration", 0.0))
        damped_amp = 1.6 * min(1.0, tension) * math.exp(-min(3.5, web_dur * 1.8))
        vibration = math.sin(self.anim_tick * 28.0 + float(getattr(self, "_web_seed", 1.0))) * damped_amp

        seed = float(getattr(self, "_web_seed", 1.0))
        segs = max(26, int(dist / 3.8))

        def bezier(t):
            # Quadratic Bézier with gravity sag + transverse flutter/vibration
            pulse = 4.0 * t * (1.0 - t)
            mid_x = (x0 + x1) * 0.5 + nx * (flutter + vibration) * pulse
            mid_y = (y0 + y1) * 0.5 + sag_amp * pulse + ny * (flutter + vibration) * pulse
            omt = 1.0 - t
            return (
                omt * omt * x0 + 2.0 * omt * t * mid_x + t * t * x1,
                omt * omt * y0 + 2.0 * omt * t * mid_y + t * t * y1,
            )

        pts = [bezier(i / segs) for i in range(segs + 1)]

        cr.save()
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_operator(cairo.OPERATOR_OVER)

        # -------------------------------------------------------------
        # Layer 1: Volumetric Mie-Scattering Glow Halo
        # -------------------------------------------------------------
        cr.set_line_width(3.6)
        cr.set_source_rgba(0.90, 0.95, 1.0, 0.10 * alpha)
        cr.move_to(pts[0][0], pts[0][1])
        for p in pts[1:]:
            cr.line_to(p[0], p[1])
        cr.stroke()

        # -------------------------------------------------------------
        # Layer 2: Primary Translucent Silk Cable Body (Tapered)
        # -------------------------------------------------------------
        for i in range(segs):
            tmid = (i + 0.5) / segs
            # Silk tapers slightly from wrist dispenser (1.55px) to anchor tip (1.05px)
            taper_w = max(0.95, 1.55 - 0.50 * tmid)
            cr.set_line_width(taper_w)
            cr.set_source_rgba(0.86, 0.92, 1.0, (0.50 + 0.15 * (1.0 - tmid)) * alpha)
            cr.move_to(pts[i][0], pts[i][1])
            cr.line_to(pts[i + 1][0], pts[i + 1][1])
            cr.stroke()

        # -------------------------------------------------------------
        # Layer 3: Braided Twin-Helix Micro-Fibrils (Spun-Silk Rope Texture)
        # -------------------------------------------------------------
        helix_cycles = max(3.0, dist / 14.0)
        cr.set_line_width(0.42)
        cr.set_source_rgba(0.93, 0.97, 1.0, 0.65 * alpha)
        # Helix A
        cr.move_to(pts[0][0], pts[0][1])
        for i in range(1, segs + 1):
            t = i / segs
            off = math.sin(t * math.pi * 2.0 * helix_cycles + seed) * 0.72
            cr.line_to(pts[i][0] + nx * off, pts[i][1] + ny * off)
        cr.stroke()
        # Helix B (Opposite Phase)
        cr.move_to(pts[0][0], pts[0][1])
        for i in range(1, segs + 1):
            t = i / segs
            off = -math.sin(t * math.pi * 2.0 * helix_cycles + seed) * 0.72
            cr.line_to(pts[i][0] + nx * off, pts[i][1] + ny * off)
        cr.stroke()

        # -------------------------------------------------------------
        # Layer 4: Crystalline High-Tensile Specular Core Hairline
        # -------------------------------------------------------------
        cr.set_line_width(0.46)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.94 * alpha)
        # Offset slightly toward upper sunlit ambient angle (-0.20 Y, +0.15 normal)
        cr.move_to(pts[0][0] + nx * 0.22, pts[0][1] + ny * 0.22 - 0.20)
        for p in pts[1:]:
            cr.line_to(p[0] + nx * 0.22, p[1] + ny * 0.22 - 0.20)
        cr.stroke()

        # -------------------------------------------------------------
        # Layer 5: Viscid Pearlescent Micro-Droplets & Glints
        # -------------------------------------------------------------
        num_droplets = max(3, int(dist / 20.0))
        for d in range(1, num_droplets):
            td = d / float(num_droplets)
            bx, by = bezier(td)
            shimmer = 0.55 + 0.45 * math.sin(self.anim_tick * 4.6 + d * 1.618 + seed)
            r = 1.15 + 0.45 * math.sin(d * 2.7 + seed)
            # Soft droplet glow
            cr.set_source_rgba(0.92, 0.96, 1.0, 0.45 * shimmer * alpha)
            cr.arc(bx, by, r + 0.8, 0, 2 * math.pi)
            cr.fill()
            # Specular point highlight
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.92 * shimmer * alpha)
            cr.arc(bx - 0.2, by - 0.2, r * 0.65, 0, 2 * math.pi)
            cr.fill()

        # -------------------------------------------------------------
        # Layer 6: Piriform Silk Attachment Disc (Branching Web Plaque at Anchor)
        # -------------------------------------------------------------
        base_ang = math.atan2(-dy, -dx)
        cr.set_source_rgba(0.94, 0.97, 1.0, 0.62 * alpha)
        # Fan of 9 branching anchor threads gripping the window frame
        fan_spread = (-1.15, -0.85, -0.55, -0.28, 0.0, 0.28, 0.55, 0.85, 1.15)
        for idx, delta in enumerate(fan_spread):
            ang = base_ang + delta
            blen = 4.0 + 4.5 * math.cos(delta * 1.2) + (idx % 3) * 1.2
            tip_x = x1 + math.cos(ang) * blen
            tip_y = y1 + math.sin(ang) * blen
            cr.set_line_width(0.48)
            cr.move_to(x1, y1)
            cr.line_to(tip_x, tip_y)
            cr.stroke()
            # Micro adhesion pad at thread termination
            cr.arc(tip_x, tip_y, 0.75, 0, 2 * math.pi)
            cr.fill()

        # -------------------------------------------------------------
        # Layer 7: Spinneret Wrist Emitter Flare (Nozzle Cone at x0, y0)
        # -------------------------------------------------------------
        if len(pts) > 4:
            p_merge = pts[min(4, len(pts) - 1)]
            for off in (-2.4, 0.0, 2.4):
                cr.set_line_width(0.42)
                cr.set_source_rgba(0.96, 0.98, 1.0, 0.70 * alpha)
                cr.move_to(x0 + nx * off, y0 + ny * off)
                cr.line_to(p_merge[0], p_merge[1])
                cr.stroke()

        cr.restore()

    def handle_landing(self, dt):
        if self.vy > 950:
            self.state = "KNOCKOUT"
            self.state_timer = 0.0
            self.vy = 0.0
            self.vx = 0.0
            self.trigger_squash(0.45)
            self.emit(3, self.x, self.y + 10, CHARACTERS[self.current_char]["particle"])
        elif self.vy > 300:
            self.vy = -self.vy * self.restitution
            self.vx *= 0.4
            self.trigger_squash(min(0.4, abs(self.vy) * 0.0007))
            self.emit(2, self.x, self.y + 10, CHARACTERS[self.current_char]["particle"])
        else:
            self.vy = 0.0
            self.vx *= math.pow(self.ground_friction, dt * 60)

    def trigger_squash(self, amount):
        self.scale_y = max(0.55, 1.0 - amount)
        self.scale_vy = -18.0 * amount

    # ------------------------------------------------------------------
    # Ground AI
    # ------------------------------------------------------------------
    def update_ground_ai(self, dt):
        think_lo, think_hi = self.profile()["idle_think"]
        sit_lo, sit_hi = self.profile()["sit_time"]
        if self.state == "IDLE":
            if self.state_timer > random.uniform(think_lo, think_hi):
                self.state_timer = 0.0
                curr_plat = self.get_current_platform()
                # Mostly sit/rest; rare motion keeps presence without stealing focus
                if curr_plat and curr_plat.get("address") != "floor" and random.random() < (0.10 if self.presence_mode != "lively" else 0.28):
                    self.start_window_top_hang(curr_plat)
                    return

                if self.profile().get("auto_taunt") and (time.time() - self._last_taunt_at) >= self.profile().get("taunt_cooldown", 48.0):
                    if random.random() < 0.20:
                        self.trigger_taunt()
                        return

                roll = random.random()
                if self.presence_mode == "focus":
                    if roll < 0.55:
                        self.state = "SITTING"
                    elif roll < 0.80:
                        self.start_walking()
                    elif roll < 0.92:
                        self.trigger_wave()
                    else:
                        self.trigger_dance()
                elif self.presence_mode == "calm":
                    if roll < 0.48:
                        self.state = "SITTING"
                    elif roll < 0.72:
                        self.start_walking()
                    elif roll < 0.86:
                        self.trigger_wave()
                    elif roll < 0.95:
                        self.trigger_dance()
                    else:
                        self.trigger_taunt()
                else:
                    if roll < 0.35:
                        self.start_walking()
                    elif roll < 0.55:
                        self.state = "SITTING"
                    elif roll < 0.72:
                        self.trigger_dance()
                    elif roll < 0.88:
                        self.trigger_wave()
                    else:
                        self.trigger_taunt()

        elif self.state == "WALKING":
            dx = self.target_x - self.x
            if abs(dx) < 8.0 or self.state_timer > random.uniform(3.5, 5.5):
                self.state = "IDLE"
                self.state_timer = 0.0
                self.vx = 0.0
            else:
                walk_speed = 72.0 if self.presence_mode != "lively" else 95.0
                self.vx = self.facing * walk_speed

        elif self.state == "SITTING":
            if self.state_timer > random.uniform(sit_lo, sit_hi):
                self.state = "IDLE"
                self.state_timer = 0.0

        elif self.state == "DANCE":
            if random.random() < 0.04 * self.profile()["particle_mul"]:
                self.emit(1, self.x, self.y - 15, CHARACTERS[self.current_char]["particle"])
            if self.state_timer > random.uniform(3.0, 4.5):
                self.state = "IDLE"
                self.state_timer = 0.0

        elif self.state == "WAVE_HANDS":
            if random.random() < 0.03 * self.profile()["particle_mul"]:
                self.emit(1, self.x, self.y - 25, "sparkle")
            if self.state_timer > random.uniform(2.5, 4.0):
                self.state = "IDLE"
                self.state_timer = 0.0

    def start_walking(self):
        plat = self.get_current_platform()
        if plat:
            self.state = "WALKING"
            self.state_timer = 0.0
            min_x = plat["x1"] + 25.0
            max_x = plat["x2"] - 25.0
            if max_x > min_x:
                self.target_x = random.uniform(min_x, max_x)
            else:
                self.target_x = self.x
            self.facing = 1.0 if self.target_x >= self.x else -1.0
        else:
            # Strictly no bottom floor roaming! Cling to screen border!
            side = "LEFT" if self.x < self.screen_width * 0.5 else "RIGHT"
            self.cling_to_screen_border(side, mode="WALL_REST")

    def trigger_dance(self):
        self.state = "DANCE"
        self.state_timer = 0.0
        self.vx = 0.0
        self.note_interaction(0.7)
        self.trigger_squash(0.15)
        self.emit(2, self.x, self.y - 15, CHARACTERS[self.current_char]["particle"])

    def trigger_wave(self):
        self.state = "WAVE_HANDS"
        self.state_timer = 0.0
        self.vx = 0.0
        self.note_interaction(0.55)
        self.trigger_squash(0.12)
        self.emit(1, self.x, self.y - 30, "sparkle")

    # ------------------------------------------------------------------
    # Actions & Interactions
    # ------------------------------------------------------------------
    def switch_character(self, cid):
        if cid in CHARACTERS and cid != self.current_char:
            self.current_char = cid
            self.base_render_scale = self.user_scale if self.user_scale else CHARACTERS[cid]["default_scale"]
            self.render_scale = self.canonical_scale()
            self.save_config()
            self.note_interaction(0.9)
            self.trigger_squash(0.2)
            if self.presence_mode == "lively":
                self.trigger_taunt()

    def trigger_special(self):
        self.state = "SPECIAL"
        self.state_timer = 0.0
        self.vx = 0.0
        self.note_interaction(0.8)
        self.emit(2, self.x, self.y - 10, CHARACTERS[self.current_char]["particle"])

    def speak(self, msg):
        # Shorter captions for calm modes — truncate long taunts
        if self.presence_mode != "lively" and len(msg) > 42:
            msg = msg[:39].rstrip() + "…"
        self.emit(1, self.x, self.y - 48, "bubble", msg)

    def trigger_taunt(self):
        now = time.time()
        cd = float(self.profile().get("taunt_cooldown", 20.0))
        if now - self._last_taunt_at < cd * 0.35 and self.presence_mode != "lively":
            return  # soft debounce — avoid spam stacks
        if now - self._last_taunt_at < 2.5:
            return
        self._last_taunt_at = now
        cdata = CHARACTERS[self.current_char]
        msg = random.choice(cdata["taunts"])
        self.note_interaction(0.55)
        self.speak(msg)
        if self.presence_mode == "lively":
            self.emit(1, self.x, self.y, cdata["particle"])

    def dismiss_pet(self, duration=45.0, reason="shoo"):
        if self.state == "AWAY":
            return
        # Soft accidental exits never dismiss — only force fling or explicit shoo
        if reason in ("off_screen", "fling") and not self._force_fling:
            return
        if reason == "shoo":
            self._force_fling = True
        cdata = CHARACTERS[self.current_char]
        farewells = {
            "hutao": ["Aiya~ See ya later! 👻", "Taking a ghost break~ 🌸", "Wheeee! Back soon! ✨", "Hu Tao zooming out! 💫"],
            "klee": ["Klee will go find fish! 💣", "Yay, adventure time! ✨", "Klee will be right back! 💥"],
            "ayaka": ["I shall take my leave for now. ❄️", "Farewell for a short while. 🌸", "Rest well, traveler. ❄️"],
            "venti": ["Off with the gentle breeze! 🍃", "Hehe, time for dandelion wine! 🍷", "May the wind protect you! 🍃"],
            "spiderman": ["Spider-Man away! 🕸️", "Friendly neighborhood break! 🕷️", "Catch you on the flip side! 🕸️"],
        }
        char_farewells = farewells.get(self.current_char, ["See you soon! ✨", "Taking a quick break! 💫"])
        msg = random.choice(char_farewells)
        self.speak(msg)
        self.emit(3, self.x, self.y, cdata.get("particle", "sparkle"))

        self.state = "AWAY"
        self.away_timer = 0.0
        self.away_duration = float(duration)
        self.is_dragging = False
        self.web_active = False
        self.particles.clear()
        self.update_input_shape()
        self.queue_draw()
        print(f"[HyprPet] Pet thrown/shooed away for {self.away_duration:.1f}s. Input shape cleared.", flush=True)

    def return_from_away(self):
        self.state_timer = 0.0
        self.away_timer = 0.0
        self._force_fling = False
        self.refresh_platforms(force=True)
        cdata = CHARACTERS[self.current_char]
        greetings = {
            "hutao": ["Tadaa! Hu Tao is back! 👻", "Did someone summon the 77th Director? ✨", "Back to haunt you! 🌸"],
            "klee": ["Klee is back! 🍀", "Did you miss Klee? 💥", "Look what Klee brought! ✨"],
            "ayaka": ["I have returned. ❄️", "Ready whenever you need. 🌸", "At your service once more. ❄️"],
            "venti": ["Yahoo! The bard has returned! 🍃", "What sweet tunes did I miss? 🎶", "The wind brings me back! 🍃"],
            "spiderman": ["Your friendly neighborhood pet is back! 🕸️", "Did somebody call Spider-Man? 🕷️", "Back on patrol! 🕸️"],
        }
        char_greetings = greetings.get(self.current_char, ["I'm back! ✨", "Missed me? 💫"])
        msg = random.choice(char_greetings)

        # Habitat on return: prefer quiet screen-edge rest in calm/focus
        target_win = self.active_window or (self.platforms[0] if self.platforms else None)
        if self.presence_mode == "focus":
            options = ["SCREEN_LEFT", "SCREEN_RIGHT"]
        elif self.presence_mode == "calm":
            options = ["SCREEN_LEFT", "SCREEN_RIGHT", "SCREEN_TOP"]
            if target_win and random.random() < 0.25:
                options.append("WIN_PERCH")
        else:
            options = ["SCREEN_LEFT", "SCREEN_RIGHT", "SCREEN_TOP"]
            if target_win:
                options.extend(["WIN_PERCH", "WIN_HANG"])

        choice = random.choice(options)
        rest_mode = "WALL_REST" if self.presence_mode != "lively" else "CLIMB_UP"
        if choice == "SCREEN_LEFT":
            self.cling_to_screen_border("LEFT", mode=rest_mode)
            self.y = random.uniform(120.0, max(140.0, self.screen_height - 240.0))
        elif choice == "SCREEN_RIGHT":
            self.cling_to_screen_border("RIGHT", mode=rest_mode)
            self.y = random.uniform(120.0, max(140.0, self.screen_height - 240.0))
        elif choice == "SCREEN_TOP":
            self.hang_on_screen_top()
        elif choice == "WIN_PERCH":
            self.perch_on_active_window()
        elif choice == "WIN_HANG":
            self.hang_upside_down_on_active_window()

        self.note_interaction(0.75)
        if self.presence_mode == "lively":
            self.speak(msg)
        self.emit(2, self.x, self.y, cdata.get("particle", "sparkle"))
        self.trigger_squash(-0.18)
        self.update_input_shape()
        self.queue_draw()
        print(f"[HyprPet] Pet returned from away to {choice} at ({self.x:.1f}, {self.y:.1f})", flush=True)

    def cling_to_screen_border(self, side="LEFT", mode="CLIMB_UP"):
        bx = 0.0 if side == "LEFT" else float(self.screen_width)
        border = {
            "type": f"SCREEN_{side}",
            "x": bx,
            "y1": 60.0,
            "y2": float(self.screen_height) - self.bottom_pad(),
            "side": side,
            "win": None,
        }
        self.start_clinging(border)
        self.cling_mode = mode

    def hang_on_screen_top(self):
        screen_win = {
            "x1": 40.0,
            "x2": float(self.screen_width - 40.0),
            "y_top": 0.0,
            "y_bot": float(self.screen_height),
            "address": "screen",
        }
        self.start_window_top_hang(screen_win)

    def cling_to_active_window(self, side="RIGHT", mode="CLIMB_UP"):
        self.refresh_platforms(force=True)
        target_win = self.active_window
        if not target_win and self.platforms:
            # Prefer the widest / focused-looking platform on this screen
            target_win = max(self.platforms, key=lambda p: (p["x2"] - p["x1"]) * (p["y_bot"] - p["y_top"]))

        if target_win:
            wall = self.window_border_edge(target_win, side)
            border = {
                "type": f"WIN_{side}",
                "x": wall,
                "y1": target_win["y_top"],
                "y2": target_win["y_bot"],
                "side": side,
                "win": target_win,
            }
            self.start_clinging(border)
            self.cling_mode = mode
            # Snap immediately — hands on the window border from the outside
            self.fit_cling_scale_to_gap(side, wall, False)
            self.x = self.compute_outward_cling_x(wall, side, False, glass_x=wall)
            self.draw_alpha = 1.0
            print(
                f"[HyprPet] cling {side} border={wall:.1f} -> x={self.x:.1f} "
                f"scale={self.render_scale:.3f} screen={self.screen_width:.0f}",
                flush=True,
            )
        else:
            # Screen border fallback
            bx = float(self.screen_width) if side == "RIGHT" else 0.0
            border = {
                "type": f"SCREEN_{side}",
                "x": bx,
                "y1": 0.0,
                "y2": float(self.screen_height),
                "side": side,
            }
            self.start_clinging(border)
            self.cling_mode = mode
            print(f"[HyprPet] cling fallback SCREEN_{side}", flush=True)

    def hang_upside_down_on_active_window(self):
        self.refresh_platforms(force=True)
        target_win = self.active_window or (self.platforms[0] if self.platforms else None)
        if target_win:
            self.start_window_top_hang(target_win)
        else:
            self.hang_on_screen_top()

    def perch_on_active_window(self):
        self.refresh_platforms(force=True)
        target_win = self.active_window or (self.platforms[0] if self.platforms else None)
        if target_win:
            self.cling_target_window = target_win
            self.cling_target_address = target_win.get("address")
            edge = self.window_border_edge(target_win, "TOP")
            if edge < 28.0:
                # Flush to screen top — prefer outer side so pet stays outside content
                side = "LEFT" if self.x < (target_win["x1"] + target_win["x2"]) * 0.5 else "RIGHT"
                self.cling_to_active_window(side, mode="WALL_REST")
            else:
                self.x = (target_win["x1"] + target_win["x2"]) * 0.5
                self.y = self.compute_stand_y(edge)
                self.state = "SITTING"
                self.state_timer = 0.0
                self.vx = 0.0
                self.vy = 0.0
                self.draw_alpha = 1.0
                self.trigger_squash(0.2)
                print(f"[HyprPet] perch top={edge:.1f} -> y={self.y:.1f}", flush=True)
        else:
            self.cling_to_screen_border("RIGHT", mode="WALL_REST")

    def try_snap_to_border(self):
        hand_offset = CHARACTERS[self.current_char]["hand_offset"] * self.render_scale
        feet_offset = CHARACTERS[self.current_char].get("feet_offset", 64.0) * self.render_scale

        # Snap to vertical border first (so outer side borders take natural priority!)
        for b in self.vertical_borders:
            if abs(self.x - b["x"]) < (hand_offset + 36.0) and (b["y1"] - 30 <= self.y <= b["y2"] + 30):
                self.start_clinging(b)
                return True

        # Snap to window top ledge
        for p in self.platforms:
            edge = self.window_border_edge(p, "TOP")
            stand = self.compute_stand_y(edge)
            if p["x1"] - 20 <= self.x <= p["x2"] + 20 and abs(self.y - edge) < 48.0:
                if self.y > edge + 8.0:
                    self.start_window_top_hang(p)
                    return True
                self.cling_target_window = p
                self.cling_target_address = p.get("address")
                self.x = max(p["x1"] + 20, min(p["x2"] - 20, self.x))
                self.y = stand
                self.state = "SITTING"
                self.state_timer = 0.0
                self.vx = 0.0
                self.vy = 0.0
                return True

        # Snap to window bottom inner sill
        for p in self.platforms:
            if p.get("address") in ("floor", "screen"):
                continue
            edge_bot = float(p["y_bot"])
            stand_bot = self.compute_bottom_cling_y(edge_bot, is_sitting=True)
            if p["x1"] - 20 <= self.x <= p["x2"] + 20 and abs(self.y - stand_bot) < 48.0:
                self.cling_target_window = p
                self.cling_target_address = p.get("address")
                self.cling_side = "BOTTOM"
                self.x = max(p["x1"] + 20, min(p["x2"] - 20, self.x))
                self.y = stand_bot
                self.state = "SITTING"
                self.state_timer = 0.0
                self.vx = 0.0
                self.vy = 0.0
                return True

        # Snap to desktop floor
        floor = self.get_screen_floor()
        stand = self.compute_stand_y(floor["y_top"])
        if abs(self.y - stand) < 48.0 and floor["x1"] <= self.x <= floor["x2"]:
            self.y = stand
            self.cling_target_window = floor
            self.cling_target_address = "floor"
            self.state = "SITTING"
            self.state_timer = 0.0
            self.vx = 0.0
            self.vy = 0.0
            return True

        return False

    # ------------------------------------------------------------------
    # Mouse Handlers
    # ------------------------------------------------------------------
    def on_button_press(self, widget, event):
        if event.button == 1:
            self.is_dragging = True
            self.web_active = False
            self._force_fling = False
            self.note_interaction(1.0)
            self.drag_offset_x = event.x - self.x
            self.drag_offset_y = event.y - self.y
            self.drag_origin_x = event.x
            self.drag_origin_y = event.y
            self.mouse_history.clear()
            self.mouse_history.append((time.time(), event.x, event.y))
            self.trigger_squash(-0.25)
            return True
        elif event.button == 3:
            self.note_interaction(0.8)
            self.show_context_menu(event)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1 and self.is_dragging:
            self.is_dragging = False
            self.mouse_history.append((time.time(), event.x, event.y))

            # Recent-sample velocity (shimeji-style) — smoother than full-drag average
            throw_vx, throw_vy = 0.0, 0.0
            if len(self.mouse_history) >= 2:
                samples = list(self.mouse_history)
                t1, x1, y1 = samples[-1]
                # Prefer last ~80ms of motion for fling impulse
                t0, x0, y0 = samples[0]
                for s in reversed(samples[:-1]):
                    if t1 - s[0] >= 0.08:
                        t0, x0, y0 = s
                        break
                    t0, x0, y0 = s
                dt = max(0.012, t1 - t0)
                throw_vx = (x1 - x0) / dt
                throw_vy = (y1 - y0) / dt

            throw_speed = math.hypot(throw_vx, throw_vy)
            travel = math.hypot(event.x - self.drag_origin_x, event.y - self.drag_origin_y)
            off = (
                event.x < -20.0
                or event.x > self.screen_width + 20.0
                or event.y < -20.0
                or event.y > self.screen_height + 20.0
            )
            if self.try_snap_to_border():
                return True

            # Smooth throw into fall physics (never disappears / dismisses)
            self.vx = max(-1800.0, min(1800.0, throw_vx * 1.15))
            self.vy = max(-1800.0, min(1800.0, throw_vy * 1.15))
            self.state = "FALLING"
            self.state_timer = 0.0
            if abs(self.vx) > 30.0:
                self.facing = 1.0 if self.vx > 0 else -1.0
                self.facing_scale = self.facing
            return True
        return False

    def on_motion_notify(self, widget, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.mouse_history.append((time.time(), event.x, event.y))
        return True

    # ------------------------------------------------------------------
    # Context Menu
    # ------------------------------------------------------------------
    def show_context_menu(self, event):
        menu = Gtk.Menu()

        # Character Switcher Submenu
        char_item = Gtk.MenuItem(label="🎭 Choose Character")
        char_menu = Gtk.Menu()
        for cid, cinfo in CHARACTERS.items():
            icon = "👻" if cid == "hutao" else ("💣" if cid == "klee" else ("🌸" if cid == "ayaka" else ("🍃" if cid == "venti" else "🕷️")))
            active_mark = " ✓" if cid == self.current_char else ""
            item = Gtk.MenuItem(label=f"{icon} {cinfo['name']} ({cinfo['series']}){active_mark}")
            item.connect("activate", lambda w, c=cid: self.switch_character(c))
            char_menu.append(item)
        char_item.set_submenu(char_menu)
        menu.append(char_item)

        # Presence / distraction profile
        presence_item = Gtk.MenuItem(label="✨ Presence Style")
        presence_menu = Gtk.Menu()
        for mode, info in PRESENCE_PROFILES.items():
            mark = " ✓" if mode == self.presence_mode else ""
            item = Gtk.MenuItem(label=f"{info['label']}{mark}")
            item.connect("activate", lambda w, m=mode: self.set_presence(m))
            presence_menu.append(item)
        presence_item.set_submenu(presence_menu)
        menu.append(presence_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Shoo / Break Submenu
        break_item = Gtk.MenuItem(label="💨 Shoo / Take a Break")
        break_menu = Gtk.Menu()
        b_30s = Gtk.MenuItem(label="⏱️ Away for 30 seconds")
        b_30s.connect("activate", lambda w: self.dismiss_pet(30.0, "menu"))
        break_menu.append(b_30s)
        b_1m = Gtk.MenuItem(label="⏱️ Away for 1 minute")
        b_1m.connect("activate", lambda w: self.dismiss_pet(60.0, "menu"))
        break_menu.append(b_1m)
        b_3m = Gtk.MenuItem(label="⏱️ Away for 3 minutes")
        b_3m.connect("activate", lambda w: self.dismiss_pet(180.0, "menu"))
        break_menu.append(b_3m)
        b_5m = Gtk.MenuItem(label="⏱️ Away for 5 minutes")
        b_5m.connect("activate", lambda w: self.dismiss_pet(300.0, "menu"))
        break_menu.append(b_5m)
        break_item.set_submenu(break_menu)
        menu.append(break_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Screen Borders Submenu (Strictly Left, Right, Top)
        screen_item = Gtk.MenuItem(label="🖥️ Screen Border Modes")
        screen_menu = Gtk.Menu()
        s_left = Gtk.MenuItem(label="🧗 Climb Left Screen Border")
        s_left.connect("activate", lambda w: self.cling_to_screen_border("LEFT", "CLIMB_UP"))
        screen_menu.append(s_left)
        s_right = Gtk.MenuItem(label="🧗 Climb Right Screen Border")
        s_right.connect("activate", lambda w: self.cling_to_screen_border("RIGHT", "CLIMB_UP"))
        screen_menu.append(s_right)
        s_top = Gtk.MenuItem(label="🤸 Hang from Top Screen Bezel")
        s_top.connect("activate", lambda w: self.hang_on_screen_top())
        screen_menu.append(s_top)
        screen_item.set_submenu(screen_menu)
        menu.append(screen_item)

        # Active Window Dynamics Submenu
        win_item = Gtk.MenuItem(label="🪟 Active Window Dynamics")
        win_menu = Gtk.Menu()
        w_left = Gtk.MenuItem(label="🧗 Climb Left Window Border")
        w_left.connect("activate", lambda w: self.cling_to_active_window("LEFT", "CLIMB_UP"))
        win_menu.append(w_left)
        w_right = Gtk.MenuItem(label="🧗 Climb Right Window Border")
        w_right.connect("activate", lambda w: self.cling_to_active_window("RIGHT", "CLIMB_UP"))
        win_menu.append(w_right)
        w_hang = Gtk.MenuItem(label="🤸 Hang Upside Down (Top of Window)")
        w_hang.connect("activate", lambda w: self.hang_upside_down_on_active_window())
        win_menu.append(w_hang)
        w_perch = Gtk.MenuItem(label="🪟 Perch on Top Titlebar")
        w_perch.connect("activate", lambda w: self.perch_on_active_window())
        win_menu.append(w_perch)
        win_item.set_submenu(win_menu)
        menu.append(win_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Actions: Sit, Dance, Wave Hands
        sit_item = Gtk.MenuItem(label="🪑 Sit & Rest")
        sit_item.connect("activate", lambda w: setattr(self, "state", "SITTING"))
        menu.append(sit_item)

        dance_item = Gtk.MenuItem(label="💃 Dance & Groove")
        dance_item.connect("activate", lambda w: self.trigger_dance())
        menu.append(dance_item)

        wave_item = Gtk.MenuItem(label="👋 Wave Hands")
        wave_item.connect("activate", lambda w: self.trigger_wave())
        menu.append(wave_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Voice / Taunt
        taunt_item = Gtk.MenuItem(label="💬 Character Dialogue / Taunt")
        taunt_item.connect("activate", lambda w: self.trigger_taunt())
        menu.append(taunt_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Size Submenu
        size_item = Gtk.MenuItem(label="📏 Size")
        size_menu = Gtk.Menu()
        for s_lbl, s_sc in [("Compact (60px)", 0.50), ("Standard (87px)", 0.68), ("Heroic (110px)", 0.85)]:
            item = Gtk.MenuItem(label=s_lbl)
            item.connect("activate", lambda w, sc=s_sc: self.set_scale(sc))
            size_menu.append(item)
        size_item.set_submenu(size_menu)
        menu.append(size_item)

        menu.append(Gtk.SeparatorMenuItem())

        # Dismiss
        quit_item = Gtk.MenuItem(label="❌ Dismiss Companion")
        quit_item.connect("activate", lambda w: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        menu.popup_at_pointer(event)

    def set_scale(self, sc):
        self.user_scale = sc
        self.base_render_scale = sc
        self.render_scale = self.canonical_scale()
        self.note_interaction(0.5)
        self.save_config()
        self.trigger_squash(0.15)

    # ------------------------------------------------------------------
    # Frame Selection & Rendering
    # ------------------------------------------------------------------
    def get_current_frame_key(self):
        cformat = CHARACTERS[self.current_char]["format"]

        if cformat == "genshin":
            if self.state == "WINDOW_TOP_HANG":
                if getattr(self, "top_mode", "LEDGE") == "UNDER":
                    # Climbing grip on top rail with arms raised overhead
                    climb_frames = ["climb1", "climb2", "climb3", "climb2"]
                    return climb_frames[int(self.anim_tick * 3.0) % len(climb_frames)]
                # Sitting on window titlebar ledge with legs dangling in front
                sit_frames = ["sp1_1", "sp1_2", "sp1_3", "sp1_4"]
                return sit_frames[int(self.anim_tick * 1.8) % len(sit_frames)]
            elif self.state == "SWINGING":
                # Airborne flight / swing posture
                swing_frames = ["sp2_1", "sp2_2", "sp2_3"] if self.current_char == "hutao" else ["fall1", "fall2", "fall1"]
                return swing_frames[int(self.anim_tick * 4.0) % len(swing_frames)]
            elif self.state == "CORNER_ARC":
                phase = getattr(self, "corner_phase", "pull")
                if phase in ("plant", "reach"):
                    return "climb2" if int(self.anim_tick * 6.0) % 2 == 0 else "climb1"
                elif phase == "pull":
                    return "climb3"
                else:  # settle
                    return "climb1"
            elif self.state == "CLINGING":
                if self.cling_side == "TOP":
                    if getattr(self, "top_mode", "LEDGE") == "UNDER":
                        climb_frames = ["climb1", "climb2", "climb3"]
                        return climb_frames[int(self.anim_tick * 6.0) % len(climb_frames)]
                    # When stopped/resting on the top rail, sit down and dangle legs!
                    if abs(getattr(self, "move_speed", 0.0)) <= 3.0:
                        sit_frames = ["sp1_1", "sp1_2", "sp1_3", "sp1_4"]
                        return sit_frames[int(self.anim_tick * 1.8) % len(sit_frames)]
                    walk_frames = ["walk1", "walk2", "walk3", "walk2"]
                    return walk_frames[int(self.anim_tick * 6.5) % len(walk_frames)]
                if self.cling_side == "BOTTOM":
                    walk_frames = ["walk1", "walk2", "walk3", "walk2"]
                    return walk_frames[int(self.anim_tick * 6.5) % len(walk_frames)]
                climb_frames = ["climb1", "climb2", "climb3"]
                if self.cling_mode in ["CLIMB_UP", "WALL_SLIDE", "ORBIT"]:
                    return climb_frames[int(self.anim_tick * 6.5) % len(climb_frames)]
                else:  # WALL_REST
                    return "climb1"
            elif self.state == "DRAGGING":
                drag_frames = ["drag1", "drag2", "drag3", "drag4", "drag5", "drag6"]
                return drag_frames[int(self.anim_tick * 8.0) % len(drag_frames)]
            elif self.state == "WALKING":
                walk_frames = ["walk1", "walk2", "walk3", "walk2"]
                return walk_frames[int(self.anim_tick * 6.5) % len(walk_frames)]
            elif self.state == "SITTING":
                sit_frames = ["sp1_1", "sp1_2", "sp1_3", "sp1_4"]
                return sit_frames[int(self.anim_tick * 2.0) % len(sit_frames)]
            elif self.state == "DANCE":
                if self.current_char == "hutao":
                    dance_frames = ["sp2_1", "sp2_2", "sp2_3"]
                elif self.current_char == "klee":
                    dance_frames = [f"sp3_{i}" for i in range(1, 6)]
                elif self.current_char == "ayaka":
                    dance_frames = [f"sp2_{i}" for i in range(1, 6)]
                else:  # venti
                    dance_frames = [f"sp3_{i}" for i in range(1, 6)]
                return dance_frames[int(self.anim_tick * 5.5) % len(dance_frames)]
            elif self.state == "WAVE_HANDS":
                if self.current_char == "hutao":
                    wave_frames = ["sp1_5", "sp1_6", "sp1_7", "sp1_8"]
                elif self.current_char == "klee":
                    wave_frames = ["sp2_1", "sp2_2", "sp2_3"]
                elif self.current_char == "ayaka":
                    wave_frames = ["sp2_1", "sp2_2", "sp2_3"]
                else:  # venti
                    wave_frames = ["sp2_1", "sp2_2", "sp2_3"]
                return wave_frames[int(self.anim_tick * 4.5) % len(wave_frames)]
            elif self.state == "SPECIAL":
                if self.current_char == "hutao":
                    sp_frames = [f"sp1_{i}" for i in range(1, 9)] + ["sp2_1", "sp2_2", "sp2_3"]
                elif self.current_char == "klee":
                    sp_frames = [f"sp3_{i}" for i in range(1, 6)]
                elif self.current_char == "ayaka":
                    sp_frames = [f"sp2_{i}" for i in range(1, 6)]
                else:
                    sp_frames = [f"sp3_{i}" for i in range(1, 6)]
                return sp_frames[int(self.anim_tick * 5.5) % len(sp_frames)]
            elif self.state == "KNOCKOUT":
                return "fall5"
            elif self.state == "FALLING":
                fall_frames = ["fall1", "fall2", "fall3"]
                return fall_frames[int(self.anim_tick * 4.5) % len(fall_frames)]
            else:  # IDLE
                return "id1_1" if int(self.state_timer * 1.2) % 4 != 0 else "id2_1"

        else:
            # Spider-Man
            if self.state == "SWINGING":
                hang_frames = ["shime15", "shime16", "shime17"]
                return hang_frames[int(self.anim_tick * 3.5) % len(hang_frames)]
            elif self.state == "WINDOW_TOP_HANG":
                if getattr(self, "hang_style", "crawl") == "crawl":
                    climb_frames = ["shime12", "shime13", "shime14"]
                    return climb_frames[int(self.anim_tick * 7.0) % len(climb_frames)]
                # Perch / sit on top rail: listen to music or look alert
                if self.state_timer > 3.0 and int(self.state_timer) % 12 >= 6:
                    music_frames = ["shime30", "shime31", "shime32", "shime33"]
                    return music_frames[int(self.anim_tick * 3.5) % len(music_frames)]
                return "shime11"
            elif self.state == "CORNER_ARC":
                phase = getattr(self, "corner_phase", "pull")
                if phase == "plant":
                    return "shime12"
                elif phase == "reach":
                    return "shime13"
                elif phase == "pull":
                    return "shime14"
                else:  # settle
                    return "shime12"
            elif self.state == "CLINGING":
                if self.cling_side == "BOTTOM":
                    walk_frames = ["shime1", "shime2", "shime1", "shime3"]
                    return walk_frames[int(self.anim_tick * 7.0) % len(walk_frames)]
                if self.cling_side == "TOP":
                    # When stopped/resting on the top rail, sit upright and dangle legs!
                    if abs(getattr(self, "move_speed", 0.0)) <= 3.0:
                        if self.cling_mode_timer > 4.0 and int(self.anim_tick) % 10 >= 5:
                            music_frames = ["shime30", "shime31", "shime32", "shime33"]
                            return music_frames[int(self.anim_tick * 3.0) % len(music_frames)]
                        return "shime11"
                    climb_frames = ["shime12", "shime13", "shime14"]
                    return climb_frames[int(self.anim_tick * 7.0) % len(climb_frames)]
                if self.cling_mode in ["CLIMB_UP", "WALL_SLIDE", "ORBIT", "BOTTOM_CRAWL"]:
                    climb_frames = ["shime12", "shime13", "shime14"]
                    return climb_frames[int(self.anim_tick * 6.5) % len(climb_frames)]
                else:  # WALL_REST
                    return "shime12"
            elif self.state == "DRAGGING":
                drag_frames = ["shime22", "shime23", "shime24", "shime25"]
                return drag_frames[int(self.anim_tick * 8.0) % len(drag_frames)]
            elif self.state == "WALKING":
                walk_frames = ["shime1", "shime2", "shime1", "shime3"]
                return walk_frames[int(self.anim_tick * 6.5) % len(walk_frames)]
            elif self.state == "SITTING":
                # Do NOT call get_current_platform() here — it uses stand math that
                # used to re-enter frame selection (RecursionError).
                on_ledge = self.cling_target_address not in (None, "")
                if on_ledge:
                    if int(self.state_timer) % 12 >= 6:
                        music_frames = ["shime30", "shime31", "shime32", "shime33"]
                        return music_frames[int(self.anim_tick * 3.0) % len(music_frames)]
                    return "shime11"
                return "shime5" if int(self.state_timer * 1.5) % 4 != 0 else "shime6"
            elif self.state == "DANCE":
                dance_frames = ["shime30", "shime31", "shime32", "shime33"]
                return dance_frames[int(self.anim_tick * 5.0) % len(dance_frames)]
            elif self.state == "WAVE_HANDS":
                wave_frames = ["shime7", "shime8", "shime7", "shime1"]
                return wave_frames[int(self.anim_tick * 4.0) % len(wave_frames)]
            elif self.state == "SPECIAL":
                dance_frames = ["shime30", "shime31", "shime32", "shime33"]
                return dance_frames[int(self.anim_tick * 5.0) % len(dance_frames)]
            elif self.state == "KNOCKOUT":
                return "shime18"
            elif self.state == "FALLING":
                if self.vy < 80.0:
                    return "shime4"
                return "shime5"
            else:
                return "shime1"

    def on_draw(self, widget, cr):
        # Ultra HD Subpixel Antialiasing for all vector curves, silk lines, and sprites
        cr.set_antialias(cairo.ANTIALIAS_BEST)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Draw Particles & Dialogue Speech Bubbles
        for p in self.particles:
            p.draw(cr)

        if self.state == "AWAY":
            return True

        alpha = max(0.92, min(1.0, self.draw_alpha))

        # Photorealistic silk web lines & ghost afterimages
        for g in list(getattr(self, "web_ghosts", []) or []):
            old_seed = self._web_seed
            self._web_seed = g.get("seed", old_seed)
            self.draw_realistic_web(cr, g["x0"], g["y0"], g["x1"], g["y1"], alpha=alpha * g["a"] * 0.75)
            self._web_seed = old_seed

        if self.web_opacity > 0.02 and (self.web_active or self.state == "SWINGING" or self.web_fade_speed > 0):
            hx = getattr(self, "web_hand_x", self.x) or self.x
            hy = getattr(self, "web_hand_y", self.y - 20) or (self.y - 20.0 * self.render_scale)
            if self.state == "SWINGING":
                hx = self.x
                hy = self.y + self.hang_foot_reach() * 0.35
            self.draw_realistic_web(
                cr, hx, hy, self.web_anchor_x, self.web_anchor_y,
                alpha=alpha * max(0.55, self.web_opacity),
            )

        # Draw Character Sprite with Ultra HD Texture Filtering
        frame_key = self.get_current_frame_key()
        surf = self.get_surface(frame_key)
        if not surf:
            cr.save()
            cr.set_source_rgba(1.0, 0.2, 0.4, 0.95)
            cr.arc(self.x, self.y, 18, 0, 2 * math.pi)
            cr.fill()
            cr.restore()
            return True

        if surf:
            underhang = (
                (self.state == "CLINGING" and self.cling_side == "TOP" and getattr(self, "top_mode", "") == "UNDER")
                or (self.state == "WINDOW_TOP_HANG" and getattr(self, "top_mode", "") == "UNDER")
            )
            rs = float(self.render_scale)

            # -------------------------------------------------------------
            # Ultra HD Directional Ambient Occlusion Contact Shadow
            # Hugs actual window borders (vertical rail, top ledge, bottom sill)
            # -------------------------------------------------------------
            if self.state not in ("FALLING", "SWINGING") and not underhang:
                cr.save()
                if self.state == "CLINGING" and self.cling_side in ("RIGHT", "LEFT"):
                    # Elongated vertical contact shadow flush against the actual window bezel
                    wall_dir = -1.0 if self.cling_side == "RIGHT" else 1.0
                    contact_reach = 17.0 * rs if CHARACTERS[self.current_char]["format"] == "shimeji" else 12.0 * rs
                    shadow_x = self.x + wall_dir * contact_reach
                    cr.translate(shadow_x, self.y - self.step_bob_y)
                    cr.scale(0.18, 1.20)
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.14 * alpha)
                    cr.arc(0, 0, 20.0 * rs, 0, 2 * math.pi)
                    cr.fill()
                elif (
                    (self.state == "CLINGING" and getattr(self, "cling_side", "") == "TOP")
                    or self.state == "WINDOW_TOP_HANG"
                    or (self.state == "SITTING" and getattr(self, "cling_side", "") == "TOP")
                ):
                    # Titlebar horizontal contact shadow anchored to physical top rail
                    rail_y = getattr(self, "_last_hang_border", self.y + 19.0 * rs)
                    cr.translate(self.x, rail_y)
                    cr.scale(1.25, 0.22)
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.22 * alpha)
                    cr.arc(0, 0, 26.0 * rs, 0, 2 * math.pi)
                    cr.fill()
                elif self.state == "CLINGING" and self.cling_side == "BOTTOM":
                    # Bottom window sill contact shadow at feet soles
                    cr.translate(self.x, self.y - self.step_bob_y + 60.0 * rs)
                    cr.scale(1.20, 0.24)
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.20 * alpha)
                    cr.arc(0, 0, 26.0 * rs, 0, 2 * math.pi)
                    cr.fill()
                elif self.state == "CORNER_ARC":
                    # Tactile corner apex contact shadow
                    cr.translate(self.grip_catch_x, self.grip_catch_y)
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.24 * alpha)
                    cr.arc(0, 0, 8.5 * rs, 0, 2 * math.pi)
                    cr.fill()
                else:
                    # Ground floor contact shadow at feet soles
                    cr.translate(self.x, self.y - self.step_bob_y + 60.0 * rs)
                    cr.scale(1.15, 0.28)
                    cr.set_source_rgba(0.0, 0.0, 0.0, 0.18 * alpha)
                    cr.arc(0, 0, 28.0 * rs, 0, 2 * math.pi)
                    cr.fill()
                cr.restore()

            if underhang:
                self.draw_ceiling_hitch(cr, alpha=alpha)

            cr.save()
            cr.translate(self.x, self.y - self.step_bob_y)

            # Smooth 3D turning scale (interpolates smoothly when turning around)
            turn_sx = -self.facing_scale
            if abs(turn_sx) < 0.08:
                turn_sx = -0.08 if self.facing_scale >= 0 else 0.08

            if (
                (self.state == "CLINGING" and getattr(self, "cling_side", "") == "TOP")
                or self.state == "WINDOW_TOP_HANG"
            ):
                is_crawling = abs(getattr(self, "move_speed", 0.0)) > 3.0 or getattr(self, "hang_style", "") == "crawl"
                if is_crawling and CHARACTERS[self.current_char]["format"] == "shimeji":
                    # Spider-Man outward rail crawl:
                    # Level crawl angle ensures BOTH hands and legs contact the top rail at the exact same row,
                    # with head held high looking forward in the direction of travel!
                    if self.facing >= 0:
                        crawl_rot = math.radians(69.0)
                        crawl_sx = -1.0
                        crawl_sy = 1.0
                    else:
                        crawl_rot = math.radians(-69.0)
                        crawl_sx = 1.0
                        crawl_sy = 1.0
                    cr.rotate(crawl_rot + self.body_angle)
                    cr.scale(crawl_sx * self.scale_x * self.render_scale, crawl_sy * self.scale_y * self.render_scale)
                else:
                    cr.rotate(self.body_angle)
                    cr.scale(turn_sx * self.scale_x * self.render_scale, self.scale_y * self.render_scale)
            elif self.state == "SWINGING":
                cr.rotate(self.body_angle)
                if CHARACTERS[self.current_char]["format"] == "shimeji":
                    cr.scale(turn_sx * self.render_scale, self.render_scale)
                else:
                    cr.scale(turn_sx * self.scale_x * self.render_scale, self.scale_y * self.render_scale)
            elif self.state == "CORNER_ARC":
                raw_facing = CHARACTERS[self.current_char].get("climb_raw_facing", "LEFT")
                if getattr(self, "corner_from", "") == "RIGHT" or (getattr(self, "corner_from", "") == "TOP" and getattr(self, "corner_to", "") == "RIGHT"):
                    arc_sx = 1.0 if raw_facing == "LEFT" else -1.0
                else:
                    arc_sx = -1.0 if raw_facing == "LEFT" else 1.0
                cr.rotate(self.body_angle)
                cr.scale(arc_sx * self.scale_x * self.render_scale, self.scale_y * self.render_scale)
            elif self.state == "CLINGING":
                raw_facing = CHARACTERS[self.current_char].get("climb_raw_facing", "LEFT")
                if self.cling_side == "RIGHT":
                    cling_sx = 1.0 if raw_facing == "LEFT" else -1.0
                elif self.cling_side == "LEFT":
                    cling_sx = -1.0 if raw_facing == "LEFT" else 1.0
                elif self.cling_side == "BOTTOM":
                    cling_sx = turn_sx
                else:
                    cling_sx = turn_sx
                cr.rotate(self.body_angle)
                if self.cling_side == "BOTTOM":
                    cr.scale(cling_sx * self.render_scale, self.render_scale)
                else:
                    cr.scale(cling_sx * self.render_scale, self.render_scale)
            else:
                cr.rotate(self.body_angle)
                cr.scale(turn_sx, 1.0)
                cr.scale(self.scale_x, self.scale_y)
                cr.scale(self.render_scale, self.render_scale)

            # Ultra HD High-Order Lanczos/Sinc Resampling Filter
            cr.set_source_surface(surf, -64, -64)
            pattern = cr.get_source()
            if hasattr(pattern, "set_filter"):
                pattern.set_filter(cairo.FILTER_BEST)
            cr.paint_with_alpha(alpha)
            cr.restore()

        return True

def main():
    pet = HyprPet()
    Gtk.main()

if __name__ == "__main__":
    main()
