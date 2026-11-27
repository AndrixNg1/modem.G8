"""Mesures ARQ/FSK simulées : TEB avant CRC, intégrité et débit après ARQ."""
import argparse
import csv
import hashlib
from pathlib import Path

from arq import EmetteurARQ, RecepteurARQ
from canal_fsk import CanalFSK

NIVEAUX = [6, 3, 0, -3, -6, -9, -12]
SORTIE = "mesures/module3/simulation_corrigee"


def comparer_charge(original, recu):
    """Comparaison positionnelle après CRC : ce n'est pas le TEB du modem."""
    substitutions = sum((a ^ b).bit_count() for a, b in zip(original, recu))
    pertes = max(len(original) - len(recu), 0) * 8
    insertions = max(len(recu) - len(original), 0) * 8
    return {
        "bits_comparables_charge": min(len(original), len(recu)) * 8,
        "bits_errones_charge": substitutions,
        "bits_perdus_charge": pertes,
        "bits_inseres_charge": insertions,
        "taux_ecart_charge": (substitutions + pertes + insertions) / (len(original) * 8) if original else None,
    }


def executer(essais=20, taille=144, graine=2026, sortie=SORTIE, niveaux=NIVEAUX, arq=True):
    if essais < 1 or taille < 1 or graine < 0 or not niveaux:
        raise ValueError("Essais/taille positifs, graine positive ou nulle et niveaux non vides requis")
    out = Path(sortie)
    out.mkdir(parents=True, exist_ok=True)
    lignes = []
    data = bytes(i % 256 for i in range(taille))
    for niveau, sb in enumerate(niveaux):
        for i in range(essais):
            # Bruit indépendant par bloc/tentative/sens ; première transmission
            # de chaque bloc identique dans les essais avec et sans ARQ.
            r = RecepteurARQ()
            c = CanalFSK('G8', sb_db=sb, seed=graine + i + 100000 * niveau)
            e = EmetteurARQ(c, r, max_attempts=5 if arq else 1)
            try:
                recu = e.transferer(data)
            except RuntimeError:
                recu = bytes(r.donnees)
            reussi = e.stats.statut == 'OK' and recu == data
            duree = e.stats.duree_simulee
            lignes.append(dict(
                sb_db=sb, essai=i, **comparer_charge(data, recu),
                bits_bruts_transmis=c.bits_bruts_transmis,
                bits_bruts_errones=c.bits_bruts_errones,
                bits_bruts_perdus=c.bits_bruts_perdus,
                bits_bruts_inseres=c.bits_bruts_inseres,
                teb_brut=c.bits_bruts_errones / c.bits_bruts_transmis if c.bits_bruts_transmis else None,
                trames_originales=e.stats.trames_originales, tentatives=e.stats.tentatives,
                retransmissions=e.stats.retransmissions, ack_emis=e.stats.ack_emis,
                ack_recus=e.stats.ack, nak_recus=e.stats.nak, doublons=e.stats.doublons_ignores,
                timeouts=e.stats.delais, octets_acceptes=e.stats.octets_acceptes,
                duree_simulee=duree, debit_utile=len(data) * 8 / duree if reussi and duree else 0,
                statut='OK' if reussi else 'ECHEC',
                sha_original=hashlib.sha256(data).hexdigest(), sha_recu=hashlib.sha256(recu).hexdigest(),
            ))
        print(f'S/B {sb:+} dB : {essais} essais')
    nom = 'resultats_awgn_arq.csv' if arq else 'resultats_awgn_sans_arq.csv'
    with (out / nom).open('w', newline='', encoding='utf8') as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0])
        writer.writeheader()
        writer.writerows(lignes)
    return lignes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--essais', type=int, default=20)
    parser.add_argument('--taille', type=int, default=144)
    parser.add_argument('--graine', type=int, default=2026)
    parser.add_argument('--sortie', default=SORTIE)
    parser.add_argument('--rapide', action='store_true')
    parser.add_argument('--sans-arq', action='store_true')
    args = parser.parse_args()
    executer(1 if args.rapide else args.essais, args.taille, args.graine, args.sortie, arq=not args.sans_arq)
