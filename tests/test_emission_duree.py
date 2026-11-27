import tempfile
import unittest
from pathlib import Path

import numpy as np

from emmettre import ajouter_garde_fin
from emettre import signal_message, ecrire_wav
from recevoir import recevoir_wav


class TestEmissionDuree(unittest.TestCase):
    def test_trois_secondes_sans_changer_le_message(self):
        for profil in ('G8', 'G8_acoustique'):
            with self.subTest(profil=profil), tempfile.TemporaryDirectory() as dossier:
                signal, _, config = signal_message('BONJOUR G8', profil, duree=3)
                joue = ajouter_garde_fin(signal, profil)
                self.assertEqual(len(joue), 3 * config['fe'])
                self.assertLessEqual(float(np.max(np.abs(joue))), .5)
                wav = ecrire_wav(Path(dossier) / 'trois_secondes.wav', joue, config['fe'])
                self.assertEqual(recevoir_wav(wav, profil)['texte'], 'BONJOUR G8')

    def test_duree_invalide_et_absence_de_troncature(self):
        for duree in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                signal_message('G8', duree=duree)
        original, _, _ = signal_message('BONJOUR G8', 'G8_acoustique')
        court, _, _ = signal_message('BONJOUR G8', 'G8_acoustique', duree=.1)
        np.testing.assert_array_equal(original, court)
