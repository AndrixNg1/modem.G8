# Module 2 — Phase 1 : émission FSK à phase continue — G8

## Périmètre

Cette phase ajoute uniquement l'émission CPFSK et ses fichiers de démonstration. Elle ne contient ni démodulation, ni ARQ, ni validation officielle J3.

## Paramètres et modèle

G8 utilise `f0=7400 Hz` (bit 0), `f1=7600 Hz` (bit 1), `R=300 bauds`, `Fe=48000 Hz` et amplitude 0,5. Ainsi `Tb=1/R=3,333 ms` et `Fe/R=160` échantillons par bit. Pour l'échantillon `n`, le modulateur applique `s[n]=0,5 sin(phi[n])`, avec `phi[n+1]=phi[n]+2π f(bit[n])/Fe`. La phase accumulée n'est donc pas remise à zéro lors d'une transition. La bande théorique indiquée est `2(f1-f0)+2R=800 Hz`; elle ne doit pas être confondue avec une mesure de bande réelle.

Bell 103 reste un profil séparé : 1070/1270 Hz, 300 bauds et 8N1. Il ne remplace pas G8.

## Texte et émission

`emettre.py` encode le texte en UTF-8. Chaque octet est transmis en 8N1 : start 0, huit bits LSB-first, stop 1. Une annonce de 0,3 s à `f1` (90 intervalles binaires à 300 bauds) précède les données dans le même appel au modulateur : la phase est donc continue entre annonce et message.

```bash
python emettre.py "BONJOUR G8" --profil G8 --sortie mesures/module2/fsk_message_G8.wav
python emettre.py "BONJOUR G8" --profil bell103 --sortie mesures/module2/fsk_message_bell103.wav
python emettre.py "BONJOUR G8" --profil G8 --jouer
python graphiques_module2.py
audacity mesures/module2/fsk_message_G8.wav
```

`--jouer` nécessite Sounddevice et un périphérique accessible. L'exécution automatisée ne prétend ni qu'un son a été entendu ni qu'un microphone a été testé.

## Fichiers produits

`mesures/module2/` contient `fsk_bit_0.wav`, `fsk_bit_1.wav`, `fsk_sequence_10110.wav`, `fsk_message_G8.wav`, `fsk_message_bell103.wav`, plus les cinq graphiques demandés. Les PNG sont des figures Python, pas des captures Audacity.

## Validation

`python -m unittest discover -s tests -v` couvre taille, durée, amplitude, fréquence par corrélation, transition sans réinitialisation de phase, entrées invalides, 8N1, profils, annonce et relecture numérique WAV. J3 doit être démontré puis validé par l'enseignant séparément.
