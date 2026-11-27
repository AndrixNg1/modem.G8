"""Acquisition volontaire de bruit ambiant, sans fabriquer de faux WAV."""
from pathlib import Path
import argparse
from audio_io import enregistrer
from config import FE

CATEGORIES = ("silencieuse", "conversation", "ventilateur", "deplacements", "exterieur", "combine")

def main():
    p = argparse.ArgumentParser(description="Enregistre un bruit ambiant réel à 48 kHz")
    p.add_argument("--categorie", choices=CATEGORIES, required=True)
    p.add_argument("--duree", type=float, default=10.)
    p.add_argument("--device")
    p.add_argument("--sortie", default="mesures/optimisation_bruit/bruits_reels")
    a = p.parse_args()
    if a.duree <= 0: p.error("--duree doit être positive")
    destination = Path(a.sortie) / f"bruit_{a.categorie}.wav"
    print(f"Acquisition réelle {a.categorie} pendant {a.duree:g} s : {destination}")
    _, stats = enregistrer(a.duree, FE, a.device, destination)
    print(f"WAV brut conservé; amplitude={stats['amplitude_max']:.3f}, écrêtage={stats['ecretage']}")

if __name__ == "__main__": main()
