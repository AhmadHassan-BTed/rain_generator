import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from rain_generator.config import VisualColors
from rain_generator.visuals import (
    ScreenShake,
    SplashDroplet,
    Ripple,
    SplashSystem,
    Drop,
    RainSystem,
    LightningBolt,
    LightningManager,
    CloudLayer
)

@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_screenshake():
    shake = ScreenShake(max_offset=20.0, decay_rate=2.0)
    assert shake.get_offset() == (0, 0)

    shake.add_trauma(0.8)
    assert shake.trauma == 0.8
    ox, oy = shake.get_offset()
    assert abs(ox) <= 20.0 and abs(oy) <= 20.0

    # Decays over time
    shake.update(0.5)
    assert shake.trauma < 0.8

def test_splash_droplet():
    drop = SplashDroplet(100, 200, 10, -50, max_life=0.2)
    alive = drop.update(0.05)
    assert alive
    assert drop.y != 200

    # After max life, should expire
    expired = drop.update(0.3)
    assert not expired

def test_ripple():
    ripple = Ripple(100, 200, max_radius=15.0, max_life=0.3)
    alive = ripple.update(0.1)
    assert alive
    assert ripple.radius > 1.0

    expired = ripple.update(0.3)
    assert not expired

def test_splash_system():
    system = SplashSystem()
    system.add_splash(150, 400, intensity=1.0)
    assert len(system.droplets) > 0
    system.update(0.05)

def test_drop_physics():
    ground_hit = []
    def on_ground(x, y, intensity):
        ground_hit.append((x, y))

    drop = Drop(x=100, y=700, layer=2, base_speed=20.0)
    drop.update(dt=0.1, wind_speed=0.5, width=800, height=720, on_ground=on_ground)
    assert drop.x != 100
    assert drop.y != 700

def test_rain_system():
    rain = RainSystem(800, 600, target_count=200)
    assert len(rain.drops) == 200

    rain.set_target_count(350)
    assert len(rain.drops) == 350

    rain.update(0.016)

def test_lightning_bolt():
    bolt = LightningBolt((400, 0), (450, 600), max_displacement=100.0)
    assert len(bolt.segments) > 0
    p1, p2, depth = bolt.segments[0]
    assert len(p1) == 2 and len(p2) == 2

def test_lightning_manager():
    colors = VisualColors()
    mgr = LightningManager(colors)
    assert not mgr.in_strike

    mgr.trigger_strike(800, 600, distance_delay=False)
    assert mgr.in_strike
    assert mgr.active_bolt is not None

    mgr.update(0.35)
    assert not mgr.in_strike

def test_cloud_layer():
    clouds = CloudLayer(800, count=8)
    assert len(clouds.clouds) == 8
    clouds.update(0.1, wind=0.5)
