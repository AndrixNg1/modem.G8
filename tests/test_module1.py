import binascii
import random
import tempfile
import unittest
from pathlib import Path
from hashlib import sha256
from source import *
from crc import crc16_ccitt
from trame import *
from transfert import *
from mesures_module1 import mesurer_rendements, mesurer_erreurs
from config import ADRESSE, N, GROUPE


class TestConfiguration(unittest.TestCase):
    def test_parametres_G8(self):
        self.assertEqual((GROUPE, ADRESSE, N), ('G8', 0x18, 48))

    def test_decoupage_G8(self):
        data = bytes(range(97))
        trames, compression = preparer_trames('test.bin', data)
        self.assertFalse(compression)
        self.assertEqual([t[1] for t in trames], [0x18] * 4)
        self.assertEqual([t[3] for t in trames[1:]], [48, 48, 1])
        self.assertEqual(reconstruire(encoder_trames(trames)), ('test.bin', data))


class TestSource(unittest.TestCase):
    def test_entropie_uniforme(self):
        self.assertAlmostEqual(entropie(bytes(range(256))), 8)
    def test_entropie_constante(self):
        self.assertEqual(entropie(b'a'*100), 0)
    def test_entropie_vide(self):
        self.assertEqual(entropie(b''), 0)
    def test_compression(self):
        for data in (b'', b'bonjour'*100, bytes(range(256))):
            self.assertEqual(decompresser(compresser(data)), data)
    def test_entete(self):
        entete = construire_entete('texte.txt', 300, 20, 1)
        self.assertEqual(lire_entete(entete), dict(nom='texte.txt', taille_orig=300, taille_tx=20, compression=True))
    def test_entete_accents_regression(self):
        self.assertEqual(lire_entete(construire_entete('été.txt', 5, 5, 0))['nom'], 'été.txt')
    def test_entete_max(self):
        entete = construire_entete('x'*18, 1, 1, 0)
        self.assertEqual(len(entete), FORMAT_ENTETE.size + 18)
        self.assertLessEqual(len(entete), N)
    def test_nom_invalide(self):
        for nom in ('../a', 'x'*19, '', 'a/b', 'é'*10):
            with self.assertRaises(ValueError):
                construire_entete(nom, 1, 1, 0)
    def test_entete_tronque(self):
        with self.assertRaises(ValueError):
            lire_entete(construire_entete('x.txt', 1, 1, 0)[:-1])


class TestCRC(unittest.TestCase):
    def test_reference_J1(self):
        self.assertEqual(crc16_ccitt(b'123456789'), 0x29B1)
    def test_reference_independante(self):
        rng = random.Random(44)
        for n in range(65):
            data = bytes(rng.randrange(256) for _ in range(n))
            self.assertEqual(crc16_ccitt(data), binascii.crc_hqx(data, 0xFFFF))
    def test_erreurs_simples(self):
        brute = construire_trame(ADRESSE, 0, bytes(range(N)))
        bits = octets_vers_bits(brute[1:-1])
        for i in range(len(bits)):
            corrompus = bits.copy()
            corrompus[i] ^= 1
            with self.assertRaises(ValueError):
                analyser_corps(bits_vers_octets(corrompus))
    def test_crc_donnee_corrompue(self):
        brute = bytearray(construire_trame(ADRESSE, 0, b'abc'))
        brute[4] ^= 1
        valides, erreurs = analyser_flux(trame_vers_bits(brute))
        self.assertEqual(valides, [])
        self.assertIn('CRC incorrect', erreurs)


class TestTrames(unittest.TestCase):
    def test_8N1_A(self):
        self.assertEqual(octet_vers_bits_8N1(0x41), [0,1,0,0,0,0,0,1,0,1])
    def test_8N1_tous_octets(self):
        data = bytes(range(256))
        bits = [b for o in data for b in octet_vers_bits_8N1(o)]
        self.assertEqual(bits_8N1_vers_octets([1,1]+bits+[1]), data)
    def test_8E2_tous_octets(self):
        data = bytes(range(256))
        bits = [b for o in data for b in octet_vers_bits_8E2(o)]
        self.assertEqual(bits_8E2_vers_octets(bits), data)
    def test_8E2_parite(self):
        bits = octet_vers_bits_8E2(1)
        self.assertEqual(bits[9], 1)
        bits[9] ^= 1
        with self.assertRaises(ValueError):
            bits_8E2_vers_octets(bits)
    def test_8N1_stop(self):
        bits = octet_vers_bits_8N1(65)
        bits[-1] = 0
        with self.assertRaises(ValueError):
            bits_8N1_vers_octets(bits)
    def test_stuffing_exemple(self):
        bits = [0,1,1,1,1,1,1,0,1]
        self.assertEqual(bit_stuffing(bits), [0,1,1,1,1,1,0,1,0,1])
    def test_stuffing_inverse(self):
        for bits in ([], [1]*5, [1]*100, [0,1]*20, octets_vers_bits(b'\x7e\xff')):
            self.assertEqual(bit_destuffing(bit_stuffing(bits)), bits)
    def test_destuffing_invalide(self):
        with self.assertRaises(ValueError):
            bit_destuffing([1]*6)
    def test_transparence(self):
        data = b'\x7e\xff'*16
        bits = trame_vers_bits(construire_trame(ADRESSE, 0, data))
        self.assertEqual(extraire_trames(bits)[0]['donnees'], data)
        self.assertFalse(any(bits[i:i+8] == FANION_BITS for i in range(8,len(bits)-8)))
    def test_limite(self):
        with self.assertRaises(ValueError):
            construire_trame(ADRESSE, 0, bytes(N+1))
    def test_flux_multiple(self):
        t = [construire_trame(ADRESSE,i,b'abc') for i in range(2)]
        self.assertEqual([r['ctrl'] for r in extraire_trames(encoder_trames(t))], [0,1])
    def test_trame_vide(self):
        self.assertEqual(extraire_trames(trame_vers_bits(construire_trame(ADRESSE,0,b'')))[0]['donnees'], b'')


class TestBoucle(unittest.TestCase):
    def test_cas_limites(self):
        for data in (b'', b'x', b'x'*1000, bytes(range(256)), b'\x7e\xff'*300):
            trames, _ = preparer_trames('test.bin',data)
            self.assertEqual(reconstruire(encoder_trames(trames)), ('test.bin',data))
    def test_fichiers_reels_J2(self):
        base = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as sortie:
            for nom in ('texte.txt','image.png','aleatoire.bin'):
                r = boucle_locale(base/'donnees'/nom,sortie)
                self.assertTrue(r['identiques'])
                self.assertEqual((base/'donnees'/nom).read_bytes(), (Path(sortie)/nom).read_bytes())
    def test_trame_manquante(self):
        trames,_ = preparer_trames('x.bin',bytes(range(256)))
        with self.assertRaises(ValueError):
            reconstruire(encoder_trames(trames[:-1]))
    def test_mauvaise_adresse(self):
        t,_ = preparer_trames('x.bin',b'')
        mauvaise = construire_trame(0x12,t[0][2],t[0][4:-3])
        with self.assertRaises(ValueError):
            reconstruire(encoder_trames([mauvaise]))
    def test_rendements(self):
        r = mesurer_rendements()
        self.assertEqual(r[0]['mesure_pct'],80)
        self.assertAlmostEqual(r[1]['mesure_pct'],100*8/12)
        self.assertAlmostEqual(r[2]['mesure_pct'],100*N/(N+7))
        self.assertLessEqual(r[3]['mesure_pct'],r[2]['mesure_pct'])
    def test_comptage_erreurs(self):
        for r in mesurer_erreurs(30):
            self.assertEqual(r['rejetees'],r['rejets_crc']+r['autres_rejets'])
            self.assertEqual(r['alterees'],r['rejetees']+r['alterees_acceptees'])


if __name__ == '__main__':
    unittest.main()
