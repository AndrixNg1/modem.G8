"""Formats asynchrones et TLM-HDLC. Bits des octets : LSB d'abord."""
from crc import crc16_ccitt
from config import N

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
