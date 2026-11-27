# Canal ARQ audio semi-duplex

## Architecture

`canal_audio_arq.py` réutilise les trames HDLC, CPFSK, prétraitement DSP et
ARQ stop-and-wait existants. Une trame est encodée ainsi : porteuse f1,
séquence `10` répétée 16 fois, bits HDLC, garde f1. Le récepteur cherche le
préambule, démodule, valide HDLC/CRC, puis émet un ACK ou NAK dans une fenêtre
audio distincte. Le pair émetteur n'écoute qu'après sa lecture : il n'y a pas
de traitement simultané de sa propre émission.

États journalisés : `IDLE`, `TRANSMISSION_I`, `ATTENTE_ACK`, `RECEPTION_I`,
`VALIDATION_CRC`, `EMISSION_ACK`, `EMISSION_NAK`, `RETRANSMISSION`, `TERMINE`
et `ABANDON`. Les temps sont monotones; le timeout et cinq tentatives restent
ceux d'`arq.py` (3 s, 5). Après la dernière trame, le récepteur reste à
l'écoute pendant une garde afin de réacquitter une retransmission causée par
la perte du dernier ACK.

Le fichier est transporté sous la forme `TLM1 + données + SHA-256(32 octets)`
dans les blocs ARQ. Le SHA est donc lui-même transporté par le son. Le fichier
n'est écrit qu'après décompression, tailles et empreinte correctes, avec ouverture
exclusive pour éviter l'écrasement.

## Commandes entre deux PC

Commencer le PC B, puis le PC A. Les index sont des exemples et ne sont jamais
codés dans le programme : vérifier-les par `python recevoir.py --liste-peripheriques`.

```bash
# PC B : écoute, valide, répond par ACK/NAK et reconstruit le fichier
python transfert_audio.py recevoir --profil G8 --protection basic \
  --entree-audio 15 --sortie-audio 13 --dossier-reception recus/ \
  --fenetre 1 --session 120 --garde-fin 5

# PC A : émet puis attend chaque ACK/NAK sonore
python transfert_audio.py envoyer exemple.txt --profil G8 --protection basic \
  --entree-audio 15 --sortie-audio 13 --timeout 3
```

Pour comparer, répéter avec `--protection off` et `--protection advanced`, en
conservant gains, volume, distance, orientation et WAV bruts. Commencer avec
un message court puis 48, 144, 1 Kio et 2 Kio à 25 cm; seulement ensuite
augmenter distance et bruit.

## Audit d'amplitude

Une valeur capturée de 2,168 est un dépassement réel du flux `float32`
Sounddevice : l'acquisition ne la normalise pas. Les WAV PCM entiers sont
normalisés seulement lors de la lecture par `recevoir.py`; les WAV flottants
gardent leur amplitude. Le moyennage stéréo ne peut pas augmenter un pic.
`audio_io.statistiques` conserve donc le maximum brut et signale l'écrêtage;
aucune normalisation après capture ne masque le problème. Réduire gain micro,
volume système ou émission avant un essai matériel.

Une acquisition contenant NaN/Inf est maintenant refusée explicitement avant
le démodulateur. Le serveur tolère une fenêtre invalide, mais s'arrête après
trois acquisitions invalides consécutives avec une erreur de périphérique/
routage compréhensible. Vérifier d'abord l'entrée seule :

```bash
python recevoir.py --micro --duree 1 --device 15 \
  --delai-depart 2 --enregistrement /tmp/test_entree_15.wav --profil G8 --protection off
```

Cette commande doit soit créer un WAV et signaler clairement son amplitude/
écrêtage, soit nommer le problème d'acquisition. Si elle échoue, ne pas lancer
le transfert : vérifier la source sélectionnée et le routage avec
`pactl list short sources`, puis choisir l'index correspondant à la source
microphone réelle (pas un monitor de sortie).

## Validation et limites

Les tests sont des simulations par mocks audio : CPFSK/HDLC, ACK sonore,
protection, basculement et saturation sont couverts. Ils ne prouvent pas la
latence PulseAudio, le routage des périphériques, les échos ou la réussite
entre deux ordinateurs. Aucun essai physique n'est déclaré dans ce dépôt.
