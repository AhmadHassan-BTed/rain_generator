"""
User interface controls: sliders, buttons, vector icons, HUD, and modal dialogs.
"""

import math
from typing import List, Tuple, Optional, Callable, Dict
import pygame
from .config import Config, UIColors

def draw_speaker_icon(surface: pygame.Surface, cx: int, cy: int, size: int, color: Tuple[int, int, int], muted: bool = False):
    """Draws a vector speaker icon with an optional mute cross."""
    w, h = size, size
    x, y = cx - w // 2, cy - h // 2

    # Speaker body
    pts = [
        (x, y + int(h * 0.3)),
        (x + int(w * 0.35), y + int(h * 0.3)),
        (x + int(w * 0.65), y + int(h * 0.1)),
        (x + int(w * 0.65), y + int(h * 0.9)),
        (x + int(w * 0.35), y + int(h * 0.7)),
        (x, y + int(h * 0.7))
    ]
    pygame.draw.polygon(surface, color, pts)

    if muted:
        # Cross lines for muted state
        cross_color = (225, 80, 80)
        pygame.draw.line(surface, cross_color, (x + int(w * 0.75), y + int(h * 0.25)), (x + w, y + int(h * 0.75)), 2)
        pygame.draw.line(surface, cross_color, (x + w, y + int(h * 0.25)), (x + int(w * 0.75), y + int(h * 0.75)), 2)
    else:
        # Sound wave arc
        arc_rect = pygame.Rect(x + int(w * 0.45), y + int(h * 0.2), int(w * 0.45), int(h * 0.6))
        try:
            pygame.draw.arc(surface, color, arc_rect, -math.pi / 3, math.pi / 3, 2)
        except Exception:
            pass

def draw_gear_icon(surface: pygame.Surface, cx: int, cy: int, radius: int, color: Tuple[int, int, int]):
    """Draws a vector gear icon."""
    pygame.draw.circle(surface, color, (cx, cy), radius, 2)
    pygame.draw.circle(surface, color, (cx, cy), max(2, radius // 2))

    # Radial teeth
    offsets = [
        (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
        (0.7, 0.7), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7)
    ]
    for dx, dy in offsets:
        p1 = (cx + int(dx * (radius - 2)), cy + int(dy * (radius - 2)))
        p2 = (cx + int(dx * (radius + 3)), cy + int(dy * (radius + 3)))
        pygame.draw.line(surface, color, p1, p2, 2)

def draw_help_icon(surface: pygame.Surface, cx: int, cy: int, radius: int, color: Tuple[int, int, int], font: pygame.font.Font):
    """Draws a circular help icon with question mark."""
    pygame.draw.circle(surface, color, (cx, cy), radius, 1)
    text = font.render("?", True, color)
    surface.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))

def draw_close_icon(surface: pygame.Surface, cx: int, cy: int, size: int, color: Tuple[int, int, int]):
    """Draws a clean vector X close icon."""
    half = size // 2
    pygame.draw.line(surface, color, (cx - half, cy - half), (cx + half, cy + half), 2)
    pygame.draw.line(surface, color, (cx - half, cy + half), (cx + half, cy - half), 2)

class Slider:
    """Draggable horizontal slider with percentage readout."""

    def __init__(self, key: str, label: str, value: float, min_val: float = 0.0, max_val: float = 1.0, is_percentage: bool = True):
        self.key = key
        self.label = label
        self.value = max(min_val, min(max_val, value))
        self.min_val = min_val
        self.max_val = max_val
        self.is_percentage = is_percentage
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.is_dragging = False
        self.is_hovered = False

    def set_bounds(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)

    def handle_event(self, event: pygame.event.Event) -> bool:
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_val_from_mouse(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                changed = True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_dragging:
                self._update_val_from_mouse(event.pos[0])
                changed = True
        return changed

    def _update_val_from_mouse(self, mouse_x: int):
        norm = (mouse_x - self.rect.x) / max(1, self.rect.width)
        norm = max(0.0, min(1.0, norm))
        self.value = self.min_val + norm * (self.max_val - self.min_val)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, colors: UIColors):
        if self.is_percentage:
            val_str = f"{int(self.value * 100)}%"
        else:
            val_str = f"{self.value:.1f}"

        label_surf = font.render(self.label, True, colors.text_primary)
        val_surf = font.render(val_str, True, colors.text_secondary)

        surface.blit(label_surf, (self.rect.x, self.rect.y - 20))
        surface.blit(val_surf, (self.rect.right - val_surf.get_width(), self.rect.y - 20))

        # Track
        track_y = self.rect.y + (self.rect.height - 6) // 2
        pygame.draw.rect(surface, colors.track_bg, (self.rect.x, track_y, self.rect.width, 6), border_radius=3)

        norm = (self.value - self.min_val) / max(0.0001, (self.max_val - self.min_val))
        fill_width = int(norm * self.rect.width)
        fill_color = colors.accent_hover if (self.is_dragging or self.is_hovered) else colors.track_fill
        if fill_width > 0:
            pygame.draw.rect(surface, fill_color, (self.rect.x, track_y, fill_width, 6), border_radius=3)

        # Thumb
        thumb_x = self.rect.x + fill_width
        thumb_y = self.rect.y + self.rect.height // 2
        thumb_radius = 8 if (self.is_dragging or self.is_hovered) else 7
        thumb_color = colors.accent_active if self.is_dragging else (255, 255, 255)
        pygame.draw.circle(surface, thumb_color, (thumb_x, thumb_y), thumb_radius)
        pygame.draw.circle(surface, colors.panel_border, (thumb_x, thumb_y), thumb_radius, 1)

class Button:
    """Styled clickable button supporting text or custom vector icon drawing."""

    def __init__(self, key: str, label: str = "", icon_type: Optional[str] = None, width: int = 120, height: int = 36):
        self.key = key
        self.label = label
        self.icon_type = icon_type  # 'speaker', 'gear', 'help', 'close'
        self.rect = pygame.Rect(0, 0, width, height)
        self.is_hovered = False
        self.is_active = False

    def set_position(self, x: int, y: int):
        self.rect.x = x
        self.rect.y = y

    def handle_event(self, event: pygame.event.Event) -> bool:
        clicked = False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_active = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_active and self.rect.collidepoint(event.pos):
                clicked = True
            self.is_active = False
        return clicked

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, colors: UIColors,
             is_selected: bool = False, muted_state: bool = False):
        if is_selected:
            bg_color = colors.accent
            border_color = colors.accent_active
            fg_color = (255, 255, 255)
        elif self.is_active:
            bg_color = (colors.accent[0] // 2, colors.accent[1] // 2, colors.accent[2] // 2)
            border_color = colors.accent_hover
            fg_color = colors.text_primary
        elif self.is_hovered:
            bg_color = (40, 50, 70)
            border_color = colors.panel_border_hover
            fg_color = colors.text_primary
        else:
            bg_color = (28, 34, 48)
            border_color = colors.panel_border
            fg_color = colors.text_secondary

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=6)

        cx = self.rect.x + self.rect.width // 2
        cy = self.rect.y + self.rect.height // 2

        if self.icon_type == "speaker":
            draw_speaker_icon(surface, cx, cy, 18, fg_color, muted=muted_state)
        elif self.icon_type == "gear":
            draw_gear_icon(surface, cx, cy, 7, fg_color)
        elif self.icon_type == "help":
            draw_help_icon(surface, cx, cy, 10, fg_color, font)
        elif self.icon_type == "close":
            draw_close_icon(surface, cx, cy, 12, fg_color)
        elif self.label:
            text_surf = font.render(self.label, True, fg_color)
            tx = self.rect.x + (self.rect.width - text_surf.get_width()) // 2
            ty = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
            surface.blit(text_surf, (tx, ty))

class SettingsModal:
    """Dialog for fine-tuning sound volumes and selecting weather presets."""

    def __init__(self, config: Config):
        self.config = config
        self.is_open = False
        self.rect = pygame.Rect(0, 0, 540, 480)

        # Volume sliders
        self.sliders: List[Slider] = [
            Slider("master", "Master Volume", config.volumes.get("master", 0.8)),
            Slider("thunder", "Thunder Volume", config.volumes.get("thunder", 0.7)),
            Slider("rain", "Rain Volume", config.volumes.get("rain", 0.6)),
            Slider("drops", "Droplet Patters", config.volumes.get("drops", 0.45)),
            Slider("wind", "Wind Intensity", config.volumes.get("wind", 0.35)),
        ]

        # Duration slider and export button
        self.duration_slider = Slider("duration", "Export Duration (sec)", value=60.0, min_val=5.0, max_val=300.0, is_percentage=False)
        self.export_btn = Button("export", label="Export Audio", width=130, height=30)
        self.export_status = ""
        self.export_status_time = 0.0

        # Close button with vector icon
        self.close_btn = Button("close", icon_type="close", width=32, height=32)

        # Preset tab buttons
        self.preset_buttons: List[Button] = [
            Button("drizzle", label="Drizzle", width=95, height=32),
            Button("steady", label="Steady", width=95, height=32),
            Button("thunderstorm", label="Storm", width=95, height=32),
            Button("gale", label="Gale", width=95, height=32),
            Button("cozy", label="Window", width=95, height=32),
        ]

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False
        for s in self.sliders:
            s.is_dragging = False
        self.duration_slider.is_dragging = False

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def resize(self, screen_width: int, screen_height: int):
        w = min(580, int(screen_width * 0.88))
        h = min(570, int(screen_height * 0.92))
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self.rect = pygame.Rect(x, y, w, h)

        self.close_btn.set_position(x + w - 42, y + 12)

        btn_w = (w - 60) // len(self.preset_buttons)
        for i, btn in enumerate(self.preset_buttons):
            btn.rect.width = btn_w
            btn.set_position(x + 30 + i * (btn_w + 5), y + 62)

        slider_y = y + 118
        for s in self.sliders:
            s.set_bounds(x + 35, slider_y, w - 70, 22)
            slider_y += 48

        # Position export controls
        self.duration_slider.set_bounds(x + 35, slider_y + 10, w - 210, 22)
        self.export_btn.set_position(x + w - 165, slider_y + 8)

    def handle_event(self, event: pygame.event.Event,
                     on_preset_select: Optional[Callable[[str], None]] = None,
                     on_export_audio: Optional[Callable[[float], None]] = None) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.close()
                return True

        if self.close_btn.handle_event(event):
            self.close()
            return True

        for btn in self.preset_buttons:
            if btn.handle_event(event):
                if on_preset_select:
                    on_preset_select(btn.key)
                return True

        for s in self.sliders:
            if s.handle_event(event):
                self.config.volumes[s.key] = s.value

        if self.duration_slider.handle_event(event):
            pass

        if self.export_btn.handle_event(event):
            dur = self.duration_slider.value
            if on_export_audio:
                on_export_audio(dur)
            import time
            self.export_status = f"Exported {int(dur)}s to rain_export.wav"
            self.export_status_time = time.time() + 4.0
            return True

        return True

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font, font_body: pygame.font.Font, current_preset: str):
        if not self.is_open:
            return

        colors = self.config.ui_colors

        # Backdrop
        dim_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 120))
        surface.blit(dim_surf, (0, 0))

        # Panel
        modal_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        modal_surf.fill(colors.panel_bg)
        surface.blit(modal_surf, (self.rect.x, self.rect.y))

        pygame.draw.rect(surface, colors.panel_border, self.rect, 2, border_radius=10)

        title_surf = font_title.render("Rain & Sound Controls", True, colors.text_primary)
        surface.blit(title_surf, (self.rect.x + 25, self.rect.y + 18))

        self.close_btn.draw(surface, font_body, colors)

        preset_header = font_body.render("Rain Mood", True, colors.text_dim)
        surface.blit(preset_header, (self.rect.x + 30, self.rect.y + 46))

        for btn in self.preset_buttons:
            btn.draw(surface, font_body, colors, is_selected=(btn.key == current_preset))

        for s in self.sliders:
            s.draw(surface, font_body, colors)

        # Draw export section
        self.duration_slider.draw(surface, font_body, colors)
        self.export_btn.draw(surface, font_body, colors)

        import time
        if self.export_status and time.time() < self.export_status_time:
            status_surf = font_body.render(self.export_status, True, colors.success)
            surface.blit(status_surf, (self.rect.x + 35, self.rect.bottom - 26))

class HelpModal:
    """Dialog displaying keybindings and controls."""

    def __init__(self, colors: UIColors):
        self.colors = colors
        self.is_open = False
        self.rect = pygame.Rect(0, 0, 480, 400)
        self.close_btn = Button("close_help", icon_type="close", width=32, height=32)

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def resize(self, width: int, height: int):
        w = min(500, int(width * 0.85))
        h = min(420, int(height * 0.85))
        self.rect = pygame.Rect((width - w) // 2, (height - h) // 2, w, h)
        self.close_btn.set_position(self.rect.right - 42, self.rect.y + 14)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_SLASH, pygame.K_QUESTION):
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.close()
                return True
        if self.close_btn.handle_event(event):
            self.close()
            return True
        return False

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font, font_body: pygame.font.Font):
        if not self.is_open:
            return

        dim = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surface.blit(dim, (0, 0))

        modal_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        modal_surf.fill(self.colors.panel_bg)
        surface.blit(modal_surf, (self.rect.x, self.rect.y))
        pygame.draw.rect(surface, self.colors.panel_border, self.rect, 2, border_radius=10)

        title = font_title.render("Controls & Shortcuts", True, self.colors.text_primary)
        surface.blit(title, (self.rect.x + 25, self.rect.y + 18))
        self.close_btn.draw(surface, font_body, self.colors)

        shortcuts = [
            ("F / F11", "Toggle Fullscreen Mode"),
            ("Space", "Pause / Resume Weather Engine"),
            ("M", "Mute / Unmute Audio"),
            ("H", "Toggle HUD Visibility"),
            ("L", "Trigger Lightning Strike"),
            ("1 - 5", "Select Weather Preset"),
            ("G", "Open Audio Track Generator"),
            ("S / Tab", "Open Settings & Mixer"),
            ("? / /", "Show / Hide Keybindings"),
            ("Esc", "Close Dialog / Exit"),
        ]

        start_y = self.rect.y + 65
        for key, desc in shortcuts:
            key_surf = font_body.render(key, True, self.colors.accent_hover)
            desc_surf = font_body.render(desc, True, self.colors.text_primary)
            surface.blit(key_surf, (self.rect.x + 35, start_y))
            surface.blit(desc_surf, (self.rect.x + 145, start_y))
            start_y += 34

class AudioGeneratorModal:
    """Dialog for configuring track duration and generating storm audio files."""

    def __init__(self, colors: UIColors):
        self.colors = colors
        self.is_open = False
        self.rect = pygame.Rect(0, 0, 560, 420)
        self.close_btn = Button("close_gen", icon_type="close", width=32, height=32)

        self.duration_slider = Slider(
            "gen_dur", "Track Length (seconds)", value=60.0, min_val=5.0, max_val=600.0, is_percentage=False
        )

        self.quick_durations = [
            ("15s", 15.0),
            ("30s", 30.0),
            ("1m", 60.0),
            ("2m", 120.0),
            ("5m", 300.0),
            ("10m", 600.0),
        ]
        self.quick_buttons = [
            Button(f"dur_{int(sec)}", label=lbl, width=54, height=28)
            for lbl, sec in self.quick_durations
        ]

        self.preset_keys = ["drizzle", "steady", "thunderstorm", "gale", "cozy"]
        self.preset_buttons = [
            Button(f"gen_{k}", label=k.capitalize() if k != "cozy" else "Window", width=95, height=30)
            for k in self.preset_keys
        ]
        self.selected_preset = "steady"
        self.generate_btn = Button("start_gen", label="Generate Audio File", width=190, height=38)
        self.status_message = ""
        self.status_time = 0.0

    def open(self, initial_preset: str = "steady"):
        self.selected_preset = initial_preset
        self.is_open = True

    def close(self):
        self.is_open = False
        self.duration_slider.is_dragging = False

    def toggle(self, initial_preset: str = "steady"):
        if self.is_open:
            self.close()
        else:
            self.open(initial_preset)

    def resize(self, width: int, height: int):
        w = min(560, int(width * 0.88))
        h = min(420, int(height * 0.88))
        x = (width - w) // 2
        y = (height - h) // 2
        self.rect = pygame.Rect(x, y, w, h)
        self.close_btn.set_position(x + w - 42, y + 14)

        qw = (w - 70) // len(self.quick_buttons)
        for i, btn in enumerate(self.quick_buttons):
            btn.rect.width = qw - 4
            btn.set_position(x + 35 + i * qw, y + 86)

        self.duration_slider.set_bounds(x + 35, y + 145, w - 70, 24)

        pw = (w - 70) // len(self.preset_buttons)
        for i, btn in enumerate(self.preset_buttons):
            btn.rect.width = pw - 4
            btn.set_position(x + 35 + i * pw, y + 215)

        self.generate_btn.rect.width = 220
        self.generate_btn.set_position(x + (w - 220) // 2, y + 280)

    def handle_event(self, event: pygame.event.Event, on_generate: Optional[Callable[[float, str], None]] = None) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.close()
                return True

        if self.close_btn.handle_event(event):
            self.close()
            return True

        for (lbl, sec), btn in zip(self.quick_durations, self.quick_buttons):
            if btn.handle_event(event):
                self.duration_slider.value = sec
                return True

        self.duration_slider.handle_event(event)

        for p_key, btn in zip(self.preset_keys, self.preset_buttons):
            if btn.handle_event(event):
                self.selected_preset = p_key
                return True

        if self.generate_btn.handle_event(event):
            dur = self.duration_slider.value
            if on_generate:
                on_generate(dur, self.selected_preset)
            import time
            self.status_message = f"Saved {int(dur)}s audio to rain_{self.selected_preset}_{int(dur)}s.wav"
            self.status_time = time.time() + 5.0
            return True

        return True

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font, font_body: pygame.font.Font):
        if not self.is_open:
            return

        import time

        dim = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 130))
        surface.blit(dim, (0, 0))

        modal_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        modal_surf.fill(self.colors.panel_bg)
        surface.blit(modal_surf, (self.rect.x, self.rect.y))
        pygame.draw.rect(surface, self.colors.panel_border, self.rect, 2, border_radius=10)

        title = font_title.render("Generate Rain Recording", True, self.colors.text_primary)
        surface.blit(title, (self.rect.x + 25, self.rect.y + 18))
        self.close_btn.draw(surface, font_body, self.colors)

        dur_hdr = font_body.render("Quick Duration", True, self.colors.text_dim)
        surface.blit(dur_hdr, (self.rect.x + 35, self.rect.y + 64))
        for (lbl, sec), btn in zip(self.quick_durations, self.quick_buttons):
            is_active = abs(self.duration_slider.value - sec) < 0.5
            btn.draw(surface, font_body, self.colors, is_selected=is_active)

        self.duration_slider.draw(surface, font_body, self.colors)

        preset_hdr = font_body.render("Rain Mood", True, self.colors.text_dim)
        surface.blit(preset_hdr, (self.rect.x + 35, self.rect.y + 192))
        for p_key, btn in zip(self.preset_keys, self.preset_buttons):
            btn.draw(surface, font_body, self.colors, is_selected=(p_key == self.selected_preset))

        self.generate_btn.draw(surface, font_body, self.colors, is_selected=True)

        if self.status_message and time.time() < self.status_time:
            status_surf = font_body.render(self.status_message, True, self.colors.success)
            sx = self.rect.x + (self.rect.width - status_surf.get_width()) // 2
            surface.blit(status_surf, (sx, self.rect.bottom - 36))

class HUD:
    """Status bar with preset badge, mute toggle, settings, audio export, and help buttons."""

    def __init__(self, config: Config):
        self.config = config
        self.preset_btn = Button("preset", label="Steady Rain", width=140, height=36)
        self.generator_btn = Button("generator", label="Export Audio", width=120, height=36)
        self.mute_btn = Button("mute", icon_type="speaker", width=42, height=36)
        self.settings_btn = Button("settings", icon_type="gear", width=42, height=36)
        self.help_btn = Button("help", icon_type="help", width=42, height=36)
        self.last_mouse_activity = 0.0
        self.alpha = 255
        self.visible = True

    def notify_activity(self):
        self.last_mouse_activity = pygame.time.get_ticks() / 1000.0

    def resize(self, width: int):
        self.preset_btn.set_position(20, 16)
        self.help_btn.set_position(width - 56, 16)
        self.settings_btn.set_position(width - 106, 16)
        self.mute_btn.set_position(width - 156, 16)
        self.generator_btn.set_position(width - 286, 16)

    def handle_event(self, event: pygame.event.Event) -> Dict[str, bool]:
        actions = {"preset": False, "mute": False, "settings": False, "generator": False, "help": False}
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.notify_activity()

        if not self.visible or self.alpha < 40:
            return actions

        if self.preset_btn.handle_event(event):
            actions["preset"] = True
        if self.generator_btn.handle_event(event):
            actions["generator"] = True
        if self.mute_btn.handle_event(event):
            actions["mute"] = True
        if self.settings_btn.handle_event(event):
            actions["settings"] = True
        if self.help_btn.handle_event(event):
            actions["help"] = True

        return actions

    def update(self, dt: float):
        if not self.visible:
            self.alpha = max(0, int(self.alpha - 600 * dt))
            return

        now = pygame.time.get_ticks() / 1000.0
        idle_time = now - self.last_mouse_activity

        if self.config.auto_hide_hud and idle_time > self.config.hud_timeout:
            self.alpha = max(0, int(self.alpha - 250 * dt))
        else:
            self.alpha = min(255, int(self.alpha + 400 * dt))

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, current_preset_name: str, fps: float):
        if self.alpha <= 5:
            return

        colors = self.config.ui_colors

        self.preset_btn.label = current_preset_name
        self.preset_btn.draw(surface, font, colors)
        self.generator_btn.draw(surface, font, colors)
        self.mute_btn.draw(surface, font, colors, muted_state=self.config.is_muted)
        self.settings_btn.draw(surface, font, colors)
        self.help_btn.draw(surface, font, colors)

        if self.config.show_fps:
            fps_str = f"{int(fps)} FPS"
            fps_surf = font.render(fps_str, True, colors.text_dim)
            surface.blit(fps_surf, (self.generator_btn.rect.x - fps_surf.get_width() - 20, 24))
