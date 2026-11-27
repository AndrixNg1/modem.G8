# Module 3 — phase 2

`canal_fsk.py` relie les trames HDLC binaires à CPFSK en boucle locale. Chaque I et ACK est modulé puis démodulé avant traitement ARQ. La séquence de synchronisation provisoire est `10` répété 16 fois, faute de spécification complète fournie. Les pertes et corruptions sont injectées dans le canal simulé; aucune transmission physique n'est effectuée.

## Mesures simulées

Deux campagnes AWGN appariées (profil G8 officiel, 144 octets, 20 essais par S/B, graine 2026) sont enregistrées dans `mesures/module3/simulation/`. À −6 dB, ARQ obtient 20/20 succès contre 13/20 sans ARQ, avec 9 retransmissions. À −9 et −12 dB, les transferts ARQ sont abandonnés après cinq tentatives; ils ne sont pas comptés comme réussites.

Les CSV, WAV CPFSK I/ACK/NAK et graphiques sont générés par `mesures_arq.py`, `synthese_module3.py` et `graphiques_module3.py`. Les durées sont simulées; aucune conclusion physique ni validation J6/J7 n'est revendiquée.
