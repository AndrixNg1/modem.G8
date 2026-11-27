"""Synthèse des CSV ARQ ; aucun essai n'est généré ni aucune mesure historique écrasée."""
import argparse
import csv
from pathlib import Path
from mesures_arq import SORTIE


def executer(base=SORTIE):
    base = Path(base)
    def lire(nom):
        with (base / nom).open(encoding='utf8') as fichier:
            return list(csv.DictReader(fichier))
    arq = lire('resultats_awgn_arq.csv')
    sans = lire('resultats_awgn_sans_arq.csv')
    niveaux = sorted({float(row['sb_db']) for row in arq}, reverse=True)
    lignes = []
    for sb in niveaux:
        x = [r for r in arq if float(r['sb_db']) == sb]
        y = [r for r in sans if float(r['sb_db']) == sb]
        if not y or {r['essai'] for r in x} != {r['essai'] for r in y}:
            raise ValueError("Campagnes non appariées : mêmes niveaux et essais requis")
        def ok(rows):
            return sum(r['statut'] == 'OK' and r['sha_original'] == r['sha_recu'] for r in rows)
        n = len(x)
        lignes.append(dict(
            sb_db=sb, essais=n, succes_arq=ok(x), succes_sans_arq=ok(y),
            taux_arq=ok(x)/n, taux_sans_arq=ok(y)/len(y),
            gain_points=100*(ok(x)/n-ok(y)/len(y)),
            retransmissions=sum(int(r['retransmissions']) for r in x),
            duree_moyenne=sum(float(r['duree_simulee']) for r in x)/n,
            debit_moyen=sum(float(r['debit_utile']) for r in x)/n,
            abandons=n-ok(x),
        ))
    if not lignes:
        raise ValueError("Campagne vide")
    with (base / 'synthese_awgn.csv').open('w', newline='', encoding='utf8') as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0])
        writer.writeheader()
        writer.writerows(lignes)
    return lignes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default=SORTIE)
    args = parser.parse_args()
    for ligne in executer(args.base):
        print(ligne)
