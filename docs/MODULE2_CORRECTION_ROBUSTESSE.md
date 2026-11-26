# Module 2 — Correction et robustesse de la transmission acoustique

## Conclusion fondée sur les WAV fournis

Le fichier `mesures/module2/physique/air/test_local_emis.wav` contient bien le signal G8 attendu : 48 kHz, 30 400 échantillons, 0,633333 s, soit 190 bits à 300 bauds. Son amplitude maximale vaut 0,5, son RMS 0,353554 et sa composante continue −4,36×10⁻⁶. Le contenu spectral est dominé par la préporteuse à 7600 Hz.

Le fichier reçu `mesures/module2/physique/air/test_local_recu.wav` contient 720 000 échantillons, soit 15 s, avec une amplitude maximale de 0,017899, un RMS de 0,001242 et une composante continue de −5,49×10⁻⁵. Son maximum élevé provient d'un transitoire au début : il ne correspond pas à un niveau FSK soutenu. Dans la bande G8 filtrée (7–8 kHz), le RMS médian par blocs de 10 ms est d'environ 4,63×10⁻⁵ et le 10e percentile d'environ 3,72×10⁻⁵. Ces niveaux restent comparables sur l'enregistrement; aucun préambule f1 suivi d'un start f0 n'est confirmé.

La puissance spectrale estimée autour de 7400 et 7600 Hz est respectivement 1,06×10⁻¹¹ et 1,13×10⁻¹¹, sans séparation FSK caractéristique. Les pics locaux de la bande se trouvent autour de 7425, 7585 et 7966 Hz à environ −114 dB/Hz; il n'y a pas de raie soutenue établie aux deux fréquences officielles. L'énergie globale est dominée par les composantes très basses fréquences. Le diagnostic conclut donc **FSK G8 non détectable dans le WAV reçu**, et non « FSK présent mais trop faible ». Le niveau de bruit avant transmission ne peut pas être isolé : aucune porteuse n'est reconnue et le début du fichier contient un transitoire. Le niveau passe-bande global est fourni à titre de bruit de fond estimé, pas comme S/B physique.

Le récepteur antérieur se verrouillait sur du bruit (position 3977 dans la mesure de référence), puis découpait le reste de ces 15 s en fenêtres binaires. Cela explique les décisions 8N1 non valides sans démontrer que l'amplitude seule était fautive. Pour ce même fichier, la longueur résiduelle calculée avec ce faux verrouillage est 23 échantillons, pas 135. Les 135 échantillons rapportés ne sont donc pas reproductibles à partir du WAV fourni et ne doivent pas être présentés comme une mesure de celui-ci. De même, son maximum mesuré (0,017899) ne correspond ni aux 0,041 ni aux 0,022 rapportés pour les deux essais. La cause exacte côté matériel (entrée sélectionnée, routage, position ou transmission acoustique) ne peut pas être identifiée avec ces seuls fichiers; aucun nouvel essai physique n'a été effectué.

## Corrections apportées

- `audio_io.normaliser_peripherique` convertit les indices numériques en entiers et est appliquée avant les appels d'acquisition et de lecture Sounddevice; les noms et `None` restent pris en charge.
- Le récepteur soustrait la composante continue et applique un passe-bande zéro-phase adapté au profil (7000–8000 Hz pour G8, bande adaptée aux tonalités Bell 103). Le signal d'entrée et les WAV acquis restent bruts; aucune normalisation ne prétend améliorer le rapport signal/bruit.
- La synchronisation exige désormais un préambule f1 soutenu puis un start f0 au-dessus du seuil d'activité estimé. Le silence initial est ignoré; les fenêtres des caractères sont ensuite recalées localement avec la période de bit estimée, et les décisions sont faites sur leurs corrélations I/Q. Aucun bit original n'est fourni au récepteur.
- Le récepteur distingue un court silence/bruit de fin d'une trame commencée mais réellement incomplète. Les restes de moins d'un bit ne déclenchent plus à eux seuls une erreur.
- Un stop invalide n'est jamais forcé à 1. Le diagnostic inclut caractère, positions start/stop, bits, énergies E0/E1 et confiance. Une recherche de reprise 8N1 est tentée; toute donnée rejetée reste signalée comme invalide/perdue.
- `diagnostic_audio.py` mesure les fichiers WAV, teste la détection et écrit cinq graphiques issus des échantillons réels.

## Tests et validations

Le jeu existant a été conservé sans modification. Les nouveaux tests couvrent les indices audio numériques, faible amplitude, bruit avant/après, fin de silence non alignée, atténuations f0/f1 différentes, écho, dérive d'horloge de 1,5 %, décalage temporel, troncature réelle, stop invalide et WAV physique fourni.

Les tests AWGN G8 à graine 2026 et 10 000 bits conservent les résultats attendus : TEB 0 à 6, 3, 0 et −3 dB; 0,0001 à −6 dB; 0,0104 à −9 dB; 0,064 à −12 dB. Cette simulation à synchronisation connue n'est pas une validation physique.

## Diagnostic et reprise des essais physiques

Depuis `modem.G8/`, produire/consulter le diagnostic du WAV reçu :

```bash
python diagnostic_audio.py mesures/module2/physique/air/test_local_recu.wav --profil G8
python recevoir.py mesures/module2/physique/air/test_local_recu.wav --profil G8 --debug
```

Le second appel doit refuser ce fichier faute de porteuse confirmée; ce résultat est volontaire et ne doit pas être contourné par une modification des données. Les PNG générés sont `signal_recu.png`, `spectre_recu.png`, `energie_f0_f1.png`, `detection_porteuse.png` et `synchronisation_bits.png` dans le dossier du WAV.

Pour un nouvel essai, vérifier d'abord les périphériques sur chaque machine et sélectionner explicitement le périphérique d'entrée/sortie. Démarrer l'acquisition avant l'émission :

```bash
python recevoir.py --liste-peripheriques
python emettre.py --liste-peripheriques
python recevoir.py --micro --duree 10 --device ID_ENTREE --profil G8 \
  --enregistrement mesures/module2/physique/air/test_local_recu.wav
```

Sur l'autre machine, lancer pendant l'acquisition :

```bash
python emettre.py "BONJOUR G8" --profil G8 \
  --sortie mesures/module2/physique/air/test_local_emis.wav \
  --jouer --device ID_SORTIE --volume 0.5
```

Après l'essai, garder les deux WAV bruts, lancer `diagnostic_audio.py`, puis `recevoir.py ... --debug`. Vérifier le niveau d'entrée et le routage si le préambule n'apparaît toujours pas. Aucune commande ci-dessus n'affirme qu'un essai physique a été réalisé.

## Commandes de validation

```bash
python -m unittest discover -s tests -v
python recevoir.py mesures/module2/physique/air/test_local_recu.wav --profil G8 --debug
python recevoir.py mesures/module2/fsk_message_G8.wav --profil G8
python recevoir.py mesures/module2/fsk_message_bell103.wav --profil bell103
python mesures_module2.py --bits 10000 --seed 2026
```
