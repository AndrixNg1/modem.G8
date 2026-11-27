import unittest
from arq import CanalSimule, RecepteurARQ, EmetteurARQ, ARQ_MAX_ATTEMPTS, ARQ_TIMEOUT

class TestARQ(unittest.TestCase):
    def transfert(self, actions=(), data=b"BONJOUR G8"):
        r=RecepteurARQ(); e=EmetteurARQ(CanalSimule(actions),r); self.assertEqual(e.transferer(data),data); return e,r
    def test_normal(self): self.assertEqual(self.transfert()[0].stats.ack,1)
    def test_perte_i(self):
        e,_=self.transfert(["perte_i"], b"A"*49); self.assertEqual(e.stats.retransmissions,1); self.assertEqual(e.stats.delais,1); self.assertEqual(e.stats.octets_acceptes,49)
    def test_corruption_i(self): e,_=self.transfert(["corruption_i"]); self.assertEqual(e.stats.nak,1)
    def test_perte_ack_doublon(self):
        e,r=self.transfert(["perte_ack"], b"G8"); self.assertEqual(r.stats.doublons_ignores,1); self.assertEqual(e.stats.doublons_ignores,1); self.assertEqual(e.stats.octets_acceptes,2); self.assertEqual(e.stats.retransmissions,1)
    def test_ack_corrompu(self): self.assertEqual(self.transfert(["corruption_ack"])[0].stats.retransmissions,1)
    def test_mauvais_ack(self): self.assertEqual(self.transfert(["mauvais_ack"])[0].stats.retransmissions,1)
    def test_nak(self): self.assertEqual(self.transfert(["nak"])[0].stats.nak,1)
    def test_plusieurs_trames_binaire(self):
        data=bytes(range(256)); e,r=self.transfert([],data); self.assertEqual(e.stats.trames_originales,6); self.assertEqual(r.donnees,data)
    def test_abandon(self):
        r=RecepteurARQ(); e=EmetteurARQ(CanalSimule(["perte_i"]*ARQ_MAX_ATTEMPTS),r)
        with self.assertRaisesRegex(RuntimeError,"5 tentatives"): e.transferer(b"x")
        self.assertEqual(e.stats.tentatives,ARQ_MAX_ATTEMPTS)
    def test_timeout_constante(self): self.assertEqual(ARQ_TIMEOUT,3.0)
