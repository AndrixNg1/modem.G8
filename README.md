# Modem acoustique — Module 1 — G8
UNH · Télématique L3 · Ass. Nathan MBAYO · 2026–2027

Modem acoustique pédagogique en Python — groupe G8, Télématique L3 à l'UNH. Le module 1 couvre l'entropie, la compression zlib, le tramage 8N1/8E2 et TLM-HDLC, le bit stuffing et le CRC-16, avec reconstruction des fichiers en boucle locale et vérification SHA-256.

Périmètre retenu : module 1, préparation des données et test en boucle locale sans son, sur un seul PC.

## Démarrage avec l'environnement ia.labo2.0 (Linux)

Dans le terminal où `ia.labo2.0` est déjà activé :

```bash
python -m unittest discover -s tests -v
python main.py crc
python main.py mesures
python graphiques.py
```

Si l'environnement n'est pas activé : `conda activate ia.labo2.0`.
Le Python utilisé pour la vérification locale est `/home/andrix-ng/anaconda3/envs/ia.labo2.0/bin/python`.

## Démarrage rapide (Windows)
1. Extraire entièrement le ZIP dans un dossier (ne pas exécuter depuis le ZIP).
2. Installer Python 3.10 ou plus récent si nécessaire. Cocher « Add Python to PATH » à l'installation.
3. Double-cliquer sur `LANCER_MODULE1.bat` ou ouvrir PowerShell dans ce dossier et saisir les commandes suivantes.

```powershell
python -m unittest discover -s tests -v
python main.py crc
python main.py mesures
```

Les trois commandes fonctionnent sans installation de bibliothèque externe. Si `python` est inconnu, essayer `py -3` à sa place. Le dossier `mesures/` contient les CSV, le résumé et les traces de tests. Les fichiers reconstruits sont dans `reception/`.

## Démonstration au professeur
- J1 : `python main.py crc` doit donner `0x29B1`.
- J2 : `python main.py boucle "C:\chemin\fichier.txt"` (remplacer le chemin). Le programme affiche les deux SHA-256 et `identiques : True`. Choisir un nom simple de 18 octets UTF-8 maximum, sinon travailler sur une copie renommée. Le contenu n'est jamais modifié à l'émission.
- Pour refaire les mesures avec les fichiers fournis en séance : placer `texte.txt`, `image.png`, `aleatoire.bin` dans `donnees/` (conserver une copie des fichiers actuels). Puis relancer `python main.py mesures`. Les anciens CSV et fichiers de réception portant les mêmes noms seront remplacés.
- Pour restaurer les fichiers de démonstration : `python generer_donnees.py` (écrase les trois fichiers du dossier `donnees/`).

## Graphiques des mesures (facultatif)

Les tests, le CRC et la boucle locale fonctionnent avec Python seul. Pour générer les graphiques des tableaux :

```bash
python -m pip install -r requirements.txt
python graphiques.py
```

## Contenu
- `source.py` : lire les octets, entropie, zlib, en-tête TLM1.
- `crc.py` : CRC-16/CCITT codé à la main, test de référence.
- `trame.py` : 8N1, 8E2, conversion LSB, TLM-HDLC, stuffing et extraction.
- `transfert.py` : découpage, en-tête, reconstruction, SHA-256.
- `config.py` : groupe G8, adresse 0x18, N=48 et bits de contrôle des trames.
- `mesures_module1.py` : trois tableaux de mesures et contrôle des fichiers.
- `tests/` : tests unitaires et de bout en bout (unittest).
- `donnees/` : trois fichiers de démonstration générés, pas des fichiers distribués par le professeur.
- `mesures/` : résultats réellement calculés et graphiques de démonstration.
- `reception/` : fichiers réellement reconstruits.
- `docs/` : notes de rapport, protocole, aide à l'oral, déclaration IA préparatoire et journal à renseigner.

## Hypothèses à confirmer avec le professeur
Les PDF donnent les signatures, champs, tailles maximales et CRC, mais pas le squelette Python original ni toutes les conventions binaires. Voir `docs/protocole.md` pour nos choix (ordre des octets, en-tête et contrôle). Le groupe retenu est G8. Si le professeur fournit un format différent, adapter le code avant l'interopérabilité. Le module 1 est fonctionnel en boucle locale selon ces conventions ; les jalons J1/J2 officiels et les visas ne sont pas acquis avant la démonstration devant le professeur.

## Travail à remettre
Joindre source.py, crc.py, trame.py et tests/, ainsi que les autres fichiers nécessaires à leur fonctionnement. Remettre les tableaux issus de la séance, le journal visé (annexe B), la fiche individuelle A1 selon le professeur, la fiche C et la déclaration IA D remplie et signée. Sauvegarder le dossier sur deux supports. Ne pas présenter les résultats pré-calculés ici comme des mesures effectuées en salle : les refaire et noter l'heure et les conditions réelles.
