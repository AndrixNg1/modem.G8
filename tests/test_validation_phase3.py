import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyser_capture_physique import comparer
from campagne_faux_positifs import capture_sans_transmission
from emettre import signal_message

class TestValidationPhase3(unittest.TestCase):
    def test_captures_sans_transmission_reproductibles(self):
        a=capture_sans_transmission('combine',48000,.1,5,7500)
        b=capture_sans_transmission('combine',48000,.1,5,7500)
        self.assertTrue(np.array_equal(a,b))
        self.assertEqual(len(capture_sans_transmission('silence',48000,.1,5,7500)),4800)
    def test_analyse_reference_apres_decodage(self):
        x,_,_=signal_message('G8')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'capture.wav'; wavfile.write(path,48000,x.astype(np.float32))
            lignes=comparer(path,'G8','G8',25,'silencieuse',1)
        self.assertEqual([r['mode'] for r in lignes],['off','basic','advanced'])
        self.assertTrue(all(r['statut']=='recu' for r in lignes))
        self.assertTrue(all(float(r['teb']) == 0 for r in lignes))

if __name__=='__main__': unittest.main()
