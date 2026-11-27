"""Artefacts de rapport issus exclusivement des CSV/WAV simulés module 3."""
from pathlib import Path
import csv, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.io import wavfile
from arq import trame_supervision
from trame import construire_trame, trame_vers_bits
from canal_fsk import SYNC
from emettre import profils
from modem_fsk import moduler, ajouter_bruit

BASE=Path('mesures/module3/simulation')
def main():
 BASE.mkdir(parents=True,exist_ok=True); p=profils('G8')
 for nom,trame in [('trame_i.wav',construire_trame(0x18,0,b'G8')),('trame_ack.wav',trame_supervision(1)),('trame_nak.wav',trame_supervision(1,True))]:
  s=moduler(SYNC+trame_vers_bits(trame),p['f0'],p['f1'],p['R'],p['fe']); wavfile.write(BASE/nom,p['fe'],s.astype('float32'))
 s,_=ajouter_bruit(s,-6,2026,True); wavfile.write(BASE/'trame_ack_bruitee.wav',p['fe'],s.astype('float32'))
 si=wavfile.read(BASE/'trame_i.wav')[1]; bi,_=ajouter_bruit(si,-6,2027,True); wavfile.write(BASE/'trame_i_bruitee.wav',p['fe'],bi.astype('float32'))
 rows=list(csv.DictReader((BASE/'synthese_awgn.csv').open())); x=np.array([float(r['sb_db']) for r in rows])
 def fig(y,n,t,l):
  f,a=plt.subplots();a.plot(x,y,'o-',label=l);a.set(xlabel='S/B (dB)',ylabel=l,title=t);a.grid();a.legend();f.tight_layout();f.savefig(BASE/n,dpi=160);plt.close(f)
 fig([float(r['taux_arq']) for r in rows],'taux_reussite_avec_sans_arq.png','Taux de réussite ARQ','ARQ')
 fig([float(r['retransmissions']) for r in rows],'retransmissions_en_fonction_sb.png','Retransmissions','nombre')
 fig([float(r['debit_moyen']) for r in rows],'debit_utile_en_fonction_sb.png','Débit utile','bit/s')
 fig([float(r['duree_moyenne']) for r in rows],'duree_moyenne_transfert.png','Durée simulée','secondes')
 fig([float(r['abandons'])/float(r['essais']) for r in rows],'taux_abandon_en_fonction_sb.png','Taux d’abandon','proportion')
 for wav,n in [('trame_i.wav','signal_trame_i.png'),('trame_ack.wav','signal_ack.png'),('trame_nak.wav','signal_nak.png')]:
  fe,z=wavfile.read(BASE/wav);f,a=plt.subplots();a.plot(np.arange(min(len(z),4000))/fe,z[:4000]);a.set(xlabel='Temps (s)',ylabel='Amplitude',title=wav);f.tight_layout();f.savefig(BASE/n,dpi=160);plt.close(f)
if __name__=='__main__': main()
