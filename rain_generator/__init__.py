"""
GenRainpy - Procedural Rain and Thunderstorm Simulator.

A rain and thunderstorm simulation engine featuring multi-layer
parallax rainfall, splash particles, branching lightning bolts,
and procedural audio synthesis.
"""

from .config import Config, DEFAULT_CONFIG
from .presets import PRESETS, StormPreset
from .audio import SoundEngine, generate_storm_audio, export_audio_file
from .visuals import RainSystem, LightningManager, SplashSystem
from .simulator import ThunderstormSimulator

__version__ = "2.0.0"
__all__ = [
    "Config",
    "DEFAULT_CONFIG",
    "PRESETS",
    "StormPreset",
    "SoundEngine",
    "generate_storm_audio",
    "export_audio_file",
    "RainSystem",
    "LightningManager",
    "SplashSystem",
    "ThunderstormSimulator",
    "__version__",
]
