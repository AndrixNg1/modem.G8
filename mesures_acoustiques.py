"""Campagne rapide de perturbations synthétiques appariées.

Elle mesure la couche FSK seulement; les métriques ARQ/SHA exigent un transfert
de fichier complet et ne sont donc pas extrapolées depuis ces résultats.
"""
from pathlib import Path
import argparse, csv
import matplotlib.pyplot as plt
import numpy as np
from config import PROFILS
from modem_fsk import demoduler, moduler, synchroniser_porteuse
from protection_signal import calculer_confiance, pretraiter_signal
from perturbations_acoustiques import appliquer


SCENARIOS = {
    "blanc": [{"type":"blanc", "sb_db":-9}],
    "rose": [{"type":"rose", "sb_db":-9}],
    "ronflement": [{"type":"ronflement", "db":-4}],
    "impulsions": [{"type":"impulsions", "db":-4, "taux":.001}],
    "tonalite_hors_bande": [{"type":"tonalite", "frequence":50, "db":-4}],
    "tonalite_dans_bande": [{"type":"tonalite", "frequence":7500, "db":-12}],
    "echo_10ms": [{"type":"echo", "retards_ms":(10,), "amplitudes":(.35,)}],
}

def campagne(essais=3):
    lignes=[]
    for nom, p in PROFILS.items():
        bits=np.random.default_rng(20261127).integers(0,2,240).tolist()
        propre=moduler(bits,p['f0'],p['f1'],p['R'],p['fe'])
        for scenario, specs in SCENARIOS.items():
            for essai in range(essais):
                perturbe=appliquer(propre,p['fe'],specs,seed=1000+essai)
                for mode in ('off','basic','advanced'):
                    traite=pretraiter_signal(perturbe,p['f0'],p['f1'],p['fe'],nom,mode)
                    rec,_,energies,_=demoduler(traite,p['f0'],p['f1'],p['R'],p['fe'],True)
                    comparables=min(len(bits),len(rec)); erreurs=sum(a!=b for a,b in zip(bits,rec)) + abs(len(bits)-len(rec))
                    confiances=[calculer_confiance(e0,e1) for e0,e1 in energies]
                    lignes.append(dict(profil=nom, scenario=scenario, essai=essai, mode=mode,
                        teb=erreurs/len(bits), bits_comparables=comparables,
                        bits_ambigus=sum(c<.1 for c in confiances), perte_synchronisation=int(comparables != len(bits))))
    return lignes

def fausses_detections(essais=20, duree=.5):
    lignes=[]
    for nom,p in PROFILS.items():
        for mode in ('off','basic','advanced'):
            faux=0
            for essai in range(essais):
                bruit=np.random.default_rng(3000+essai).normal(0,.02,round(duree*p['fe']))
                y=pretraiter_signal(bruit,p['f0'],p['f1'],p['fe'],nom,mode)
                try: synchroniser_porteuse(y,p['f0'],p['f1'],p['R'],p['fe'],min_porteuse_bits=8); faux+=1
                except ValueError: pass
            lignes.append(dict(profil=nom,mode=mode,essais=essais,fausses_detections=faux))
    return lignes

def produire(lignes, faux, sortie):
    sortie=Path(sortie); csvdir=sortie/'csv'; graph=sortie/'graphiques'; csvdir.mkdir(parents=True,exist_ok=True); graph.mkdir(parents=True,exist_ok=True)
    for path, rows in ((csvdir/'campagne_perturbations_synthetiques.csv',lignes),(csvdir/'fausses_detections.csv',faux)):
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
    # G8 est le graphique lisible; les trois profils restent dans le CSV.
    fig,ax=plt.subplots(figsize=(11,4))
    scenarios=list(SCENARIOS)
    for mode in ('off','basic','advanced'):
        vals=[np.mean([r['teb'] for r in lignes if r['profil']=='G8' and r['mode']==mode and r['scenario']==s]) for s in scenarios]
        ax.plot(scenarios,vals,marker='o',label=mode)
    ax.tick_params(axis='x',rotation=25); ax.set(ylabel='TEB moyen',title='G8 — perturbations synthétiques appariées'); ax.legend(); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(graph/'teb_par_type_bruit.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4)); labels=[f"{r['profil']}\n{r['mode']}" for r in faux]; ax.bar(labels,[r['fausses_detections'] for r in faux]); ax.set(ylabel='Fausses détections',title='Bruit synthétique sans transmission'); fig.tight_layout(); fig.savefig(graph/'fausses_detections.png',dpi=150); plt.close(fig)

def main():
    a=argparse.ArgumentParser(); a.add_argument('--essais',type=int,default=3); a.add_argument('--sortie',default='mesures/optimisation_bruit'); args=a.parse_args()
    if args.essais<1: a.error('--essais positif requis')
    lignes=campagne(args.essais); faux=fausses_detections()
    produire(lignes,faux,args.sortie); print(f"{len(lignes)} lignes synthétiques, {len(faux)} mesures de faux préambules")
if __name__=='__main__': main()
