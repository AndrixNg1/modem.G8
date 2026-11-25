"""Génère les graphiques à partir des CSV de mesures, après installation de matplotlib."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import N

BASE = Path(__file__).resolve().parent / 'mesures'

def lire(nom):
    with (BASE/nom).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter=';'))

def sauver(fig, nom):
    fig.tight_layout()
    fig.savefig(BASE/nom, dpi=160)
    plt.close(fig)

r = lire('compression.csv')
fig, ax = plt.subplots(figsize=(7.5,4.5))
x = list(range(len(r)))
ax.bar([i-.18 for i in x], [int(a['taille']) for a in r], .36, label='Original')
ax.bar([i+.18 for i in x], [int(a['compresse']) for a in r], .36, label='Compressé zlib')
ax.set_xticks(x,[a['fichier'] for a in r]); ax.set_ylabel('Octets'); ax.set_title('Compression des fichiers de démonstration'); ax.legend()
sauver(fig, 'compression.png')
r = lire('rendements.csv')
fig, ax = plt.subplots(figsize=(8,4.5))
ax.barh([a['format'] for a in r], [float(a['mesure_pct']) for a in r]); ax.set_xlim(0,100); ax.set_xlabel('Rendement (%)'); ax.set_title(f'Rendement mesuré, {N} octets utiles'); ax.invert_yaxis()
for i,a in enumerate(r): ax.text(float(a['mesure_pct'])+1,i,f"{float(a['mesure_pct']):.2f}%",va='center')
sauver(fig,'rendements.png')
r = lire('erreurs.csv')
fig, ax = plt.subplots(figsize=(7.5,4.5))
x = list(range(len(r))); crc = [int(a['rejets_crc']) for a in r]
ax.bar(x,crc,.45,label='Rejets CRC'); ax.bar(x,[int(a['autres_rejets']) for a in r],.45,bottom=crc,label='Autres rejets')
ax.plot(x,[float(a['rejets_theoriques']) for a in r],marker='o',label='Altérations théoriques')
ax.set_xticks(x,[f"{float(a['p']):.0e}" for a in r]); ax.set_xlabel('Probabilité d’inversion par bit'); ax.set_ylabel('Trames / 1000'); ax.set_title('Erreurs : simulation numérique'); ax.legend()
sauver(fig,'erreurs.png')
