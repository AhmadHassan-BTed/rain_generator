import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from rain_generator.config import Config
from rain_generator.simulator import ThunderstormSimulator, parse_args
from rain_generator.presets import PRESETS

@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_parse_args_defaults():
    args = parse_args([])
    assert args.preset == "steady"
    assert args.width == 1080
    assert args.height == 720
    assert not args.fullscreen
    assert not args.mute

def test_parse_args_custom():
    args = parse_args(["--preset", "thunderstorm", "--fullscreen", "--mute", "-W", "800", "-H", "600"])
    assert args.preset == "thunderstorm"
    assert args.fullscreen
    assert args.mute
    assert args.width == 800
    assert args.height == 600

def test_simulator_lifecycle():
    config = Config(screen_width=640, screen_height=480, is_muted=True)
    sim = ThunderstormSimulator(config=config, preset_name="drizzle")

    assert sim.current_preset_key == "drizzle"
    assert sim.width == 640
    assert sim.height == 480

    # Preset cycle
    sim.cycle_preset()
    assert sim.current_preset_key != "drizzle"

    # Mute toggle
    assert sim.config.is_muted
    sim.toggle_mute()
    assert not sim.config.is_muted

    # Manual lightning strike
    sim.trigger_manual_lightning()
    assert sim.lightning.in_strike

    # Resize
    sim._on_resize(800, 600)
    assert sim.width == 800
    assert sim.height == 600

    # Simulation step
    sim.update(0.016)

    # Cleanup
    sim.cleanup()
