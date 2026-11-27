"""Perturbations acoustiques *synthétiques* et reproductibles pour le modem.

Les fonctions retournent un nouveau tableau et ne représentent jamais une
capture physique. Les niveaux sont relatifs au RMS du signal utile.
"""
from __future__ import annotations
import numpy as np


def _signal(x):
    y = np.asarray(x, dtype=float)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError("Signal mono fini requis")
    return y


def _rms(x): return float(np.sqrt(np.mean(np.asarray(x, float) ** 2))) if len(x) else 0.


def _niveau(signal, db):
    return _rms(signal) * 10 ** (float(db) / 20)


def bruit_blanc(signal, sb_db, seed=0):
    x = _signal(signal); rng = np.random.default_rng(seed)
    return x + rng.normal(0, _niveau(x, -sb_db), len(x))


def bruit_rose(signal, sb_db, seed=0):
    """Bruit 1/sqrt(f), normalisé à la puissance demandée."""
    x = _signal(signal); rng = np.random.default_rng(seed)
    if not len(x): return x.copy()
    freqs = np.fft.rfftfreq(len(x)); phases = rng.normal(size=len(freqs)) + 1j*rng.normal(size=len(freqs))
    phases[0] = 0; phases[1:] /= np.sqrt(freqs[1:])
    bruit = np.fft.irfft(phases, len(x)); bruit *= _niveau(x, -sb_db) / max(_rms(bruit), np.finfo(float).eps)
    return x + bruit


def ronflement(signal, fe, db=-20, fondamentale=50, harmoniques=3):
    x = _signal(signal); t = np.arange(len(x)) / fe; niveau = _niveau(x, db)
    bruit = sum(np.sin(2*np.pi*fondamentale*k*t) / k for k in range(1, harmoniques + 1))
    return x + bruit * niveau / max(_rms(bruit), np.finfo(float).eps)


def tonalite(signal, fe, frequence, db=-20):
    x = _signal(signal); t = np.arange(len(x)) / fe
    return x + _niveau(x, db) * np.sqrt(2) * np.sin(2*np.pi*frequence*t)


def impulsions(signal, db=-8, taux=0.0005, seed=0):
    x = _signal(signal); rng = np.random.default_rng(seed); y = x.copy()
    n = max(1, round(len(x) * taux)) if len(x) else 0
    if n: y[rng.choice(len(x), n, replace=False)] += _niveau(x, db) * rng.choice((-1, 1), n)
    return y


def attenuation(signal, facteur=.5):
    if not 0 <= facteur <= 1: raise ValueError("facteur dans [0, 1] requis")
    return _signal(signal) * facteur


def echo(signal, fe, retards_ms=(10,), amplitudes=(.3,)):
    x = _signal(signal)
    if len(retards_ms) != len(amplitudes): raise ValueError("retards et amplitudes incompatibles")
    y = x.copy()
    for retard_ms, amplitude in zip(retards_ms, amplitudes):
        d = round(float(retard_ms) * fe / 1000)
        if d > 0 and d < len(x): y[d:] += float(amplitude) * x[:-d]
    return y


def derive_horloge(signal, facteur=1.01):
    """Ré-échantillonnage déterministe, représentant une horloge décalée."""
    x = _signal(signal)
    if facteur <= 0: raise ValueError("facteur positif requis")
    positions = np.arange(0, len(x), facteur)
    return np.interp(positions, np.arange(len(x)), x) if len(x) else x.copy()


def autre_modem(signal, interferent, rapport_db=-10):
    x, z = _signal(signal), _signal(interferent)
    z = np.resize(z, len(x)); z *= _niveau(x, rapport_db) / max(_rms(z), np.finfo(float).eps)
    return x + z


def appliquer(signal, fe, perturbations, seed=0):
    """Applique une liste de dictionnaires, ex. ``[{"type":"echo",...}]``."""
    y = _signal(signal).copy()
    for i, spec in enumerate(perturbations):
        spec = dict(spec); kind = spec.pop("type")
        if kind == "blanc": y = bruit_blanc(y, seed=seed+i, **spec)
        elif kind == "rose": y = bruit_rose(y, seed=seed+i, **spec)
        elif kind == "ronflement": y = ronflement(y, fe, **spec)
        elif kind == "tonalite": y = tonalite(y, fe, **spec)
        elif kind == "impulsions": y = impulsions(y, seed=seed+i, **spec)
        elif kind == "attenuation": y = attenuation(y, **spec)
        elif kind == "echo": y = echo(y, fe, **spec)
        elif kind == "derive": y = derive_horloge(y, **spec)
        else: raise ValueError(f"Perturbation inconnue : {kind}")
    return y
