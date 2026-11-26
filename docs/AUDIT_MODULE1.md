# Audit final — Module 1 — Modem acoustique G8

**Date d'exécution :** 26 novembre 2026  
**Périmètre :** dépôt fourni, sans modification du code de production. Un changement non indexé de `mesures/boucle_locale.csv` était déjà présent au début de l'audit : il ne porte que sur les chemins absolus de destination et a été préservé.

## 1. Résumé général

Le noyau numérique du module 1 est fiable dans le périmètre effectivement implémenté : préparation de source, CRC-16/CCITT-FALSE, trames 8N1/8E2, TLM-HDLC, stuffing et boucle locale sans audio. Les fichiers fournis sont reconstruits à l'identique, avec égalité octet par octet et SHA-256.

Le dépôt n'est toutefois pas un livrable module 1 complet au regard du cahier d'audit : il manque l'environnement audio, les scripts `main.py`, `mesures_module1.py` et `graphiques.py`, les graphiques, `requirements.txt`, les documents/annexes annoncés et la configuration FSK G8 (7400/7600 Hz, 48 kHz, 300 bauds). Les fréquences Bell 103 ne sont pas présentes, ce qui est correct à ce stade.

## 2. Analyse par fichier

| Élément | Statut | Constat et preuve |
|---|---|---|
| `source.py` | CONFORME | Lecture binaire (`Path.read_bytes`), entropie de Shannon et cas vide, zlib réversible, statistiques Qc/taux/gain, en-tête `TLM1`. Les noms UTF-8 sont acceptés ; séparateurs, caractères interdits, tailles et en-têtes tronqués sont contrôlés. |
| En-tête TLM1 | PARTIELLEMENT CONFORME | Convention propre documentée dans les commentaires : `magic(4) | compression(1) | taille originale uint32 BE | taille transmise uint32 BE | taille nom(1) | nom UTF-8`, avec nom limité à 18 octets. Le README renvoie à `docs/protocole.md`, mais ce document est absent : la distinction professeur/choix local est donc insuffisamment livrée. |
| `crc.py` | CONFORME | Implémentation manuelle MSB-first, polynôme `0x1021`, init. `0xFFFF`, masque 16 bits, pas de réflexion/XOR final. Le vecteur `123456789` retourne `0x29B1`. |
| `trame.py` | CONFORME | 8N1 et 8E2 LSB-first, fanions `0x7E`, données max. 48, CRC sur adresse→données, CRC sérialisé big-endian selon convention locale, stuffing hors fanions, extraction de flux et contrôles adresse/contrôle/séquence/dernière trame. |
| Tests | PARTIELLEMENT CONFORME | 33 tests réussissent et couvrent les principaux cas. La détection double/rafale a été contrôlée indépendamment lors de l'audit, mais ces scénarios ne sont pas encore des tests de régression versionnés. |
| `mesures/` | CONFORME | Les CSV et `resultats.txt` sont cohérents avec le recalcul effectué. La formule de prédiction utilise bien les longueurs de trames individuelles avec stuffing. |
| README | PARTIELLEMENT CONFORME | Commandes et périmètre numérique bien décrits, mais il référence des fichiers inexistants : `docs/journal_a_completer.md`, `docs/protocole.md` et `docs/declaration_IA.md`. |
| Audio/configuration FSK | NON CONFORME | Aucun `requirements.txt`, aucune dépendance NumPy/SciPy/Sounddevice/Matplotlib, aucun générateur WAV 1 kHz, aucun contrôle 48 kHz, aucune constante f0/f1/débit. Aucun test physique n'a donc été mené. |
| Scripts/livrables d'orchestration | NON CONFORME | `main.py`, `mesures_module1.py` et `graphiques.py` sont absents. |
| Annexes A1–E, journal et déclaration IA | NON CONFORME | Absents du dépôt fourni ; leur présence ne peut pas être déduite des commentaires du README. |

## 3. Configuration G8

| Paramètre demandé | Statut | Vérification |
|---|---|---|
| Groupe G8, adresse `0x18`, charge utile 48 octets | CONFORME | Constantes `GROUPE`, `ADRESSE`, `N` dans `trame.py` ; testés. |
| CRC `0x1021`, init. `0xFFFF` | CONFORME | `crc.py` et test indépendant `binascii.crc_hqx`. |
| f0=7400 Hz, f1=7600 Hz, Fe=48000 Hz, 300 bauds | NON CONFORME | Non définis dans le dépôt. |
| Ancienne configuration G1 / Bell 103 | CONFORME | Recherche textuelle : aucune occurrence de G1, 1070 ou 1270 Hz. |

## 4. Tests réellement exécutés

| Commande | Résultat |
|---|---|
| `git status --short` | État initial : `M mesures/boucle_locale.csv`, uniquement sur les chemins absolus de destination ; changement préexistant préservé. |
| `python -m unittest discover -s tests -v` | **33/33 OK**, 0,267 s. |
| `python crc.py` | `CRC("123456789") = 0x29B1`. |
| `python tests/test_module1.py --mesures` | Recalcul complet réussi ; valeurs identiques à celles attendues ci-dessous. |
| `python main.py crc` | Échec attendu : fichier `main.py` absent. |
| `python main.py mesures` | Échec attendu : fichier `main.py` absent. |
| `python graphiques.py` | Échec attendu : fichier `graphiques.py` absent. |
| Import `source`, `crc`, `trame` | Réussi, sans expérience ni interface déclenchée. |

Contrôles indépendants non ajoutés au dépôt : toutes les **89 676** inversions doubles possibles d'un corps maximal de 53 octets (424 bits) ont été rejetées ; les **6 664** rafales contiguës possibles de 1 à 16 bits ont toutes été rejetées. Les boucles locales vides, 1 octet, 48 octets, 49 octets, volumineuses, toutes valeurs 0..255 et nom `été.bin` ont reconstruit exactement la source.

## 5. Résultats expérimentaux vérifiés

Les valeurs recalculées correspondent aux données communiquées :

| Fichier | Original | H | Compressé | Qc | Gain |
|---|---:|---:|---:|---:|---:|
| `texte.txt` | 2800 | 4,1214 | 138 | 20,2899 | 95,07 % |
| `image.png` | 12420 | 7,9792 | 12431 | 0,9991 | -0,09 % |
| `aleatoire.bin` | 4096 | 7,9533 | 4107 | 0,9973 | -0,27 % |

Les rendements sont cohérents : 8N1 `384/480 = 80 %`, 8E2 `384/576 = 66,67 %`, HDLC sans stuffing `384/440 = 87,27 %`, HDLC avec stuffing `384/447 = 85,91 %`. Ce dernier est une mesure pour une trame pseudo-aléatoire donnée, pas une constante théorique.

Pour 1 000 trames par probabilité (graine 2026), les résultats sont : `p=1e-4` : 43 altérées/rejetées (CRC 38, autres 5) ; `p=1e-3` : 370 (CRC 283, autres 87) ; `p=1e-2` : 990 (CRC 395, autres 595). La prédiction est correctement calculée par trame, `Pe = 1 - (1-p)^n`, où `n` inclut le stuffing ; valeurs attendues 43,66, 360,21 et 988,75 altérations sur 1000. « Rejet CRC » et « autre rejet structurel/fanion » sont correctement distingués.

Les trois boucles réelles fournies ont égalité binaire et SHA-256 : `texte.txt` (`5c6401…def1`), `image.png` (`ea05f4…2e1f`) et `aleatoire.bin` (`4c172d…3189`).

## 6. Bugs et incohérences détectés

1. **Bloquant pour la complétude du module** : l'environnement et la chaîne audio exigés ne sont pas implémentés. Il est impossible de vérifier le WAV 1 kHz, Audacity ou le matériel micro/haut-parleur ; aucune expérience physique n'est revendiquée.
2. **Important** : la configuration de transmission n'est pas centralisée : seules adresse/taille existent dans `trame.py`; les paramètres FSK G8 et le débit sont absents. Le module 2 nécessiterait sinon d'introduire ces valeurs au moment de l'intégration.
3. **Important** : README incohérent avec le contenu livré et trois commandes obligatoires échouent car leurs scripts n'existent pas.
4. **Important administrativement** : annexes A1–E, journal de laboratoire, déclaration IA et sauvegarde sur deux supports ne sont pas vérifiables dans ce dépôt.
5. **Amélioration de qualité** : versionner les scénarios CRC d'erreurs doubles/rafales et les cas J2 48/49 octets, nom accentué et grande taille, actuellement vérifiés pendant cet audit mais pas tous explicitement dans la suite.

## 7. Préparation au module 2

Les primitives sont réutilisables : l'encodeur 8N1 produit bien des listes de bits 0/1 et le décodeur n'a pas de dépendance audio. Les imports sont sans effet de bord et le traitement est suffisamment séparé pour accueillir `modem_fsk.py`, `emettre.py` et `recevoir.py`.

Avant l'intégration, créer un module de configuration unique (adresse, MTU, CRC, f0/f1 G8, Fe, débit ; Bell 103 explicitement réservé aux tests de compatibilité), puis y faire dépendre les futurs composants audio. Cela évitera les valeurs codées en dur et préservera les protocoles existants.

## 8. Corrections recommandées

| Priorité | Action |
|---|---|
| P0 | Ajouter la configuration G8 audio et les scripts/mesures effectivement demandés, ou rectifier le périmètre officiel du module 1 si l'audio est hors périmètre. |
| P0 | Ajouter `requirements.txt`, test WAV 1 kHz/48 kHz et documenter précisément l'impossibilité éventuelle d'un test matériel. |
| P1 | Ajouter/mettre à jour `main.py`, `mesures_module1.py`, `graphiques.py` et les graphiques correspondant aux CSV. |
| P1 | Livrer réellement les documents annoncés et compléter les annexes A1–E, journal, déclaration IA et preuve de sauvegarde. |
| P2 | Transformer les contrôles CRC et limites J2 ci-dessus en tests de régression, puis documenter le format TLM1 dans `docs/protocole.md`. |

## 9. Vérifications physiques et administratives restantes

- Validation officielle J1/J2 par l'enseignant : **NON VÉRIFIÉ**.
- Lecture du WAV dans Audacity, amplitude/durée/Fe, sortie haut-parleur et entrée microphone : **NON VÉRIFIÉ** (implémentation absente).
- Réponses Annexe A1, journal visé, déclaration IA/erreur corrigée, annexes C–E et double sauvegarde : **NON VÉRIFIÉ**.

## 10. Verdict final

**GO SOUS CONDITIONS :** le noyau numérique sans son est techniquement prêt à être réutilisé par le module 2. Le module 1 ne peut pas être déclaré complet comme livrable pédagogique final tant que les éléments P0/P1 et les validations physiques/administratives ci-dessus ne sont pas fournis ou explicitement déclarés hors périmètre.

## 11. Finalisation effectuée le 26 novembre 2026

### Fichiers créés

`config.py`, `requirements.txt`, `audio_test.py`, `main.py`, `mesures_module1.py`, `graphiques.py`, `tests/test_finalisation.py`, `docs/protocole.md`, `docs/journal_a_completer.md`, `docs/declaration_IA.md`, `docs/annexe_A1.md`, `docs/suivi_jalons.md`, `docs/resultats_commentes.md`; les sept sorties graphiques et `mesures/tonalite_1000Hz.wav` ont aussi été générés à partir des mesures réelles.

### Fichiers modifiés

`crc.py` et `trame.py` importent désormais les constantes partagées de `config.py`, sans modifier les algorithmes. `README.md` documente les nouvelles commandes et limites. La modification locale préexistante de `mesures/boucle_locale.csv` a été préservée.

### Corrections et preuves de non-régression

- Paramètres G8, CRC et future configuration Bell 103 isolés dans `config.py`.
- Tonalité numérique mono 1 kHz/48 kHz/deux secondes/amplitude 0,5, avec contrôles de durée, crête, écrêtage et fréquence FFT. Aucune écoute ni capture micro n'est revendiquée.
- Mesures reproductibles extraites dans `mesures_module1.py`; graine 2026 et longueur individuelle avec stuffing conservées.
- Graphiques issus des CSV : entropie, compression, rendements, erreurs CRC, boucle locale, signal et spectre.
- Six tests de régression ajoutés (configuration, CRC double, rafales 1–16 bits, limites 48/49/volumineux avec nom UTF-8, WAV et imports). La suite compte maintenant **39 tests réussis, 0 échec**.

Commandes exécutées : `python -m unittest discover -s tests -v`, `python crc.py`, `python main.py environnement`, `python main.py crc`, `python main.py mesures`, `python tests/test_module1.py --mesures`, `python graphiques.py` (backend non interactif) et `python main.py audio`. CRC = `0x29B1`; les trois SHA-256 source/réception sont inchangés et égaux.

### Limites restantes

`numpy`, `scipy` et `matplotlib` sont disponibles dans l'environnement vérifié; `sounddevice` y est absent. La commande `python main.py environnement` retourne donc 1 de façon explicite, tandis que la génération WAV sans lecture est validée. Installer les dépendances avec `python -m pip install -r requirements.txt` dans l'environnement de travail avant d'utiliser `--jouer`; PortAudio et les autorisations de périphérique peuvent aussi être requis. Les validations physiques, Audacity, microphone, signatures, visas et annexes Word restent à réaliser.

**Verdict après finalisation : GO SOUS CONDITIONS pour le module 2.** La base numérique et les interfaces de préparation sont prêtes; la disponibilité effective de lecture audio et les validations pédagogiques restent des conditions externes.
