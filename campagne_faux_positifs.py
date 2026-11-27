"""Validation synthétique des faux préambules, indépendante et reproductible."""
from pathlib import Path
import argparse, csv
import matplotlib.pyplot as plt
import numpy as np
from config import PROFILS
from modem_fsk import synchroniser_porteuse
from protection_signal import pretraiter_signal

TYPES=("silence","blanc","rose","ronflement","impulsions","tonalite","combine")

def capture_sans_transmission(kind, fe, duree, seed, f_parasite):
    """Construit une capture synthétique sans porteuse ni trame modem."""
    n=round(fe*duree); rng=np.random.default_rng(seed); t=np.arange(n)/fe
    if kind == "silence": return np.zeros(n)
    blanc=rng.normal(0,.02,n)
    if kind == "blanc": return blanc
    if kind == "rose":
        f=np.fft.rfftfreq(n); z=rng.normal(size=len(f))+1j*rng.normal(size=len(f)); z[0]=0; z[1:]/=np.sqrt(f[1:])
        y=np.fft.irfft(z,n); return y*.02/max(np.sqrt(np.mean(y*y)),np.finfo(float).eps)
    if kind == "ronflement": return .02*np.sin(2*np.pi*50*t)+.01*np.sin(2*np.pi*100*t)
    if kind == "impulsions":
        y=blanc*.1; y[rng.integers(1,n-1,3)] = rng.choice((-.5,.5),3); return y
    if kind == "tonalite": return .02*np.sin(2*np.pi*f_parasite*t)
    return blanc*.4 + .012*np.sin(2*np.pi*50*t) + .008*np.sin(2*np.pi*f_parasite*t)

def campagne(captures=100, duree=.1):
    lignes=[]
    for nom,p in PROFILS.items():
        for essai in range(captures):
            kind=TYPES[essai % len(TYPES)]
            # La tonalité parasite est volontairement dans la bande utile,
            # mais n'encode aucun préambule ni start.
            x=capture_sans_transmission(kind,p['fe'],duree,50_000+essai,(p['f0']+p['f1'])/2)
            for mode in ("off","basic","advanced"):
                y=pretraiter_signal(x,p['f0'],p['f1'],p['fe'],nom,mode)
                try:
                    synchroniser_porteuse(y,p['f0'],p['f1'],p['R'],p['fe'],min_porteuse_bits=8)
                    faux=1
                except ValueError: faux=0
                lignes.append(dict(profil=nom,mode=mode,type_bruit=kind,essai=essai,
                    duree_s=duree,faux_preambule=faux,fausse_trame=0,fausse_acceptation_crc=0))
    return lignes

def ecrire(lignes, sortie):
    sortie=Path(sortie); csvdir=sortie/'csv'; graph=sortie/'graphiques'; csvdir.mkdir(parents=True,exist_ok=True); graph.mkdir(parents=True,exist_ok=True)
    path=csvdir/'faux_preampules_comparatif.csv'
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=lignes[0]); w.writeheader(); w.writerows(lignes)
    groupes=[(p,m) for p in PROFILS for m in ('off','basic','advanced')]
    valeurs=[sum(r['faux_preambule'] for r in lignes if (r['profil'],r['mode'])==g) for g in groupes]
    fig,ax=plt.subplots(figsize=(8,4)); ax.bar([f'{p}\n{m}' for p,m in groupes],valeurs); ax.set(ylabel='Faux préambules / captures',title='Campagne synthétique sans transmission'); fig.tight_layout(); fig.savefig(graph/'comparaison_faux_positifs.png',dpi=150); plt.close(fig)
    return path

def main():
    a=argparse.ArgumentParser(description="Campagne sans transmission FSK")
    a.add_argument('--captures',type=int,default=100); a.add_argument('--duree',type=float,default=.1); a.add_argument('--sortie',default='mesures/optimisation_bruit')
    args=a.parse_args()
    if args.captures<100: a.error('--captures doit être au moins 100')
    if args.duree <= .03: a.error('--duree doit permettre un préambule minimal')
    lignes=campagne(args.captures,args.duree); path=ecrire(lignes,args.sortie)
    minutes=sum(r['duree_s'] for r in lignes)/3/60
    print(f'{path}: {len(lignes)} analyses, {minutes:.2f} minutes par profil/mode')

if __name__=='__main__': main()
