"""Formats asynchrones et TLM-HDLC. Bits des octets : LSB d'abord."""
from crc import crc16_ccitt
from pathlib import Path
from hashlib import sha256
from source import lire_octets, compresser, decompresser, construire_entete, lire_entete

GROUPE = 'G8'
ADRESSE = 0x18
N = 48
CTRL_SUPERVISION = 0x80
CTRL_DERNIERE = 0x40
CTRL_SEQUENCE = 0x01

FANION = 0x7E
FANION_BITS = [0, 1, 1, 1, 1, 1, 1, 0]


def octet_vers_bits(o: int) -> list[int]:
    if not 0 <= o <= 255:
        raise ValueError('Octet hors limites')
    return [(o >> i) & 1 for i in range(8)]


def octets_vers_bits(donnees: bytes) -> list[int]:
    return [bit for o in donnees for bit in octet_vers_bits(o)]


def bits_vers_octets(bits) -> bytes:
    if len(bits) % 8 or any(b not in (0, 1) for b in bits):
        raise ValueError('Bits invalides ou nombre non multiple de 8')
    return bytes(sum(bits[i + j] << j for j in range(8)) for i in range(0, len(bits), 8))


def octet_vers_bits_8N1(o: int) -> list[int]:
    return [0] + octet_vers_bits(o) + [1]


def octet_vers_bits_8E2(o: int) -> list[int]:
    donnees = octet_vers_bits(o)
    return [0] + donnees + [sum(donnees) % 2, 1, 1]


def bits_8N1_vers_octets(bits) -> bytes:
    resultat = bytearray()
    i = 0
    while i < len(bits):
        if bits[i] == 1:  # repos de la ligne
            i += 1
            continue
        if i + 10 > len(bits):
            raise ValueError('Caractère 8N1 tronqué')
        if bits[i + 9] != 1:
            raise ValueError('Bit de stop 8N1 invalide')
        resultat.extend(bits_vers_octets(bits[i + 1:i + 9]))
        i += 10
    return bytes(resultat)


def bits_8E2_vers_octets(bits) -> bytes:
    resultat = bytearray()
    i = 0
    while i < len(bits):
        if bits[i] == 1:
            i += 1
            continue
        if i + 12 > len(bits):
            raise ValueError('Caractère 8E2 tronqué')
        if bits[i + 10:i + 12] != [1, 1]:
            raise ValueError('Bits de stop 8E2 invalides')
        if sum(bits[i + 1:i + 10]) % 2:
            raise ValueError('Parité 8E2 invalide')
        resultat.extend(bits_vers_octets(bits[i + 1:i + 9]))
        i += 12
    return bytes(resultat)


def construire_trame(adr, ctrl, donnees) -> bytes:
    """Trame brute avec ses deux fanions, CRC en big endian (convention locale)."""
    donnees = bytes(donnees)
    if len(donnees) > N:
        raise ValueError(f'Données limitées à {N} octets')
    corps = bytes([adr, ctrl, len(donnees)]) + donnees
    crc = crc16_ccitt(corps).to_bytes(2, 'big')
    return bytes([FANION]) + corps + crc + bytes([FANION])


def bit_stuffing(bits) -> list[int]:
    resultat = []
    uns = 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError('Bit invalide')
        resultat.append(bit)
        uns = uns + 1 if bit == 1 else 0
        if uns == 5:
            resultat.append(0)
            uns = 0
    return resultat


def bit_destuffing(bits) -> list[int]:
    resultat = []
    uns = 0
    i = 0
    while i < len(bits):
        bit = bits[i]
        if bit not in (0, 1):
            raise ValueError('Bit invalide')
        resultat.append(bit)
        uns = uns + 1 if bit == 1 else 0
        i += 1
        if uns == 5:
            if i == len(bits) or bits[i] != 0:
                raise ValueError('Zéro de stuffing manquant')
            i += 1
            uns = 0
    return resultat


def trame_vers_bits(trame: bytes, stuffing=True) -> list[int]:
    if len(trame) < 7 or trame[0] != FANION or trame[-1] != FANION:
        raise ValueError('Trame brute invalide')
    corps = octets_vers_bits(trame[1:-1])
    return FANION_BITS + (bit_stuffing(corps) if stuffing else corps) + FANION_BITS


def analyser_corps(corps: bytes) -> dict:
    if len(corps) < 5:
        raise ValueError('Corps trop court')
    adr, ctrl, longueur = corps[:3]
    if longueur > N or len(corps) != longueur + 5:
        raise ValueError('Longueur incohérente')
    recu = int.from_bytes(corps[-2:], 'big')
    calcule = crc16_ccitt(corps[:-2])
    if recu != calcule:
        raise ValueError('CRC incorrect')
    return dict(adr=adr, ctrl=ctrl, longueur=longueur, donnees=corps[3:-2], crc=recu)


def analyser_flux(bits) -> tuple[list[dict], list[str]]:
    """Cherche les fanions et distingue les trames valides des corps rejetés."""
    bits = list(bits)
    valides, erreurs = [], []
    debut = None
    i = 0
    while i <= len(bits) - 8:
        if bits[i:i + 8] != FANION_BITS:
            i += 1
            continue
        if debut is not None and i > debut:
            try:
                corps = bits_vers_octets(bit_destuffing(bits[debut:i]))
                valides.append(analyser_corps(corps))
            except ValueError as exc:
                erreurs.append(str(exc))
        debut = i + 8
        i += 8
    if debut is None and bits:
        erreurs.append('Aucun fanion détecté')
    elif debut is not None and debut < len(bits):
        erreurs.append('Bits résiduels après le dernier fanion')
    return valides, erreurs


def extraire_trames(bits) -> list[dict]:
    return analyser_flux(bits)[0]


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


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='J2 : boucle locale G8, sans son')
    parser.add_argument('fichier')
    parser.add_argument('--sortie', default=str(Path(__file__).resolve().parent / 'reception'))
    args = parser.parse_args()
    resultat = boucle_locale(args.fichier, args.sortie)
    for cle, valeur in resultat.items():
        print(f'{cle} : {valeur}')
    raise SystemExit(int(not resultat['identiques']))
