# Modem acoustique — Module 1 — G8
UNH · Télématique L3 · Ass. Nathan MBAYO · 2026–2027

Préparation des données : entropie, compression zlib, trames 8N1/8E2 et TLM-HDLC, bit stuffing, CRC-16 et boucle locale sans son.

## Fichiers à remettre

- `source.py` : lecture, entropie, compression et en-tête TLM1.
- `crc.py` : CRC-16/CCITT (polynôme 0x1021, initialisation 0xFFFF).
- `trame.py` : formats, stuffing et boucle locale ; paramètres G8 intégrés (adresse 0x18, 48 octets par trame).
- `tests/test_module1.py` : vérifications et calcul des tableaux demandés.
- `mesures/` : tableaux entropie/compression, rendements, erreurs détectées et résultats SHA-256.
- `docs/journal_a_completer.md` : journal à compléter avec les heures et conditions réelles, puis à faire viser.

Les trois fichiers de démonstration sont dans `donnees/`. Utiliser les fichiers de l'enseignant lorsqu'ils sont fournis. Les fichiers reconstruits sont dans `reception/`.

Les conventions binaires sont précisées dans `docs/protocole.md`. La déclaration IA, exigée en cas d'utilisation de l'IA, se trouve dans `docs/declaration_IA.md`.

## Exécuter dans ia.labo2.0

Depuis la racine du projet, dans le terminal où l'environnement est activé :

```bash
python -m unittest discover -s tests -v
python crc.py
python tests/test_module1.py --mesures
```

Python seul suffit ; aucune bibliothèque externe n'est utilisée pour ces commandes.

J1 : `python crc.py` doit afficher `0x29B1`.

J2 : tester le fichier imposé par l'enseignant :

```bash
python trame.py "donnees/texte.txt"
```

La commande affiche les deux SHA-256 et `identiques : True`. La limite actuelle du nom est de 18 octets UTF-8 ; voir les conventions du protocole.

Pour recalculer les tableaux avec les fichiers de la séance, placer `texte.txt`, `image.png` et `aleatoire.bin` dans `donnees/`, puis relancer `python tests/test_module1.py --mesures`. Les résultats précédents et fichiers reçus de mêmes noms sont remplacés.

## Outils ajoutés et exécution

`config.py` centralise G8 : adresse `0x18`, charge utile 48 octets, f0/f1 `1800/3600 Hz`, Fe `48000 Hz`, débit `100 bauds`, amplitude `0.5`, CRC `0x1021`/`0xFFFF`. Cette variante est réglée pour une liaison acoustique haut-parleur/microphone. Bell 103 est isolé dans `BELL103` pour les essais de compatibilité.

Sous Ubuntu, créer un environnement virtuel puis installer les dépendances Python :

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

`sounddevice` peut nécessiter PortAudio fourni par le système. Le projet ne réalise aucune installation système automatique.

```bash
python main.py environnement
python main.py crc
python main.py boucle donnees/texte.txt
python main.py mesures
python graphiques.py
python main.py audio
python main.py audio --jouer
```

`audio` crée `mesures/tonalite_1000Hz.wav`, mono, 1 kHz, 48 kHz, deux secondes et amplitude 0,5. Sans `--jouer`, aucun périphérique n'est sollicité; l'écoute et le microphone restent des validations humaines. Les graphiques proviennent des CSV et ne sont pas des captures Audacity.

Voir `docs/protocole.md`, `docs/AUDIT_MODULE1.md`, `docs/resultats_commentes.md` et les gabarits d'annexes. Les validations officielles, signatures, expériences physiques et annexes Word externes ne sont pas prétendues comme effectuées.

## Validation en séance

J1 et J2 restent à faire valider par l'enseignant. Remplir le journal avec les mesures réelles, comparer à la fiche A1 et compléter les annexes applicables. Sauvegarder le dossier sur deux supports. Chaque membre doit pouvoir expliquer le code.
