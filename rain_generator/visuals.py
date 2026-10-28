"""
Visual effects: rain layers, splash particles, lightning, and clouds.
"""

import math
import random
import time
from typing import List, Tuple, Optional, Callable
import pygame
from .config import VisualColors

class ScreenShake:
    """Calculates camera offsets based on decaying trauma."""

    def __init__(self, max_offset: float = 18.0, decay_rate: float = 2.2):
        self.max_offset = max_offset
        self.decay_rate = decay_rate
        self.trauma = 0.0

    def add_trauma(self, amount: float):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt: float):
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - self.decay_rate * dt)

    def get_offset(self) -> Tuple[int, int]:
        if self.trauma <= 0.01:
            return 0, 0
        shake = (self.trauma ** 2) * self.max_offset
        ox = random.uniform(-shake, shake)
        oy = random.uniform(-shake, shake)
        return int(ox), int(oy)

class SplashDroplet:
    """Upward splash particle spawned when a raindrop hits the ground."""
    __slots__ = ("x", "y", "vx", "vy", "gravity", "alpha", "max_life", "life", "radius")

    def __init__(self, x: float, y: float, vx: float, vy: float, max_life: float = 0.28):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.gravity = 980.0
        self.max_life = max_life
        self.life = 0.0
        self.alpha = 220
        self.radius = random.uniform(1.0, 1.8)

    def update(self, dt: float) -> bool:
        self.life += dt
        if self.life >= self.max_life:
            return False
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alpha = int(220 * (1.0 - (self.life / self.max_life)))
        return True

class Ripple:
    """Ground ripple ring expanding on water impact."""
    __slots__ = ("x", "y", "radius", "max_radius", "growth_speed", "alpha", "life", "max_life")

    def __init__(self, x: float, y: float, max_radius: float = 14.0, max_life: float = 0.4):
        self.x = x
        self.y = y
        self.radius = 1.0
        self.max_radius = max_radius
        self.max_life = max_life
        self.life = 0.0
        self.growth_speed = max_radius / max_life
        self.alpha = 180

    def update(self, dt: float) -> bool:
        self.life += dt
        if self.life >= self.max_life:
            return False
        self.radius += self.growth_speed * dt
        self.alpha = int(180 * (1.0 - (self.life / self.max_life)))
        return True

class SplashSystem:
    """Manages ground splashes and ripples."""

    def __init__(self, max_droplets: int = 400, max_ripples: int = 150):
        self.droplets: List[SplashDroplet] = []
        self.ripples: List[Ripple] = []
        self.max_droplets = max_droplets
        self.max_ripples = max_ripples

    def add_splash(self, x: float, y: float, intensity: float = 1.0, wind_bias: float = 0.0):
        if len(self.droplets) < self.max_droplets:
            count = random.randint(2, 4)
            for _ in range(count):
                speed_x = random.uniform(-60, 60) + (wind_bias * 25.0)
                speed_y = random.uniform(-140, -60) * intensity
                self.droplets.append(SplashDroplet(x, y, speed_x, speed_y, max_life=random.uniform(0.18, 0.32)))

        if len(self.ripples) < self.max_ripples and random.random() < 0.6:
            self.ripples.append(Ripple(x, y, max_radius=random.uniform(8.0, 16.0) * intensity))

    def update(self, dt: float):
        self.droplets = [d for d in self.droplets if d.update(dt)]
        self.ripples = [r for r in self.ripples if r.update(dt)]

    def draw(self, surface: pygame.Surface, ground_y: int):
        for r in self.ripples:
            if r.alpha <= 0 or r.radius <= 0.5:
                continue
            rect = pygame.Rect(
                int(r.x - r.radius),
                int(r.y - (r.radius * 0.35)),
                int(r.radius * 2),
                int(max(1, r.radius * 0.7))
            )
            color = (180, 210, 245)
            try:
                pygame.draw.ellipse(surface, color, rect, 1)
            except Exception:
                pass

        for d in self.droplets:
            if d.alpha <= 0:
                continue
            color = (200, 225, 255)
            pygame.draw.circle(surface, color, (int(d.x), int(d.y)), max(1, int(d.radius)))

class Drop:
    """Raindrop particle with parallax depth layer."""
    __slots__ = ("x", "y", "layer", "speed", "length", "thickness", "color")

    def __init__(self, x: float, y: float, layer: int, base_speed: float):
        self.x = x
        self.y = y
        self.layer = layer  # 0: far, 1: mid, 2: near

        if layer == 0:
            self.speed = base_speed * random.uniform(0.65, 0.85)
            self.length = random.uniform(8, 14)
            self.thickness = 1
            self.color = (130, 155, 185)
        elif layer == 1:
            self.speed = base_speed * random.uniform(0.9, 1.15)
            self.length = random.uniform(16, 26)
            self.thickness = 1
            self.color = (170, 195, 225)
        else:
            self.speed = base_speed * random.uniform(1.25, 1.6)
            self.length = random.uniform(28, 44)
            self.thickness = 2
            self.color = (215, 235, 255)

    def update(self, dt: float, wind_speed: float, width: int, height: int, on_ground: Callable[[float, float, float], None]):
        layer_wind_mult = 0.5 + 0.35 * self.layer
        vx = wind_speed * 180.0 * layer_wind_mult
        vy = self.speed * 40.0

        self.x += vx * dt
        self.y += vy * dt

        if self.y >= height:
            if self.layer >= 1 and random.random() < 0.85:
                intensity = 0.7 if self.layer == 1 else 1.2
                on_ground(self.x, height - 2, intensity)
            self.y = random.uniform(-60, -10)
            self.x = random.uniform(-50, width + 50)

        if self.x < -80:
            self.x = width + random.uniform(0, 40)
        elif self.x > width + 80:
            self.x = -random.uniform(0, 40)

    def draw(self, surface: pygame.Surface, wind_speed: float):
        layer_wind_mult = 0.5 + 0.35 * self.layer
        vx_ratio = (wind_speed * 180.0 * layer_wind_mult) / max(1.0, self.speed * 40.0)

        tail_x = self.x - (vx_ratio * self.length)
        tail_y = self.y - self.length

        pygame.draw.line(surface, self.color, (int(tail_x), int(tail_y)), (int(self.x), int(self.y)), self.thickness)

class RainSystem:
    """Manages rain particles and wind variance."""

    def __init__(self, width: int, height: int, target_count: int = 800):
        self.width = width
        self.height = height
        self.target_count = target_count
        self.drops: List[Drop] = []
        self.splashes = SplashSystem()

        self.current_wind = 0.0
        self.target_wind = 0.0
        self.wind_gust_timer = 0.0
        self.wind_gust_interval = 4.0
        self.wind_base = 0.0
        self.wind_gust_strength = 0.5

        self._init_drops()

    def _init_drops(self):
        self.drops.clear()
        for _ in range(self.target_count):
            self.drops.append(self._spawn_random_drop())

    def _spawn_random_drop(self) -> Drop:
        layer_choice = random.choices([0, 1, 2], weights=[0.45, 0.40, 0.15])[0]
        x = random.uniform(-50, self.width + 50)
        y = random.uniform(-100, self.height)
        return Drop(x, y, layer_choice, base_speed=random.uniform(16.0, 24.0))

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height

    def set_target_count(self, count: int):
        self.target_count = max(50, count)
        if len(self.drops) < self.target_count:
            for _ in range(self.target_count - len(self.drops)):
                self.drops.append(self._spawn_random_drop())
        elif len(self.drops) > self.target_count:
            self.drops = self.drops[:self.target_count]

    def set_wind_parameters(self, base_wind: float, gust_strength: float):
        self.wind_base = base_wind
        self.wind_gust_strength = gust_strength

    def update(self, dt: float):
        self.wind_gust_timer += dt
        if self.wind_gust_timer >= self.wind_gust_interval:
            self.wind_gust_timer = 0.0
            self.wind_gust_interval = random.uniform(3.0, 7.0)
            self.target_wind = self.wind_base + random.uniform(-self.wind_gust_strength, self.wind_gust_strength)

        self.current_wind += (self.target_wind - self.current_wind) * min(1.0, dt * 1.5)

        def on_ground(gx: float, gy: float, intensity: float):
            self.splashes.add_splash(gx, gy, intensity, wind_bias=self.current_wind)

        for drop in self.drops:
            drop.update(dt, self.current_wind, self.width, self.height, on_ground)

        self.splashes.update(dt)

    def draw(self, surface: pygame.Surface):
        ground_rect = pygame.Rect(0, self.height - 12, self.width, 12)
        pygame.draw.rect(surface, (12, 16, 24), ground_rect)

        self.splashes.draw(surface, self.height)

        for drop in self.drops:
            drop.draw(surface, self.current_wind)

class LightningBolt:
    """Midpoint-displacement branching lightning bolt."""

    def __init__(self, start_pt: Tuple[float, float], end_pt: Tuple[float, float], max_displacement: float = 130.0):
        self.segments: List[Tuple[Tuple[float, float], Tuple[float, float], int]] = []
        self._generate(start_pt, end_pt, max_displacement, min_length=14.0, branch_chance=0.38, depth=0)

    def _generate(self, p1: Tuple[float, float], p2: Tuple[float, float],
                  disp: float, min_length: float, branch_chance: float, depth: int):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = math.hypot(dx, dy)

        if dist < min_length or depth > 6:
            self.segments.append((p1, p2, depth))
            return

        mx = (p1[0] + p2[0]) / 2.0
        my = (p1[1] + p2[1]) / 2.0

        nx = -dy / dist
        ny = dx / dist
        offset = random.uniform(-disp, disp)
        mid = (mx + nx * offset, my + ny * offset)

        self._generate(p1, mid, disp * 0.58, min_length, branch_chance, depth + 1)
        self._generate(mid, p2, disp * 0.58, min_length, branch_chance, depth + 1)

        if random.random() < branch_chance and dist > min_length * 2.0:
            angle = random.uniform(0.35, 0.75) * (-1 if random.random() < 0.5 else 1)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            bx = dx * cos_a - dy * sin_a
            by = dx * sin_a + dy * cos_a
            b_len = dist * random.uniform(0.35, 0.65)
            b_norm = math.hypot(bx, by)
            b_end = (mid[0] + (bx / b_norm) * b_len, mid[1] + (by / b_norm) * b_len)
            self._generate(mid, b_end, disp * 0.45, min_length * 1.5, branch_chance * 0.3, depth + 2)

    def draw(self, surface: pygame.Surface, alpha_scale: float = 1.0):
        if not self.segments or alpha_scale <= 0.05:
            return

        core_color = (255, 255, 255)
        glow_color = (160, 205, 255)

        for p1, p2, depth in self.segments:
            thickness = max(1, 3 - min(2, depth))
            if depth <= 1 and thickness > 1:
                pygame.draw.line(surface, glow_color, p1, p2, thickness + 4)
            pygame.draw.line(surface, core_color, p1, p2, thickness)

class LightningManager:
    """Manages lightning strike timing and sky flash rendering."""

    def __init__(self, visual_colors: VisualColors):
        self.colors = visual_colors
        self.active_bolt: Optional[LightningBolt] = None
        self.flash_alpha = 0.0
        self.flash_timer = 0.0
        self.strike_duration = 0.28
        self.in_strike = False
        self.screen_shake = ScreenShake()
        self.on_thunder_trigger: Optional[Callable[[float, float], None]] = None

    def trigger_strike(self, width: int, height: int, distance_delay: bool = True, shake_mult: float = 1.0):
        self.in_strike = True
        self.flash_alpha = 1.0
        self.flash_timer = self.strike_duration

        start_x = random.uniform(width * 0.2, width * 0.8)
        end_x = start_x + random.uniform(-150, 150)
        end_y = random.uniform(height * 0.65, height * 0.95)
        self.active_bolt = LightningBolt((start_x, 0), (end_x, end_y))

        self.screen_shake.add_trauma(0.85 * shake_mult)

        if self.on_thunder_trigger:
            simulated_dist_km = random.uniform(0.1, 1.8) if distance_delay else 0.0
            delay = simulated_dist_km * 0.9
            vol_scale = max(0.6, 1.0 - (simulated_dist_km * 0.25))
            self.on_thunder_trigger(delay, vol_scale)

    def update(self, dt: float):
        self.screen_shake.update(dt)

        if self.in_strike:
            self.flash_timer -= dt
            if self.flash_timer <= 0.0:
                self.in_strike = False
                self.flash_alpha = 0.0
                self.active_bolt = None
            else:
                progress = 1.0 - (self.flash_timer / self.strike_duration)
                if progress < 0.25:
                    self.flash_alpha = 1.0
                elif progress < 0.45:
                    self.flash_alpha = 0.35 + 0.5 * math.sin(progress * 40.0)
                else:
                    decay = (1.0 - progress) / 0.55
                    self.flash_alpha = max(0.0, decay ** 2)

    def draw(self, surface: pygame.Surface, width: int, height: int):
        if self.flash_alpha > 0.02:
            r = int(self.colors.sky_clear[0] + (self.colors.sky_flash[0] - self.colors.sky_clear[0]) * self.flash_alpha)
            g = int(self.colors.sky_clear[1] + (self.colors.sky_flash[1] - self.colors.sky_clear[1]) * self.flash_alpha)
            b = int(self.colors.sky_clear[2] + (self.colors.sky_flash[2] - self.colors.sky_clear[2]) * self.flash_alpha)
            surface.fill((r, g, b))
        else:
            surface.fill(self.colors.sky_clear)

        if self.active_bolt and self.flash_alpha > 0.1:
            self.active_bolt.draw(surface, self.flash_alpha)

class CloudLayer:
    """Background cloud puffs drifting with wind."""

    def __init__(self, width: int, count: int = 12):
        self.width = width
        self.clouds = []
        for _ in range(count):
            self.clouds.append({
                "x": random.uniform(0, width),
                "y": random.uniform(-40, 80),
                "radius_x": random.uniform(90, 220),
                "radius_y": random.uniform(40, 90),
                "speed": random.uniform(4.0, 10.0),
                "base_alpha": random.randint(35, 70)
            })

    def resize(self, width: int):
        self.width = width

    def update(self, dt: float, wind: float):
        for c in self.clouds:
            c["x"] += (c["speed"] + wind * 20.0) * dt
            if c["x"] - c["radius_x"] > self.width + 50:
                c["x"] = -c["radius_x"] - 30
            elif c["x"] + c["radius_x"] < -80:
                c["x"] = self.width + c["radius_x"] + 30

    def draw(self, surface: pygame.Surface, flash_alpha: float = 0.0):
        tint = int(25 + 40 * (1.0 - flash_alpha))
        color = (tint, tint + 5, tint + 12)

        for c in self.clouds:
            rect = pygame.Rect(
                int(c["x"] - c["radius_x"]),
                int(c["y"] - c["radius_y"]),
                int(c["radius_x"] * 2),
                int(c["radius_y"] * 2)
            )
            try:
                pygame.draw.ellipse(surface, color, rect)
            except Exception:
                pass
