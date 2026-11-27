# Modem acoustique G8 — modules 1 à 3
UNH · Télématique L3 · Ass. Nathan MBAYO · 2026–2027

Préparation des données, CPFSK, réception audio et ARQ. Le transfert complet de fichiers jusqu'à 2 Kio est maintenant intégré en simulation locale ; le canal ARQ audio entre deux PC reste à implémenter.

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

Le noyau du module 1 utilise la bibliothèque standard. La suite complète des modules 1 à 3 nécessite les dépendances de `requirements.txt`.

J1 : `python crc.py` doit afficher `0x29B1`.

J2 : tester le fichier imposé par l'enseignant :

```bash
python trame.py "donnees/texte.txt"
```

La commande affiche les deux SHA-256 et `identiques : True`. La limite actuelle du nom est de 18 octets UTF-8 ; voir les conventions du protocole.

Pour recalculer les tableaux avec les fichiers de la séance, placer `texte.txt`, `image.png` et `aleatoire.bin` dans `donnees/`, puis relancer `python tests/test_module1.py --mesures`. Les résultats précédents et fichiers reçus de mêmes noms sont remplacés.

## Outils ajoutés et exécution

`config.py` centralise G8 : adresse `0x18`, charge utile 48 octets, f0/f1 `7400/7600 Hz`, Fe `48000 Hz`, débit `300 bauds`, amplitude `0.5`, CRC `0x1021`/`0xFFFF`. Le profil expérimental `G8_acoustique` utilise `1800/3600 Hz` à `100 bauds` pour les essais haut-parleur/microphone; il ne remplace pas le profil officiel. Bell 103 reste disponible pour les essais de compatibilité.

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

Voir [le rapport général d'évolution du projet](docs/RAPPORT_EVOLUTION_PROJET.md), `docs/protocole.md`, `docs/AUDIT_MODULE1.md`, `docs/resultats_commentes.md` et les gabarits d'annexes. Les validations officielles, signatures, expériences physiques et annexes Word externes ne sont pas prétendues comme effectuées.

## Transfert de fichier ARQ/FSK simulé

```bash
python main.py fichier-simuler donnees/message_g8.txt --sortie reception/mon_essai
python main.py fichier-simuler donnees/message_g8.txt --sortie reception/mon_essai_perte --actions ok perte_ack
```

La sortie donne les deux SHA-256, `identiques: true` et les statistiques ARQ.
Les fichiers existants sont préservés. Cette commande ne joue aucun son et ne
relie pas deux machines. Les essais complets couvrent TXT, CSV, PNG, ZIP, BIN,
fichier vide, 1 Kio et 2 Kio.

Les nouveaux résultats corrigés restent séparés dans
`mesures/module3/simulation_corrigee/` :

```bash
python mesures_arq.py
python mesures_arq.py --sans-arq
python synthese_module3.py
python graphiques_module3.py
```

Voir la [phase 3](docs/MODULE3_PHASE3.md) et le [guide pratique pour deux PC](docs/GUIDE_DEUX_PC.md).
**Aucun réseau commun n'est nécessaire pour les essais acoustiques.** Le guide
donne les commandes du premier test sonore et distingue celui-ci d'un transfert
de fichier avec ACK/NAK audio, encore à implémenter.

## Protection contre le bruit

La réception WAV accepte `--protection off|basic|advanced`. `basic` conserve le
passe-bande historique et est le défaut; `advanced` ajoute uniquement la
neutralisation prudente des clics isolés. Les détails, résultats AWGN
reproductibles et limites sont dans [OPTIMISATION_PROTECTION_SIGNAL.md](docs/OPTIMISATION_PROTECTION_SIGNAL.md).

```bash
python recevoir.py capture.wav --profil G8 --protection basic
python mesures_protection_signal.py --essais 20
python mesures_acoustiques.py --essais 3
python enregistrer_bruit_ambiant.py --categorie ventilateur --duree 30 --device 2
python campagne_faux_positifs.py --captures 100
```

Les perturbations de la phase 2 sont synthétiques et reproductibles; les
captures microphone ne sont créées que par la dernière commande. Voir la
[documentation de protection](docs/OPTIMISATION_PROTECTION_SIGNAL.md) pour le
protocole entre deux PC et les limites ARQ physiques.

Pour analyser une capture réellement obtenue avec les trois protections, sans
utiliser la référence pendant le décodage :

```bash
python analyser_capture_physique.py capture.wav --profil G8 --reference "message de test" --archiver
```

## ARQ audio semi-duplex

Le transfert audio entre deux PC est disponible via [transfert_audio.py](transfert_audio.py).
Les commandes exactes, l'architecture, la convention SHA-256 et les limites
matérielles sont dans [CANAL_ARQ_PHYSIQUE.md](docs/CANAL_ARQ_PHYSIQUE.md).

## Validation en séance

J1 et J2 restent à faire valider par l'enseignant. Remplir le journal avec les mesures réelles, comparer à la fiche A1 et compléter les annexes applicables. Sauvegarder le dossier sur deux supports. Chaque membre doit pouvoir expliquer le code.
