"""Réception WAV FSK : prétraitement, synchronisation et tramage 8N1."""
from pathlib import Path
import argparse
import sys
import numpy as np
from scipy.io import wavfile
from config import FE, PROFILS
from emettre import profils
from modem_fsk import (
    energie,
    estimer_seuil_activite,
    pretraiter_signal,
    synchroniser_porteuse,
)
from audio_io import enregistrer, formater_peripheriques


def lire_wav(chemin):
    """Lit mono/stéréo; le stéréo est moyenné et l'entier mis à l'échelle."""
    fe, donnees = wavfile.read(chemin)
    x = np.asarray(donnees)
    if np.issubdtype(x.dtype, np.integer):
        maximum = max(abs(np.iinfo(x.dtype).min), np.iinfo(x.dtype).max)
        x = x.astype(np.float64) / maximum
    else:
        x = x.astype(np.float64)
    if x.ndim == 2:
        x = x.mean(axis=1)
    elif x.ndim != 1:
        raise ValueError("WAV mono ou stéréo requis")
    return int(fe), x


def _mesurer_symbole(signal, debut, periode, f0, f1, fe):
    fin = debut + periode
    if debut < 0 or fin > len(signal):
        return None
    fenetre = signal[debut:fin]
    e0, e1 = energie(fenetre, f0, fe), energie(fenetre, f1, fe)
    return e0, e1, (e1 - e0) / (e0 + e1 + np.finfo(float).eps)


def _ajuster_caractere(signal, centre, periode_nominale, f0, f1, fe, seuil, rayon=3):
    """Ajuste la phase et la période locale sur les bits start/stop et données."""
    variation = max(2, round(periode_nominale * .04))
    meilleur = None
    for periode in range(periode_nominale - variation, periode_nominale + variation + 1):
        if periode <= 0:
            continue
        for debut in range(max(0, centre - rayon), centre + rayon + 1):
            mesures = [_mesurer_symbole(signal, debut + k * periode, periode, f0, f1, fe)
                       for k in range(10)]
            if any(m is None for m in mesures):
                continue
            energies = [(m[0], m[1]) for m in mesures]
            niveaux = [np.sqrt(e0 + e1) for e0, e1 in energies]
            if niveaux[0] < seuil:
                continue
            confiances = [m[2] for m in mesures]
            score = -2 * confiances[0] + 2 * confiances[9] + .2 * np.mean(
                np.abs(confiances[1:9])) \
                - .05 * abs(periode - periode_nominale) \
                - .01 * abs(debut - centre)
            if meilleur is None or score > meilleur["score"]:
                meilleur = {
                    "debut": debut,
                    "periode": periode,
                    "energies": energies,
                    "bits": [int(e1 > e0) for e0, e1 in energies],
                    "confiances": confiances,
                    "score": float(score),
                    "niveau_start": float(niveaux[0]),
                }
    return meilleur


def _start_actif(signal, debut, periode, f0, f1, fe, seuil):
    mesure = _mesurer_symbole(signal, debut, periode, f0, f1, fe)
    return bool(mesure and np.sqrt(mesure[0] + mesure[1]) > seuil
                and mesure[0] > mesure[1])


def _chercher_reprise(signal, debut, periode, p, fe, seuil):
    borne = min(len(signal) - 10 * periode, debut + 12 * periode)
    for candidat in range(debut + periode, max(debut + periode, borne) + 1, max(1, periode // 4)):
        ajuste = _ajuster_caractere(signal, candidat, periode, p["f0"], p["f1"], fe, seuil, 1)
        if (ajuste and ajuste["confiances"][0] < -.15
                and ajuste["confiances"][9] > .15):
            return ajuste["debut"]
    return None


def recevoir_signal(signal, profil="G8", decoder_utf8=True, fe=FE, debug=False):
    """Décode une capture sans aligner les bits sur le début ni la fin du WAV."""
    p = profils(profil)
    signal = np.asarray(signal, dtype=np.float64)
    if fe != p["fe"] or fe != FE:
        raise ValueError(f"Fe WAV {fe} Hz incompatible (attendu {p['fe']} Hz)")
    if signal.ndim != 1 or not np.isfinite(signal).all():
        raise ValueError("Signal mono fini requis")
    if not np.any(np.abs(signal) > 1e-12):
        raise ValueError("Signal silencieux : aucune transmission détectée")

    brut = signal.copy()
    traite = pretraiter_signal(brut, p["f0"], p["f1"], fe)
    seuil, bruit = estimer_seuil_activite(traite, fe)
    periode_nominale = fe // p["R"]
    if debug:
        print(f"Prétraitement {p['nom']}: RMS bas de référence={bruit:.6g}, "
              f"seuil porteuse={seuil:.6g}; WAV brut conservé.", file=sys.stderr)
    debut = synchroniser_porteuse(
        # L'émetteur annonce chaque trame avec f1. Exiger une large
        # part de ce préambule empêche une brève
        # fluctuation f0 au milieu de l'annonce d'être prise pour un start.
        traite, p["f0"], p["f1"], p["R"], fe,
        min_porteuse_bits=max(1, round(.75 * p["annonce_secondes"] * p["R"])))
    if debug:
        print(f"Porteuse f1 détectée; début estimé du start={debut} "
              f"({debut / fe:.6f} s).", file=sys.stderr)

    octets = bytearray()
    bits_recus = []
    energies_recues = []
    debuts_caracteres = []
    erreurs_tramage = []
    position = debut
    periode_estimee = float(periode_nominale)
    caracteres = 0
    while True:
        centre = round(position)
        restant = len(traite) - centre
        # La synchronisation peut être décalée de quelques échantillons :
        # laisser l'ajustement local examiner le dernier caractère avant de
        # conclure à une troncature.
        tolerance_fin = max(24, round(.04 * periode_nominale))
        if restant < 10 * periode_nominale - tolerance_fin:
            # Une erreur de tramage déjà relevée reste l'erreur utile à
            # rapporter, même si la recherche de reprise aboutit près de la
            # fin de la capture.
            if erreurs_tramage:
                break
            if _start_actif(traite, centre, periode_nominale, p["f0"], p["f1"], fe, seuil):
                raise ValueError(
                    f"Transmission tronquée avant le caractère {caracteres + 1}: "
                    f"{max(0, restant)} échantillons après le début du bit de start")
            break

        ajuste = _ajuster_caractere(
            traite, centre, round(periode_estimee), p["f0"], p["f1"], fe, seuil)
        if ajuste is None:
            if _start_actif(traite, centre, periode_nominale, p["f0"], p["f1"], fe, seuil):
                raise ValueError(
                    f"Transmission tronquée avant le caractère {caracteres + 1}: "
                    f"{max(0, restant)} échantillons après le début du bit de start")
            break
        if ajuste["confiances"][0] >= -.05:
            break

        bits = ajuste["bits"]
        energies = ajuste["energies"]
        confiance_stop = ajuste["confiances"][9]
        position_stop = ajuste["debut"] + 9 * ajuste["periode"]
        caracteres += 1
        debuts_caracteres.append(ajuste["debut"])
        bits_recus.extend(bits)
        energies_recues.extend(energies)

        if debug:
            print(f"Caractère {caracteres}: start={ajuste['debut']}, "
                  f"stop={position_stop}, période={ajuste['periode']} échantillons, "
                  f"bits={''.join(map(str, bits))}, "
                  f"confiance_stop={confiance_stop:.3f}.", file=sys.stderr)

        if bits[9] != 1:
            reprise = _chercher_reprise(
                traite, ajuste["debut"], ajuste["periode"], p, fe, seuil)
            detail = (
                f"Caractère {caracteres}, position={ajuste['debut']}, "
                f"bits={bits}, E0/E1 stop={energies[9][0]:.6g}/"
                f"{energies[9][1]:.6g}, confiance={confiance_stop:.3f}, "
                f"start={ajuste['debut']}, stop={position_stop}; "
                f"bit de stop 8N1 invalide"
            )
            if reprise is not None:
                detail += f"; resynchronisation possible à {reprise} (donnée précédente invalide)"
            else:
                detail += "; aucune reprise 8N1 valide détectée"
            if debug:
                print(detail, file=sys.stderr)
            erreurs_tramage.append(detail)
            if reprise is None:
                raise ValueError(f"Erreur de tramage 8N1 : {detail}")
            position = reprise
            continue

        octet = sum(bits[i + 1] << i for i in range(8))
        octets.append(octet)
        periode_estimee = (periode_estimee * (caracteres - 1) + ajuste["periode"]) / caracteres
        position = ajuste["debut"] + 10 * periode_estimee

    if not caracteres:
        raise ValueError("Porteuse détectée mais aucun caractère 8N1 complet trouvé")
    if erreurs_tramage:
        raise ValueError(
            "Erreur de tramage 8N1; données invalides/perdues après resynchronisation : "
            + " | ".join(erreurs_tramage)
        )

    texte = None
    if decoder_utf8:
        try:
            texte = bytes(octets).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Erreur de décodage UTF-8 : {exc}") from exc
    ambigus = sum(abs(e1 - e0) / (e0 + e1 + np.finfo(float).eps) < .10
                  for e0, e1 in energies_recues)
    return {
        "profil": p["nom"],
        "debut_echantillon": debut,
        "fin_echantillon": round(position),
        "debits_caracteres": debuts_caracteres,
        "bits": bits_recus,
        "ambigus": ambigus,
        "energies": energies_recues,
        "octets": bytes(octets),
        "texte": texte,
    }


def recevoir_wav(chemin, profil="G8", decoder_utf8=True, debug=False):
    fe, signal = lire_wav(chemin)
    return recevoir_signal(signal, profil, decoder_utf8, fe, debug)


def main():
    parser = argparse.ArgumentParser(description="Récepteur WAV CPFSK + 8N1")
    parser.add_argument("wav", nargs="?")
    parser.add_argument("--profil", choices=tuple(PROFILS), default="G8")
    parser.add_argument("--sortie-octets", help="fichier de sauvegarde des octets reçus")
    parser.add_argument("--binaire", action="store_true", help="ne pas interpréter les octets comme UTF-8")
    parser.add_argument("--micro", action="store_true", help="acquérir puis décoder (pas une réception temps réel)")
    parser.add_argument("--duree", type=float, default=10.0)
    parser.add_argument("--device")
    parser.add_argument("--enregistrement", help="WAV brut acquis")
    parser.add_argument("--liste-peripheriques", action="store_true")
    parser.add_argument("--debug", action="store_true", help="afficher les mesures et la synchronisation")
    a = parser.parse_args()
    if a.liste_peripheriques:
        print(formater_peripheriques())
        return
    if a.micro and a.wav:
        parser.error("choisir WAV ou --micro, pas les deux")
    if not a.micro and not a.wav:
        parser.error("WAV ou --micro requis")
    try:
        if a.micro:
            signal, stats = enregistrer(a.duree, FE, a.device, a.enregistrement)
            print(f"acquisition : amplitude={stats['amplitude_max']:.3f}, écrêtage={stats['ecretage']}")
            if stats["ecretage"]:
                raise ValueError(
                    "Acquisition saturée : réduire --volume à l'émission, "
                    "le volume système ou le gain du microphone avant de décoder"
                )
            resultat = recevoir_signal(signal, a.profil, not a.binaire, FE, a.debug)
        else:
            resultat = recevoir_wav(a.wav, a.profil, not a.binaire, a.debug)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    if a.sortie_octets:
        Path(a.sortie_octets).write_bytes(resultat["octets"])
    if resultat["texte"] is not None:
        print(resultat["texte"])
    else:
        print(resultat["octets"].hex())
    print(f"caractères={len(resultat['octets'])}, départ={resultat['debut_echantillon']}, "
          f"fin={resultat['fin_echantillon']}, ambigus={resultat['ambigus']}")


if __name__ == "__main__":
    main()
