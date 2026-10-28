"""
Configuration parameters and color definitions.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass
class UIColors:
    panel_bg: Tuple[int, int, int, int] = (14, 17, 24, 225)
    panel_border: Tuple[int, int, int] = (46, 56, 74)
    panel_border_hover: Tuple[int, int, int] = (68, 84, 110)
    text_primary: Tuple[int, int, int] = (210, 220, 230)
    text_secondary: Tuple[int, int, int] = (120, 134, 154)
    text_dim: Tuple[int, int, int] = (75, 86, 102)
    accent: Tuple[int, int, int] = (46, 96, 160)
    accent_hover: Tuple[int, int, int] = (62, 116, 185)
    accent_active: Tuple[int, int, int] = (80, 138, 210)
    track_bg: Tuple[int, int, int] = (24, 30, 42)
    track_fill: Tuple[int, int, int] = (46, 96, 160)
    danger: Tuple[int, int, int] = (210, 70, 85)
    success: Tuple[int, int, int] = (45, 170, 125)

@dataclass
class VisualColors:
    sky_clear: Tuple[int, int, int] = (8, 11, 17)
    sky_flash: Tuple[int, int, int] = (205, 220, 240)
    cloud_tint: Tuple[int, int, int] = (18, 23, 32)
    lightning_core: Tuple[int, int, int] = (250, 252, 255)
    lightning_inner: Tuple[int, int, int] = (185, 210, 240)
    lightning_outer: Tuple[int, int, int] = (100, 145, 215)
    ground_tint: Tuple[int, int, int] = (6, 8, 12)

@dataclass
class Config:
    screen_width: int = 1080
    screen_height: int = 720
    fullscreen: bool = False
    fps: int = 60
    title: str = "Rain and Thunderstorm Simulator"

    volumes: Dict[str, float] = field(default_factory=lambda: {
        "master": 0.8,
        "thunder": 0.7,
        "rain": 0.6,
        "drops": 0.45,
        "wind": 0.35
    })
    is_muted: bool = False

    intensity: str = "Medium"
    drop_count: int = 800
    rain_speed_min: float = 14.0
    rain_speed_max: float = 26.0
    wind_speed: float = 0.0
    wind_variation: float = 1.0
    lightning_enabled: bool = True
    branching_lightning: bool = True
    screen_shake_enabled: bool = True
    clouds_enabled: bool = True
    splashes_enabled: bool = True
    thunder_distance_delay: bool = True

    auto_hide_hud: bool = True
    hud_timeout: float = 3.5
    show_fps: bool = False

    ui_colors: UIColors = field(default_factory=UIColors)
    visual_colors: VisualColors = field(default_factory=VisualColors)

    def get_effective_volume(self, channel: str) -> float:
        if self.is_muted:
            return 0.0
        master = self.volumes.get("master", 1.0)
        channel_vol = self.volumes.get(channel, 0.5)
        return float(max(0.0, min(1.0, master * channel_vol)))

DEFAULT_CONFIG = Config()
