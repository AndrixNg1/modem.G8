"""Transfert de fichier bout en bout ARQ/FSK en simulation locale uniquement."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import zlib

from arq import EmetteurARQ, RecepteurARQ, ARQ_TIMEOUT, ARQ_MAX_ATTEMPTS
from canal_fsk import CanalFSK
from source import FORMAT_ENTETE, construire_entete, lire_entete, compresser

TAILLE_MAX = 2048  # Périmètre de la démonstration finale : 2 Kio.


def preparer_paquet(nom, original):
    if len(original) > TAILLE_MAX:
        raise ValueError("Démonstration limitée à 2048 octets (2 Kio)")
    candidat = compresser(original)
    compression = len(candidat) < len(original)
    transmis = candidat if compression else original
    entete = construire_entete(nom, len(original), len(transmis), compression)
    return entete + transmis, compression


def decoder_paquet(paquet):
    """Vérifie l'en-tête, les tailles et la fin zlib avant toute écriture."""
    if len(paquet) < FORMAT_ENTETE.size:
        raise ValueError("En-tête de fichier tronqué")
    longueur_nom = FORMAT_ENTETE.unpack_from(paquet)[-1]
    fin_entete = FORMAT_ENTETE.size + longueur_nom
    entete = lire_entete(paquet[:fin_entete])
    if entete['taille_orig'] > TAILLE_MAX or entete['taille_tx'] > TAILLE_MAX:
        raise ValueError("Taille annoncée supérieure à 2 Kio")
    transmis = paquet[fin_entete:]
    if len(transmis) != entete['taille_tx']:
        raise ValueError("Paquet incomplet ou données supplémentaires")
    if entete['compression']:
        decodeur = zlib.decompressobj()
        try:
            original = decodeur.decompress(transmis, TAILLE_MAX + 1)
        except zlib.error as exc:
            raise ValueError("Données zlib invalides") from exc
        if not decodeur.eof or decodeur.unused_data or decodeur.unconsumed_tail:
            raise ValueError("Flux zlib incomplet ou taille excessive")
    else:
        original = transmis
    if len(original) != entete['taille_orig']:
        raise ValueError("Taille du fichier reconstruit incorrecte")
    return entete['nom'], original


def simuler_fichier(chemin, sortie='reception/module3', profil='G8', sb_db=None,
                    seed=2026, actions=(), timeout=ARQ_TIMEOUT,
                    max_attempts=ARQ_MAX_ATTEMPTS):
    chemin = Path(chemin)
    original = chemin.read_bytes()
    paquet, compression = preparer_paquet(chemin.name, original)
    destination = Path(sortie) / chemin.name
    if destination.resolve() == chemin.resolve():
        raise ValueError("La réception doit être séparée du fichier original")
    if destination.exists():
        raise FileExistsError("Le fichier reçu existe déjà : choisir un autre dossier")
    recepteur = RecepteurARQ()
    canal = CanalFSK(profil, actions=actions, sb_db=sb_db, seed=seed)
    emetteur = EmetteurARQ(canal, recepteur, timeout=timeout, max_attempts=max_attempts)
    recu = emetteur.transferer(paquet)
    nom, contenu = decoder_paquet(recu)
    h1, h2 = sha256(original).hexdigest(), sha256(contenu).hexdigest()
    if nom != chemin.name or contenu != original or h1 != h2:
        raise ValueError("Le fichier reçu ne correspond pas à l'original")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Aucun fichier partiel ni remplacement silencieux d'un résultat existant.
    with destination.open('xb') as fichier:
        fichier.write(contenu)
    return dict(
        mode='SIMULATION_LOCALE', profil=profil, fichier=nom,
        taille_originale=len(original), taille_paquet=len(paquet), compression=compression,
        sha256_original=h1, sha256_recu=sha256(destination.read_bytes()).hexdigest(),
        identiques=True, destination=str(destination),
        statistiques=asdict(emetteur.stats),
        debit_fichier_bit_s=len(original)*8/emetteur.stats.duree_simulee,
        teb_brut=canal.bits_bruts_errones/canal.bits_bruts_transmis,
    )
