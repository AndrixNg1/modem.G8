# Module 2 — Phase 2 : démodulation FSK et synchronisation

## Méthode

La décision par bit utilise les corrélations quadratures : `E(f)=(Σx[n]cos(2πfn/Fe))²+(Σx[n]sin(2πfn/Fe))²`. Elle est indépendante de la phase initiale; le bit reçu est 0 si `E(f0) >= E(f1)`, sinon 1. Une décision dont l'écart relatif est inférieur à 10 % est signalée ambiguë. Ce n'est pas une décision FFT.

`synchroniser_porteuse` balaie les fenêtres à l'échantillon près, cherche une fenêtre f0 précédée de porteuse f1 et ajuste la phase f1 sur les échantillons antérieurs pour centrer le premier start. Le silence initial est donc accepté. Le silence final explicite est retiré avant la vérification des bits complets; une partie non entière d'un bit déclenche une erreur de troncature.

`recevoir.py` lit les WAV mono ou moyenne les canaux stéréo, normalise PCM entier, exige 48 kHz, réutilise `bits_8N1_vers_octets` de `trame.py`, puis décode UTF-8 explicitement. `--binaire` conserve les octets non UTF-8.

## Commandes

```bash
python recevoir.py mesures/module2/fsk_message_G8.wav --profil G8
python recevoir.py mesures/module2/fsk_message_bell103.wav --profil bell103
python validation_module2.py
python -m unittest discover -s tests -v
```

Pour référence manuelle seulement, l'aide installée est affichée par `minimodem --help` (cette version affiche l'usage mais signale aussi l'option comme non reconnue). Ses options vérifiées sont `--tx/--rx`, `-8`, `-R`, `-M`, `-S` et `-f`.

```bash
# WAV Bell 103 local produit par notre émetteur, décodé par Minimodem
minimodem --rx 300 -8 -R 48000 -M 1270 -S 1070 -f mesures/module2/fsk_message_bell103.wav

# Référence Bell 103 produite par Minimodem (format de sortie accepté par sa version)
printf 'BONJOUR G8' | minimodem --tx 300 -8 -R 48000 -M 1270 -S 1070 -f ref_bell103_local.wav
python recevoir.py ref_bell103_local.wav --profil bell103
```

La première commande a réellement retourné `BONJOUR G8` avec `bps=300.00`. La seconde a été produite localement, puis notre récepteur a réellement retourné `BONJOUR G8`; Minimodem avait ajouté une queue de porteuse de 56 échantillons, ignorée car inférieure à un demi-bit. Ce contrôle externe n'est pas exécuté par Python. Aucun `ref_bell103.wav` officiel n'est présent dans ce dépôt; le WAV Bell 103 livré est une référence locale, pas celle de l'enseignant.

## Résultats et limites

`validation_module2.py` produit les réceptions texte, le CSV (porteuse exclue du TEB) et trois graphiques à partir des WAV réellement traités. Les boucles G8 et Bell 103 locales valident les octets exacts. Cette validation ne couvre pas encore bruit gaussien, câble/air, différence d'horloge, porteuse externe inconnue ou validation officielle J3/J4.
