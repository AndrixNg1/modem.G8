"""Tonalité de contrôle du module 1, sans modulation ni expérience physique."""
from pathlib import Path
import importlib
import sys
import numpy as np
from scipy.io import wavfile
from config import AMPLITUDE, FE


def environnement(lister_peripheriques=False):
    """Affiche les bibliothèques disponibles; ne nécessite aucun périphérique."""
    print("Python :", sys.version.split()[0])
    ok = True
    for nom in ("numpy", "scipy", "sounddevice", "matplotlib"):
        try:
            module = importlib.import_module(nom)
            print(f"{nom} : OK", getattr(module, "__version__", ""))
        except (ImportError, OSError) as exc:
            print(f"{nom} : indisponible - {exc}")
            ok = False
    if lister_peripheriques:
        try:
            import sounddevice as sd
            print(sd.query_devices())
        except (ImportError, OSError) as exc:
            print("Périphériques audio non disponibles :", exc)
    print("Audacity et toute écoute restent des validations manuelles.")
    return ok


def generer_tonalite(chemin, duree=2.0, amplitude=AMPLITUDE, frequence=1000, fe=FE):
    """Écrit un WAV PCM mono et retourne ses mesures numériques."""
    if duree <= 0 or fe <= 0 or frequence <= 0 or not 0 < amplitude <= 1:
        raise ValueError("Durée, fréquence, Fe ou amplitude invalides")
    echantillons = int(round(duree * fe))
    temps = np.arange(echantillons, dtype=np.float64) / fe
    signal = amplitude * np.sin(2 * np.pi * frequence * temps)
    chemin = Path(chemin); chemin.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(chemin, fe, signal.astype(np.float32))
    dominant = float(np.fft.rfftfreq(echantillons, 1 / fe)[np.argmax(np.abs(np.fft.rfft(signal))[1:]) + 1])
    return {"chemin": str(chemin), "fe": fe, "echantillons": echantillons,
            "duree": echantillons / fe, "amplitude_max": float(np.max(np.abs(signal))),
            "ecretage": bool(np.max(np.abs(signal)) >= 1), "frequence_dominante": dominant}


def jouer_tonalite(chemin):
    """Lecture facultative : ne constitue pas une preuve d'écoute physique."""
    import sounddevice as sd
    fe, signal = wavfile.read(chemin)
    sd.play(signal, fe); sd.wait()

