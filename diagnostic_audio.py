"""Mesures et graphiques de diagnostic pour un enregistrement audio réel."""
from pathlib import Path
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import welch
from emettre import profils
from modem_fsk import energie, estimer_seuil_activite, pretraiter_signal, synchroniser_porteuse


def lire_wav(chemin):
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
    if not np.isfinite(x).all():
        raise ValueError("Le WAV contient des échantillons non finis")
    return int(fe), x


def analyser_signal(signal, fe, profil="G8"):
    p = profils(profil)
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or fe != p["fe"]:
        raise ValueError("Signal mono et fréquence d'échantillonnage du profil requis")
    if not x.size:
        raise ValueError("WAV vide")

    filtre = pretraiter_signal(x, p["f0"], p["f1"], fe)
    taille = max(1, fe // 100)
    debuts = np.arange(0, len(x), taille)
    temps = debuts / fe
    rms_bande = np.empty(len(debuts))
    e0 = np.empty(len(debuts))
    e1 = np.empty(len(debuts))
    for i, debut in enumerate(debuts):
        bloc = filtre[debut:min(debut + taille, len(filtre))]
        rms_bande[i] = np.sqrt(np.mean(bloc ** 2))
        e0[i] = energie(bloc, p["f0"], fe)
        e1[i] = energie(bloc, p["f1"], fe)

    seuil, bruit_global = estimer_seuil_activite(filtre, fe)
    debut_porteuse = None
    erreur_detection = None
    try:
        debut_porteuse = synchroniser_porteuse(
            filtre, p["f0"], p["f1"], p["R"], fe, min_porteuse_bits=24)
    except ValueError as exc:
        erreur_detection = str(exc)

    debut_donnees = debut_porteuse
    debut_porteuse = None
    if debut_donnees is not None and rms_bande.size:
        actifs = np.flatnonzero(rms_bande > seuil)
        actifs_avant_start = actifs[temps[actifs] <= debut_donnees / fe]
        if actifs_avant_start.size:
            debut_porteuse = int(debuts[actifs_avant_start[0]])
        actifs = actifs[temps[actifs] >= debut_donnees / fe]
        if actifs.size:
            fin_transmission = int(min(len(x), debuts[actifs[-1]] + taille))
        else:
            fin_transmission = None
        avant = rms_bande[temps < (debut_porteuse / fe if debut_porteuse is not None else 0)]
        bruit_avant = float(np.median(avant)) if avant.size else None
    else:
        debut_donnees = None
        fin_transmission = None
        bruit_avant = None

    nperseg = min(len(x), max(256, fe))
    frequences, densite = welch(x, fe, nperseg=nperseg, scaling="density")
    pas = fe / nperseg
    energie_f0 = float(np.sum(densite[np.abs(frequences - p["f0"]) <= 2 * pas]) * pas)
    energie_f1 = float(np.sum(densite[np.abs(frequences - p["f1"]) <= 2 * pas]) * pas)
    bande_spectre = (frequences >= 0) & (frequences <= fe / 2)
    pics = np.argsort(densite[bande_spectre])[-10:][::-1]
    pics_hz = frequences[bande_spectre][pics]
    pics_db = 10 * np.log10(np.maximum(densite[bande_spectre][pics], np.finfo(float).tiny))
    bande_g8 = (frequences >= p["f0"] - 400) & (frequences <= p["f1"] + 400)
    pics_g8 = np.argsort(densite[bande_g8])[-5:][::-1]
    pics_g8_hz = frequences[bande_g8][pics_g8]
    pics_g8_db = 10 * np.log10(
        np.maximum(densite[bande_g8][pics_g8], np.finfo(float).tiny))

    return {
        "profil": p,
        "fe": fe,
        "duree": len(x) / fe,
        "echantillons": len(x),
        "amplitude_max": float(np.max(np.abs(x))),
        "rms": float(np.sqrt(np.mean(x ** 2))),
        "composante_continue": float(np.mean(x)),
        "frequences": frequences,
        "densite_spectrale": densite,
        "pics_spectraux": list(zip(pics_hz.tolist(), pics_db.tolist())),
        "pics_bande_utile": list(zip(pics_g8_hz.tolist(), pics_g8_db.tolist())),
        "energie_f0": energie_f0,
        "energie_f1": energie_f1,
        "temps_blocs": temps,
        "rms_bande": rms_bande,
        "energie_blocs_f0": e0,
        "energie_blocs_f1": e1,
        "seuil_activite": seuil,
        "bruit_global_estime": bruit_global,
        "bruit_avant_transmission": bruit_avant,
        "debut_porteuse": debut_porteuse,
        "debut_donnees": debut_donnees,
        "fin_transmission": fin_transmission,
        "erreur_detection": erreur_detection,
        "signal_brut": x,
    }


def _creer_graphiques(mesures, sortie):
    sortie = Path(sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    x = mesures["signal_brut"]
    fe = mesures["fe"]
    f0, f1 = mesures["profil"]["f0"], mesures["profil"]["f1"]

    pas = max(1, len(x) // 150000)
    t = np.arange(0, len(x), pas) / fe
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t, x[::pas], linewidth=.5)
    ax.set(title="Signal WAV brut reçu", xlabel="Temps (s)", ylabel="Amplitude")
    ax.grid(True, alpha=.25)
    fig.tight_layout()
    fig.savefig(sortie / "signal_recu.png", dpi=150)
    plt.close(fig)

    freqs, densite = mesures["frequences"], mesures["densite_spectrale"]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(freqs, 10 * np.log10(np.maximum(densite, np.finfo(float).tiny)), linewidth=.7)
    ax.axvline(f0, color="tab:orange", linestyle="--", label=f"f0 {f0} Hz")
    ax.axvline(f1, color="tab:red", linestyle="--", label=f"f1 {f1} Hz")
    ax.set(xlim=(0, fe / 2), title="Spectre de puissance du WAV brut",
           xlabel="Fréquence (Hz)", ylabel="Densité (dB/Hz)")
    ax.grid(True, alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(sortie / "spectre_recu.png", dpi=150)
    plt.close(fig)

    temps = mesures["temps_blocs"]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(temps, mesures["energie_blocs_f0"], label=f"Energie f0 ({f0} Hz)")
    ax.plot(temps, mesures["energie_blocs_f1"], label=f"Energie f1 ({f1} Hz)")
    ax.set(title="Energie de corrélation par bloc de 10 ms", xlabel="Temps (s)", ylabel="Energie")
    ax.grid(True, alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(sortie / "energie_f0_f1.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(temps, mesures["rms_bande"], label="RMS après passe-bande")
    ax.axhline(mesures["seuil_activite"], color="tab:red", linestyle="--",
               label="Seuil d'activité estimé")
    if mesures["debut_porteuse"] is not None:
        ax.axvline(mesures["debut_porteuse"] / fe, color="tab:green", linestyle=":",
                   label="Début estimé de porteuse")
    if mesures["debut_donnees"] is not None:
        ax.axvline(mesures["debut_donnees"] / fe, color="tab:purple", linestyle="--",
                   label="Début estimé des données (start)")
    ax.set(title="Détection de porteuse (décision indépendante des données d'origine)",
           xlabel="Temps (s)", ylabel="Amplitude RMS")
    ax.grid(True, alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(sortie / "detection_porteuse.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 4))
    start = mesures["debut_donnees"]
    if start is not None:
        taille_bit = fe // mesures["profil"]["R"]
        nombre = min(300, max(0, (len(x) - start) // taille_bit))
        bits, contraste, positions = [], [], []
        filtre = pretraiter_signal(x, f0, f1, fe)
        for i in range(nombre):
            debut = start + i * taille_bit
            bloc = filtre[debut:debut + taille_bit]
            if len(bloc) != taille_bit:
                break
            e0b, e1b = energie(bloc, f0, fe), energie(bloc, f1, fe)
            bits.append(int(e1b > e0b))
            contraste.append((e1b - e0b) / (e0b + e1b + np.finfo(float).eps))
            positions.append(debut / fe)
        if bits:
            ax.step(positions, bits, where="post", label="Décision observée 0/1")
            ax.plot(positions, contraste, alpha=.7, label="Confiance normalisée")
            ax.set_ylim(-1.1, 1.1)
            ax.legend()
    else:
        ax.text(.5, .5, "Aucune porteuse f1 suivie d'un start détectable",
                ha="center", va="center", transform=ax.transAxes)
    ax.set(title="Synchronisation des fenêtres binaires détectées",
           xlabel="Temps (s)", ylabel="Décision / confiance")
    ax.grid(True, alpha=.25)
    fig.tight_layout()
    fig.savefig(sortie / "synchronisation_bits.png", dpi=150)
    plt.close(fig)
    return sortie


def afficher_rapport(mesures):
    print(f"Profil : {mesures['profil']['nom']} ({mesures['profil']['f0']}/{mesures['profil']['f1']} Hz)")
    print(f"Durée : {mesures['duree']:.6f} s")
    print(f"Fréquence d'échantillonnage : {mesures['fe']} Hz")
    print(f"Amplitude maximale : {mesures['amplitude_max']:.9g}")
    print(f"Puissance RMS : {mesures['rms']:.9g}")
    print(f"Composante continue : {mesures['composante_continue']:.9g}")
    print("Pics spectraux (Hz, dB/Hz) : " +
          ", ".join(f"{f:.2f} Hz ({d:.1f} dB/Hz)" for f, d in mesures["pics_spectraux"][:8]))
    print("Pics spectraux dans la bande utile (Hz, dB/Hz) : " +
          ", ".join(f"{f:.2f} Hz ({d:.1f} dB/Hz)" for f, d in mesures["pics_bande_utile"]))
    print(f"Energie spectrale f0 : {mesures['energie_f0']:.9g}")
    print(f"Energie spectrale f1 : {mesures['energie_f1']:.9g}")
    print(f"RMS bas de référence passe-bande (q10) : {mesures['bruit_global_estime']:.9g}")
    if mesures["bruit_avant_transmission"] is None:
        if mesures["debut_donnees"] is None:
            print("Niveau du bruit avant transmission : non estimable (aucune porteuse confirmée)")
        else:
            print("Niveau du bruit avant transmission : non estimable (porteuse présente dès le début du WAV)")
    else:
        print(f"Niveau du bruit avant transmission : "
              f"{mesures['bruit_avant_transmission']:.9g} RMS")
    print(f"Position estimée du début de porteuse : "
          f"{mesures['debut_porteuse'] if mesures['debut_porteuse'] is not None else 'non détectée'}")
    print(f"Début estimé des données (bit de start) : "
          f"{mesures['debut_donnees'] if mesures['debut_donnees'] is not None else 'non détecté'}")
    print(f"Fin estimée de la transmission : "
          f"{mesures['fin_transmission'] if mesures['fin_transmission'] is not None else 'non détectée'}")
    print("FSK présent : " + ("oui, préambule f1/start confirmé" if mesures["debut_donnees"] is not None
                               else "non détectable avec le seuil et le préambule requis"))
    if mesures["erreur_detection"]:
        print(f"Détail synchronisation : {mesures['erreur_detection']}")


def main():
    parser = argparse.ArgumentParser(description="Diagnostic d'un enregistrement audio réel")
    parser.add_argument("wav", help="WAV brut à analyser")
    parser.add_argument("--profil", choices=("G8", "bell103"), default="G8")
    parser.add_argument("--sortie", help="dossier des PNG (par défaut, dossier du WAV)")
    args = parser.parse_args()
    fe, signal = lire_wav(args.wav)
    mesures = analyser_signal(signal, fe, args.profil)
    afficher_rapport(mesures)
    sortie = _creer_graphiques(mesures, args.sortie or Path(args.wav).parent)
    print(f"Graphiques écrits dans : {sortie}")


if __name__ == "__main__":
    main()
