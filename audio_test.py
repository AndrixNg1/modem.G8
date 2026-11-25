"""Vérification de l'environnement et tonalité 1 kHz (pas un modem FSK)."""
from pathlib import Path
import importlib
import math
import struct
import sys
import wave


def environnement():
    print('Python :', sys.version.split()[0])
    ok = True
    for module in ('numpy', 'scipy', 'sounddevice', 'matplotlib'):
        try:
            m = importlib.import_module(module)
            print(module, ': OK', getattr(m, '__version__', ''))
        except (ImportError, OSError) as e:
            print(module, ': non disponible -', e)
            ok = False
    print('Audacity : vérifier manuellement son ouverture.')
    return ok


def tonalite(chemin, jouer=False):
    fe = 48000
    samples = [int(0.15 * 32767 * math.sin(2*math.pi*1000*i/fe)) for i in range(fe)]
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(chemin), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fe)
        f.writeframes(struct.pack('<'+'h'*len(samples), *samples))
    print('WAV 1 kHz, 1 seconde, 48 kHz :', chemin)
    if jouer:
        import numpy as np
        import sounddevice as sd
        sd.play(np.array(samples, dtype=np.float32)/32768, fe)
        sd.wait()
        print('Lecture terminée. Confirmer à l’oreille / avec le micro et Audacity.')
    return chemin
