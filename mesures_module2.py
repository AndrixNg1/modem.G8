"""Mesure reproductible du TEB brut CPFSK sous AWGN (phase 3)."""
from pathlib import Path
import argparse, csv
import numpy as np
from scipy.io import wavfile
from config import PROFILS, profil as profil_config
from modem_fsk import moduler, ajouter_bruit, demoduler

SB_DB = [6, 3, 0, -3, -6, -9, -12]
N_BITS = 10_000
GRAINE = 2026
BASE = Path(__file__).resolve().parent / "mesures" / "module2" / "bruit"

def comparer_bits(emis, recus):
    """Compte aussi pertes/insertions, sans tronquer silencieusement."""
    erreurs_decision = sum(a != b for a, b in zip(emis, recus))
    ecart_longueur = abs(len(emis) - len(recus))
    return erreurs_decision + ecart_longueur, erreurs_decision, ecart_longueur

def sequence_test(n_bits=N_BITS, seed=GRAINE):
    if not isinstance(n_bits, int) or n_bits <= 0: raise ValueError("Nombre de bits positif requis")
    return np.random.default_rng(seed).integers(0, 2, n_bits, dtype=np.int8).tolist()

def _nom_sb(sb): return f"plus{sb}" if sb > 0 else ("0" if sb == 0 else f"moins{abs(sb)}")

def executer(bits=N_BITS, seed=GRAINE, sortie=BASE, profil="G8"):
    p=profil_config(profil); f0,f1,r,fe=p["f0"],p["f1"],p["R"],p["fe"]
    sortie=Path(sortie); sortie.mkdir(parents=True,exist_ok=True)
    emis=sequence_test(bits,seed)
    (sortie/"sequence_test_10000.txt").write_text("".join(map(str,emis))+"\n",encoding="ascii")
    reference=moduler(emis,f0,f1,r,fe); wavfile.write(sortie/"signal_reference.wav",fe,reference.astype(np.float32))
    lignes=[]
    for index,sb in enumerate(SB_DB):
        bruit,info=ajouter_bruit(reference,sb,seed=seed+index,retourner_infos=True)
        wavfile.write(sortie/f"signal_sb_{_nom_sb(sb)}.wav",fe,bruit.astype(np.float32))
        recus,ambigus,_,reste=demoduler(bruit,f0,f1,r,fe,True)
        erreurs,decisions,ecart=comparer_bits(emis,recus)
        statut="OK" if not reste and not ecart else f"ECHEC longueur={ecart}, reste={reste}"
        lignes.append({"profil":profil,"graine":seed,"sb_db_demande":sb,"sb_db_mesure":info["sb_db_mesure"],"puissance_signal":info["puissance_signal"],"puissance_bruit":info["puissance_bruit"],"bits_transmis":len(emis),"bits_recus":len(recus),"erreurs":erreurs,"erreurs_decision":decisions,"ecart_longueur":ecart,"bits_ambigus":sum(ambigus),"TEB":erreurs/len(emis),"statut":statut})
    with (sortie/"resultats_teb.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(lignes[0]),delimiter=";"); w.writeheader(); w.writerows(lignes)
    texte=["TEB CPFSK G8 sous AWGN — séquence locale (pas la séquence officielle)",f"bits={bits}; graine={seed}; synchronisation connue; porteuse/8N1/CRC exclus",""]
    texte += [f"S/B demandé={r['sb_db_demande']:>3} dB | mesuré={r['sb_db_mesure']:.3f} dB | erreurs={r['erreurs']} | ambigus={r['bits_ambigus']} | TEB={r['TEB']:.6g} | {r['statut']}" for r in lignes]
    (sortie/"resultats_teb.txt").write_text("\n".join(texte)+"\n",encoding="utf-8")
    print("\n".join(texte)); return lignes

if __name__ == "__main__":
    p=argparse.ArgumentParser(description="Mesure AWGN/TEB CPFSK G8")
    p.add_argument("--bits",type=int,default=N_BITS); p.add_argument("--seed",type=int,default=GRAINE); p.add_argument("--sortie",default=str(BASE)); p.add_argument("--profil",choices=tuple(PROFILS),default="G8")
    a=p.parse_args(); executer(a.bits,a.seed,a.sortie,a.profil)
