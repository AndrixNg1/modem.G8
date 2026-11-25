"""Mesures reproductibles du module 1, sans audio ni matériel."""
from pathlib import Path
import csv
import random
from config import N, ADRESSE, GROUPE
from source import lire_octets, statistiques
from trame import (construire_trame, trame_vers_bits, octet_vers_bits_8N1,
                   octet_vers_bits_8E2, analyser_flux)
from transfert import boucle_locale

BASE = Path(__file__).resolve().parent
FICHIERS = ['texte.txt', 'image.png', 'aleatoire.bin']


def ecrire_csv(chemin, lignes):
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(lignes)


def mesurer_source(dossier):
    return [dict(fichier=nom, **statistiques(lire_octets(Path(dossier) / nom))) for nom in FICHIERS]


def mesurer_rendements():
    # Une trame pleine de données pseudo-aléatoires, reproductible.
    rng = random.Random(2026)
    donnees = bytes(rng.randrange(256) for _ in range(N))
    utiles = 8 * N
    trame = construire_trame(ADRESSE, 0, donnees)
    valeurs = [('8N1', 8/10, sum(len(octet_vers_bits_8N1(o)) for o in donnees)),
               ('8E2', 8/12, sum(len(octet_vers_bits_8E2(o)) for o in donnees)),
               ('TLM-HDLC sans stuffing', N/(N+7), len(trame_vers_bits(trame, False))),
               ('TLM-HDLC avec stuffing', None, len(trame_vers_bits(trame)))]
    return [dict(format=nom, bits_utiles=utiles, bits_emis=n,
                 theorique_pct=100*t if t is not None else None,
                 mesure_pct=100*utiles/n) for nom,t,n in valeurs]


def mesurer_erreurs(essais=1000):
    """Inversions indépendantes sur tout le flux, fanions et stuffing inclus.

    Une absence de trame valide est un rejet, mais pas forcément dû au CRC.
    Les catégories sont exclusives au niveau de chaque essai.
    """
    rng = random.Random(2026)
    resultats = []
    for p in (1e-4, 1e-3, 1e-2):
        alters = rejets = crc = structure = non_detectees = 0
        somme_prob = somme_n = 0
        for i in range(essais):
            donnees = bytes(rng.randrange(256) for _ in range(N))
            bits = trame_vers_bits(construire_trame(ADRESSE, 0, donnees))
            n = len(bits)
            somme_n += n
            somme_prob += 1 - (1-p)**n
            recus = [b ^ int(rng.random() < p) for b in bits]
            modifies = recus != bits
            alters += modifies
            trames, erreurs = analyser_flux(recus)
            # Chaque essai représente exactement une trame isolée, sans bruit hors fanions.
            accepte = len(trames) == 1 and not erreurs and recus[:8] == bits[:8] and recus[-8:] == bits[-8:]
            if not accepte:
                rejets += 1
                if 'CRC incorrect' in erreurs:
                    crc += 1
                else:
                    structure += 1
            elif modifies:
                non_detectees += 1
        resultats.append(dict(p=p, essais=essais, bits_moyens=somme_n/essais,
                               alterees=alters, rejetees=rejets,
                               rejets_crc=crc, autres_rejets=structure,
                               alterees_acceptees=non_detectees,
                               proba_theorique=somme_prob/essais,
                               rejets_theoriques=somme_prob))
    return resultats


def executer(dossier=BASE/'donnees', sortie=BASE/'mesures', reception=BASE/'reception'):
    sortie = Path(sortie)
    source = mesurer_source(dossier)
    rendements = mesurer_rendements()
    erreurs = mesurer_erreurs()
    boucles = [boucle_locale(Path(dossier)/nom, reception) for nom in FICHIERS]
    for nom, lignes in [('compression', source), ('rendements', rendements), ('erreurs', erreurs), ('boucle_locale', boucles)]:
        ecrire_csv(sortie / (nom + '.csv'), lignes)
    lignes = [f'MODULE 1 - {GROUPE} | Mesures numériques en boucle locale', '',
              'COMPRESSION (zlib, y compris si la compression augmente la taille)']
    for r in source:
        taux = 'indéfini' if r['Gc'] is None else f"{r['Gc']:.2f}%"
        lignes.append(f"{r['fichier']:16} {r['taille']:6} o | H={r['H']:.4f} | compressé={r['compresse']} o | Qc={r['Qc']:.4f} | Gc={taux}")
    lignes += ['', f'RENDEMENTS ({N} octets utiles, une trame pleine, graine 2026)']
    for r in rendements:
        theo = 'variable selon les bits' if r['theorique_pct'] is None else f"{r['theorique_pct']:.2f}%"
        lignes.append(f"{r['format']:25} {r['bits_utiles']}/{r['bits_emis']} bits | théorie : {theo} | mesure : {r['mesure_pct']:.2f}%")
    lignes += ['', 'ERREURS (1000 trames par p, graine 2026, canal simulé)']
    for r in erreurs:
        lignes.append(f"p={r['p']:.0e} | altérées={r['alterees']} | rejetées={r['rejetees']} (CRC={r['rejets_crc']}, autres={r['autres_rejets']}) | altérées acceptées={r['alterees_acceptees']} | théorie={r['rejets_theoriques']:.2f}/1000")
    lignes += ['', 'BOUCLE LOCALE - comparaison SHA-256']
    for r in boucles:
        lignes += [f"{r['fichier']} | {r['trames']} trames | {r['bits']} bits | compression={r['compression']} | identiques={r['identiques']}", f"  original : {r['sha256_original']}", f"  reçu     : {r['sha256_recu']}"]
    texte = '\n'.join(lignes) + '\n'
    (sortie/'resultats.txt').write_text(texte, encoding='utf-8')
    print(texte)
    if not all(r['identiques'] for r in boucles):
        raise RuntimeError('Échec de la boucle locale')
    return source, rendements, erreurs, boucles
