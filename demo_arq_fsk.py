"""Démonstration ARQ/FSK locale, sans périphérique audio."""
import argparse
from arq import EmetteurARQ, RecepteurARQ
from canal_fsk import CanalFSK

SCENARIOS={"parfait":[],"perte-i":["perte_i"],"perte-ack":["ok","perte_ack"],"corruption-i":["corruption_i"],"corruption-ack":["ok","corruption_ack"],"nak":["nak"],"echec":["perte_i"]*5}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--profil",default="G8"); p.add_argument("--scenario",choices=SCENARIOS,default="parfait"); p.add_argument("--sb",type=float); p.add_argument("--seed",type=int,default=2026); a=p.parse_args()
 r=RecepteurARQ(); c=CanalFSK(a.profil,SCENARIOS[a.scenario],a.sb,a.seed); e=EmetteurARQ(c,r)
 try: recu=e.transferer(b"BONJOUR G8")
 except RuntimeError as exc: print("ECHEC:",exc); recu=b""
 print(f"scenario={a.scenario} profil={a.profil} reçu={recu!r}"); print(e.stats); print("événements:", c.evenements)
if __name__=="__main__": main()
