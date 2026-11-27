"""Compare une même capture WAV réelle entre protections, sans aider le décodage."""
from pathlib import Path
import argparse, csv, time
import numpy as np
from audio_io import statistiques
from config import PROFILS
from emettre import encoder_message
from recevoir import lire_wav, recevoir_signal

CHAMPS=("wav","profil","mode","distance_cm","categorie_bruit","essai","statut","message",
        "teb","bits_comparables","bits_ambigus","amplitude_max","rms","ecretage",
        "temps_traitement_s","detail")

def comparer(wav, profil="G8", reference=None, distance_cm=None, categorie_bruit="inconnue", essai=None):
    """Décode séparément chaque mode; ``reference`` ne sert qu'au TEB final."""
    fe,x=lire_wav(wav); mesures=[]
    attendus=encoder_message(reference) if reference is not None else None
    acquisition=statistiques(x); rms=float(np.sqrt(np.mean(x*x))) if len(x) else 0.
    for mode in ('off','basic','advanced'):
        t0=time.perf_counter()
        try:
            r=recevoir_signal(x,profil,decoder_utf8=False,fe=fe,protection=mode)
            bits=r['bits']; comparable=min(len(bits),len(attendus)) if attendus is not None else None
            teb=(sum(a!=b for a,b in zip(bits,attendus))+abs(len(bits)-len(attendus)))/len(attendus) if attendus else None
            statut='recu'; detail=''
            message=r['octets'].hex()
            ambigus=r['ambigus']
        except ValueError as exc:
            statut='rejete'; detail=str(exc); message=''; teb=None; comparable=None; ambigus=None
        mesures.append(dict(wav=str(wav),profil=profil,mode=mode,distance_cm=distance_cm or '',
            categorie_bruit=categorie_bruit,essai=essai or '',statut=statut,message=message,
            teb=teb if teb is not None else '',bits_comparables=comparable if comparable is not None else '',
            bits_ambigus=ambigus if ambigus is not None else '',amplitude_max=acquisition['amplitude_max'],
            rms=rms,ecretage=acquisition['ecretage'],temps_traitement_s=time.perf_counter()-t0,detail=detail))
    return mesures

def archiver(lignes, chemin):
    chemin=Path(chemin); chemin.parent.mkdir(parents=True,exist_ok=True); nouveau=not chemin.exists()
    with chemin.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=CHAMPS); 
        if nouveau: w.writeheader()
        w.writerows(lignes)

def main():
    a=argparse.ArgumentParser(description="Analyse une capture WAV réelle dans les trois modes")
    a.add_argument('wav'); a.add_argument('--profil',choices=tuple(PROFILS),default='G8')
    a.add_argument('--reference',help='message attendu, utilisé seulement après décodage pour le TEB')
    a.add_argument('--distance-cm',type=float); a.add_argument('--categorie-bruit',default='inconnue'); a.add_argument('--essai',type=int)
    a.add_argument('--archiver',action='store_true',help='ajouter l’analyse réelle au CSV physique')
    a.add_argument('--sortie',default='mesures/optimisation_bruit/physique/resultats_physiques.csv')
    args=a.parse_args(); lignes=comparer(args.wav,args.profil,args.reference,args.distance_cm,args.categorie_bruit,args.essai)
    for r in lignes: print(f"{r['mode']}: {r['statut']}; TEB={r['teb'] or 'non calculable'}; {r['detail']}")
    if args.archiver: archiver(lignes,args.sortie); print(f'Analyse archivée : {args.sortie}')

if __name__=='__main__': main()
