"""Graphiques de résultats produits par le module 1, backend sans interface."""
from pathlib import Path
import csv
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from audio_test import generer_tonalite

BASE=Path(__file__).resolve().parent/"mesures"
def lire(nom):
    with (BASE/nom).open(encoding="utf-8-sig") as f: return list(csv.DictReader(f,delimiter=";"))
def sauver(fig,nom): fig.tight_layout(); fig.savefig(BASE/nom,dpi=160); plt.close(fig)
def main():
    BASE.mkdir(exist_ok=True); c=lire("compression.csv"); x=np.arange(len(c))
    fig,ax=plt.subplots(); ax.bar(x-.2,[float(a["taille"]) for a in c],.4,label="Original"); ax.bar(x+.2,[float(a["compresse"]) for a in c],.4,label="zlib"); ax.set(xticks=x,xticklabels=[a["fichier"] for a in c],ylabel="Taille (octets)",title="Compression"); ax.legend(); sauver(fig,"compression.png")
    fig,ax=plt.subplots(); ax.bar(x,[float(a["H"]) for a in c]); ax.set(xticks=x,xticklabels=[a["fichier"] for a in c],ylabel="Entropie (bits/octet)",title="Entropie de Shannon"); sauver(fig,"entropie.png")
    r=lire("rendements.csv"); fig,ax=plt.subplots(); ax.barh([a["format"] for a in r],[float(a["mesure_pct"]) for a in r]); ax.set(xlabel="Rendement (%)",xlim=(0,100),title="Rendements mesurés"); sauver(fig,"rendements.png")
    e=lire("erreurs.csv"); x=np.arange(len(e)); crc=[float(a["rejets_crc"]) for a in e]; fig,ax=plt.subplots(); ax.bar(x,crc,label="Rejets CRC"); ax.bar(x,[float(a["autres_rejets"]) for a in e],bottom=crc,label="Autres rejets"); ax.plot(x,[float(a["rejets_theoriques"]) for a in e],"o-",label="Altérations théoriques"); ax.set(xticks=x,xticklabels=[f"{float(a['p']):.0e}" for a in e],xlabel="Probabilité par bit",ylabel="Trames / 1000",title="Détection des erreurs"); ax.legend(); sauver(fig,"erreurs_crc.png")
    b=lire("boucle_locale.csv"); fig,ax=plt.subplots(); ax.bar([a["fichier"] for a in b],[int(a["bits"]) for a in b]); ax.set(ylabel="Bits émis",title="Boucle locale (SHA-256 identiques)"); sauver(fig,"boucle_locale.png")
    wav=BASE/"tonalite_1000Hz.wav"; generer_tonalite(wav) if not wav.exists() else None; fe,s=wavfile.read(wav); s=np.asarray(s,dtype=float); t=np.arange(len(s))/fe
    fig,ax=plt.subplots(); ax.plot(t[:min(len(t),2400)],s[:min(len(s),2400)]); ax.set(xlabel="Temps (s)",ylabel="Amplitude",title="Signal 1 kHz (aperçu)"); sauver(fig,"signal_1000Hz.png")
    f=np.fft.rfftfreq(len(s),1/fe); a=np.abs(np.fft.rfft(s)); fig,ax=plt.subplots(); ax.plot(f,a); ax.set(xlim=(0,3000),xlabel="Fréquence (Hz)",ylabel="Amplitude",title="Spectre du signal 1 kHz"); sauver(fig,"spectre_1000Hz.png")
if __name__=="__main__": main()
