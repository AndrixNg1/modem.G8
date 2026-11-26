import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_io import enregistrer, jouer, normaliser_peripherique
from config import FE, R
from diagnostic_audio import analyser_signal
from emettre import encoder_message, signal_message
from modem_fsk import pretraiter_signal
from recevoir import recevoir_signal


ROOT = Path(__file__).resolve().parents[1]


def signal_periode_variable(bits, periode, amplitude=0.03):
    p = int(np.ceil(len(bits) * periode))
    freqs = np.empty(p)
    for i, bit in enumerate(bits):
        debut, fin = round(i * periode), round((i + 1) * periode)
        freqs[debut:fin] = 7600 if bit else 7400
    phase = 2 * np.pi * np.cumsum(freqs) / FE
    return amplitude * np.sin(phase)


class FauxPeripherique:
    def __init__(self):
        self.joue = None
        self.enregistre = None

    def query_devices(self, device=None):
        return {"name": str(device), "max_input_channels": 1,
                "max_output_channels": 1, "default_samplerate": FE}

    def check_input_settings(self, **kwargs):
        return None

    def check_output_settings(self, **kwargs):
        return None

    def play(self, signal, fe, device=None):
        self.joue = device

    def rec(self, n, **kwargs):
        self.enregistre = kwargs["device"]
        return np.zeros((n, 1), dtype=np.float32)

    def wait(self):
        return None


class TestReceptionRobuste(unittest.TestCase):
    def setUp(self):
        self.signal, self.bits, self.profil = signal_message("BONJOUR G8")

    def test_identifiants_numeriques_passes_a_sounddevice(self):
        faux = FauxPeripherique()
        self.assertEqual(normaliser_peripherique("15"), 15)
        self.assertEqual(normaliser_peripherique("13"), 13)
        with patch("audio_io._sd", return_value=faux):
            jouer(np.array([.1]), device="15")
            self.assertEqual(faux.joue, 15)
            enregistrer(.001, device="13")
            self.assertEqual(faux.enregistre, 13)

    def test_faible_amplitude(self):
        resultat = recevoir_signal(self.signal * .02)
        self.assertEqual(resultat["texte"], "BONJOUR G8")

    def test_bruit_avant_apres_et_silence_final_non_aligne(self):
        rng = np.random.default_rng(2026)
        bruit = rng.normal(0, .0005, 1200)
        capture = np.r_[bruit, self.signal * .2, rng.normal(0, .0005, 135)]
        resultat = recevoir_signal(capture)
        self.assertEqual(resultat["texte"], "BONJOUR G8")

    def test_attenuation_differente_des_frequences(self):
        attenue = self.signal.copy()
        for i, bit in enumerate(self.bits):
            attenue[i * (FE // R):(i + 1) * (FE // R)] *= .25 if bit == 0 else .7
        self.assertEqual(recevoir_signal(attenue)["texte"], "BONJOUR G8")

    def test_echo_et_decalage_de_synchronisation(self):
        echo = np.r_[np.zeros(80), self.signal[:-80]] * .12
        capture = np.r_[np.zeros(37), self.signal * .2 + echo, np.zeros(91)]
        resultat = recevoir_signal(capture)
        self.assertEqual(resultat["texte"], "BONJOUR G8")
        self.assertLessEqual(
            abs(resultat["debut_echantillon"] - (37 + 90 * (FE // R))),
            (FE // R) // 2,
        )

    def test_derive_horloge_de_1_5_pourcent(self):
        bits = [1] * int(.3 * R) + encoder_message("BONJOUR G8")
        capture = signal_periode_variable(bits, 160 * 1.015)
        resultat = recevoir_signal(capture)
        self.assertEqual(resultat["texte"], "BONJOUR G8")

    def test_troncature_reelle_est_signalee(self):
        with self.assertRaisesRegex(ValueError, "Transmission tronquée"):
            recevoir_signal(self.signal[:-20])

    def test_stop_invalide_diagnostique_sans_le_forcer(self):
        bits = [1] * 90 + [0] + [0] * 8 + [0]
        from modem_fsk import moduler
        capture = moduler(bits, self.profil["f0"], self.profil["f1"], R)
        with self.assertRaisesRegex(ValueError, "Caractère 1.*E0/E1.*start=.*stop="):
            recevoir_signal(capture, debug=True)

    def test_stop_invalide_tente_reprise_sur_le_caractere_suivant(self):
        bits = [1] * 90 + [0] + [1] * 8 + [0] + encoder_message("B")
        from modem_fsk import moduler
        capture = moduler(bits, self.profil["f0"], self.profil["f1"], R)
        with self.assertRaisesRegex(ValueError, "resynchronisation possible"):
            recevoir_signal(capture)

    def test_wav_physique_sans_porteuse_g8_detectable(self):
        chemin = ROOT / "mesures/module2/physique/air/test_local_recu.wav"
        fe, capture = wavfile.read(chemin)
        mesures = analyser_signal(capture, fe, "G8")
        self.assertEqual(mesures["duree"], 15.0)
        self.assertIsNone(mesures["debut_porteuse"])
        self.assertIsNone(mesures["fin_transmission"])
        self.assertGreater(mesures["amplitude_max"], mesures["bruit_global_estime"])

    def test_pretraitement_retire_continu_sans_modifier_lentree(self):
        x = self.signal + .2
        brut = x.copy()
        traite = pretraiter_signal(x, self.profil["f0"], self.profil["f1"])
        self.assertTrue(np.array_equal(x, brut))
        self.assertLess(abs(float(np.mean(traite))), 1e-4)


if __name__ == "__main__":
    unittest.main()
