"""Commandes de démonstration : python main.py --help."""
import argparse
from crc import crc16_ccitt
from transfert import boucle_locale
from mesures_module1 import executer, BASE
from config import GROUPE


def main():
    parser = argparse.ArgumentParser(description=f'Modem acoustique {GROUPE} - Module 1 (boucle locale)')
    sub = parser.add_subparsers(dest='commande')
    sub.add_parser('crc', help='J1 : test de référence')
    b = sub.add_parser('boucle', help='J2 : reconstruire un fichier imposé')
    b.add_argument('fichier')
    b.add_argument('--sortie', default=str(BASE/'reception'))
    m = sub.add_parser('mesures', help='Trois tableaux et vérification des 3 fichiers')
    m.add_argument('--donnees', default=str(BASE/'donnees'))
    m.add_argument('--sortie', default=str(BASE/'mesures'))
    m.add_argument('--reception', default=str(BASE/'reception'))
    args = parser.parse_args()
    if args.commande == 'crc':
        r = crc16_ccitt(b'123456789')
        print(f'CRC("123456789") = 0x{r:04X} | attendu : 0x29B1')
        return int(r != 0x29B1)
    if args.commande == 'boucle':
        r = boucle_locale(args.fichier, args.sortie)
        for k,v in r.items():
            print(f'{k} : {v}')
        return int(not r['identiques'])
    if args.commande in (None, 'mesures'):
        if args.commande is None:
            executer()
        else:
            executer(args.donnees, args.sortie, args.reception)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
