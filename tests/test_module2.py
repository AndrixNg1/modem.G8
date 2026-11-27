import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import F0, F1, R, FE, AMPLITUDE, SAMPLES_PER_BIT
from modem_fsk import moduler
from emettre import encoder_message, profils, signal_message, ecrire_wav, ANNONCE_SECONDES
from modem_fsk import energie, demoduler, synchroniser_porteuse
from recevoir import recevoir_wav

class TestFSKPhase1(unittest.TestCase):
    def test_bit_zero_et_un(self):
        self.assertEqual(len(moduler([0],F0,F1,R)), SAMPLES_PER_BIT)
        self.assertEqual(len(moduler([1],F0,F1,R)), SAMPLES_PER_BIT)
    def test_nombre_duree_amplitude_et_ecretage(self):
        s=moduler([1,0,1],F0,F1,R)
        self.assertEqual(len(s),3*SAMPLES_PER_BIT); self.assertAlmostEqual(len(s)/FE,3/R)
        self.assertLessEqual(np.max(np.abs(s)),AMPLITUDE); self.assertLess(np.max(np.abs(s)),1)
    def test_frequences_par_correlation(self):
        t=np.arange(SAMPLES_PER_BIT)/FE
        for bit,bonne,mauvaise in ((0,F0,F1),(1,F1,F0)):
            s=moduler([bit],F0,F1,R)
            energie=lambda f: abs(np.vdot(s,np.exp(2j*np.pi*f*t)))
            self.assertGreater(energie(bonne), energie(mauvaise))
    def test_phase_non_reinitialisee_transition(self):
        s=moduler([0,1],F0,F1,R)
        attendu=AMPLITUDE*np.sin(SAMPLES_PER_BIT*2*np.pi*F0/FE)
        self.assertAlmostEqual(s[SAMPLES_PER_BIT],attendu,places=12)
        self.assertNotAlmostEqual(s[SAMPLES_PER_BIT],0.0,places=8)
    def test_vide_bits_et_parametres_invalides(self):
        self.assertEqual(moduler([],F0,F1,R).size,0)
        for bits in ([2],["1"]):
            with self.assertRaises(ValueError): moduler(bits,F0,F1,R)
        for args in ((F0,F1,0),(F0,F0,R),(F0,F1,301)):
            with self.assertRaises(ValueError): moduler([0],*args)
    def test_8n1_et_profils(self):
        self.assertEqual(encoder_message("A"),[0,1,0,0,0,0,0,1,0,1])
        self.assertEqual(profils("G8")["f0"],7400); self.assertEqual(profils("bell103")["f1"],1270)
    def test_porteuse_annonce_et_wav(self):
        signal,bits,p=signal_message("A","G8")
        self.assertEqual(bits[:int(ANNONCE_SECONDES*R)],[1]*90)
        self.assertEqual(len(signal),(90+10)*SAMPLES_PER_BIT)
        with tempfile.TemporaryDirectory() as d:
            chemin=ecrire_wav(Path(d)/"fsk.wav",signal,p["fe"]); fe,lu=wavfile.read(chemin)
            self.assertEqual(fe,FE); self.assertEqual(len(lu),len(signal)); self.assertLessEqual(np.max(np.abs(lu)),AMPLITUDE)

    def test_energie_phase_et_demodulation(self):
        s0=moduler([0],F0,F1,R); s1=moduler([1],F0,F1,R)
        self.assertGreater(energie(s0,F0,FE),energie(s0,F1,FE))
        self.assertGreater(energie(s1,F1,FE),energie(s1,F0,FE))
        self.assertAlmostEqual(energie(np.zeros(160),F0,FE),0)
        self.assertEqual(demoduler(moduler([0,1,1,0],F0,F1,R),F0,F1,R),[0,1,1,0])

    def test_synchronisation_silences_et_decalage(self):
        signal,bits,p=signal_message("HELLO WORLD","G8")
        decale=np.r_[np.zeros(37),signal,np.zeros(91)]
        self.assertEqual(synchroniser_porteuse(decale,F0,F1,R,FE),37+90*SAMPLES_PER_BIT)
        with tempfile.TemporaryDirectory() as d:
            chemin=ecrire_wav(Path(d)/"decale.wav",decale)
            self.assertEqual(recevoir_wav(chemin)["texte"],"HELLO WORLD")

    def test_boucles_utf8_longue_et_binaire(self):
        for texte in ("BONJOUR G8","Université Nouveaux Horizons","Télématique G8","A"*160):
            signal,_,p=signal_message(texte,"G8")
            with tempfile.TemporaryDirectory() as d:
                chemin=ecrire_wav(Path(d)/"message.wav",signal,p["fe"])
                self.assertEqual(recevoir_wav(chemin,"G8")["texte"],texte)
        brut=bytes(range(256)); bits=[1]*90+[b for o in brut for b in [0]+[(o>>i)&1 for i in range(8)]+[1]]
        with tempfile.TemporaryDirectory() as d:
            chemin=ecrire_wav(Path(d)/"bin.wav",moduler(bits,F0,F1,R))
            self.assertEqual(recevoir_wav(chemin,"G8",False)["octets"],brut)

    def test_bell103_troncature_silence_et_tramage_invalide(self):
        signal,_,p=signal_message("BONJOUR G8","bell103")
        with tempfile.TemporaryDirectory() as d:
            chemin=ecrire_wav(Path(d)/"bell.wav",signal,p["fe"])
            self.assertEqual(recevoir_wav(chemin,"bell103")["texte"],"BONJOUR G8")
            silence=ecrire_wav(Path(d)/"silence.wav",np.zeros(500))
            with self.assertRaises(ValueError): recevoir_wav(silence)
            tronque=ecrire_wav(Path(d)/"tronc.wav",signal[:-200])
            with self.assertRaises(ValueError): recevoir_wav(tronque,"bell103")
            invalide=ecrire_wav(Path(d)/"invalide.wav",moduler([1]*90+[0]+[0]*8+[0],p["f0"],p["f1"],p["R"]))
            with self.assertRaises(ValueError): recevoir_wav(invalide,"bell103")
