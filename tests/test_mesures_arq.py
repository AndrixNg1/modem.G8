import tempfile
import unittest
from unittest.mock import patch

from arq import EmetteurARQ, RecepteurARQ, CanalSimule
from canal_fsk import CanalFSK
from mesures_arq import comparer_charge, executer


class TestMesuresARQ(unittest.TestCase):
    def test_erreurs_par_bit_et_ecarts_de_longueur(self):
        self.assertEqual(comparer_charge(b'\x00', b'\x01')['bits_errones_charge'], 1)
        self.assertEqual(comparer_charge(b'\x00', b'\xff')['bits_errones_charge'], 8)
        self.assertEqual(comparer_charge(b'abc', b'ab')['bits_perdus_charge'], 8)
        self.assertEqual(comparer_charge(b'a', b'ab')['bits_inseres_charge'], 8)

    def test_timeout_unique_et_configurable_sur_les_deux_canaux(self):
        for canal in (CanalSimule(['perte_i'] * 5), CanalFSK(actions=['perte_i'] * 5)):
            emetteur = EmetteurARQ(canal, RecepteurARQ(), timeout=1.5)
            with self.assertRaises(RuntimeError):
                emetteur.transferer(b'x')
            self.assertEqual(emetteur.stats.duree_simulee, 7.5)
            self.assertEqual(emetteur.stats.delais, 5)

    def test_ack_incorrect_attend_le_timeout(self):
        e = EmetteurARQ(CanalSimule(['mauvais_ack']), RecepteurARQ(), timeout=2)
        self.assertEqual(e.transferer(b'x'), b'x')
        self.assertEqual(e.stats.duree_simulee, 2)

    def test_bilan_recepteur_preserve_si_tous_les_ack_sont_perdus(self):
        e = EmetteurARQ(CanalSimule(['perte_ack'] * 5), RecepteurARQ())
        with self.assertRaises(RuntimeError):
            e.transferer(b'abc')
        self.assertEqual(e.stats.octets_acceptes, 3)
        self.assertEqual(e.stats.ack_emis, 5)
        self.assertEqual(e.stats.doublons_ignores, 4)

    def test_teb_mesure_avant_crc_meme_si_la_trame_est_rejetee(self):
        from modem_fsk import demoduler as demodulation
        def corrompre(signal, *args, **kwargs):
            bits = demodulation(signal, *args, **kwargs)
            bits[50] ^= 1
            return bits
        canal = CanalFSK()
        with patch('canal_fsk.demoduler', side_effect=corrompre):
            with self.assertRaises(RuntimeError):
                EmetteurARQ(canal, RecepteurARQ(), max_attempts=1).transferer(b'abc')
        self.assertEqual(canal.bits_bruts_errones, 1)
        self.assertGreater(canal.bits_bruts_transmis, 24)

    def test_csv_teb_et_taille_superieure_a_256(self):
        with tempfile.TemporaryDirectory() as dossier:
            ligne = executer(essais=1, taille=300, sortie=dossier, niveaux=[6])[0]
            self.assertEqual(ligne['octets_acceptes'], 300)
            self.assertEqual(ligne['bits_comparables_charge'], 2400)
            self.assertEqual(ligne['teb_brut'], 0)
            self.assertEqual(ligne['sha_original'], ligne['sha_recu'])

    def test_donnees_en_echec_ne_comptent_pas_comme_debit_utile(self):
        with tempfile.TemporaryDirectory() as dossier:
            ligne = executer(essais=1, sortie=dossier, niveaux=[-30])[0]
            self.assertEqual(ligne['statut'], 'ECHEC')
            self.assertEqual(ligne['debit_utile'], 0)
            self.assertGreater(ligne['teb_brut'], 0)
