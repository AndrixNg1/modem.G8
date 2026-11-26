"""Preuves numériques reproductibles de la boucle WAV CPFSK phase 2."""
from pathlib import Path
import csv
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from config import F0, F1, FE, R
from emettre import encoder_message, signal_message
from recevoir import recevoir_wav

BASE=Path(__file__).resolve().parent/"mesures"/"module2"
def main():
    BASE.mkdir(parents=True,exist_ok=True); lignes=[]
    for profil,nom in (("G8","fsk_message_G8.wav"),("bell103","fsk_message_bell103.wav")):
        r=recevoir_wav(BASE/nom,profil); (BASE/("reception_G8.txt" if profil=="G8" else "reception_bell103.txt")).write_text(r["texte"]+"\n",encoding="utf-8")
        emis=encoder_message("BONJOUR G8"); recus=r["bits"]; erreurs=sum(a!=b for a,b in zip(emis,recus))+abs(len(emis)-len(recus)); teb=erreurs/max(len(emis),len(recus),1)
        lignes.append({"profil":profil,"original":"BONJOUR G8","bits_transmis":len(emis),"bits_recus":len(recus),"erreurs":erreurs,"TEB":teb,"octets_egaux":r["octets"]==b"BONJOUR G8","statut":"OK" if not erreurs else "ECHEC"})
    with (BASE/"resultats_boucle_audio.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=lignes[0].keys(),delimiter=";"); w.writeheader(); w.writerows(lignes)
    signal,bits,_=signal_message("BONJOUR G8","G8"); r=recevoir_wav(BASE/"fsk_message_G8.wav","G8"); t=np.arange(len(signal))/FE
    fig,ax=plt.subplots(); ax.plot(t[:15000],signal[:15000]); ax.axvline(r["debut_echantillon"]/FE,color="r",label="start détecté"); ax.set(xlabel="Temps (s)",ylabel="Amplitude",title="Synchronisation porteuse → start"); ax.legend(); fig.tight_layout(); fig.savefig(BASE/"synchronisation.png",dpi=160); plt.close(fig)
    e=np.asarray(r["energies"]); fig,ax=plt.subplots(); ax.plot(e[:,0],label=f"E0 ({F0} Hz)"); ax.plot(e[:,1],label=f"E1 ({F1} Hz)"); ax.set(xlabel="Index bit",ylabel="Énergie de corrélation",title="Énergies de décision FSK"); ax.legend(); fig.tight_layout(); fig.savefig(BASE/"energies_f0_f1.png",dpi=160); plt.close(fig)
    fig,ax=plt.subplots(); x=np.arange(len(emis)); ax.step(x,emis,where="mid",label="émis"); ax.step(x,r["bits"],where="mid",linestyle="--",label="reçu"); ax.set(xlabel="Bit de données (porteuse exclue)",ylabel="Valeur",ylim=(-.2,1.2),title="Bits émis et reçus"); ax.legend(); fig.tight_layout(); fig.savefig(BASE/"bits_emis_recus.png",dpi=160); plt.close(fig)
if __name__=="__main__": main()
