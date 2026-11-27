# Essais du modem G8 entre deux PC

## Réseau et matériel

Les deux PC n'ont pas besoin du même Wi-Fi, ni d'Internet, d'adresse IP ou de
Bluetooth : le modem transmet par le son. Internet peut servir à récupérer le
projet et installer les dépendances avant la séance, pas à transporter les données.

Copier la même version du projet sur les deux PC. Prévoir un haut-parleur sur
le PC A et un microphone sur le PC B pour le premier essai à sens unique.
Pour le futur ARQ réel, chaque PC doit pouvoir émettre et recevoir du son,
car B devra renvoyer les ACK/NAK à A.

Pour les essais par air, commencer dans une pièce calme, à environ 25 cm,
avec un volume modéré. Choisir les vrais périphériques audio, pas une entrée
« Monitor » de la sortie locale. Éviter les traitements de voix, réduction de
bruit et annulation d'écho s'ils éliminent les tonalités ; conserver les WAV bruts.

Un essai par câble demande une sortie audio de A et une entrée ligne compatible
de B. Une prise casque ou une prise combinée casque/micro n'est pas forcément une
entrée ligne. Vérifier les connecteurs et niveaux du matériel avant branchement ;
ne pas supposer qu'un simple câble entre deux sorties casque constitue un canal.
Pour un ARQ bidirectionnel par câble, il faut aussi un trajet de B vers A.

## Installation sur les deux machines

Ouvrir un terminal dans la racine de la copie locale du projet :

```bash
python -m venv .venv
```

Activer l'environnement :

- Ubuntu/Linux : `source .venv/bin/activate`
- Windows PowerShell : `.\.venv\Scripts\Activate.ps1`

Si `python` n'est pas disponible, utiliser `python3` sous Linux ou `py` sous
Windows pour créer l'environnement. Ensuite :

```bash
python -m pip install -r requirements.txt
python main.py crc
python emettre.py --liste-peripheriques
```

Le CRC doit donner `0x29B1`. Sounddevice nécessite PortAudio et l'accès au
microphone dans les réglages du système. Les indices de périphériques diffèrent
sur chaque PC et peuvent changer lorsqu'on rebranche une carte audio.

## Premier essai réel : un message court

Ce test vérifie le trajet A → B. Il n'envoie pas encore un fichier avec ARQ.
Sur les deux PC, utiliser le même profil.

Sur le PC B, démarrer d'abord l'enregistrement :

```bash
python recevoir.py --micro --duree 15 --profil G8 --enregistrement mesures/reception_pc_b.wav --debug
```

Puis, immédiatement sur le PC A :

```bash
python emettre.py "BONJOUR G8" --profil G8 --duree 3 --jouer --volume 0.5 --sortie mesures/emission_pc_a.wav
```

Si le périphérique par défaut est incorrect, ajouter `--device INDEX` avec
l'indice d'entrée de B ou l'indice de sortie de A obtenus par la liste.
Attendre la fin des 15 secondes : le récepteur décode après l'acquisition,
pas pendant. La validation est l'affichage exact de `BONJOUR G8` sur B.

`--duree 3` prolonge le son à trois secondes pour ce message, sans modifier
le débit ni répéter les données. La porteuse avant le message est allongée.
La durée est un minimum : un message plus long n'est jamais tronqué. L'écoute
sur B reste de quinze secondes ; ne pas attendre sa ligne `acquisition` avant
de lancer A, car elle s'affiche seulement après l'enregistrement.

Si le profil officiel 7400/7600 Hz ne passe pas sur le matériel, refaire les
deux commandes avec `--profil G8_acoustique` (1800/3600 Hz, 100 bauds). Ce
profil est expérimental : une réussite ne valide pas le profil officiel G8.

Pour vérifier le trajet de retour, inverser les rôles : A enregistre, B émet.
Cela reste deux essais manuels, pas un échange automatique d'ACK/NAK.

## En cas d'échec

Sur B, garder la capture originale et la réanalyser sans réenregistrer :

```bash
python recevoir.py mesures/reception_pc_b.wav --profil G8 --debug
python diagnostic_audio.py mesures/reception_pc_b.wav --profil G8
```

Employer le profil réellement émis. Vérifier le microphone autorisé et actif,
le bon périphérique, le volume, la saturation et la présence des fréquences.
Si la capture est saturée, baisser le gain ou le volume ; augmenter le volume
sans mesure ne corrige pas un mauvais routage. Si elle est tronquée, augmenter
la durée et démarrer B avant A.

Archiver séparément les WAV de chaque essai, le profil, les périphériques,
la distance, le volume et le texte réellement reçu.

## Passage au fichier complet

La commande `python main.py fichier-simuler ...` valide maintenant un fichier
complet avec ARQ/FSK et SHA-256 **dans un seul processus**. Elle ne transmet
rien au second PC. Il n'existe pas encore de commande fiable d'émission/réception
de fichier avec ARQ audio entre deux processus : il reste à implémenter le
canal semi-duplex et l'échange réel des ACK/NAK avant la démonstration J6/J7.

Après cette intégration, démarrer le récepteur B, puis l'émetteur A, transmettre
un fichier de 2 Kio maximum et comparer les SHA-256 sur les deux machines :

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('chemin_du_fichier'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

Le nom et le chemin peuvent différer ; les deux empreintes et les octets doivent
correspondre. Une simulation ou un message court reçu ne suffisent pas à déclarer
le transfert complet de fichier physiquement validé.
