"""Point d'entrée du module 1; aucune modulation FSK n'est implémentée ici."""
import argparse
from pathlib import Path
from config import GROUPE
from crc import crc16_ccitt
from trame import boucle_locale
from mesures_module1 import BASE, executer
from audio_test import environnement, generer_tonalite, jouer_tonalite

def main():
    parser=argparse.ArgumentParser(description=f"Modem acoustique {GROUPE} — module 1")
    sub=parser.add_subparsers(dest="commande", required=True)
    sub.add_parser("environnement", help="vérifier dépendances et audio disponible")
    sub.add_parser("crc", help="J1 : vecteur CRC de référence")
    boucle=sub.add_parser("boucle", help="J2 : boucle locale sans son"); boucle.add_argument("fichier"); boucle.add_argument("--sortie",default=str(BASE/"reception"))
    mesures=sub.add_parser("mesures", help="recalculer les tableaux reproductibles"); mesures.add_argument("--donnees",default=str(BASE/"donnees")); mesures.add_argument("--sortie",default=str(BASE/"mesures")); mesures.add_argument("--reception",default=str(BASE/"reception"))
    audio=sub.add_parser("audio",help="créer la tonalité WAV de contrôle"); audio.add_argument("--jouer",action="store_true")
    args=parser.parse_args()
    if args.commande=="environnement": return 0 if environnement() else 1
    if args.commande=="crc":
        valeur=crc16_ccitt(b"123456789"); print(f'CRC("123456789") = 0x{valeur:04X}'); return int(valeur != 0x29B1)
    if args.commande=="boucle":
        resultat=boucle_locale(args.fichier,args.sortie); [print(f"{k} : {v}") for k,v in resultat.items()]; return int(not resultat["identiques"])
    if args.commande=="mesures": executer(args.donnees,args.sortie,args.reception); return 0
    resultat=generer_tonalite(BASE/"mesures"/"tonalite_1000Hz.wav"); print(resultat)
    if args.jouer: jouer_tonalite(resultat["chemin"])
    return 0
if __name__=="__main__": raise SystemExit(main())
