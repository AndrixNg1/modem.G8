import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import GROUPE, ADRESSE, N, F0, F1, FE, R, AMPLITUDE, CRC_POLYNOME, CRC_INIT, BELL103
from trame import construire_trame, octets_vers_bits, bits_vers_octets, analyser_corps, preparer_trames, encoder_trames, reconstruire
from audio_test import generer_tonalite

class TestFinalisation(unittest.TestCase):
    def test_configuration_g8_et_bell103(self):
        self.assertEqual((GROUPE,ADRESSE,N,F0,F1,FE,R,AMPLITUDE,CRC_POLYNOME,CRC_INIT),("G8",0x18,48,7400,7600,48000,300,.5,0x1021,0xFFFF))
        self.assertEqual(BELL103,{"F0":1070,"F1":1270,"R":300,"FORMAT":"8N1"})
    def test_crc_erreurs_doubles_echantillon(self):
        bits=octets_vers_bits(construire_trame(ADRESSE,0,bytes(range(N)))[1:-1])
        for a,b in ((0,1),(7,200),(100,len(bits)-1)):
            corrompus=bits.copy(); corrompus[a]^=1; corrompus[b]^=1
            with self.assertRaises(ValueError): analyser_corps(bits_vers_octets(corrompus))
    def test_rafales_jusqu_a_16_bits(self):
        bits=octets_vers_bits(construire_trame(ADRESSE,0,bytes(range(N)))[1:-1])
        for largeur in range(1,17):
            corrompus=bits.copy()
            for i in range(10,10+largeur): corrompus[i]^=1
            with self.assertRaises(ValueError): analyser_corps(bits_vers_octets(corrompus))
    def test_limites_et_nom_utf8(self):
        for data in (bytes(range(48)),bytes(range(49)),bytes(range(256))*20):
            trames,_=preparer_trames("été.bin",data)
            self.assertEqual(reconstruire(encoder_trames(trames)),("été.bin",data))
    def test_wav_1000hz(self):
        with tempfile.TemporaryDirectory() as dossier:
            r=generer_tonalite(Path(dossier)/"ton.wav")
            self.assertTrue(Path(r["chemin"]).is_file()); self.assertEqual(r["fe"],48000)
            self.assertEqual(r["echantillons"],96000); self.assertAlmostEqual(r["duree"],2)
            self.assertLessEqual(r["amplitude_max"],.5); self.assertFalse(r["ecretage"])
            self.assertAlmostEqual(r["frequence_dominante"],1000)
    def test_imports_sans_effet_de_bord(self):
        import config, source, crc, trame, mesures_module1, audio_test
