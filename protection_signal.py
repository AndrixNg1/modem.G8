"""Protections DSP optionnelles pour la réception FSK.

Les fonctions de ce module ne modifient jamais leur entrée.  Elles restent
volontairement conservatrices : aucune décision de bit ni correction vers un
CRC attendu n'est faite ici.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, welch


BANDES = {
    "G8": (7000.0, 8000.0),
    "G8_acoustique": (1500.0, 3900.0),
    "bell103": (700.0, 1650.0),
}


def _mono(signal):
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("Signal mono fini requis")
    return x


def supprimer_composante_continue(signal):
    """Retourne le signal centré; un signal vide est accepté."""
    x = _mono(signal)
    return x - (float(np.mean(x)) if x.size else 0.0)


def bande_profil(f0, f1, fe, nom_profil=None):
    """Bande expérimentale documentée, ou bande prudente pour un profil tiers."""
    if nom_profil in BANDES:
        return BANDES[nom_profil]
    return max(100.0, f0 - 270.0), min(fe / 2 - 100.0, f1 + 270.0)


def filtre_passe_bande(signal, fe, bas, haut, ordre=4, temps_reel=False):
    """Filtre Butterworth SOS; ``sosfilt`` est réservé au flux temps réel."""
    x = _mono(signal)
    if not (fe > 0 and 0 < bas < haut < fe / 2 and ordre in (2, 4, 6)):
        raise ValueError("Bande sous Nyquist et ordre 2, 4 ou 6 requis")
    if not x.size:
        return x.copy()
    sos = butter(ordre, (bas, haut), btype="bandpass", fs=fe, output="sos")
    if temps_reel:
        return sosfilt(sos, x)
    # sosfiltfilt ne peut pas traiter de très courts fragments.
    padlen = 3 * (2 * len(sos) + 1)
    return sosfiltfilt(sos, x) if len(x) > padlen else sosfilt(sos, x)


def detecter_impulsions(signal, seuil_mad=8.0):
    """Repère clics isolés et saturation persistante sans confondre une CPFSK."""
    x = _mono(signal)
    if not x.size:
        return {"impulsions": np.zeros(0, dtype=bool), "saturation": False,
                "echantillons_satures": 0}
    mediane = float(np.median(x)); mad = float(np.median(np.abs(x - mediane)))
    limite = max(1e-10, seuil_mad * 1.4826 * mad)
    pics = np.abs(x - mediane) > limite
    isoles = np.zeros(len(x), dtype=bool)
    if len(x) >= 3:
        isoles[1:-1] = pics[1:-1] & ~pics[:-2] & ~pics[2:]
    ecretes = int(np.count_nonzero(np.abs(x) >= .999))
    return {"impulsions": isoles, "saturation": ecretes >= max(3, int(.001 * len(x))),
            "echantillons_satures": ecretes}


def reduire_bruit(signal, impulsions=None):
    """Réduit uniquement les clics isolés; pas de débruitage vocal/spectral."""
    x = _mono(signal).copy()
    masque = detecter_impulsions(x)["impulsions"] if impulsions is None else np.asarray(impulsions, bool)
    if masque.shape != x.shape:
        raise ValueError("Masque d'impulsions incompatible")
    indices = np.flatnonzero(masque)
    for i in indices:
        if 0 < i < len(x) - 1:
            x[i] = (x[i - 1] + x[i + 1]) / 2
    return x


def estimer_bruit(signal, fe, reference=None):
    """Estime RMS, puissance et DSP d'une référence explicitement sans porteuse.

    Sans ``reference``, aucun niveau est inventé : ``estimable`` vaut False.
    """
    _mono(signal)
    if reference is None:
        return {"estimable": False, "raison": "référence de bruit absente", "rms": None,
                "puissance": None, "frequences": np.array([]), "dsp": np.array([])}
    bruit = _mono(reference)
    if not bruit.size:
        return {"estimable": False, "raison": "référence de bruit vide", "rms": None,
                "puissance": None, "frequences": np.array([]), "dsp": np.array([])}
    nperseg = min(len(bruit), max(32, min(fe, 4096)))
    freqs, dsp = welch(bruit, fs=fe, nperseg=nperseg, scaling="density")
    puissance = float(np.mean(bruit ** 2))
    return {"estimable": True, "raison": None, "rms": float(np.sqrt(puissance)),
            "puissance": puissance, "frequences": freqs, "dsp": dsp}


def mesurer_sb(signal, bruit=None, puissance_bruit=None):
    """S/B en dB, calculable seulement avec une référence de bruit."""
    x = _mono(signal)
    pb = float(np.mean(_mono(bruit) ** 2)) if bruit is not None else puissance_bruit
    ps = float(np.mean(x ** 2)) if x.size else 0.0
    if pb is None or pb <= 0 or ps <= 0:
        return None
    return float(10 * np.log10(ps / pb))


def calculer_confiance(e0, e1, epsilon=np.finfo(float).eps):
    """Confiance normalisée non signée d'une décision FSK."""
    e0, e1 = np.asarray(e0, float), np.asarray(e1, float)
    return np.abs(e1 - e0) / (e1 + e0 + epsilon)


def egaliser_frequences(energies_f0, energies_f1):
    """Retourne les gains relatifs; sans référence alternée, ne rien compenser.

    Le récepteur 8N1 actuel n'expose pas une séquence alternée connue, donc
    l'appelant doit fournir des mesures déjà étiquetées. Cette fonction est
    disponible pour une campagne expérimentale, pas activée arbitrairement.
    """
    e0, e1 = np.asarray(energies_f0, float), np.asarray(energies_f1, float)
    if not e0.size or not e1.size or np.any(e0 < 0) or np.any(e1 < 0):
        return {"gain_f0": 1.0, "gain_f1": 1.0, "applicable": False}
    m0, m1 = float(np.median(e0)), float(np.median(e1))
    if m0 <= 0 or m1 <= 0:
        return {"gain_f0": 1.0, "gain_f1": 1.0, "applicable": False}
    cible = np.sqrt(m0 * m1)
    return {"gain_f0": cible / m0, "gain_f1": cible / m1, "applicable": True}


def pretraiter_signal(signal, f0, f1, fe, nom_profil=None, mode="basic", ordre=4,
                       temps_reel=False, reference_bruit=None, retourner_infos=False):
    """Pipeline unique : off, basic (continu+passe-bande), advanced (+clics)."""
    if mode not in {"off", "basic", "advanced"}:
        raise ValueError("protection attend off, basic ou advanced")
    x = _mono(signal)
    infos = {"mode": mode, "impulsions": 0, "bruit": estimer_bruit(x, fe, reference_bruit)}
    if mode == "off" or not x.size:
        resultat = x.copy()
    else:
        y = supprimer_composante_continue(x)
        if mode == "advanced":
            impulsions = detecter_impulsions(y)
            infos.update({"impulsions": int(np.count_nonzero(impulsions["impulsions"])),
                          "saturation": impulsions["saturation"]})
            y = reduire_bruit(y, impulsions["impulsions"])
        bas, haut = bande_profil(f0, f1, fe, nom_profil)
        resultat = filtre_passe_bande(y, fe, bas, haut, ordre, temps_reel)
        infos["bande"] = (bas, haut); infos["ordre"] = ordre
    return (resultat, infos) if retourner_infos else resultat
