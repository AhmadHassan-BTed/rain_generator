# GenRainpy - Rain and Thunderstorm Simulator

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)](https://www.python.org/)
[![pygame](https://img.shields.io/badge/pygame-2.1%2B-green?style=flat-square)](https://www.pygame.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A procedural rain and thunderstorm simulator built with Python, Pygame, NumPy, and SciPy. Features multi-layer parallax rainfall, particle splash physics, fractal branching lightning strikes, and real-time procedural audio synthesis.

---

## Features

- **Parallax Rainfall:** Multi-depth rain layers with independent velocities, lengths, opacities, and wind deflection angles.
- **Particle Splashes & Ripples:** Water droplets eject upward on surface collision with expanding ground ripples.
- **Fractal Branching Lightning:** Midpoint displacement generation producing branching lightning bolts, multi-phase sky illumination, and camera trauma shake.
- **Procedural Sound Synthesis:**
  - Real-time lowpass filtered rain ambiance.
  - Granular droplet impact synthesis using decaying sinusoids.
  - Modulated wind noise responsive to current wind velocity.
  - Realistic thunder playback with optional distance delay (speed of sound physics).
- **Interactive Controls & Audio Mixer:**
  - Live volume sliders for Master, Thunder, Rain Ambiance, Droplet Patters, and Wind.
  - Five weather presets: Drizzle, Steady Rain, Thunderstorm, Gale Storm, and Window Rain.
  - Auto-hiding HUD for uncluttered ambient viewing.
- **Resolution & Fullscreen Support:** Dynamic layout recalculation supporting window resizing and seamless fullscreen toggling.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/azuletto/rain_generator.git
   cd rain_generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install in editable mode:
   ```bash
   pip install -e .
   ```

---

## Usage

Run via the main launcher:
```bash
python thunderstorm_simulator.py
```

Or via module execution:
```bash
python -m rain_generator
```

### CLI Arguments

```bash
python -m rain_generator --preset thunderstorm --fullscreen
python -m rain_generator --preset drizzle --mute -W 1280 -H 720
```

Available options:
- `-p`, `--preset`: Weather preset (`drizzle`, `steady`, `thunderstorm`, `gale`, `cozy`)
- `-i`, `--intensity`: Intensity level (`Low`, `Medium`, `High`, `Extreme`)
- `-f`, `--fullscreen`: Launch in fullscreen mode
- `-m`, `--mute`: Launch with audio muted
- `-W`, `--width`: Window width in pixels (default: 1080)
- `-H`, `--height`: Window height in pixels (default: 720)
- `--fps`: Target framerate (default: 60)
- `--no-shake`: Disable camera shake on lightning
- `-d`, `--duration`: Audio export duration in seconds (default: 60)
- `-o`, `--export`: Output filepath to generate and export audio directly without GUI

### Audio Track Export

Generate an ambient audio file of any custom length (e.g. 2 minutes of thunderstorm audio):

```bash
python thunderstorm_simulator.py --duration 120 --export thunderstorm_2m.wav --preset thunderstorm
```

You can also click the **Export Audio** button in the top HUD (or press `G`) while running the simulator to open the interactive generator dialog.

---

## Controls & Keybindings

| Key | Action |
| --- | --- |
| `F` / `F11` | Toggle Fullscreen mode |
| `Space` | Pause / Resume simulation |
| `M` | Mute / Unmute audio |
| `G` | Open Audio Track Generator dialog |
| `H` | Toggle HUD visibility |
| `L` | Trigger manual lightning bolt and thunder |
| `1` - `5` | Switch presets (1: Drizzle, 2: Steady, 3: Storm, 4: Gale, 5: Window) |
| `S` / `Tab` | Open Settings and Audio Mixer dialog |
| `?` / `/` | Open Keybindings help dialog |
| `Esc` | Close open dialog or exit simulation |

---

## Testing

Run the test suite using pytest:
```bash
pytest
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
