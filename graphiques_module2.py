"""Démonstrations et graphiques CPFSK issus des signaux réellement générés."""
from pathlib import Path
import csv
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from config import F0, F1, R, FE, BANDWIDTH_THEORIQUE
from modem_fsk import moduler
from emettre import signal_message, ecrire_wav

BASE = Path(__file__).resolve().parent / "mesures" / "module2"
def save(fig, name): fig.tight_layout(); fig.savefig(BASE/name, dpi=160); plt.close(fig)
def plot_signal(sig, name, title, samples=640):
    t=np.arange(min(len(sig),samples))/FE; fig,ax=plt.subplots(); ax.plot(t,sig[:len(t)]); ax.set(xlabel="Temps (s)",ylabel="Amplitude",title=title); save(fig,name)
def main():
    BASE.mkdir(parents=True,exist_ok=True)
    zero=moduler([0],F0,F1,R); un=moduler([1],F0,F1,R); seq=moduler([1,0,1,1,0],F0,F1,R)
    for n,s in (("fsk_bit_0",zero),("fsk_bit_1",un),("fsk_sequence_10110",seq)): ecrire_wav(BASE/(n+".wav"),s)
    g8,_,p=signal_message("BONJOUR G8","G8"); b103,_,p2=signal_message("BONJOUR G8","bell103")
    ecrire_wav(BASE/"fsk_message_G8.wav",g8,p["fe"]); ecrire_wav(BASE/"fsk_message_bell103.wav",b103,p2["fe"])
    plot_signal(zero,"fsk_bit_0.png",f"FSK bit 0 — {F0} Hz (durée 1/R)")
    plot_signal(un,"fsk_bit_1.png",f"FSK bit 1 — {F1} Hz (durée 1/R)")
    plot_signal(seq,"fsk_sequence.png","FSK séquence 10110 — changements de fréquence",len(seq))
    f=np.fft.rfftfreq(len(seq),1/FE); a=np.abs(np.fft.rfft(seq)); fig,ax=plt.subplots(); ax.plot(f,a); ax.axvline(F0,color="C1",label=f"f0={F0} Hz"); ax.axvline(F1,color="C2",label=f"f1={F1} Hz"); ax.axvspan(F0-BANDWIDTH_THEORIQUE/2,F1+BANDWIDTH_THEORIQUE/2,alpha=.15,label=f"Bande théorique {BANDWIDTH_THEORIQUE} Hz"); ax.set(xlim=(6500,8500),xlabel="Fréquence (Hz)",ylabel="Amplitude",title="Spectre FSK (bande théorique, non mesurée)"); ax.legend(); save(fig,"fsk_spectre.png")
    t=np.arange(len(seq))/FE; fig,ax=plt.subplots(); ax.plot(t,seq); [ax.axvline(i/R,color="black",alpha=.35) for i in range(1,5)]; ax.set(xlabel="Temps (s)",ylabel="Amplitude",title="CPFSK : phase conservée aux transitions de bit"); save(fig,"fsk_phase_continue.png")
    bruit=BASE/"bruit"
    if (bruit/"resultats_teb.csv").exists():
        with (bruit/"resultats_teb.csv").open(encoding="utf-8-sig") as f: lignes=list(csv.DictReader(f,delimiter=";"))
        sb=np.array([float(x["sb_db_demande"]) for x in lignes]); teb=np.array([float(x["TEB"]) for x in lignes]); mesure=np.array([float(x["sb_db_mesure"]) for x in lignes]); erreurs=np.array([int(x["erreurs"]) for x in lignes]); n=int(lignes[0]["bits_transmis"])
        positifs=teb[teb>0]; limite=(positifs.min()/10 if len(positifs) else 1/(2*n)); affichage=np.where(teb>0,teb,limite)
        fig,ax=plt.subplots(); ax.semilogy(sb,affichage,"o-",label="TEB expérimental"); zeros=teb==0
        if zeros.any(): ax.semilogy(sb[zeros],np.full(zeros.sum(),limite),"v",label=f"TEB=0 (affiché à {limite:g})")
        ax.set(xlabel="Rapport S/B demandé (dB)",ylabel="TEB (échelle logarithmique)",title="TEB CPFSK G8 sous AWGN"); ax.grid(True,which="both"); ax.legend(); save(fig,"teb_en_fonction_sb.png")
        fig,ax=plt.subplots(); ax.bar(sb,erreurs,width=.7); ax.set(xlabel="Rapport S/B demandé (dB)",ylabel="Bits erronés / 10 000",title="Erreurs binaires observées"); save(fig,"erreurs_par_sb.png")
        fig,ax=plt.subplots(); ax.plot(sb,mesure,"o-",label="S/B mesuré"); ax.plot(sb,sb,"--",label="S/B demandé"); ax.set(xlabel="S/B demandé (dB)",ylabel="S/B (dB)",title="S/B demandé et mesuré"); ax.legend(); save(fig,"comparaison_sb_theorique_mesure.png")
        fe,ref=wavfile.read(bruit/"signal_reference.wav"); _,n6=wavfile.read(bruit/"signal_sb_moins6.wav"); t=np.arange(min(1600,len(ref)))/fe
        fig,ax=plt.subplots(); ax.plot(t,ref[:len(t)],label="référence"); ax.plot(t,n6[:len(t)],alpha=.7,label="S/B -6 dB"); ax.set(xlabel="Temps (s)",ylabel="Amplitude",title="Signal CPFSK et AWGN"); ax.legend(); save(fig,"comparaison_signaux_bruites.png")
        fig,ax=plt.subplots()
        for nom,data in (("référence",ref),("S/B -6 dB",n6)):
            f=np.fft.rfftfreq(len(data),1/fe); ax.plot(f,20*np.log10(np.maximum(np.abs(np.fft.rfft(data)),1e-12)),label=nom)
        ax.set(xlim=(0,12000),xlabel="Fréquence (Hz)",ylabel="Module FFT (dB arbitraire)",title="Spectres : signal et bruit"); ax.legend(); save(fig,"spectres_signaux_bruites.png")
if __name__ == "__main__": main()
