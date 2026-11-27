import io
import random
import tempfile
import unittest
import zipfile
from pathlib import Path

from transfert_fichier import simuler_fichier, preparer_paquet, decoder_paquet


class TestTransfertFichier(unittest.TestCase):
    def test_fichiers_complets_arq_fsk_sha256(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as fichier:
            fichier.writestr('message.txt', 'Bonjour G8')
        png = bytes.fromhex(
            '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489'
            '0000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
        cas = {
            'message.txt': 'Bonjour G8 — université'.encode(),
            'tableau.csv': b'nom;valeur\nG8;48\n',
            'image.png': png,
            'archive.zip': archive.getvalue(),
            'binaire.bin': bytes(range(256)),
            'vide.bin': b'',
            'un_kio.bin': random.Random(1).randbytes(1024),
            'deux_kio.bin': random.Random(2).randbytes(2048),
        }
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier)
            for nom, contenu in cas.items():
                with self.subTest(nom=nom):
                    source = base / nom
                    source.write_bytes(contenu)
                    resultat = simuler_fichier(source, base / 'recu')
                    self.assertEqual((base / 'recu' / nom).read_bytes(), contenu)
                    self.assertEqual(source.read_bytes(), contenu)
                    self.assertEqual(resultat['sha256_original'], resultat['sha256_recu'])
                    self.assertEqual(resultat['statistiques']['statut'], 'OK')
                    self.assertEqual(resultat['statistiques']['octets_acceptes'], resultat['taille_paquet'])
                    self.assertEqual(resultat['teb_brut'], 0)
                    self.assertEqual(resultat['mode'], 'SIMULATION_LOCALE')

    def test_compression_choisie_seulement_si_utile(self):
        for contenu, attendu in ((b'A' * 2048, True), (bytes(range(256)), False), (b'', False)):
            paquet, compression = preparer_paquet('test.bin', contenu)
            self.assertIs(compression, attendu)
            self.assertEqual(decoder_paquet(paquet), ('test.bin', contenu))

    def test_perte_ack_retransmission_sans_dupliquer_le_fichier(self):
        with tempfile.TemporaryDirectory() as dossier:
            source = Path(dossier) / 'source.bin'
            source.write_bytes(random.Random(3).randbytes(100))
            resultat = simuler_fichier(source, Path(dossier) / 'recu', actions=['ok', 'perte_ack'])
            self.assertEqual(resultat['statistiques']['doublons_ignores'], 1)
            self.assertEqual(resultat['statistiques']['ack_perdus'], 1)
            self.assertEqual(resultat['statistiques']['retransmissions'], 1)
            self.assertTrue(resultat['identiques'])

    def test_abandon_ne_produit_pas_un_fichier_recu(self):
        with tempfile.TemporaryDirectory() as dossier:
            source = Path(dossier) / 'source.txt'
            source.write_bytes(b'G8')
            destination = Path(dossier) / 'recu'
            with self.assertRaises(RuntimeError):
                simuler_fichier(source, destination, actions=['perte_i'] * 5)
            self.assertFalse(destination.exists())

    def test_entete_tailles_troncature_et_compression_invalides(self):
        paquet, _ = preparer_paquet('test.bin', b'A' * 100)
        for invalide in (b'', paquet[:-1], paquet + b'x', b'XXXX' + paquet[4:]):
            with self.subTest(invalide=invalide[:10]), self.assertRaises(ValueError):
                decoder_paquet(invalide)
        with self.assertRaises(ValueError):
            preparer_paquet('../test', b'x')
        with self.assertRaises(ValueError):
            preparer_paquet('test.bin', b'x' * 2049)

    def test_ne_remplace_ni_source_ni_resultat_existant(self):
        with tempfile.TemporaryDirectory() as dossier:
            source = Path(dossier) / 'test.txt'
            source.write_bytes(b'original')
            with self.assertRaises(ValueError):
                simuler_fichier(source, dossier)
            destination = Path(dossier) / 'recu'
            destination.mkdir()
            (destination / source.name).write_bytes(b'preuve precedente')
            with self.assertRaises(FileExistsError):
                simuler_fichier(source, destination)
            self.assertEqual(source.read_bytes(), b'original')
            self.assertEqual((destination / source.name).read_bytes(), b'preuve precedente')
