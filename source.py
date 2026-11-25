"""Module 1 : lecture, entropie, compression et en-tête TLM1."""
from collections import Counter
from math import log2
from pathlib import Path
import struct
import zlib

# Convention locale : magic, indicateur, taille originale, taille transmise,
# longueur du nom en octets UTF-8. Entiers non signés, big endian.
FORMAT_ENTETE = struct.Struct('>4sBIIB')


def lire_octets(chemin) -> bytes:
    return Path(chemin).read_bytes()


def entropie(donnees: bytes) -> float:
    if not donnees:
        return 0.0
    total = len(donnees)
    return -sum((n / total) * log2(n / total) for n in Counter(donnees).values())


def compresser(donnees) -> bytes:
    return zlib.compress(donnees)


def decompresser(donnees) -> bytes:
    return zlib.decompress(donnees)


def verifier_nom(nom):
    if not isinstance(nom, str) or not nom or nom in ('.', '..'):
        raise ValueError('Nom de fichier invalide')
    if any(c in nom for c in '/\\:\0<>"|?*') or any(ord(c) < 32 for c in nom):
        raise ValueError('Le nom doit être un nom de fichier simple')
    code = nom.encode('utf-8')
    if len(code) > 18:
        raise ValueError('Nom limité à 18 octets UTF-8 selon la convention du protocole')
    return code


def construire_entete(nom, taille_orig, taille_tx, compression) -> bytes:
    code = verifier_nom(nom)
    if compression not in (0, 1):
        raise ValueError('Compression : 0 ou 1')
    if not all(isinstance(n, int) and 0 <= n <= 0xFFFFFFFF for n in (taille_orig, taille_tx)):
        raise ValueError('Tailles hors limites (uint32)')
    if not compression and taille_orig != taille_tx:
        raise ValueError('Tailles différentes sans compression')
    return FORMAT_ENTETE.pack(b'TLM1', compression, taille_orig, taille_tx, len(code)) + code


def lire_entete(entete: bytes) -> dict:
    if len(entete) < FORMAT_ENTETE.size:
        raise ValueError('En-tête tronqué')
    magic, compression, orig, tx, longueur = FORMAT_ENTETE.unpack_from(entete)
    code = entete[FORMAT_ENTETE.size:]
    if magic != b'TLM1' or compression not in (0, 1) or len(code) != longueur:
        raise ValueError('En-tête invalide')
    nom = code.decode('utf-8')
    verifier_nom(nom)
    if not compression and orig != tx:
        raise ValueError('Tailles incohérentes')
    return dict(nom=nom, taille_orig=orig, taille_tx=tx, compression=bool(compression))


def statistiques(donnees: bytes) -> dict:
    avant, apres = len(donnees), len(compresser(donnees))
    return dict(taille=avant, H=entropie(donnees), compresse=apres,
                Qc=avant / apres, zeta_c=apres / avant if avant else None,
                Gc=(1 - apres / avant) * 100 if avant else None)
