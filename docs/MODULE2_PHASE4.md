# Module 2 — Phase 4 : préparation de transmission physique G8

## Architecture et limites

`emettre.py` crée/sauvegarde le CPFSK G8 puis peut le jouer via `audio_io.py`. `recevoir.py --micro` effectue d'abord une acquisition finie à 48 kHz, sauvegarde éventuellement le WAV brut, puis réutilise exactement la réception WAV de phase 2. Ce n'est pas encore une réception temps réel continue. Les paramètres restent f0=7400 Hz, f1=7600 Hz, 300 bauds, 48 kHz, annonce f1 de 0,3 s, 8N1 et 160 échantillons par bit.

L'acquisition et la lecture sont protégées contre périphérique incompatible, erreur PortAudio, signal mono invalide et écrêtage. Les périphériques sont sélectionnables explicitement; aucun choix implicite de périphérique par défaut n'est requis. Aucune expérience câble/air n'a été réalisée par ce logiciel ou déclarée dans ce dépôt.

Les valeurs `--device 15` et `--device "13"` sont normalisées en indices entiers avant toute opération PortAudio; un nom tel que `--device "USB Audio"` reste textuel et l'absence de `--device` conserve le périphérique par défaut. La liste affiche désormais index, nom, canaux entrée/sortie et fréquence par défaut. `emmettre.py` est le nom historique contenant l'implémentation; `emettre.py` est l'alias correctement orthographié, sans duplication de logique.

## Commandes

```bash
# Sur chaque machine : identifier les indices/identifiants disponibles
python emettre.py --liste-peripheriques
python recevoir.py --liste-peripheriques

# Ordinateur B — démarrer avant A; acquisition finie de 10 s
python recevoir.py --micro --duree 10 --device ID_ENTREE --profil G8 \
  --enregistrement mesures/module2/physique/air/recu.wav --sortie-octets recu.bin

# Ordinateur A — créer simultanément l'archive WAV et jouer sur la sortie choisie
python emettre.py "BONJOUR G8" --profil G8 --sortie mesures/module2/physique/air/emis.wav \
  --jouer --device ID_SORTIE --volume 0.5

# Décodage hors ligne de l'enregistrement B
python recevoir.py mesures/module2/physique/air/recu.wav --profil G8 --sortie-octets recu.bin
python mesures_physiques.py --initialiser
```

## Câble et air

Pour le câble, utiliser deux interfaces compatibles niveau ligne et vérifier masse commune, niveau, saturation et connecteurs. Ne pas relier directement une sortie casque à une entrée micro ou à une prise combinée sans vérifier les niveaux; une interface audio USB est l'alternative recommandée.

Pour J5 air : placer haut-parleur et microphone à 0,5 m, volume modéré, aucun câble audio entre les machines, enregistrer avant émission puis conserver les WAV émis/reçus. Répéter éventuellement à 0,25, 1 et 2 m, mais 0,5 m est la mesure prioritaire. Refaire pour `BONJOUR G8` et une chaîne ASCII de 160 caractères.

## Mesures et conditions

`mesures_physiques.py --initialiser` crée les dossiers `cable/`, `air/` et les CSV vides. Il n'écrit aucune ligne fictive. Lors d'un essai observé, renseigner date/heure, canal, distance, volume, périphériques, positions, bruit ambiant, échos et observations dans `conditions_experimentales.csv`; conserver WAV, texte/bit original et reçu. Le TEB brut compte erreurs de décision **et** différences de longueur : bits perdus ou insérés ne sont jamais ignorés. Le TEB caractère 8N1 doit être rapporté séparément.

Un niveau sonore seul ne fournit pas un S/B physique fiable. Pour l'estimer, enregistrer séparément le bruit ambiant et signal+bruit avec gain, distance et positions identiques, puis documenter précisément les bandes et fenêtres employées.

## Validation

Les tests automatisés utilisent des mocks Sounddevice et valident sélection, erreurs, écrêtage, WAV et réception hors ligne. Ils rejouent aussi les WAV avec atténuation à 15 %, composante continue et écho simple retardé de 80 échantillons. Ils ne prouvent ni écoute, ni microphone, ni liaison par câble/air. J5 exige la démonstration physique devant l'enseignant et n'est pas déclaré validé ici.

Après capture, diagnostiquer d'abord le WAV brut, puis décoder avec les informations de synchronisation :

```bash
python diagnostic_audio.py mesures/module2/physique/air/recu.wav --profil G8
python recevoir.py mesures/module2/physique/air/recu.wav --profil G8 --debug
```

Le diagnostic mesure le niveau passe-bande, le spectre et l'énergie des tonalités, estime le début de porteuse et du start, puis écrit cinq PNG dans le dossier du WAV. En l'absence de préambule f1 crédible, la réception échoue explicitement au lieu de prendre du bruit pour des bits. Voir [le rapport de correction de robustesse](./MODULE2_CORRECTION_ROBUSTESSE.md) pour les résultats mesurés des WAV physiques fournis et les commandes de reprise.
