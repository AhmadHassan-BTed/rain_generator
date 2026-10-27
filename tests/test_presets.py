import pytest
from rain_generator.presets import PRESETS, INTENSITY_TO_PRESET, PRESET_KEYS, StormPreset

def test_preset_definitions():
    assert len(PRESETS) >= 5
    for key, preset in PRESETS.items():
        assert isinstance(preset, StormPreset)
        assert preset.drop_count > 0
        assert preset.rain_speed_min < preset.rain_speed_max
        assert preset.thunder_interval_range[0] < preset.thunder_interval_range[1]
        assert preset.rain_audio_intensity > 0
        assert preset.drop_audio_rate > 0
        assert 0.0 <= preset.cloud_density <= 1.0

def test_intensity_mapping():
    for intensity, preset_key in INTENSITY_TO_PRESET.items():
        assert preset_key in PRESETS

def test_preset_keys():
    for key in PRESET_KEYS:
        assert key in PRESETS
