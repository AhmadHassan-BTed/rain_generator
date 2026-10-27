"""
Rain and Thunderstorm Simulator.

Main entry point providing backwards compatibility with the original simulator
interface while running the overhauled weather simulation and audio engine.
"""

import sys
import numpy as np
from scipy.signal import butter, lfilter

from rain_generator.config import Config, DEFAULT_CONFIG
from rain_generator.simulator import ThunderstormSimulator, main
from rain_generator.audio import (
    lowpass_filter,
    SoundEngine,
    generate_storm_audio,
    export_audio_file,
)

# Legacy compatibility helpers
def filtro_passa_baixa(dados, cutoff, fs, ordem=8):
    """Lowpass filter (legacy Portuguese alias)."""
    return lowpass_filter(dados, cutoff, fs, ordem)

def gerar_ruido_chuva(tamanho, taxa_amostragem=44100, intensidade=2.0):
    """Generates procedural rain noise (legacy alias)."""
    ruido = np.random.normal(0, 0.20 * intensidade, tamanho)
    chuva_suave = filtro_passa_baixa(ruido, cutoff=1800, fs=taxa_amostragem)
    return np.clip(chuva_suave, -1.0, 1.0)

def gerar_chuva(tamanho, taxa_amostragem=44100, intensidade_escala=1.0, num_base=3):
    """Legacy rain block generator."""
    return gerar_ruido_chuva(tamanho, taxa_amostragem, intensidade_escala)

if __name__ == "__main__":
    main()
