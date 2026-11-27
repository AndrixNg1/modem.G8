# Module 3 — phase 1 ARQ

`arq.py` implémente un stop-and-wait semi-duplex simulé. Les trames I utilisent directement `construire_trame` et son CRC-16; le bit de contrôle 0 alterne N(S). Les ACK/NAK sont des trames de supervision de longueur zéro : N(R) est le prochain numéro attendu.

Après chaque émission, l'émetteur attend un ACK valide jusqu'à 3 s simulées. Une perte, un ACK invalide ou NAK entraîne la retransmission, au maximum cinq tentatives. Le récepteur ré-ACKe les doublons sans recopier leur charge utile.

Les statistiques de l'émetteur décrivent les tentatives et ACK reçus; celles du récepteur décrivent acceptation, octets, doublons et ACK émis. Le bilan de transfert publie les compteurs récepteur pertinents sans les additionner. `duree_simulee` est actuellement la somme des délais injectés par le canal; les durées de modulation et de basculement ne sont pas modélisées dans `CanalSimule`.

Exécuter `python demo_arq.py` et `python -m unittest tests.test_arq -v`. Cette phase reste strictement simulée : aucune transmission audio, aucun jalon J6/J7 n'est déclaré validé.
