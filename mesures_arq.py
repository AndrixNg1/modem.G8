"""Campagne AWGN reproductible ARQ/FSK (simulation, jamais mesure physique)."""
from pathlib import Path
import argparse,csv,hashlib
from canal_fsk import CanalFSK
from arq import EmetteurARQ,RecepteurARQ

NIVEAUX=[6,3,0,-3,-6,-9,-12]
def executer(essais=20,taille=144,graine=2026,sortie='mesures/module3/simulation',niveaux=NIVEAUX,arq=True):
 out=Path(sortie); out.mkdir(parents=True,exist_ok=True); lignes=[]
 data=bytes(range(256))[:taille]
 for sb in niveaux:
  for i in range(essais):
   r=RecepteurARQ(); c=CanalFSK('G8',sb_db=sb,seed=graine+i+100*sb); e=EmetteurARQ(c,r,max_attempts=5 if arq else 1)
   try: recu=e.transferer(data); statut='OK'
   except RuntimeError: recu=bytes(r.donnees); statut='ECHEC'
   lignes.append(dict(sb_db=sb,essai=i,bits_comparables=len(data)*8,bits_errones=sum(a!=b for a,b in zip(data,recu))*8,teb_brut='',trames_originales=e.stats.trames_originales,tentatives=e.stats.tentatives,retransmissions=e.stats.retransmissions,ack_emis=e.stats.ack_emis,ack_recus=e.stats.ack,nak_recus=e.stats.nak,doublons=e.stats.doublons_ignores,timeouts=e.stats.delais,octets_acceptes=e.stats.octets_acceptes,duree_simulee=e.stats.duree_simulee,debit_utile=(len(recu)*8/e.stats.duree_simulee if e.stats.duree_simulee else 0),statut=statut,sha_original=hashlib.sha256(data).hexdigest(),sha_recu=hashlib.sha256(recu).hexdigest()))
  print(f'S/B {sb:+} dB : {essais} essais')
 with (out/('resultats_awgn_arq.csv' if arq else 'resultats_awgn_sans_arq.csv')).open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=lignes[0]);w.writeheader();w.writerows(lignes)
 return lignes
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--essais',type=int,default=20);p.add_argument('--taille',type=int,default=144);p.add_argument('--graine',type=int,default=2026);p.add_argument('--sortie',default='mesures/module3/simulation');p.add_argument('--rapide',action='store_true');p.add_argument('--sans-arq',action='store_true');a=p.parse_args();executer(1 if a.rapide else a.essais,a.taille,a.graine,a.sortie,arq=not a.sans_arq)
