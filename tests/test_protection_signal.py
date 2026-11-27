import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import FE, PROFILS
from modem_fsk import moduler, energie
from protection_signal import (supprimer_composante_continue, filtre_passe_bande,
    estimer_bruit, mesurer_sb, detecter_impulsions, reduire_bruit,
    pretraiter_signal, calculer_confiance)


class TestProtectionSignal(unittest.TestCase):
    def test_continu_et_entree_preservee(self):
        x = np.array([.2, .3, .4]); brut = x.copy()
        self.assertAlmostEqual(float(np.mean(supprimer_composante_continue(x))), 0)
        self.assertTrue(np.array_equal(x, brut))

    def test_passe_bande_conserve_fsk_et_attenue_50hz(self):
        t = np.arange(FE) / FE
        x = np.sin(2*np.pi*7400*t) + np.sin(2*np.pi*50*t)
        y = filtre_passe_bande(x, FE, 7000, 8000, ordre=4)
        self.assertGreater(energie(y, 7400, FE), 100 * energie(y, 50, FE))

    def test_profils_et_modes(self):
        for nom, p in PROFILS.items():
            bits = [0, 1] * 5
            x = moduler(bits, p['f0'], p['f1'], p['R'], p['fe'])
            y = pretraiter_signal(x, p['f0'], p['f1'], p['fe'], nom, 'basic')
            self.assertEqual(y.shape, x.shape, nom)
        x = np.array([.2, -.1])
        self.assertTrue(np.array_equal(pretraiter_signal(x, 7400, 7600, FE, 'G8', 'off'), x))

    def test_bruit_explicitement_non_estimable_sans_reference(self):
        x = np.zeros(100)
        self.assertFalse(estimer_bruit(x, FE)['estimable'])
        bruit = np.random.default_rng(1).normal(0, .01, 1000)
        estimation = estimer_bruit(x, FE, bruit)
        self.assertTrue(estimation['estimable'])
        self.assertAlmostEqual(estimation['puissance'], float(np.mean(bruit**2)))
        self.assertIsNotNone(mesurer_sb(np.ones(100), bruit=bruit))

    def test_clic_isole_et_confiance(self):
        x = np.zeros(20); x[10] = 1.
        stats = detecter_impulsions(x)
        self.assertTrue(stats['impulsions'][10])
        self.assertEqual(reduire_bruit(x, stats['impulsions'])[10], 0.)
        self.assertAlmostEqual(float(calculer_confiance(2, 2)), 0.)
        self.assertGreater(float(calculer_confiance(1, 100)), .9)


if __name__ == '__main__':
    unittest.main()
