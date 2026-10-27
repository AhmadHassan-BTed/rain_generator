"""
Procedural audio synthesis and thunder sound playback.
"""

import os
import time
import random
import logging
import threading
from typing import List, Optional, Callable
import numpy as np
from scipy.signal import butter, lfilter
import pygame

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except (ImportError, OSError):
    HAS_SOUNDDEVICE = False

logger = logging.getLogger(__name__)

def lowpass_filter(data: np.ndarray, cutoff: float, fs: int, order: int = 4) -> np.ndarray:
    """Apply Butterworth low-pass filter to signal."""
    nyquist = 0.5 * fs
    normal_cutoff = max(0.01, min(0.99, cutoff / nyquist))
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, data)

def bandpass_filter(data: np.ndarray, lowcut: float, highcut: float, fs: int, order: int = 2) -> np.ndarray:
    """Apply Butterworth band-pass filter to signal."""
    nyquist = 0.5 * fs
    low = max(0.01, min(0.98, lowcut / nyquist))
    high = max(low + 0.01, min(0.99, highcut / nyquist))
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)

class ProceduralRainSynthesizer:
    """Synthesizes rain noise, individual drop impacts, and wind sound."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.rain_cutoff = 1900.0
        self.rain_scale = 1.0
        self.drop_rate = 1.0
        self.wind_level = 0.0
        self._wind_phase = 0.0

    def generate_rain_noise(self, length: int, intensity: float = 1.0) -> np.ndarray:
        noise = np.random.normal(0, 0.22 * intensity, length).astype(np.float32)
        filtered = lowpass_filter(noise, cutoff=self.rain_cutoff, fs=self.sample_rate)
        return filtered.astype(np.float32)

    def generate_drop_impacts(self, length: int, rate_multiplier: float = 1.0) -> np.ndarray:
        """Synthesizes raindrop impacts using decaying sinusoids."""
        buffer = np.zeros(length, dtype=np.float32)
        expected_drops = int(max(0, 16 * rate_multiplier * (length / self.sample_rate)))
        if expected_drops <= 0:
            return buffer

        drop_count = np.random.poisson(expected_drops)
        if drop_count <= 0:
            return buffer

        positions = np.random.randint(0, max(1, length - 400), drop_count)
        for pos in positions:
            duration = np.random.randint(180, 500)
            t = np.linspace(0, duration / self.sample_rate, duration, endpoint=False)
            freq = np.random.uniform(1600, 3800)
            decay = np.exp(-t * np.random.uniform(40, 100))
            sine = np.sin(2 * np.pi * freq * t) * decay
            end = min(length, pos + duration)
            actual_len = end - pos
            amplitude = np.random.uniform(0.04, 0.16)
            buffer[pos:end] += (sine[:actual_len] * amplitude).astype(np.float32)

        return buffer

    def generate_wind_noise(self, length: int, wind_strength: float = 0.5) -> np.ndarray:
        """Generates wind noise using bandpassed noise and low-frequency modulation."""
        if wind_strength <= 0.05:
            return np.zeros(length, dtype=np.float32)

        noise = np.random.normal(0, 0.18, length).astype(np.float32)
        center_freq = 280.0 + (wind_strength * 220.0)
        lowcut = max(60.0, center_freq - 140.0)
        highcut = min(1200.0, center_freq + 180.0)

        wind_band = bandpass_filter(noise, lowcut, highcut, self.sample_rate)

        t = np.linspace(0, length / self.sample_rate, length, endpoint=False)
        gust = 0.7 + 0.3 * np.sin(2 * np.pi * 0.4 * t + self._wind_phase)
        self._wind_phase = (self._wind_phase + 2 * np.pi * 0.4 * (length / self.sample_rate)) % (2 * np.pi)

        return (wind_band * gust * min(1.5, wind_strength)).astype(np.float32)

class SoundEngine:
    """Manages audio streams, thunder playback, and channel volume mixing."""

    def __init__(self, sounds_dir: Optional[str] = None):
        self.sample_rate = 44100
        self.block_size = 2048
        self.synthesizer = ProceduralRainSynthesizer(self.sample_rate)

        self._stream: Optional[sd.OutputStream] = None if HAS_SOUNDDEVICE else None
        self._stream_running = False
        self._audio_available = HAS_SOUNDDEVICE
        self._lock = threading.Lock()

        self.master_volume = 0.8
        self.rain_volume = 0.6
        self.drops_volume = 0.45
        self.wind_volume = 0.35
        self.thunder_volume = 0.7
        self.is_muted = False

        self.rain_intensity_scale = 1.0
        self.drop_rate_scale = 1.0
        self.wind_speed = 0.0

        self._delayed_thunders: List[dict] = []
        self._delayed_lock = threading.Lock()

        self.thunder_sounds: List[pygame.mixer.Sound] = []
        self._init_mixer(sounds_dir)

    def _init_mixer(self, sounds_dir: Optional[str] = None):
        """Initializes pygame.mixer and loads available thunder sound clips."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            except Exception as e:
                logger.warning(f"Could not initialize pygame.mixer: {e}")
                return

        candidates = []
        if sounds_dir and os.path.isdir(sounds_dir):
            candidates.append(sounds_dir)
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "..", "sounds"),
            os.path.join(os.getcwd(), "sounds"),
            "sounds"
        ])

        found_dir = None
        for candidate in candidates:
            norm = os.path.normpath(candidate)
            if os.path.isdir(norm):
                found_dir = norm
                break

        if found_dir:
            for i in range(1, 11):
                path = os.path.join(found_dir, f"thunder_{i}.wav")
                if os.path.exists(path):
                    try:
                        sound = pygame.mixer.Sound(path)
                        self.thunder_sounds.append(sound)
                    except Exception as err:
                        logger.warning(f"Failed to load thunder sound {path}: {err}")
        else:
            logger.warning("No sounds directory found for thunder clips.")

    def _audio_callback(self, outdata: np.ndarray, frames: int, time_info, status):
        """Output stream callback."""
        if status:
            logger.debug(f"Audio stream status: {status}")

        if self.is_muted or self.master_volume <= 0.001:
            outdata.fill(0)
            return

        with self._lock:
            eff_rain = self.rain_volume * self.master_volume
            eff_drops = self.drops_volume * self.master_volume
            eff_wind = self.wind_volume * self.master_volume
            rain_scale = self.rain_intensity_scale
            drop_scale = self.drop_rate_scale
            wind_speed = abs(self.wind_speed)

        rain = self.synthesizer.generate_rain_noise(frames, rain_scale) * eff_rain
        drops = self.synthesizer.generate_drop_impacts(frames, drop_scale) * eff_drops
        wind = self.synthesizer.generate_wind_noise(frames, wind_speed) * eff_wind

        mixed = rain + drops + wind
        mixed = np.tanh(mixed)

        if outdata.shape[1] == 1:
            outdata[:] = mixed.reshape(-1, 1)
        elif outdata.shape[1] == 2:
            outdata[:, 0] = mixed
            outdata[:, 1] = mixed
        else:
            outdata[:] = np.repeat(mixed.reshape(-1, 1), outdata.shape[1], axis=1)

    def start(self):
        """Starts audio output stream."""
        if not HAS_SOUNDDEVICE or self._stream_running:
            return

        try:
            self._stream = sd.OutputStream(
                channels=2,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self._audio_callback,
                latency="high"
            )
            self._stream.start()
            self._stream_running = True
        except Exception as e:
            logger.warning(f"Could not open sounddevice stream: {e}")
            self._audio_available = False
            self._stream_running = False

    def stop(self):
        """Stops audio stream."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            finally:
                self._stream = None
                self._stream_running = False

    def update_parameters(self,
                          master_vol: float,
                          rain_vol: float,
                          drops_vol: float,
                          wind_vol: float,
                          thunder_vol: float,
                          is_muted: bool,
                          rain_intensity: float,
                          drop_rate: float,
                          wind_speed: float):
        """Updates volume and storm parameters."""
        with self._lock:
            self.master_volume = max(0.0, min(1.0, master_vol))
            self.rain_volume = max(0.0, min(1.0, rain_vol))
            self.drops_volume = max(0.0, min(1.0, drops_vol))
            self.wind_volume = max(0.0, min(1.0, wind_vol))
            self.thunder_volume = max(0.0, min(1.0, thunder_vol))
            self.is_muted = is_muted
            self.rain_intensity_scale = max(0.1, rain_intensity)
            self.drop_rate_scale = max(0.1, drop_rate)
            self.wind_speed = wind_speed

    def play_thunder(self, delay: float = 0.0, volume_scale: float = 1.0):
        """Plays a thunder clip, optionally queued with a delay."""
        if not self.thunder_sounds:
            return

        sound = random.choice(self.thunder_sounds)
        eff_vol = 0.0 if self.is_muted else (self.thunder_volume * self.master_volume * volume_scale)
        eff_vol = max(0.0, min(1.0, eff_vol))

        if delay <= 0.05:
            sound.set_volume(eff_vol)
            sound.play()
        else:
            with self._delayed_lock:
                self._delayed_thunders.append({
                    "trigger_time": time.time() + delay,
                    "sound": sound,
                    "volume": eff_vol
                })

    def process_delayed_thunders(self):
        """Fires any queued thunder clips whose trigger time has elapsed."""
        if not self._delayed_thunders:
            return

        now = time.time()
        with self._delayed_lock:
            remaining = []
            for item in self._delayed_thunders:
                if now >= item["trigger_time"]:
                    sound = item["sound"]
                    vol = 0.0 if self.is_muted else min(1.0, item["volume"] * (self.master_volume / max(0.01, self.master_volume)))
                    sound.set_volume(vol)
                    sound.play()
                else:
                    remaining.append(item)
            self._delayed_thunders = remaining

def generate_storm_audio(
    duration: float,
    preset_name: str = "steady",
    sample_rate: int = 44100,
    volumes: Optional[dict] = None,
    sounds_dir: Optional[str] = None,
    include_thunder: bool = True
) -> np.ndarray:
    """
    Generates a continuous storm audio track of specified duration in seconds.
    Returns stereo int16 audio array of shape (N, 2).
    """
    import scipy.io.wavfile as wavfile
    from .presets import PRESETS

    preset = PRESETS.get(preset_name, PRESETS["steady"])
    vol_dict = {
        "master": 0.8,
        "rain": 0.6,
        "drops": 0.45,
        "wind": 0.35,
        "thunder": 0.7
    }
    if volumes:
        vol_dict.update(volumes)

    total_samples = int(duration * sample_rate)
    synth = ProceduralRainSynthesizer(sample_rate=sample_rate)

    eff_rain = vol_dict["rain"] * vol_dict["master"]
    eff_drops = vol_dict["drops"] * vol_dict["master"]
    eff_wind = vol_dict["wind"] * vol_dict["master"]
    eff_thunder = vol_dict["thunder"] * vol_dict["master"]

    rain = synth.generate_rain_noise(total_samples, preset.rain_audio_intensity) * eff_rain
    drops = synth.generate_drop_impacts(total_samples, preset.drop_audio_rate) * eff_drops
    wind = synth.generate_wind_noise(total_samples, preset.wind_audio_intensity) * eff_wind

    mono_ambient = rain + drops + wind
    stereo = np.column_stack((mono_ambient, mono_ambient)).astype(np.float32)

    # Layer thunder clips
    if include_thunder and eff_thunder > 0.01:
        candidates = []
        if sounds_dir and os.path.isdir(sounds_dir):
            candidates.append(sounds_dir)
        candidates.extend([
            os.path.join(os.path.dirname(__file__), "..", "sounds"),
            os.path.join(os.getcwd(), "sounds"),
            "sounds"
        ])
        found_dir = None
        for c in candidates:
            norm = os.path.normpath(c)
            if os.path.isdir(norm):
                found_dir = norm
                break

        t_files = []
        if found_dir:
            for i in range(1, 11):
                p = os.path.join(found_dir, f"thunder_{i}.wav")
                if os.path.exists(p):
                    t_files.append(p)

        if t_files:
            current_time = random.uniform(*preset.thunder_interval_range)
            while current_time < duration:
                start_sample = int(current_time * sample_rate)
                clip_path = random.choice(t_files)
                try:
                    tsr, tdata = wavfile.read(clip_path)
                    tfloat = tdata.astype(np.float32) / 32768.0
                    if len(tfloat.shape) == 1:
                        tfloat = np.column_stack((tfloat, tfloat))
                    clip_len = min(len(tfloat), total_samples - start_sample)
                    if clip_len > 0:
                        stereo[start_sample:start_sample + clip_len] += tfloat[:clip_len] * eff_thunder
                except Exception as err:
                    logger.debug(f"Could not load thunder clip {clip_path}: {err}")

                current_time += random.uniform(*preset.thunder_interval_range)

    # Soft clipping / saturation
    stereo = np.tanh(stereo)
    int16_audio = (np.clip(stereo, -1.0, 1.0) * 32767).astype(np.int16)
    return int16_audio

def export_audio_file(
    filepath: str,
    duration: float,
    preset_name: str = "steady",
    sample_rate: int = 44100,
    volumes: Optional[dict] = None,
    sounds_dir: Optional[str] = None
) -> str:
    """
    Generates storm audio of specified duration and saves to a WAV file.
    """
    import scipy.io.wavfile as wavfile

    audio_data = generate_storm_audio(
        duration=duration,
        preset_name=preset_name,
        sample_rate=sample_rate,
        volumes=volumes,
        sounds_dir=sounds_dir
    )
    wavfile.write(filepath, sample_rate, audio_data)
    return os.path.abspath(filepath)
