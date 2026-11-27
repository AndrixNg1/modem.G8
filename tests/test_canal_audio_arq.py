import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from arq import EmetteurARQ, RecepteurARQ, trame_supervision
from canal_audio_arq import CanalAudioARQ, ServeurAudioARQ, decoder_capture, signal_trame
from trame import construire_trame

class TestCanalAudioARQ(unittest.TestCase):
    def test_trame_audio_decodee_et_protection(self):
        brute=construire_trame(0x18,0,b'G8')
        for mode in ('off','basic','advanced'):
            recu,info=decoder_capture(signal_trame(brute), 'G8', mode)
            self.assertEqual(recu,brute); self.assertEqual(info['ambigus'],0)

    def test_emetteur_recoit_ack_sonore_simule(self):
        joue=[]
        def faux_jouer(signal,*args): joue.append(signal)
        def faux_enregistrer(*args): return signal_trame(trame_supervision(1)), {'ecretage':False}
        with patch('canal_audio_arq.jouer',faux_jouer), patch('canal_audio_arq.enregistrer',faux_enregistrer), patch('canal_audio_arq.time.sleep'):
            c=CanalAudioARQ('G8','basic',ecoute_ack=.01)
            e=EmetteurARQ(c,RecepteurARQ(),timeout=.01)
            e.transferer(b'G8')
        self.assertEqual(e.stats.ack,1); self.assertEqual(c.journal.etat,'ATTENTE_ACK'); self.assertTrue(joue)

    def test_recepteur_emet_ack_et_nak(self):
        emis=[]
        with patch('canal_audio_arq.jouer',lambda signal,*args: emis.append(signal)), patch('canal_audio_arq.time.sleep'):
            s=ServeurAudioARQ('G8','basic')
            ack=s.traiter_capture(signal_trame(construire_trame(0x18,0,b'X')))
            corrompue=bytearray(construire_trame(0x18,0,b'X')); corrompue[-3] ^= 1
            nak=s.traiter_capture(signal_trame(bytes(corrompue)))
            silence=s.traiter_capture(np.zeros(100))
        self.assertIsNotNone(ack); self.assertTrue(nak[2] & 0x20); self.assertIsNone(silence); self.assertEqual(len(emis),2)

    def test_saturation_non_normalisee(self):
        from audio_io import statistiques
        stats=statistiques(np.array([2.168,-.2],dtype=np.float32))
        self.assertAlmostEqual(stats['amplitude_max'],2.168,places=5)
        self.assertTrue(stats['ecretage'])
    def test_nan_ne_devient_pas_silence(self):
        from audio_io import statistiques
        with self.assertRaisesRegex(ValueError,'non finis'):
            statistiques(np.array([0.,np.nan]))

if __name__=='__main__': unittest.main()
