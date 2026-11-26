import csv
import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import F0, F1, R, FE
from modem_fsk import moduler, demoduler, ajouter_bruit
from mesures_module2 import comparer_bits, executer

class TestBruitModule2(unittest.TestCase):
    def setUp(self): self.signal=moduler([0,1]*50,F0,F1,R)
    def test_reproductibilite_et_original(self):
        original=self.signal.copy(); a,ia=ajouter_bruit(self.signal,3,2026,True); b,ib=ajouter_bruit(self.signal,3,2026,True)
        self.assertTrue(np.array_equal(a,b)); self.assertTrue(np.array_equal(self.signal,original)); self.assertFalse(np.array_equal(a,self.signal))
    def test_sb_mesure_et_absence_ecretage(self):
        bruit,info=ajouter_bruit(self.signal,-6,42,True)
        self.assertAlmostEqual(info["sb_db_mesure"],-6,delta=.7); self.assertGreater(np.max(np.abs(bruit)),.5)
    def test_entrees_invalides(self):
        for signal,sb in (([],0),(np.zeros(10),0),(self.signal,float("nan"))):
            with self.assertRaises(ValueError): ajouter_bruit(signal,sb)
    def test_comparaison_stricte(self):
        self.assertEqual(comparer_bits([0,1],[0,1]),(0,0,0))
        self.assertEqual(comparer_bits([0,1,1],[0,0]),(2,1,1))
    def test_demodulation_sans_bruit_et_moderee(self):
        bits=[0,1,1,0]*30
        self.assertEqual(demoduler(moduler(bits,F0,F1,R),F0,F1,R),bits)
        bruite=ajouter_bruit(moduler(bits,F0,F1,R),6,2026)
        self.assertEqual(len(demoduler(bruite,F0,F1,R)),len(bits))
    def test_csv_mesures_petit(self):
        with tempfile.TemporaryDirectory() as d:
            lignes=executer(100,2026,Path(d))
            self.assertEqual(len(lignes),7)
            with (Path(d)/"resultats_teb.csv").open(encoding="utf-8-sig") as f: self.assertEqual(len(list(csv.DictReader(f,delimiter=";"))),7)
