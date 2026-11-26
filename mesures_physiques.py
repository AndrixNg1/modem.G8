"""Archivage et comparaison de mesures physiques, sans inventer d'essai."""
from pathlib import Path
import argparse, csv
import numpy as np

BASE=Path(__file__).resolve().parent/"mesures"/"module2"/"physique"
CHAMPS_RESULTATS=("date_heure","canal","original","bits_transmis","bits_recus","bits_errones","bits_perdus","bits_inseres","bits_ambigus","TEB","duree_s","amplitude_max","ecretage","synchronisation","statut")
CHAMPS_CONDITIONS=("date_heure","canal","distance_m","volume","device_emission","device_reception","position","bruit_ambiant","echos","observations")

def initialiser(base=BASE):
    base=Path(base); (base/"cable").mkdir(parents=True,exist_ok=True); (base/"air").mkdir(exist_ok=True)
    for nom,champs in (("resultats_physiques.csv",CHAMPS_RESULTATS),("conditions_experimentales.csv",CHAMPS_CONDITIONS)):
        fichier=base/nom
        if not fichier.exists():
            with fichier.open("w",encoding="utf-8-sig",newline="") as f: csv.DictWriter(f,fieldnames=champs,delimiter=";").writeheader()
    return base

def comparer_bits_physiques(emis,recus):
    """Comparaison transparente : les écarts de longueur deviennent des erreurs."""
    emis,recus=list(emis),list(recus)
    pertes=max(len(emis)-len(recus),0); insertions=max(len(recus)-len(emis),0)
    erreurs=sum(a!=b for a,b in zip(emis,recus))+pertes+insertions
    return {"bits_transmis":len(emis),"bits_recus":len(recus),"bits_errones":erreurs,
            "bits_perdus":pertes,"bits_inseres":insertions,"TEB":erreurs/len(emis) if emis else None}

def ajouter_resultat(ligne,base=BASE):
    initialiser(base)
    with (Path(base)/"resultats_physiques.csv").open("a",encoding="utf-8-sig",newline="") as f: csv.DictWriter(f,fieldnames=CHAMPS_RESULTATS,delimiter=";").writerow(ligne)

def main():
    p=argparse.ArgumentParser(description="Préparer/archiver les mesures physiques G8")
    p.add_argument("--initialiser",action="store_true",help="crée seulement tableaux et dossiers vides")
    p.add_argument("--base",default=str(BASE)); a=p.parse_args(); initialiser(a.base)
    print(f"Tableaux physiques prêts dans {a.base}; aucune mesure physique n'a été créée.")
if __name__=="__main__": main()
