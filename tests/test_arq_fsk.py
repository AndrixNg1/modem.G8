import unittest
from arq import EmetteurARQ, RecepteurARQ
from canal_fsk import CanalFSK
class TestARQFSK(unittest.TestCase):
 def test_sans_bruit_binaire(self):
  r=RecepteurARQ(); e=EmetteurARQ(CanalFSK('G8'),r); d=bytes(range(256)); self.assertEqual(e.transferer(d),d)
 def test_perte_i(self):
  r=RecepteurARQ(); e=EmetteurARQ(CanalFSK('G8',actions=['perte_i']),r); self.assertEqual(e.transferer(b'G8'),b'G8'); self.assertEqual(e.stats.retransmissions,1)
 def test_ack_perdu_doublon(self):
  r=RecepteurARQ(); e=EmetteurARQ(CanalFSK('G8',actions=['ok','perte_ack']),r); self.assertEqual(e.transferer(b'G8'),b'G8'); self.assertEqual(r.stats.doublons_ignores,1)
 def test_nak_transporte_fsk(self):
  r=RecepteurARQ(); c=CanalFSK('G8',actions=['nak']); e=EmetteurARQ(c,r); self.assertEqual(e.transferer(b'G8'),b'G8'); self.assertEqual(e.stats.nak,1); self.assertEqual(e.stats.retransmissions,1); self.assertIn('NAK transporté par FSK',c.evenements)
