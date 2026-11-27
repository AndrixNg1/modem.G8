"""Campagne reproductible de comparaison des protections FSK.

Les résultats sont explicitement des simulations : aucun fichier de ce script
ne prétend représenter un enregistrement physique.
"""
from pathlib import Path
import argparse
import csv
import numpy as np
import matplotlib.pyplot as plt
from config import PROFILS
from modem_fsk import ajouter_bruit, demoduler, moduler
from protection_signal import calculer_confiance, pretraiter_signal


def perturber(signal, fe, sb_db, seed, nature="awgn"):
    """Ajoute une perturbation synthétique identifiée, avec graine stable."""
    x, info = ajouter_bruit(signal, sb_db, seed, True)
    if nature == "awgn":
        return x, info
    t = np.arange(len(x)) / fe
    sigma = np.sqrt(info["puissance_bruit"])
    rng = np.random.default_rng(seed)
    if nature == "50hz": x += sigma * np.sqrt(2) * np.sin(2*np.pi*50*t)
    elif nature == "tonalite": x += sigma * np.sqrt(2) * np.sin(2*np.pi*7300*t)
    elif nature == "impulsions":
        positions = rng.integers(1, len(x)-1, max(1, len(x)//10000)); x[positions] += 8*sigma
    elif nature == "echo":
        retard = max(1, fe // 200); x[retard:] += .35 * signal[:-retard]
    else: raise ValueError("perturbation attend awgn, 50hz, tonalite, impulsions ou echo")
    return x, info


def campagne(profil="G8", essais=20, niveaux=(6, 3, 0, -3, -6, -9, -12), nature="awgn"):
    p = PROFILS[profil]; rng = np.random.default_rng(20261127)
    bits = rng.integers(0, 2, 240).tolist()
    propre = moduler(bits, p['f0'], p['f1'], p['R'], p['fe'])
    lignes = []
    for sb in niveaux:
        for essai in range(essais):
            bruit, info = perturber(propre, p['fe'], sb, 10_000 + essai, nature)
            for mode in ("off", "basic", "advanced"):
                traite = pretraiter_signal(bruit, p['f0'], p['f1'], p['fe'], p['nom'], mode)
                recus, ambigus, energies, _ = demoduler(traite, p['f0'], p['f1'], p['R'], p['fe'], True)
                erreurs = sum(a != b for a, b in zip(bits, recus)) + abs(len(bits)-len(recus))
                confiance = [calculer_confiance(a, b) for a, b in energies]
                lignes.append({"profil": profil, "perturbation": nature, "mode": mode,
                    "sb_db": sb, "essai": essai, "teb": erreurs / len(bits),
                    "bits_ambigus": int(sum(c < .10 for c in confiance)),
                    "sb_avant_db": info['sb_db_mesure'], "bits": len(bits)})
    return lignes


def ecrire_resultats(lignes, sortie):
    sortie = Path(sortie); csv_dir = sortie / "csv"; graphs = sortie / "graphiques"
    for d in (sortie / "simulation", sortie / "physique", sortie / "wav", csv_dir, graphs): d.mkdir(parents=True, exist_ok=True)
    chemin = csv_dir / "campagne_awgn.csv"
    with chemin.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lignes[0]); w.writeheader(); w.writerows(lignes)
    fig, ax = plt.subplots()
    for mode in ("off", "basic", "advanced"):
        points = [(s, np.mean([r['teb'] for r in lignes if r['mode']==mode and r['sb_db']==s]))
                  for s in sorted({r['sb_db'] for r in lignes})]
        ax.plot(*zip(*points), marker='o', label=mode)
    ax.set(xlabel="S/B injecté (dB)", ylabel="TEB moyen", title="Simulation AWGN reproductible")
    ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(graphs / "teb_comparatif.png", dpi=150)
    plt.close(fig)
    return chemin


def main():
    a = argparse.ArgumentParser(description="Mesures simulées de protection du signal")
    a.add_argument("--profil", choices=tuple(PROFILS), default="G8")
    a.add_argument("--essais", type=int, default=20)
    a.add_argument("--perturbation", default="awgn")
    a.add_argument("--sortie", default="mesures/optimisation_bruit")
    args = a.parse_args()
    if args.essais < 1: a.error("--essais doit être positif")
    lignes = campagne(args.profil, args.essais, nature=args.perturbation)
    print(ecrire_resultats(lignes, args.sortie))


if __name__ == '__main__': main()
