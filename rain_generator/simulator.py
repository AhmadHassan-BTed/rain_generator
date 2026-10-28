"""
Main simulation loop and event handling.
"""

import sys
import time
import random
import argparse
import pygame
from typing import Optional, List

from .config import Config, DEFAULT_CONFIG
from .presets import PRESETS, StormPreset, INTENSITY_TO_PRESET, PRESET_KEYS
from .audio import SoundEngine
from .visuals import RainSystem, LightningManager, CloudLayer
from .ui import HUD, SettingsModal, HelpModal, AudioGeneratorModal

class ThunderstormSimulator:
    """Application class managing the simulation window, audio, and user events."""

    def __init__(self, config: Optional[Config] = None, preset_name: str = "steady"):
        self.config = config or DEFAULT_CONFIG
        self.running = False
        self.paused = False

        if preset_name not in PRESETS:
            preset_name = INTENSITY_TO_PRESET.get(preset_name, "steady")
        self.current_preset_key = preset_name
        self.preset = PRESETS[self.current_preset_key]

        if not pygame.get_init():
            pygame.init()

        self.width = self.config.screen_width
        self.height = self.config.screen_height
        self.is_fullscreen = self.config.fullscreen

        display_flags = pygame.RESIZABLE
        if self.is_fullscreen:
            display_flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode((self.width, self.height), display_flags)
        pygame.display.set_caption(self.config.title)
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.Font(None, 28)
        self.font_body = pygame.font.Font(None, 22)
        self.font_hud = pygame.font.Font(None, 24)

        self.rain = RainSystem(self.width, self.height, self.preset.drop_count)
        self.lightning = LightningManager(self.config.visual_colors)
        self.clouds = CloudLayer(self.width, count=14)

        self.audio = SoundEngine()
        self.lightning.on_thunder_trigger = self._on_lightning_thunder_trigger

        self.hud = HUD(self.config)
        self.settings_modal = SettingsModal(self.config)
        self.generator_modal = AudioGeneratorModal(self.config.ui_colors)
        self.help_modal = HelpModal(self.config.ui_colors)

        self.apply_preset(self.current_preset_key)

        self.next_strike_time = time.time() + random.uniform(*self.preset.thunder_interval_range)
        self._on_resize(self.width, self.height)

    def _on_resize(self, width: int, height: int):
        """Handles window resize events."""
        self.width = width
        self.height = height
        self.rain.resize(width, height)
        self.clouds.resize(width)
        self.hud.resize(width)
        self.settings_modal.resize(width, height)
        self.generator_modal.resize(width, height)
        self.help_modal.resize(width, height)

    def _on_lightning_thunder_trigger(self, delay: float, volume_scale: float):
        self.audio.play_thunder(delay=delay, volume_scale=volume_scale)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.config.screen_width, self.config.screen_height), pygame.RESIZABLE)

        w, h = self.screen.get_size()
        self._on_resize(w, h)

    def apply_preset(self, preset_key: str):
        """Applies parameters from a preset."""
        if preset_key not in PRESETS:
            return

        self.current_preset_key = preset_key
        self.preset = PRESETS[preset_key]

        self.rain.set_target_count(self.preset.drop_count)
        self.rain.set_wind_parameters(self.preset.wind_mean, self.preset.wind_gust_strength)
        self.next_strike_time = time.time() + random.uniform(*self.preset.thunder_interval_range)
        self._sync_audio_parameters()

    def _sync_audio_parameters(self):
        """Syncs volume and weather variables to the audio engine."""
        self.audio.update_parameters(
            master_vol=self.config.volumes.get("master", 0.8),
            rain_vol=self.config.volumes.get("rain", 0.6),
            drops_vol=self.config.volumes.get("drops", 0.45),
            wind_vol=self.config.volumes.get("wind", 0.35),
            thunder_vol=self.config.volumes.get("thunder", 0.7),
            is_muted=self.config.is_muted,
            rain_intensity=self.preset.rain_audio_intensity,
            drop_rate=self.preset.drop_audio_rate,
            wind_speed=self.rain.current_wind
        )

    def cycle_preset(self):
        keys = PRESET_KEYS
        idx = (keys.index(self.current_preset_key) + 1) % len(keys)
        self.apply_preset(keys[idx])

    def trigger_manual_lightning(self):
        """Triggers an immediate lightning strike."""
        self.lightning.trigger_strike(
            self.width,
            self.height,
            distance_delay=self.config.thunder_distance_delay,
            shake_mult=self.preset.screen_shake_mult
        )
        self.next_strike_time = time.time() + random.uniform(*self.preset.thunder_interval_range)

    def toggle_mute(self):
        self.config.is_muted = not self.config.is_muted
        self._sync_audio_parameters()

    def export_audio(self, duration: float, preset_name: Optional[str] = None, filepath: Optional[str] = None):
        """Exports audio in a background worker thread."""
        import threading
        from .audio import export_audio_file

        preset = preset_name or self.current_preset_key
        if not filepath:
            filepath = f"rain_{preset}_{int(duration)}s.wav"

        def _worker():
            try:
                export_audio_file(
                    filepath=filepath,
                    duration=duration,
                    preset_name=preset,
                    volumes=self.config.volumes
                )
            except Exception as e:
                print(f"Audio export failed: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def handle_event(self, event: pygame.event.Event):
        """Dispatches pygame events."""
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self._on_resize(event.w, event.h)
            return

        if self.generator_modal.is_open:
            if self.generator_modal.handle_event(event, on_generate=lambda dur, pr: self.export_audio(dur, preset_name=pr)):
                return

        if self.help_modal.is_open:
            if self.help_modal.handle_event(event):
                return

        if self.settings_modal.is_open:
            if self.settings_modal.handle_event(
                event,
                on_preset_select=self.apply_preset,
                on_export_audio=self.export_audio
            ):
                self._sync_audio_parameters()
                return

        hud_actions = self.hud.handle_event(event)
        if hud_actions["preset"]:
            self.cycle_preset()
            return
        if hud_actions["generator"]:
            self.generator_modal.toggle(self.current_preset_key)
            return
        if hud_actions["mute"]:
            self.toggle_mute()
            return
        if hud_actions["settings"]:
            self.settings_modal.toggle()
            return
        if hud_actions["help"]:
            self.help_modal.toggle()
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_f, pygame.K_F11):
                self.toggle_fullscreen()
            elif event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_m:
                self.toggle_mute()
            elif event.key == pygame.K_g:
                self.generator_modal.toggle(self.current_preset_key)
            elif event.key == pygame.K_h:
                self.hud.visible = not self.hud.visible
            elif event.key == pygame.K_l:
                self.trigger_manual_lightning()
            elif event.key in (pygame.K_s, pygame.K_TAB):
                self.settings_modal.toggle()
            elif event.key in (pygame.K_SLASH, pygame.K_QUESTION):
                self.help_modal.toggle()
            elif event.key == pygame.K_ESCAPE:
                if self.generator_modal.is_open:
                    self.generator_modal.close()
                elif self.settings_modal.is_open:
                    self.settings_modal.close()
                elif self.help_modal.is_open:
                    self.help_modal.close()
                else:
                    self.running = False
            elif pygame.K_1 <= event.key <= pygame.K_5:
                idx = event.key - pygame.K_1
                if idx < len(PRESET_KEYS):
                    self.apply_preset(PRESET_KEYS[idx])

    def update(self, dt: float):
        """Updates scene physics, particles, and audio."""
        self.hud.update(dt)

        if self.paused:
            return

        self.rain.update(dt)
        self.clouds.update(dt, self.rain.current_wind)
        self.lightning.update(dt)

        self._sync_audio_parameters()
        self.audio.process_delayed_thunders()

        if self.config.lightning_enabled and time.time() >= self.next_strike_time:
            self.lightning.trigger_strike(
                self.width,
                self.height,
                distance_delay=self.config.thunder_distance_delay,
                shake_mult=self.preset.screen_shake_mult
            )
            self.next_strike_time = time.time() + random.uniform(*self.preset.thunder_interval_range)

    def draw(self):
        """Renders scene."""
        shake_x, shake_y = (0, 0)
        if self.config.screen_shake_enabled:
            shake_x, shake_y = self.lightning.screen_shake.get_offset()

        self.lightning.draw(self.screen, self.width, self.height)

        if self.config.clouds_enabled:
            self.clouds.draw(self.screen, self.lightning.flash_alpha)

        self.rain.draw(self.screen)

        fps = self.clock.get_fps()
        preset_badge = self.preset.display_name
        self.hud.draw(self.screen, self.font_hud, preset_badge, fps)

        if self.settings_modal.is_open:
            self.settings_modal.draw(self.screen, self.font_title, self.font_body, self.current_preset_key)

        if self.generator_modal.is_open:
            self.generator_modal.draw(self.screen, self.font_title, self.font_body)

        if self.help_modal.is_open:
            self.help_modal.draw(self.screen, self.font_title, self.font_body)

        pygame.display.flip()

    def run(self):
        """Main execution loop."""
        self.running = True
        self.audio.start()

        try:
            while self.running:
                dt = self.clock.tick(self.config.fps) / 1000.0
                dt = min(0.1, dt)

                for event in pygame.event.get():
                    self.handle_event(event)

                self.update(dt)
                self.draw()
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleans up audio and pygame resources."""
        self.audio.stop()
        pygame.quit()

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rain and thunderstorm simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-p", "--preset",
        choices=["drizzle", "steady", "thunderstorm", "gale", "cozy"],
        default="steady",
        help="Initial weather preset"
    )
    parser.add_argument(
        "-i", "--intensity",
        choices=["Low", "Medium", "High", "Extreme"],
        default=None,
        help="Intensity level selector"
    )
    parser.add_argument(
        "-f", "--fullscreen",
        action="store_true",
        help="Launch in fullscreen mode"
    )
    parser.add_argument(
        "-m", "--mute",
        action="store_true",
        help="Start with audio muted"
    )
    parser.add_argument(
        "-W", "--width",
        type=int,
        default=1080,
        help="Window width in pixels"
    )
    parser.add_argument(
        "-H", "--height",
        type=int,
        default=720,
        help="Window height in pixels"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Target framerate"
    )
    parser.add_argument(
        "--no-shake",
        action="store_true",
        help="Disable screen shake on lightning"
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        default=60.0,
        help="Audio export duration in seconds"
    )
    parser.add_argument(
        "-o", "--export", "--generate-audio",
        dest="export_path",
        type=str,
        default=None,
        help="Path to generate and export audio file of specified duration without opening GUI"
    )
    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)

    preset = args.preset
    if args.intensity:
        preset = INTENSITY_TO_PRESET.get(args.intensity, "steady")

    if args.export_path:
        from .audio import export_audio_file
        print(f"Generating {args.duration:.1f}s of '{preset}' rain audio...")
        saved_path = export_audio_file(
            filepath=args.export_path,
            duration=args.duration,
            preset_name=preset
        )
        print(f"Exported audio file: {saved_path}")
        return

    config = Config(
        screen_width=args.width,
        screen_height=args.height,
        fullscreen=args.fullscreen,
        fps=args.fps,
        is_muted=args.mute,
        screen_shake_enabled=not args.no_shake
    )

    sim = ThunderstormSimulator(config=config, preset_name=preset)
    sim.run()

if __name__ == "__main__":
    main()
