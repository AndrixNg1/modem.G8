"""Modulation FSK binaire CPFSK du module 2, phase 1 (sans démodulation)."""
import numpy as np
from scipy.signal import butter, sosfiltfilt
from config import AMPLITUDE, FE


def moduler(bits, f0, f1, R, fe=FE) -> np.ndarray:
    """Retourne une FSK mono à phase continue, amplitude fixe 0,5.

    Chaque bit occupe exactement ``fe / R`` échantillons. La phase est
    cumulée échantillon par échantillon : elle n'est jamais remise à zéro
    à une frontière de bit.
    """
    if not all(isinstance(v, (int, np.integer)) and v > 0 for v in (f0, f1, R, fe)):
        raise ValueError("f0, f1, R et fe doivent être des entiers positifs")
    if f0 >= fe / 2 or f1 >= fe / 2 or f0 == f1:
        raise ValueError("Fréquences invalides vis-à-vis de Nyquist")
    if fe % R:
        raise ValueError("fe doit être divisible par R pour une durée de bit entière")
    valeurs = list(bits)
    if any(bit not in (0, 1) for bit in valeurs):
        raise ValueError("Les bits doivent valoir 0 ou 1")
    if not valeurs:
        return np.array([], dtype=np.float64)
    freqs = np.repeat(np.where(np.asarray(valeurs, dtype=np.int8) == 0, f0, f1), fe // R)
    increment = 2 * np.pi * freqs / fe
    phase = np.empty(len(freqs), dtype=np.float64)
    phase[0] = 0.0
    phase[1:] = np.cumsum(increment[:-1])
    return AMPLITUDE * np.sin(phase)


def energie(fenetre, f, fe):
    """Énergie de corrélation I/Q à la fréquence ``f``.

    ``E(f)=(Σx cos(2πfn/Fe))²+(Σx sin(2πfn/Fe))²``. Les deux
    quadratures rendent la mesure indépendante de la phase du signal.
    Une fenêtre vide ou silencieuse a une énergie nulle.
    """
    x = np.asarray(fenetre, dtype=np.float64)
    if x.ndim != 1 or f <= 0 or fe <= 0 or f >= fe / 2:
        raise ValueError("Fenêtre 1D et fréquence valide sous Nyquist requises")
    if not x.size:
        return 0.0
    n = np.arange(x.size)
    i = np.dot(x, np.cos(2 * np.pi * f * n / fe))
    q = np.dot(x, np.sin(2 * np.pi * f * n / fe))
    return float(i * i + q * q)


def demoduler(signal, f0, f1, R, fe=FE, retourner_infos=False):
    """Démodule des bits déjà alignés; les restes partiels sont signalés.

    La synchronisation temporelle relève de :func:`synchroniser_porteuse`.
    Avec ``retourner_infos=True``, renvoie aussi les décisions ambiguës et
    les paires d'énergies ``(E0, E1)`` pour les mesures/diagnostics.
    """
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or not all(isinstance(v, (int, np.integer)) and v > 0 for v in (f0, f1, R, fe)) or fe % R:
        raise ValueError("Signal mono, paramètres positifs et fe divisible par R requis")
    taille = fe // R
    incomplet = len(x) % taille
    bits, ambigus, energies = [], [], []
    for debut in range(0, len(x) - incomplet, taille):
        e0, e1 = energie(x[debut:debut + taille], f0, fe), energie(x[debut:debut + taille], f1, fe)
        bits.append(int(e1 > e0)); energies.append((e0, e1))
        ambigus.append((max(e0, e1) == 0) or abs(e1 - e0) / (e0 + e1) < .10)
    if retourner_infos:
        return bits, ambigus, energies, incomplet
    return bits


def pretraiter_signal(signal, f0, f1, fe=FE):
    """Retire le continu et le bruit hors bande sans modifier le signal brut."""
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("Signal mono fini requis")
    if not (0 < f0 < f1 < fe / 2):
        raise ValueError("Fréquences valides sous Nyquist requises")
    if not x.size:
        return x.copy()

    x = x - float(np.mean(x))
    if f0 >= 7000 and f1 <= 8000:
        bas, haut = 7000.0, 8000.0
    else:
        bas, haut = max(100.0, f0 - 270.0), min(fe / 2 - 100.0, f1 + 270.0)
    if len(x) < 32 or haut <= bas:
        return x
    sos = butter(4, (bas, haut), btype="bandpass", fs=fe, output="sos")
    return sosfiltfilt(sos, x)


def estimer_seuil_activite(signal, fe=FE):
    """Estime le niveau de bruit et un seuil d'activité depuis des blocs de 10 ms."""
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or fe <= 0:
        raise ValueError("Signal mono et fréquence d'échantillonnage valide requis")
    taille = max(1, fe // 100)
    blocs = [x[i:i + taille] for i in range(0, len(x) - taille + 1, taille)]
    if not blocs:
        return 1e-10, 0.0
    niveaux = np.sqrt(np.mean(np.asarray(blocs) ** 2, axis=1))
    q10, q90, q99 = np.quantile(niveaux, (.10, .90, .99))
    if q99 <= 1.5 * max(q10, 1e-10):
        seuil = q10 * .25
    elif q99 > 4 * max(q10, 1e-10):
        seuil = max(q10 * 3, q99 * .08)
    else:
        seuil = q99 * 1.5
    seuil = max(seuil, 1e-10)
    return float(seuil), float(q10)


def _energies_glissantes(signal, f, fe, taille):
    """Corrélations I/Q de toutes les fenêtres possibles (pour synchro)."""
    n = np.arange(len(signal))
    melange = np.asarray(signal, dtype=np.float64) * np.exp(-2j * np.pi * f * n / fe)
    cumul = np.concatenate(([0j], np.cumsum(melange)))
    sommes = cumul[taille:] - cumul[:-taille]
    return np.abs(sommes) ** 2


def synchroniser_porteuse(signal, f0, f1, R, fe=FE, min_porteuse_bits=1):
    """Trouve le premier start `0` après une porteuse `1`, même avec silence.

    Les fenêtres sont balayées échantillon par échantillon, donc le début du
    WAV n'a pas à coïncider avec une frontière de 160 échantillons. La durée
    exacte de la porteuse n'est pas supposée : seul un ou plusieurs bits f1
    immédiatement précédant le start sont exigés.
    """
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or fe % R or min_porteuse_bits < 1:
        raise ValueError("Signal mono et paramètres de synchronisation invalides")
    taille = fe // R
    if len(x) < (min_porteuse_bits + 1) * taille:
        raise ValueError("Signal trop court pour contenir porteuse et start")
    e0 = _energies_glissantes(x, f0, fe, taille); e1 = _energies_glissantes(x, f1, fe, taille)
    niveau = np.sqrt(e0 + e1)
    q10, q90 = np.quantile(niveau, (.10, .90))
    seuil = max(q10 * .25, np.finfo(float).eps)
    candidats = np.flatnonzero((e0 > 1.15 * e1) & (niveau > seuil))
    for candidat in candidats:
        if candidat < min_porteuse_bits * taille:
            continue
        indices = candidat - np.arange(1, min_porteuse_bits + 1) * taille
        if (np.all(niveau[indices] > seuil)
                and np.all(e1[indices] > 1.15 * e0[indices])):
            bas = max(min_porteuse_bits * taille, candidat - taille)
            haut = min(len(e0) - taille, candidat + taille)
            essais = np.arange(bas, haut + 1)
            score = np.zeros(len(essais))
            epsilon = np.finfo(float).eps
            for k in range(1, min_porteuse_bits + 1):
                precedente = essais - k * taille
                score += np.log((e1[precedente] + epsilon) / (e0[precedente] + epsilon))
            score += np.log((e0[essais] + epsilon) / (e1[essais] + epsilon))
            approx = int(essais[np.argmax(score)])
            rayon = taille // 2
            debuts_fines = range(max(min_porteuse_bits * taille, approx - rayon),
                                 min(len(x) - taille, approx + rayon) + 1)
            erreurs = []
            for debut_fin in debuts_fines:
                erreur = 0.0
                for frequence, debut_fenetre, fin_fenetre in (
                    (f1, debut_fin - min_porteuse_bits * taille, debut_fin),
                    (f0, debut_fin, debut_fin + taille),
                ):
                    n = np.arange(debut_fenetre, fin_fenetre)
                    matrice = np.column_stack((
                        np.cos(2 * np.pi * frequence * n / fe),
                        np.sin(2 * np.pi * frequence * n / fe),
                    ))
                    coefficients = np.linalg.lstsq(
                        matrice, x[debut_fenetre:fin_fenetre], rcond=None)[0]
                    residu = x[debut_fenetre:fin_fenetre] - matrice @ coefficients
                    erreur += float(np.mean(residu ** 2))
                erreurs.append(erreur)
            minimum = min(erreurs)
            tol = max(np.finfo(float).eps, abs(minimum) * 1e-5)
            return int(debuts_fines[next(i for i, err in enumerate(erreurs)
                                          if err <= minimum + tol)])
    raise ValueError("Porteuse f1 suivie d'un bit de start f0 introuvable")


def ajouter_bruit(signal, sb_db, seed=None, retourner_infos=False):
    """Ajoute un AWGN sans écrêtage et, optionnellement, ses métadonnées.

    ``sb_db`` est le rapport puissance signal/bruit demandé. La fonction ne
    modifie jamais l'entrée. Avec ``retourner_infos=True``, les puissances et
    le S/B effectivement mesuré sur ce tirage sont renvoyés avec le signal.
    """
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all() or not np.isscalar(sb_db) or not np.isfinite(sb_db):
        raise ValueError("Signal mono fini et S/B dB fini requis")
    if not x.size:
        raise ValueError("Impossible de bruiter un signal vide")
    ps = float(np.mean(x ** 2))
    if ps == 0:
        raise ValueError("Impossible de définir un S/B pour un signal silencieux")
    rapport = 10.0 ** (float(sb_db) / 10.0)
    pb_cible = ps / rapport
    bruit = np.random.default_rng(seed).normal(0.0, np.sqrt(pb_cible), size=x.shape)
    pb = float(np.mean(bruit ** 2))
    sb_mesure = float(10.0 * np.log10(ps / pb))
    perturbe = x + bruit
    if retourner_infos:
        return perturbe, {"puissance_signal": ps, "puissance_bruit": pb,
                           "sigma": float(np.sqrt(pb_cible)), "sb_db_mesure": sb_mesure}
    return perturbe
