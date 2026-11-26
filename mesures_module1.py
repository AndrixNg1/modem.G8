"""Mesures reproductibles du module 1 (canal numérique, sans matériel)."""
from pathlib import Path
import csv, random
from config import N, ADRESSE, GROUPE
from source import lire_octets, statistiques
from trame import construire_trame, trame_vers_bits, octet_vers_bits_8N1, octet_vers_bits_8E2, analyser_flux, boucle_locale

BASE = Path(__file__).resolve().parent
FICHIERS = ("texte.txt", "image.png", "aleatoire.bin")

def ecrire_csv(chemin, lignes):
    chemin = Path(chemin); chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
        writer.writeheader(); writer.writerows(lignes)

def mesurer_source(dossier):
    return [dict(fichier=n, **statistiques(lire_octets(Path(dossier) / n))) for n in FICHIERS]

def mesurer_rendements():
    rng = random.Random(2026); donnees = bytes(rng.randrange(256) for _ in range(N)); utiles = 8*N
    trame = construire_trame(ADRESSE, 0, donnees)
    valeurs = [("8N1", 8/10, 10*N), ("8E2", 8/12, 12*N),
               ("TLM-HDLC sans stuffing", N/(N+7), len(trame_vers_bits(trame, False))),
               ("TLM-HDLC avec stuffing", None, len(trame_vers_bits(trame)))]
    return [dict(format=nom, bits_utiles=utiles, bits_emis=bits, theorique_pct=None if t is None else 100*t, mesure_pct=100*utiles/bits) for nom,t,bits in valeurs]

def mesurer_erreurs(essais=1000):
    rng = random.Random(2026); resultats = []
    for p in (1e-4, 1e-3, 1e-2):
        alterees = rejetees = crc = autres = acceptees = 0; probabilites = []; longueurs = []
        for _ in range(essais):
            data = bytes(rng.randrange(256) for _ in range(N)); bits = trame_vers_bits(construire_trame(ADRESSE, 0, data)); n=len(bits)
            recus=[b ^ int(rng.random() < p) for b in bits]; modifie = recus != bits
            alterees += modifie; longueurs.append(n); probabilites.append(1-(1-p)**n)
            trames, erreurs = analyser_flux(recus); accepte = len(trames)==1 and not erreurs and recus[:8]==bits[:8] and recus[-8:]==bits[-8:]
            if not accepte:
                rejetees += 1
                if "CRC incorrect" in erreurs: crc += 1
                else: autres += 1
            elif modifie: acceptees += 1
        resultats.append(dict(p=p, essais=essais, bits_moyens=sum(longueurs)/essais, alterees=alterees, rejetees=rejetees, rejets_crc=crc, autres_rejets=autres, alterees_acceptees=acceptees, proba_theorique=sum(probabilites)/essais, rejets_theoriques=sum(probabilites)))
    return resultats

def executer(dossier=BASE/"donnees", sortie=BASE/"mesures", reception=BASE/"reception"):
    sortie=Path(sortie); source=mesurer_source(dossier); rendements=mesurer_rendements(); erreurs=mesurer_erreurs(); boucles=[boucle_locale(Path(dossier)/n,reception) for n in FICHIERS]
    for nom,lignes in (("compression",source),("rendements",rendements),("erreurs",erreurs),("boucle_locale",boucles)): ecrire_csv(sortie/(nom+".csv"),lignes)
    lignes=[f"MODULE 1 - {GROUPE} | Mesures numériques en boucle locale", "", "COMPRESSION (zlib, y compris si la compression augmente la taille)"]
    lignes += [f"{r['fichier']:16} {r['taille']:6} o | H={r['H']:.4f} | compressé={r['compresse']} o | Qc={r['Qc']:.4f} | Gc={'indéfini' if r['Gc'] is None else f'{r['Gc']:.2f}%'}" for r in source]
    lignes += ["", f"RENDEMENTS ({N} octets utiles, une trame pleine, graine 2026)"] + [f"{r['format']:25} {r['bits_utiles']}/{r['bits_emis']} bits | théorie : {'variable selon les bits' if r['theorique_pct'] is None else f'{r['theorique_pct']:.2f}%'} | mesure : {r['mesure_pct']:.2f}%" for r in rendements]
    lignes += ["", "ERREURS (1000 trames par p, graine 2026, canal simulé)"] + [f"p={r['p']:.0e} | altérées={r['alterees']} | rejetées={r['rejetees']} (CRC={r['rejets_crc']}, autres={r['autres_rejets']}) | altérées acceptées={r['alterees_acceptees']} | théorie={r['rejets_theoriques']:.2f}/1000" for r in erreurs]
    lignes += ["", "BOUCLE LOCALE - comparaison SHA-256"]
    for r in boucles: lignes += [f"{r['fichier']} | {r['trames']} trames | {r['bits']} bits | compression={r['compression']} | identiques={r['identiques']}", f"  original : {r['sha256_original']}", f"  reçu     : {r['sha256_recu']}"]
    texte="\n".join(lignes)+"\n"; (sortie/"resultats.txt").write_text(texte,encoding="utf-8"); print(texte)
    if not all(r["identiques"] for r in boucles): raise RuntimeError("Échec de la boucle locale")
    return source,rendements,erreurs,boucles

if __name__ == "__main__": executer()
