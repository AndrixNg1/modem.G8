# Bilan final — module 2

Le modem réalise une CPFSK à phase continue, avec annonce porteuse, tramage 8N1, détection par corrélation I/Q, synchronisation et contrôle des bits stop.

| Profil | f0/f1 | Débit | Statut |
|---|---|---:|---|
| G8 | 7400/7600 Hz | 300 bauds | Profil officiel, conformité J3 à démontrer physiquement |
| G8_acoustique | 1800/3600 Hz | 100 bauds | Essai air réussi, variante expérimentale non officielle |
| bell103 | 1070/1270 Hz | 300 bauds | Compatibilité locale à vérifier avec la référence officielle |

La démonstration acoustique documentée a reçu `BONJOUR G8` (10 caractères, 0 bit ambigu, sans écrêtage) avec `G8_acoustique`. J3, J4 et J5 restent soumis à la validation de l'enseignant. Les étudiants doivent compléter et vérifier la déclaration d'usage de l'IA avant remise.

Commandes : `python emettre.py "BONJOUR G8" --profil G8_acoustique --jouer` puis `python recevoir.py --micro --profil G8_acoustique`.
