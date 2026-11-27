"""Préparation d'une émission 8N1/FSK à phase continue, sans démodulation."""
from pathlib import Path
import argparse
import math
import numpy as np
from scipy.io import wavfile
from config import FE, PROFILS, profil as profil_config
from modem_fsk import moduler
from trame import octet_vers_bits_8N1
from audio_io import jouer, formater_peripheriques

ANNONCE_SECONDES = .3
# L'arrêt d'un flux audio peut couper les derniers échantillons.  Cette garde
# f1 est hors trame : elle laisse donc le bit stop final intégralement audible.
GARDE_FIN_SECONDES = 0.05

def profils(nom="G8"):
    return profil_config(nom)

def encoder_message(message):
    """UTF-8; chaque octet est encodé 8N1, LSB first (10 bits/octet)."""
    return [bit for octet in message.encode("utf-8") for bit in octet_vers_bits_8N1(octet)]

def _avec_annonce(donnees, p, duree=None):
    """Allonge seulement la porteuse ; ne ralentit ni ne répète le message."""
    annonce_bits = int(p["annonce_secondes"] * p["R"])
    if duree is not None:
        if not math.isfinite(duree) or duree <= 0:
            raise ValueError("La durée doit être positive et finie")
        garde_bits = int(p["garde_fin_secondes"] * p["R"])
        annonce_bits = max(annonce_bits, math.ceil(duree * p["R"]) - len(donnees) - garde_bits)
    return [1] * annonce_bits + donnees

def signal_message(message, profil="G8", duree=None):
    p = profils(profil)
    bits = _avec_annonce(encoder_message(message), p, duree)
    signal = moduler(bits, p["f0"], p["f1"], p["R"], p["fe"])
    return signal, bits, p

def signal_bits(bits, profil="G8", duree=None):
    """Séquence brute de test, précédée de l'annonce f1 sans 8N1."""
    p=profils(profil); valeurs=list(bits)
    if any(b not in (0,1) for b in valeurs): raise ValueError("Bits de test : 0 ou 1")
    return moduler(_avec_annonce(valeurs,p,duree),p["f0"],p["f1"],p["R"],p["fe"]), valeurs, p

def ajouter_garde_fin(signal, profil="G8"):
    """Ajoute une garde de silence pour préserver la fin sans faux start."""
    p = profils(profil)
    # Une garde f1 protège la lecture mais, après passage acoustique, ses
    # échos peuvent ressembler à un bit start f0 et créer un caractère fantôme
    # après le dernier octet. Du silence a la même fonction de marge de sortie.
    garde = np.zeros(round(p["garde_fin_secondes"] * p["fe"]), dtype=np.float64)
    return np.concatenate((np.asarray(signal, dtype=np.float64), garde))

def ecrire_wav(chemin, signal, fe=FE):
    chemin = Path(chemin); chemin.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(chemin, fe, np.asarray(signal, dtype=np.float32)); return chemin

def main():
    parser=argparse.ArgumentParser(description="Émission CPFSK 8N1, sans démodulation")
    parser.add_argument("message", nargs="?", help="texte encodé UTF-8")
    parser.add_argument("--profil", choices=tuple(PROFILS), default="G8")
    parser.add_argument("--sortie", default="mesures/module2/fsk_message.wav")
    parser.add_argument("--jouer", action="store_true")
    parser.add_argument("--device", help="périphérique de sortie explicite")
    parser.add_argument("--volume",type=float,default=1.0,help="gain ]0,1], sans écrêtage")
    parser.add_argument("--duree", type=float, help="durée sonore minimale en secondes, garde comprise ; allonge la porteuse sans modifier le débit")
    parser.add_argument("--liste-peripheriques",action="store_true")
    parser.add_argument("--bits",help="séquence binaire brute de test (annonce incluse dans le signal)")
    a=parser.parse_args()
    if a.liste_peripheriques:
        print(formater_peripheriques()); return
    try:
        if a.bits is not None: signal,bits,p=signal_bits([int(b) for b in a.bits],a.profil,a.duree)
        elif a.message is not None: signal,bits,p=signal_message(a.message,a.profil,a.duree)
        else: parser.error("message ou --bits requis")
    except ValueError as exc:
        parser.error(str(exc))
    # La garde protège la fin de lecture physique et est aussi conservée dans
    # le WAV afin que celui-ci reproduise exactement le signal joué.
    signal_joue = ajouter_garde_fin(signal, a.profil)
    sortie=ecrire_wav(a.sortie,signal_joue,p["fe"])
    print(f"{p['nom']} : {len(bits)} bits, {len(signal_joue)} échantillons, durée sonore={len(signal_joue)/p['fe']:.3f} s, {sortie}", flush=True)
    if a.jouer:
        try: jouer(signal_joue,p["fe"],a.device,a.volume)
        except (RuntimeError, ValueError) as exc: parser.error(str(exc))
if __name__ == "__main__": main()
