"""Préparation d'une émission 8N1/FSK à phase continue, sans démodulation."""
from pathlib import Path
import argparse
import numpy as np
from scipy.io import wavfile
from config import F0, F1, R, FE, BELL103
from modem_fsk import moduler
from trame import octet_vers_bits_8N1
from audio_io import jouer, formater_peripheriques

ANNONCE_SECONDES = 0.8
# L'arrêt d'un flux audio peut couper les derniers échantillons.  Cette garde
# f1 est hors trame : elle laisse donc le bit stop final intégralement audible.
GARDE_FIN_SECONDES = 0.05

def profils(nom="G8"):
    if nom.upper() == "G8": return {"nom":"G8", "f0":F0, "f1":F1, "R":R, "fe":FE}
    if nom.lower() == "bell103": return {"nom":"Bell 103", "f0":BELL103["F0"], "f1":BELL103["F1"], "R":BELL103["R"], "fe":FE}
    raise ValueError("Profil attendu : G8 ou bell103")

def encoder_message(message):
    """UTF-8; chaque octet est encodé 8N1, LSB first (10 bits/octet)."""
    return [bit for octet in message.encode("utf-8") for bit in octet_vers_bits_8N1(octet)]

def signal_message(message, profil="G8"):
    p = profils(profil); annonce_bits = int(ANNONCE_SECONDES * p["R"])
    bits = [1] * annonce_bits + encoder_message(message)
    signal = moduler(bits, p["f0"], p["f1"], p["R"], p["fe"])
    return signal, bits, p

def signal_bits(bits, profil="G8"):
    """Séquence brute de test, précédée de l'annonce f1 sans 8N1."""
    p=profils(profil); valeurs=list(bits)
    if any(b not in (0,1) for b in valeurs): raise ValueError("Bits de test : 0 ou 1")
    return moduler([1]*int(ANNONCE_SECONDES*p["R"])+valeurs,p["f0"],p["f1"],p["R"],p["fe"]), valeurs, p

def ajouter_garde_fin(signal, profil="G8"):
    """Ajoute une garde f1 de fin pour une lecture sur périphérique audio.

    Elle n'ajoute aucune donnée 8N1 : le récepteur s'arrête naturellement
    après le dernier bit stop, puisqu'aucun nouveau bit start f0 ne suit.
    """
    p = profils(profil)
    garde = moduler([1] * int(GARDE_FIN_SECONDES * p["R"]),
                    p["f0"], p["f1"], p["R"], p["fe"])
    return np.concatenate((np.asarray(signal, dtype=np.float64), garde))

def ecrire_wav(chemin, signal, fe=FE):
    chemin = Path(chemin); chemin.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(chemin, fe, np.asarray(signal, dtype=np.float32)); return chemin

def main():
    parser=argparse.ArgumentParser(description="Émission CPFSK 8N1, sans démodulation")
    parser.add_argument("message", nargs="?", help="texte encodé UTF-8")
    parser.add_argument("--profil", choices=("G8", "bell103"), default="G8")
    parser.add_argument("--sortie", default="mesures/module2/fsk_message.wav")
    parser.add_argument("--jouer", action="store_true")
    parser.add_argument("--device", help="périphérique de sortie explicite")
    parser.add_argument("--volume",type=float,default=1.0,help="gain ]0,1], sans écrêtage")
    parser.add_argument("--liste-peripheriques",action="store_true")
    parser.add_argument("--bits",help="séquence binaire brute de test (annonce incluse dans le signal)")
    a=parser.parse_args()
    if a.liste_peripheriques:
        print(formater_peripheriques()); return
    if a.bits is not None: signal,bits,p=signal_bits([int(b) for b in a.bits],a.profil)
    elif a.message is not None: signal,bits,p=signal_message(a.message,a.profil)
    else: parser.error("message ou --bits requis")
    # La garde protège la fin de lecture physique et est aussi conservée dans
    # le WAV afin que celui-ci reproduise exactement le signal joué.
    signal_joue = ajouter_garde_fin(signal, a.profil)
    sortie=ecrire_wav(a.sortie,signal_joue,p["fe"])
    print(f"{p['nom']} : {len(bits)} bits utiles, {len(signal_joue)} échantillons, {sortie}")
    if a.jouer:
        try: jouer(signal_joue,p["fe"],a.device,a.volume)
        except (RuntimeError, ValueError) as exc: parser.error(str(exc))
if __name__ == "__main__": main()
