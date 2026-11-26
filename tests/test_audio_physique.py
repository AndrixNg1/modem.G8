import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
from scipy.io import wavfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import audio_io
from emettre import signal_message, ecrire_wav
from recevoir import recevoir_wav
from mesures_physiques import initialiser, comparer_bits_physiques

class FauxSD:
    def __init__(self): self.joue=None
    def query_devices(self,device=None):
        infos=[{"name":"mock","max_input_channels":1,"max_output_channels":1,"default_samplerate":48000},
               {"name":"sortie seule","max_input_channels":0,"max_output_channels":2,"default_samplerate":44100}]
        if device == "inexistant": raise ValueError("absent")
        if isinstance(device,int): return infos[device]
        if isinstance(device,str): return infos[0]
        return infos
    def check_input_settings(self,**kw): return None
    def check_output_settings(self,**kw): return None
    def play(self,x,fe,device=None): self.joue=(x,fe,device)
    def rec(self,n,**kw): return np.zeros((n,1),np.float32)
    def wait(self): return None

class TestAudioPhysique(unittest.TestCase):
    def test_stats_et_ecretage(self):
        self.assertTrue(audio_io.statistiques(np.array([1.]))["ecretage"])
        self.assertFalse(audio_io.statistiques(np.array([.5]))["ecretage"])
    def test_mock_peripheriques_jeu_acquisition(self):
        faux=FauxSD()
        with patch("audio_io._sd",return_value=faux):
            self.assertEqual(audio_io.lister_peripheriques()[0]["name"],"mock")
            self.assertIn("entrée=1",audio_io.formater_peripheriques())
            self.assertEqual(audio_io.jouer(np.array([.5,-.5]),device="mock")["amplitude_max"],.5)
            x,stats=audio_io.enregistrer(.001,device="mock"); self.assertEqual(len(x),48); self.assertEqual(stats["amplitude_max"],0)
    def test_normalisation_indices_noms_et_defaut(self):
        self.assertEqual(audio_io.normaliser_peripherique("15"),15)
        self.assertEqual(audio_io.normaliser_peripherique(" USB Audio "),"USB Audio")
        self.assertIsNone(audio_io.normaliser_peripherique(None))
        faux=FauxSD()
        with patch("audio_io._sd",return_value=faux):
            audio_io.jouer(np.array([.5]),device="0")
            self.assertEqual(faux.joue[2],0)
            audio_io.enregistrer(.001,device=None)
            with self.assertRaisesRegex(RuntimeError,"aucun canal entrée"): audio_io.enregistrer(.001,device="1")
            with self.assertRaisesRegex(RuntimeError,"introuvable"): audio_io.enregistrer(.001,device="inexistant")
    def test_erreurs_audio_et_wav_compatible(self):
        with self.assertRaises(ValueError): audio_io.jouer(np.array([1.]),volume=1)
        signal,_,p=signal_message("BONJOUR G8")
        with tempfile.TemporaryDirectory() as d:
            f=ecrire_wav(Path(d)/"x.wav",signal,p["fe"]); self.assertEqual(recevoir_wav(f)["texte"],"BONJOUR G8")
    def test_comparaison_et_csv_vides(self):
        self.assertEqual(comparer_bits_physiques([0,1,1],[0,0]),{"bits_transmis":3,"bits_recus":2,"bits_errones":2,"bits_perdus":1,"bits_inseres":0,"TEB":2/3})
        with tempfile.TemporaryDirectory() as d:
            base=initialiser(d); self.assertTrue((base/"cable").is_dir()); self.assertTrue((base/"resultats_physiques.csv").is_file())

    def test_attenuation_continue_et_echo_simple(self):
        signal,_,p=signal_message("BONJOUR G8")
        variantes=(signal*.15, signal+.03, signal+np.r_[np.zeros(80),signal[:-80]]*.15)
        with tempfile.TemporaryDirectory() as d:
            for i,signal_test in enumerate(variantes):
                f=ecrire_wav(Path(d)/f"v{i}.wav",signal_test,p["fe"])
                self.assertEqual(recevoir_wav(f)["texte"],"BONJOUR G8")
