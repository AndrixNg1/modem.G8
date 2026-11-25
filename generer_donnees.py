"""Crée les trois fichiers de démonstration, sans dépendance externe."""
from pathlib import Path
import random
import struct
import zlib


def generer(dossier):
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    texte = ('Le modem acoustique transmet des données numériques par le son. '
             'Le codage source réduit les redondances et le CRC contrôle les erreurs.\n')
    (dossier/'texte.txt').write_bytes((texte*20).encode('utf-8'))
    rng = random.Random(2026)
    (dossier/'aleatoire.bin').write_bytes(bytes(rng.randrange(256) for _ in range(4096)))
    # PNG RGB valide, pixels pseudo-aléatoires : déjà compressé par zlib.
    w, h = 64, 64
    brut = b''.join(b'\0' + bytes(rng.randrange(256) for _ in range(3*w)) for _ in range(h))
    def chunk(nom, data):
        return struct.pack('>I', len(data)) + nom + data + struct.pack('>I', zlib.crc32(nom+data))
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w,h,8,2,0,0,0))
           + chunk(b'IDAT', zlib.compress(brut)) + chunk(b'IEND', b''))
    (dossier/'image.png').write_bytes(png)


if __name__ == '__main__':
    generer(Path(__file__).resolve().parent/'donnees')
