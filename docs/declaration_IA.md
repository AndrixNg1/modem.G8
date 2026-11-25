# Annexe D — éléments préparatoires (à vérifier et recopier sur la fiche officielle)
Groupe retenu : G8. Outil : ChatGPT (GPT-6.2 pour la préparation initiale ; Codex pour l'adaptation G8 et les tests dans ia.labo2.0).

| Partie | Demande à l'IA | Éléments repris | Vérification à effectuer par le groupe |
|---|---|---|---|
| Codage source | Écrire les fonctions de l'annexe E | source.py, format d'en-tête local | Lire le code, refaire les tests d'entropie et compression |
| CRC | Implémenter CRC-16/CCITT | crc.py | Test J1, comparaison indépendante de référence dans tests/ |
| Tramage et transfert | Construire les formats et la boucle locale | trame.py (boucle locale incluse) | Refaire les tests et J2 sur le fichier imposé |
| Mesures | Automatiser les tableaux | tests/test_module1.py (mesures incluses), données de démonstration, CSV | Refaire les mesures avec les fichiers de la séance |

## Erreur de l'IA observée pendant la génération du projet
Le premier brouillon de `construire_entete` enregistrait `len(nom)` dans le champ de longueur du nom. Le test sur `été.txt` a échoué : sept caractères, mais neuf octets UTF-8. Le décodeur a rejeté l'en-tête. Correction : utiliser `len(code)`, où `code` est le nom encodé en UTF-8. Le test a alors réussi. Voir `trace_correction_IA.txt`, générée lors de l'exécution, et `test_entete_accents_regression`.

Pour que le groupe vérifie lui-même l'erreur : faire une copie de source.py, remplacer provisoirement `len(code)` par `len(nom)` uniquement dans le retour de `construire_entete`, puis exécuter `python -m unittest discover -s tests -k accents -v`. Observer l'échec. Restaurer le fichier original et relancer : succès attendu. Ne pas remettre une version défectueuse. Noter qui a exécuté le test et la date réelle. Le groupe ne doit pas certifier avoir lui-même détecté l'erreur avant d'avoir reproduit la vérification.

Signatures : à compléter par les cinq membres sur l'annexe D officielle.
