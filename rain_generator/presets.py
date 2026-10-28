"""
Atmospheric presets defining physical and acoustic parameters.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class StormPreset:
    name: str
    display_name: str
    description: str
    drop_count: int
    rain_speed_min: float
    rain_speed_max: float
    wind_mean: float
    wind_gust_strength: float
    thunder_interval_range: Tuple[float, float]
    rain_audio_intensity: float
    drop_audio_rate: float
    wind_audio_intensity: float
    cloud_density: float
    screen_shake_mult: float = 1.0

PRESETS: Dict[str, StormPreset] = {
    "drizzle": StormPreset(
        name="drizzle",
        display_name="Solitary Drizzle",
        description="Quiet drops tapping against an empty windowsill in the dark.",
        drop_count=350,
        rain_speed_min=8.0,
        rain_speed_max=16.0,
        wind_mean=0.2,
        wind_gust_strength=0.3,
        thunder_interval_range=(50.0, 100.0),
        rain_audio_intensity=0.7,
        drop_audio_rate=0.6,
        wind_audio_intensity=0.2,
        cloud_density=0.4,
        screen_shake_mult=0.4
    ),
    "steady": StormPreset(
        name="steady",
        display_name="Midnight Rain",
        description="Cold, continuous rainfall falling steadily over desolate streets.",
        drop_count=800,
        rain_speed_min=14.0,
        rain_speed_max=25.0,
        wind_mean=0.5,
        wind_gust_strength=0.7,
        thunder_interval_range=(25.0, 55.0),
        rain_audio_intensity=1.2,
        drop_audio_rate=1.0,
        wind_audio_intensity=0.45,
        cloud_density=0.7,
        screen_shake_mult=0.9
    ),
    "thunderstorm": StormPreset(
        name="thunderstorm",
        display_name="Distant Thunder",
        description="Heavy rain with low, solitary rumbles echoing across a forgotten horizon.",
        drop_count=1350,
        rain_speed_min=18.0,
        rain_speed_max=32.0,
        wind_mean=1.1,
        wind_gust_strength=1.4,
        thunder_interval_range=(10.0, 24.0),
        rain_audio_intensity=1.9,
        drop_audio_rate=1.7,
        wind_audio_intensity=0.75,
        cloud_density=0.9,
        screen_shake_mult=1.5
    ),
    "gale": StormPreset(
        name="gale",
        display_name="Cold Tempest",
        description="Bitter wind and sideways rain sweeping through an abandoned city.",
        drop_count=1800,
        rain_speed_min=22.0,
        rain_speed_max=38.0,
        wind_mean=2.2,
        wind_gust_strength=2.0,
        thunder_interval_range=(5.0, 14.0),
        rain_audio_intensity=2.4,
        drop_audio_rate=2.0,
        wind_audio_intensity=1.1,
        cloud_density=1.0,
        screen_shake_mult=2.0
    ),
    "cozy": StormPreset(
        name="cozy",
        display_name="Nostalgia",
        description="Slow, muted droplets sliding down glass while memories linger.",
        drop_count=420,
        rain_speed_min=9.0,
        rain_speed_max=17.0,
        wind_mean=0.0,
        wind_gust_strength=0.15,
        thunder_interval_range=(70.0, 140.0),
        rain_audio_intensity=0.85,
        drop_audio_rate=1.1,
        wind_audio_intensity=0.12,
        cloud_density=0.5,
        screen_shake_mult=0.3
    ),
}

INTENSITY_TO_PRESET = {
    "Low": "drizzle",
    "Medium": "steady",
    "High": "thunderstorm",
    "Extreme": "gale",
}

PRESET_KEYS = list(PRESETS.keys())
