# Module 3 — phase 3 : fichiers complets en simulation

État au 27 novembre 2026 : la chaîne locale lit un vrai fichier, décide de la
compression zlib, ajoute l'en-tête TLM1, découpe le paquet en blocs de 48 octets,
puis fait traverser chaque I et chaque ACK/NAK par CPFSK. Le récepteur ARQ
assemble les blocs sans doublons. L'en-tête et les tailles sont vérifiés avant
décompression et écriture ; les SHA-256 et les octets sont comparés à l'original.

Cette commande est une simulation dans un seul processus : elle ne sollicite
ni haut-parleur ni microphone et ne connecte pas deux PC.

## Exécuter un transfert

Depuis la racine, dans l'environnement Python du projet :

```bash
python main.py fichier-simuler donnees/message_g8.txt --sortie reception/mon_essai
python main.py fichier-simuler donnees/message_g8.txt --sortie reception/mon_essai_perte --actions ok perte_ack
```

Le deuxième essai perd le premier ACK, retransmet et ignore le doublon.
Un dossier de réception contenant déjà le fichier est refusé pour conserver
les preuves précédentes. Le nom reste limité à 18 octets UTF-8 selon TLM1 ; la
démonstration accepte au maximum 2048 octets avant compression, fichier vide inclus.
Un abandon ou un paquet invalide ne produit pas de fichier reçu.

Le paquet est `en-tête TLM1 | données éventuellement compressées`. La limite
d'en-tête est déterminée par le champ longueur du nom. Le paquet est ensuite
segmenté par ARQ ; il ne faut pas confondre cette interface avec les trames
de la boucle locale J2, où l'en-tête occupe une trame séparée.

## Corrections des mesures

- Le timeout est compté une seule fois, à l'émetteur, et respecte sa valeur
  configurée. Un ACK absent ou invalide entraîne l'attente ; un NAK valide
  autorise la retransmission immédiate.
- Les statistiques du récepteur sont récupérées même si l'émetteur abandonne.
- Le nombre de bits différents utilise le poids binaire du XOR, pas huit
  erreurs pour chaque octet différent. Pertes et insertions sont séparées.
- Le TEB brut est compté avant CRC sur les bits réellement modulés puis
  démodulés, synchronisation provisoire incluse et supposée connue, dans les
  deux sens et sur les retransmissions. Il ne représente pas le canal physique.
- Les réalisations AWGN sont indépendantes par essai/bloc/tentative/sens.
  Avec et sans ARQ, la première émission d'un même bloc utilise le même bruit.
- Le débit utile du transfert est nul en cas d'abandon, même si une partie
  de la charge a été reçue. Il est exprimé en bit/s.
- La taille demandée n'est plus tronquée silencieusement à 256 octets.

Les nouvelles campagnes sont dans `mesures/module3/simulation_corrigee/`.
Les CSV historiques de `simulation/` restent intacts et ne doivent pas être
mélangés aux nouveaux résultats. À −6 dB, les nouveaux essais donnent 20/20
avec ARQ, 11/20 sans retransmission, et 13 retransmissions au total. Ce résultat
remplace la comparaison historique 20/20 contre 13/20 pour la nouvelle campagne.

```bash
python mesures_arq.py
python mesures_arq.py --sans-arq
python synthese_module3.py
python graphiques_module3.py
python -m unittest discover -s tests -v
```

## Essais couverts et suite

Les tests couvrent TXT, CSV, PNG, ZIP, binaire, fichier vide, 1 Kio et 2 Kio,
compression utile/inutile, perte d'ACK, abandon, paquet tronqué, tailles
incohérentes et protection des fichiers existants.

La suite est le canal audio ARQ semi-duplex : émission d'une I, écoute de
l'ACK/NAK sur l'autre PC, temporisation réelle, retransmission puis fermeture
de session. Il n'est pas encore implémenté. Le [guide deux PC](GUIDE_DEUX_PC.md)
décrit le premier essai sonore réalisable et les limites actuelles.
