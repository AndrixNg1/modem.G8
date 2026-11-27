import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perturbations_acoustiques import appliquer, attenuation, derive_horloge, echo, impulsions, ronflement
from modem_fsk import synchroniser_porteuse
from protection_signal import pretraiter_signal

class TestPerturbationsAcoustiques(unittest.TestCase):
    def setUp(self): self.x=np.sin(2*np.pi*1000*np.arange(4800)/48000)
    def test_reproductibilite_et_entree_preservee(self):
        brut=self.x.copy()
        a=appliquer(self.x,48000,[{'type':'blanc','sb_db':0},{'type':'impulsions','db':-5}],7)
        b=appliquer(self.x,48000,[{'type':'blanc','sb_db':0},{'type':'impulsions','db':-5}],7)
        self.assertTrue(np.array_equal(a,b)); self.assertTrue(np.array_equal(self.x,brut))
    def test_echo_attenuation_derive_et_ronflement(self):
        self.assertLess(np.max(np.abs(attenuation(self.x,.5))),np.max(np.abs(self.x)))
        self.assertTrue(np.any(echo(self.x,48000,(1,3),(.2,.1)) != self.x))
        self.assertNotEqual(len(derive_horloge(self.x,1.01)),len(self.x))
        self.assertTrue(np.any(ronflement(self.x,48000) != self.x))
    def test_impulsions(self):
        self.assertTrue(np.any(impulsions(self.x,taux=.01,seed=3) != self.x))
    def test_faux_preambule_bruit_filtre_rejete(self):
        bruit=np.random.default_rng(3001).normal(0,.02,24000)
        y=pretraiter_signal(bruit,7400,7600,48000,'G8','basic')
        with self.assertRaises(ValueError):
            synchroniser_porteuse(y,7400,7600,300,48000,min_porteuse_bits=8)

if __name__ == '__main__': unittest.main()
