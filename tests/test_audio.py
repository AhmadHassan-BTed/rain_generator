import os
import numpy as np
import pytest
from rain_generator.audio import (
    lowpass_filter,
    bandpass_filter,
    ProceduralRainSynthesizer,
    SoundEngine
)

def test_lowpass_filter():
    fs = 44100
    data = np.random.normal(0, 1.0, 1000)
    filtered = lowpass_filter(data, cutoff=2000, fs=fs, order=4)
    assert filtered.shape == data.shape
    assert np.all(np.isfinite(filtered))

def test_bandpass_filter():
    fs = 44100
    data = np.random.normal(0, 1.0, 1000)
    filtered = bandpass_filter(data, lowcut=200, highcut=600, fs=fs, order=2)
    assert filtered.shape == data.shape
    assert np.all(np.isfinite(filtered))

def test_procedural_synthesizer():
    synth = ProceduralRainSynthesizer(sample_rate=44100)

    # Rain noise
    noise = synth.generate_rain_noise(2048, intensity=1.5)
    assert len(noise) == 2048
    assert np.all(np.isfinite(noise))
    assert np.max(np.abs(noise)) < 2.0

    # Droplet impacts
    drops = synth.generate_drop_impacts(2048, rate_multiplier=2.0)
    assert len(drops) == 2048
    assert np.all(np.isfinite(drops))

    # Wind noise
    wind = synth.generate_wind_noise(2048, wind_strength=0.8)
    assert len(wind) == 2048
    assert np.all(np.isfinite(wind))

    # Zero wind produces silence
    calm = synth.generate_wind_noise(1024, wind_strength=0.0)
    assert np.all(calm == 0.0)

def test_sound_engine_volume_updates():
    engine = SoundEngine()
    engine.update_parameters(
        master_vol=0.9,
        rain_vol=0.5,
        drops_vol=0.4,
        wind_vol=0.3,
        thunder_vol=0.8,
        is_muted=False,
        rain_intensity=1.2,
        drop_rate=1.0,
        wind_speed=0.5
    )
    assert engine.master_volume == 0.9
    assert engine.rain_volume == 0.5
    assert not engine.is_muted

    # Audio callback simulation
    outdata = np.zeros((512, 2), dtype=np.float32)
    engine._audio_callback(outdata, 512, None, None)
    assert outdata.shape == (512, 2)
    assert np.all(np.isfinite(outdata))
    assert np.max(np.abs(outdata)) <= 1.0

def test_sound_engine_mute():
    engine = SoundEngine()
    engine.update_parameters(
        master_vol=1.0,
        rain_vol=1.0,
        drops_vol=1.0,
        wind_vol=1.0,
        thunder_vol=1.0,
        is_muted=True,
        rain_intensity=1.0,
        drop_rate=1.0,
        wind_speed=0.5
    )
    outdata = np.ones((256, 2), dtype=np.float32)
    engine._audio_callback(outdata, 256, None, None)
    assert np.all(outdata == 0.0)

def test_generate_storm_audio():
    from rain_generator.audio import generate_storm_audio
    # Generate 1.5 seconds of audio
    data = generate_storm_audio(duration=1.5, preset_name="steady", sample_rate=22050)
    assert data.shape == (int(1.5 * 22050), 2)
    assert data.dtype == np.int16
    assert np.any(data != 0)

def test_export_audio_file(tmp_path):
    from rain_generator.audio import export_audio_file
    out_file = str(tmp_path / "test_rain.wav")
    result = export_audio_file(out_file, duration=1.0, preset_name="drizzle", sample_rate=22050)
    assert os.path.exists(result)
    assert os.path.getsize(result) > 1000
