# Optimisation — protection contre les bruits extérieurs

## Audit et choix retenus

Avant cette évolution, `modem_fsk.py` retirait déjà le continu, supprimait un
clic pleine échelle isolé et appliquait un Butterworth passe-bande ordre 4 par
`sosfiltfilt`. `recevoir.py` disposait déjà des corrélations I/Q, du contraste
`(E1-E0)/(E1+E0)`, de la recherche de porteuse, de l'ajustement local de
période et de la détection de trame 8N1 tronquée. `audio_io.py` distinguait le
clic de l'écrêtage durable. Il aurait donc été incorrect de superposer un autre
filtrage au récepteur.

`protection_signal.py` est l'unique couche DSP : elle centralise ces opérations
et expose des fonctions testables. Elle ne modifie jamais un signal WAV brut et
ne force jamais un bit pour faire passer un CRC.

| Mode | Traitement |
|---|---|
| `off` | signal brut, pour référence |
| `basic` (défaut de réception) | retrait DC puis passe-bande SOS |
| `advanced` | basic + interpolation des seuls clics isolés détectés par MAD |

Le débruitage spectral de parole et l'annulation d'écho adaptative ne sont pas
activés : ils n'ont pas de référence appropriée et risquent de déformer les
transitions CPFSK. `estimer_bruit` refuse explicitement d'estimer le bruit sans
segment de référence garanti sans porteuse. `egaliser_frequences` reste une API
expérimentale : il n'est pas activé car la trame 8N1 actuelle ne fournit pas de
séquence alternée connue, donc l'inférer depuis les données serait biaisé.

## Paramètres

Les fréquences et débits ne changent pas. Butterworth utilise toujours
`output="sos"`; l'analyse WAV emploie `sosfiltfilt`, tandis que
`filtre_passe_bande(..., temps_reel=True)` emploie `sosfilt`.

| Profil | Bande basic | Ordres supportés |
|---|---:|---:|
| G8 | 7 000–8 000 Hz | 2, 4, 6 (4 retenu) |
| G8_acoustique | 1 500–3 900 Hz | 2, 4, 6 (4 retenu) |
| Bell 103 | 700–1 650 Hz | 2, 4, 6 (4 retenu) |

La confiance par symbole est `abs(E1-E0)/(E1+E0+epsilon)`. Un symbole sous
0,10 est compté ambigu dans les diagnostics; il reste une décision observable,
pas une correction.

## Résultats de simulation AWGN

Commande réellement exécutée :

```bash
python mesures_protection_signal.py --essais 20
```

Même séquence de 240 bits et mêmes 20 réalisations par niveau pour les trois
modes (graine fixe). Les valeurs ci-dessous sont des TEB moyens, pas des essais
acoustiques physiques.

| S/B injecté (dB) | off | basic | advanced |
|---:|---:|---:|---:|
| +6 | 0 | 0 | 0 |
| +3 | 0 | 0 | 0 |
| 0 | 0 | 0 | 0 |
| -3 | 0 | 0 | 0 |
| -6 | 0,00021 | 0 | 0 |
| -9 | 0,00979 | 0,00458 | 0,00458 |
| -12 | 0,05813 | 0,04313 | 0,04313 |

La campagne ne démontre pas de gain supplémentaire de `advanced` sur AWGN :
ce mode est donc optionnel, pas imposé au canal ARQ. Le CSV et le graphique
sont dans `mesures/optimisation_bruit/csv/` et `graphiques/`. Les répertoires
`physique/` et `wav/` sont volontairement vides : aucune mesure physique ou
WAV extérieur n'a été inventé.

## Reproduction et limites

```bash
python recevoir.py capture.wav --profil G8 --protection off
python recevoir.py capture.wav --profil G8 --protection basic
python recevoir.py capture.wav --profil G8 --protection advanced
python mesures_protection_signal.py --essais 20 --perturbation echo
pytest -q
```

Les simulations supplémentaires disponibles sont `50hz`, `tonalite`,
`impulsions` et `echo`; elles sont toutes explicitement synthétiques. Il reste
à exécuter et consigner le protocole physique (distance, salle, ventilateur,
orientation) avant toute affirmation sur deux PC. Les ACK/NAK audio physiques
ne sont pas créés par cette évolution; `CanalFSK` accepte néanmoins
`protection=` pour comparer les modes dans sa simulation ARQ.

## Phase 2 — perturbations acoustiques et faux préambules

`perturbations_acoustiques.py` ajoute des générateurs déterministes de bruit
blanc et rose, ronflement 50 Hz/harmoniques, clics, tonalités, atténuation,
échos multiples (dont 1, 3, 5, 10, 20 et 50 ms configurables), dérive
d'horloge et combinaisons. Ils sont tous marqués synthétiques.

L'audit de la campagne AWGN confirme que le TEB compare toujours les 240 bits
émis, ajoute explicitement les bits manquants et réutilise la même graine par
essai pour `off`, `basic` et `advanced`. Les filtres SOS ont une réponse et un
retard vérifiables par les tests; l'analyse WAV emploie le zéro-phase, tandis
que la primitive temps réel conserve `sosfilt`.

Une campagne rapide réellement exécutée (`python mesures_acoustiques.py
--essais 3`) produit 189 lignes dans
`mesures/optimisation_bruit/csv/campagne_perturbations_synthetiques.csv` et
les graphiques `teb_par_type_bruit.png` et `fausses_detections.png`. Pour G8,
seul l'AWGN à -9 dB est défavorable : TEB `off=0,0069`,
`basic=advanced=0,0056`; les autres scénarios rapides ont donné 0 avec les
trois modes. Ce résultat ne prouve pas une robustesse universelle.

La campagne complète a ensuite été exécutée avec `--essais 20` (1 260 lignes,
trois profils, sept scénarios, trois modes). Pour G8 et AWGN -9 dB, le TEB
moyen est `off=0,00771`, `basic=advanced=0,00354`; les six autres scénarios
à l'intensité définie par ce banc donnent un TEB nul. Les CSV ont été remplacés
par cette campagne complète; ce sont toujours des simulations appariées.

Le banc initial de faux préambules (20 bruits synthétiques sans transmission
par profil/mode) a exposé une faiblesse, ensuite traitée en phase 3.

Pour capturer réellement un bruit, sans création automatique de fichier :

```bash
python enregistrer_bruit_ambiant.py --categorie ventilateur --duree 30 --device 2
```

Le WAV brut est alors écrit dans `mesures/optimisation_bruit/bruits_reels/`.
Pour les essais deux PC, conserver les mêmes gains et enregistrer chaque WAV :

```bash
# PC émetteur
python emettre.py "message de test" --profil G8 --device 2 --jouer
# PC récepteur, une capture par mode et par distance
python recevoir.py --micro --duree 10 --device 3 --enregistrement mesures/optimisation_bruit/wav/25cm_basic.wav --profil G8 --protection basic
```

Répéter à 25 cm, 50 cm et 1 m, silencieux puis bruité (idéalement dix fois).
Les métriques ARQ, débit utile et SHA-256 nécessitent encore le canal audio
semi-duplex complet : elles ne sont pas déduites de la campagne FSK.

## Phase 3 — faux préambules et validation physique préparée

Les fausses détections ont été reproduites avec les graines 3010 (G8) et
3006/3010 (Bell 103). Elles proviennent d'une coïncidence étroite du bruit
filtré, non d'un transitoire de bord. La synchronisation conserve la
cohérence I/Q supérieure à 8 mais relève le contraste minimal de 2 à 3. Un
sinus FSK nominal conserve environ 6, ce qui préserve la marge testée.

```bash
python campagne_faux_positifs.py --captures 100
```

Cette commande a été exécutée : 100 captures indépendantes sans transmission,
par profil et par mode (900 analyses), réparties entre silence, blanc, rose,
ronflement, clics, tonalité dans la bande et combinaison. Résultat : **0/100
faux préambule**, 0 fausse trame et 0 acceptation CRC pour chacun des neuf
couples profil/mode. Chaque capture dure 0,1 s; ce résultat bref ne remplace
pas une longue prise de son réelle. Les preuves sont
`csv/faux_preampules_comparatif.csv` et
`graphiques/comparaison_faux_positifs.png`.

`analyser_capture_physique.py` analyse la même capture WAV avec `off`,
`basic` et `advanced`. Une référence éventuelle sert seulement après le
décodage à calculer le TEB; elle n'est jamais fournie au démodulateur.

```bash
python analyser_capture_physique.py capture.wav --profil G8 \
  --reference "message de test" --distance-cm 25 --categorie-bruit silencieuse \
  --essai 1 --archiver
```

Il n'y a toujours aucune nouvelle mesure physique, ni transfert de fichier
ARQ audio semi-duplex, ni ACK/NAK sonore ou SHA-256 de fichier sur l'air. Les
CSV et graphiques physiques de distance/retransmission ne sont donc pas
fabriqués; ce sont les expériences restantes à réaliser sur deux PC.

L'outil a été exécuté sans archivage sur le WAV historique
`mesures/module2/physique/air/test_local_recu.wav` : les trois modes le
rejettent par « porteuse f1 suivie d'un start f0 introuvable ». Cette absence
de faux message est un diagnostic reproductible du fichier existant, pas un
nouvel essai de transmission.
