"""Boucle locale : fichier -> trames -> bits -> fichier. Aucun canal audio."""
from pathlib import Path
from hashlib import sha256
from config import ADRESSE, N, CTRL_DERNIERE, CTRL_SEQUENCE, CTRL_SUPERVISION
from source import lire_octets, compresser, decompresser, construire_entete, lire_entete
from trame import construire_trame, trame_vers_bits, analyser_flux


def preparer_trames(nom, original: bytes):
    candidat = compresser(original)
    compression = len(candidat) < len(original)
    transmis = candidat if compression else original
    entete = construire_entete(nom, len(original), len(transmis), compression)
    blocs = [entete] + [transmis[i:i + N] for i in range(0, len(transmis), N)]
    trames = []
    for i, bloc in enumerate(blocs):
        ctrl = i % 2
        if i == len(blocs) - 1:
            ctrl |= CTRL_DERNIERE
        trames.append(construire_trame(ADRESSE, ctrl, bloc))
    return trames, compression


def encoder_trames(trames):
    return [bit for trame in trames for bit in trame_vers_bits(trame)]


def reconstruire(bits):
    trames, erreurs = analyser_flux(bits)
    if erreurs or not trames:
        raise ValueError(f'Flux invalide : {erreurs}')
    for i, trame in enumerate(trames):
        ctrl = trame['ctrl']
        if trame['adr'] != ADRESSE or ctrl & CTRL_SUPERVISION or ctrl & 0x3E:
            raise ValueError('Adresse ou contrôle invalide')
        if (ctrl & CTRL_SEQUENCE) != i % 2:
            raise ValueError('Séquence incorrecte')
        if bool(ctrl & CTRL_DERNIERE) != (i == len(trames) - 1):
            raise ValueError('Indicateur dernière trame incorrect')
    entete = lire_entete(trames[0]['donnees'])
    donnees = b''.join(t['donnees'] for t in trames[1:])
    if len(donnees) != entete['taille_tx']:
        raise ValueError('Taille transmise incorrecte')
    original = decompresser(donnees) if entete['compression'] else donnees
    if len(original) != entete['taille_orig']:
        raise ValueError('Taille originale incorrecte')
    return entete['nom'], original


def boucle_locale(chemin, dossier='reception') -> dict:
    chemin = Path(chemin)
    original = lire_octets(chemin)
    trames, compression = preparer_trames(chemin.name, original)
    bits = encoder_trames(trames)
    nom, recu = reconstruire(bits)
    destination = Path(dossier) / nom
    if destination.resolve() == chemin.resolve():
        raise ValueError('Choisir un autre dossier de réception')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(recu)
    h1 = sha256(original).hexdigest()
    h2 = sha256(destination.read_bytes()).hexdigest()
    return dict(fichier=nom, taille=len(original), compression=compression,
                trames=len(trames), bits=len(bits), sha256_original=h1, sha256_recu=h2,
                identiques=h1 == h2, destination=str(destination))
