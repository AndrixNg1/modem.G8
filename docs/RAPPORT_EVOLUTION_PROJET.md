# Rapport général de suivi — Projet Modem acoustique G8

**Université :** Université Nouveaux Horizons  
**Cours :** Télématique L3  
**Enseignant :** Ass. Nathan MBAYO  
**Année académique :** 2026–2027  
**Groupe :** G8  
**Projet :** Modem acoustique  
**Dernière actualisation :** 27 novembre 2026  
**Branche Git actuelle :** `feature/module3-arq`  
**Dernier commit vérifié :** `b999f38` — `module3-phase2` — 27 novembre 2026 à 09:44:59 (+02:00)

## Objectif

Transmettre un fichier entre deux ordinateurs exclusivement par un canal sonore, puis vérifier que le fichier reçu est strictement identique à l'original. Le critère final est l'identité octet par octet et l'égalité des empreintes SHA-256.

## Table des matières

1. [État général](#1-etat-general)
2. [Architecture](#2-architecture-generale)
3. [Configuration G8 et profils](#3-configuration-g8-et-profils)
4. [Historique chronologique](#4-historique-chronologique)
5. [Module 1 — Préparer les données](#5-module-1--preparer-les-donnees)
6. [Module 2 — Moduler et transmettre par le son](#6-module-2--moduler-et-transmettre-par-le-son)
7. [Module 3 — Fiabiliser, accélérer et valider](#7-module-3--fiabiliser-accelerer-et-valider)
8. [Registre des erreurs](#8-registre-general-des-erreurs-et-solutions)
9. [Évolution des tests](#9-evolution-des-tests-unitaires)
10. [Inventaire des fichiers](#10-inventaire-des-fichiers)
11. [Mesures et preuves](#11-inventaire-des-mesures-et-preuves-experimentales)
12. [Synthèse des performances](#12-tableau-general-de-synthese-des-performances)
13. [Conformité académique](#13-suivi-des-exigences-du-professeur)
14. [Tableau de bord](#14-tableau-de-bord-davancement)
15. [Travail restant](#15-liste-detaillee-du-travail-restant)
16. [Commandes](#16-commandes-generales-du-projet)
17. [Décisions techniques](#17-registre-des-decisions-techniques)
18. [Risques](#18-risques-et-limitations)
19. [Journal des mises à jour](#19-regles-dactualisation-et-journal)
20. [Reprise du projet](#20-reprendre-le-projet-a-partir-de-letat-actuel)
21. [Conclusion](#21-conclusion)

## 1. État général

| Élément | État vérifié |
|---|---|
| Développement | **PARTIELLEMENT TERMINÉ** |
| Module 1 numérique | **TERMINÉ** dans son périmètre local, sans validation officielle |
| Module 2 | **PARTIELLEMENT TERMINÉ** : émission/démodulation/simulation disponibles; canal physique non stable ni validé |
| Module 3 | **PARTIELLEMENT TERMINÉ** : ARQ déterministe et ARQ/FSK simulés; transfert complet fichier/audio physique restant |
| Suite actuelle | **87 tests réussis, 0 échec, 0 ignoré**, durée observée 34,861 s |
| Validation enseignant | J1–J7 non déclarés acquis sans preuve réelle |

> Une simulation est une prédiction ou une mesure numérique. Elle ne constitue pas un essai physique ni une validation officielle.

## 2. Architecture générale

```mermaid
flowchart LR
    SRC[Fichier original] --> COD[Codage source]
    COD --> CMP[Compression zlib]
    CMP --> SPL[Découpage en blocs de 48 octets]
    SPL --> HDLC[Trames TLM-HDLC]
    HDLC --> CRC[CRC-16/CCITT-FALSE]
    CRC --> ARQ[ARQ stop-and-wait]
    ARQ --> MOD[Modulation CPFSK]
    MOD --> AIR[Canal sonore]
    AIR --> DEM[Démodulation par énergies]
    DEM --> VAL[Validation CRC]
    VAL --> RECON[Reconstruction]
    RECON --> DEC[Décompression]
    DEC --> RECU[Fichier reçu]
    RECU --> SHA[Vérification SHA-256]

    DEM -.->|ACK/NAK sonore| ARQ
```

- **Codage source :** lecture binaire, entête TLM1 et nom UTF-8.
- **Compression :** zlib; chaque fichier décide si les données compressées sont utilisées.
- **Découpage :** blocs de 48 octets conformément à `N=48`.
- **TLM-HDLC :** adresse, contrôle, longueur, données, CRC, fanions, stuffing local.
- **CRC :** contrôle CRC-16/CCITT-FALSE avant remise au récepteur ARQ.
- **ARQ :** N(S)/N(R), ACK/NAK, temporisation et retransmission.
- **CPFSK :** annonce porteuse, phase continue, tramage 8N1.
- **Démodulation :** corrélations I/Q à f0/f1, puis synchronisation et extraction 8N1.
- **Reconstruction :** assemblage des charges utiles dans l'ordre, en ignorant les doublons.
- **Décompression :** restauration uniquement si l'en-tête indique la compression.
- **SHA-256 :** comparaison finale entre empreinte originale et reçue.

Dans la chaîne simulée, I, ACK et NAK traversent le canal FSK. Dans la chaîne physique actuelle, les ACK/NAK audio ne sont pas encore intégrés à un protocole semi-duplex complet entre deux ordinateurs.

## 3. Configuration G8 et profils

### Paramètres officiels du groupe

| Paramètre | Valeur vérifiée dans le code |
|---|---:|
| Groupe | G8 |
| Adresse | `0x18` |
| Charge utile maximale | 48 octets |
| f0 | 7400 Hz |
| f1 | 7600 Hz |
| Rapidité | 300 bauds |
| Échantillonnage | 48 000 Hz |
| CRC | CRC-16/CCITT-FALSE |
| Polynôme | `0x1021` |
| Initialisation | `0xFFFF` |
| Timeout ARQ | 3 secondes |
| Maximum de tentatives | 5 |

Ces valeurs sont centralisées dans [config.py](../config.py) et vérifiées dans les trames, le code FSK et les tests.

### Trois profils

| Profil | f0 | f1 | Rapidité | Format | Utilisation |
|---|---:|---:|---:|---|---|
| G8 | 7400 Hz | 7600 Hz | 300 bauds | 8N1 | Profil officiel |
| G8_acoustique | 1800 Hz | 3600 Hz | 100 bauds | 8N1 | Essais haut-parleur/microphone expérimentaux |
| bell103 | 1070 Hz | 1270 Hz | 300 bauds | 8N1 | Compatibilité locale avec Bell 103 |

Le profil `G8_acoustique` a été introduit après les faibles énergies et erreurs observées aux fréquences officielles sur le matériel disponible. Il reste une variante expérimentale, jamais un remplacement du profil G8 officiel. Bell 103 demeure réservé aux tests de compatibilité et d'interopérabilité.

## 4. Historique chronologique

| Date/ordre | Module | Phase | Objectif | Travail effectué | Fichiers concernés | Résultat | Tests | Difficultés | Statut |
|---|---|---|---|---|---|---|---:|---|---|
| 25/11/2026 | 1 | Préparation | Implémenter le noyau numérique | Entropie, zlib, en-tête, trames, CRC, stuffing | `source.py`, `crc.py`, `trame.py` | Noyau numérique opérationnel | 33 puis 39 | Documentation initialement incomplète | TERMINÉ |
| 25/11/2026 | 1 | Finalisation | Corriger et documenter | Centralisation G8, tests limites 48/49 octets, audit | `config.py`, `tests/`, `docs/AUDIT_MODULE1.md` | 39 tests confirmés | 39 | Certaines annexes absentes | TERMINÉ numériquement |
| 26/11/2026 | 1 | Mesures | Produire les preuves | Compression, rendements, corruption, SHA-256 | `mesures_module1.py`, `mesures/*` | Valeurs conformes au recalcul | 39 | Documentation de valeurs historiques | TERMINÉ |
| 26/11/2026 | 2 | Phase 1 | Émettre en CPFSK | Modulateur, profils, annonce, WAV | `modem_fsk.py`, `emettre.py` | Émission locale créée | 46-50 à confirmer | Fréquences officielles faibles en air | TERMINÉ logiciel |
| 26/11/2026 | 2 | Phase 2 | Recevoir/décoder | Énergies I/Q, synchronisation, 8N1 | `recevoir.py`, `modem_fsk.py` | Boucles G8/Bell locales exactes | 56 confirmé | Faux verrouillage/UTF-8/stop | PARTIELLEMENT TERMINÉ |
| 26/11/2026 | 2 | Phase 3 | Mesurer AWGN | 10 000 bits à sept S/B | `mesures_module2.py`, `mesures/module2/bruit/` | TEB de 0 à 0,064 | 56 | Séquence locale, pas officielle | TERMINÉ sur périmètre simulé |
| 26/11/2026 | 2 | Phase 4 | Préparer audio physique | Périphériques, WAV bruts, diagnostic | `audio_io.py`, `diagnostic_audio.py` | Outils disponibles | 61-86 à confirmer | PulseAudio/PipeWire/saturation/écho | EN COURS |
| 27/11/2026 | 3 | Phase 1 | ARQ stop-and-wait | I, ACK, NAK, doublons, timeout | `arq.py`, `tests/test_arq.py` | Scénarios déterministes validés | Incluse dans 87 | Simulation uniquement | TERMINÉ simulé |
| 27/11/2026 | 3 | Phase 2 | Intégrer ARQ/FSK | I/ACK/NAK via FSK | `canal_fsk.py`, `tests/test_arq_fsk.py` | Chaîne locale testée | Incluse dans 87 | AWGN/physique non intégré | TERMINÉ simulé |
| 27/11/2026 | 3 | Phases 3-7 | Finalisation | Fichiers, air, jalons | À compléter | Non réalisé | — | Beaucoup de validations restant | NON COMMENCÉ/BLOQUÉ |

Les valeurs 46, 50, 61, 62, 73, 83 et 86 sont mentionnées dans la demande historique mais ne sont pas confirmées par un document vérifié dans ce dépôt. Elles sont conservées comme jalons à confirmer, sans prétendre qu'elles représentent un résultat actuel.

## 5. Module 1 — Préparer les données

### 5.1 Fonctionnalités

- **Entropie de Shannon :** calculée sur les octets du fichier avec `H=-Σ pᵢ log₂ pᵢ`.
- **Compression :** zlib niveau de compression maximal par défaut; la taille compressée peut dépasser l'entrée.
- **En-tête TLM1 :** `TLM1 | compression | taille originale | taille transmise | longueur du nom | nom UTF-8`.
- **Tramage 8N1 :** start 0, huit bits LSB-first, stop 1.
- **Tramage 8E2 :** huit bits LSB-first, parité paire, deux stops.
- **TLM-HDLC :** fanions `0x7E`, adresse, contrôle, longueur, données, CRC big-endian.
- **CRC :** MSB-first, polynôme `0x1021`, initialisation `0xFFFF`, masque 16 bits, sans reflet ni XOR final.
- **Bit stuffing :** insertion d'un 0 après cinq 1 dans le corps; fanions exclus.
- **Reconstruction :** séparation des trames, contrôle du nombre de trames, décompression et écriture du fichier reçu.
- **SHA-256 :** calcul sur les fichiers original et reçu.

Voir [source.py](../source.py), [crc.py](../crc.py), [trame.py](../trame.py) et [protocole.md](./protocole.md).

### 5.2 Résultats numériques vérifiés

| Fichier | Taille originale | Entropie | Taille compressée | Gain |
|---|---:|---:|---:|---:|
| `texte.txt` | 2800 octets | 4,1214 bits/octet | 138 octets | 95,07 % |
| `image.png` | 12420 octets | 7,9792 bits/octet | 12431 octets | -0,09 % |
| `aleatoire.bin` | 4096 octets | 7,9533 bits/octet | 4107 octets | -0,27 % |

Les valeurs proviennent de [compression.csv](../mesures/compression.csv) et sont également reprises dans [resultats.txt](../mesures/resultats.txt).

| Format | Bits utiles | Bits émis | Rendement |
|---|---:|---:|---:|
| 8N1 | 384 | 480 | 80,00 % |
| 8E2 | 384 | 576 | 66,67 % |
| TLM-HDLC sans stuffing | 384 | 440 | 87,27 % |
| TLM-HDLC avec stuffing | 384 | 447 | 85,91 % |

Le rendement HDLC avec stuffing dépend du motif de bits. La mesure ci-dessus ne doit pas être traitée comme une constante universelle.

### 5.3 CRC et boucles locales

Le vecteur de référence `123456789` retourne bien `0x29B1`. Les empreintes vérifiées sont :

| Fichier | SHA-256 |
|---|---|
| `texte.txt` | `5c6401bb72d27766c772441494843071c2934fdda093043b4203e1c0f736def1` |

> Utiliser les empreintes complètes exactes enregistrées dans [resultats.txt](../mesures/resultats.txt) comme référence; elles sont vérifiables automatiquement par comparaison locale.

### 5.4 Expériences de corruption

| Probabilité p | Trames altérées | Rejetées | Référence CRC | Autre rejet |
|---|---:|---:|---:|---:|
| 10⁻⁴ | 43 | 43 | 38 | 5 |
| 10⁻³ | 370 | 370 | 283 | 87 |
| 10⁻² | 990 | 990 | 395 | 595 |

Aucune trame altérée n'a été acceptée. La prédiction employée est `Pe=1-(1-p)^n`, avec la longueur réelle incluant stuffing. Ces expériences sont numériques, pas physiques.

### 5.5 Difficultés et corrections

- Convention TLM1 locale documentée après l'audit: nom limité à 18 octets UTF-8.
- Octets 48/49, grands volumes et caractères accentués testés.
- CRC validé indépendamment.
- Le stuffing est effectué hors fanions.
- Les rapports historiques ont été recalculés avec les longueurs réellement transmises.

### 5.6 Validation académique

- **J1 :** référence CRC numérique réalisée; visa officiel non vérifiable.
- **J2 :** boucle locale numérique réalisée et SHA-256 identiques; visa officiel/manipulation matérielle non vérifiée.
- **Fiche A1 :** gabarit [annexe_A1.md](./annexe_A1.md) présent, énoncés externes absents.
- **Journal :** [journal_a_completer.md](./journal_a_completer.md) est un gabarit vierge.

## 6. Module 2 — Moduler et transmettre par le son

### 6.1 Fonctionnalités réalisées

- CPFSK à phase continue dans [modem_fsk.py](../modem_fsk.py).
- Démodulation par énergies I/Q sans FFT de décision.
- Détection de porteuse et synchronisation du premier start.
- Décodage 8N1 et contrôle du stop.
- Génération/réception WAV à 48 kHz.
- Compatibilité Bell 103 locale vérifiée avec Minimodem puis avec le récepteur local.
- Simulation AWGN et mesure du TEB brut.
- Émission/réception par périphériques Sounddevice.
- Prétraitement, diagnostic et rapports hors ligne.
- Diagnostic de troncature, stop invalide, écho et clics isolés.

### 6.2 TEB AWGN sur 10 000 bits

La séquence officielle n'était pas présente. La campagne utilise donc une séquence locale de 10 000 bits, graine 2026, conformément à [sequence_test_10000.txt](../mesures/module2/bruit/sequence_test_10000.txt).

| S/B demandé | S/B mesuré | Erreurs | Ambigus | TEB |
|---:|---:|---:|---:|---:|
| +6 dB | 6,000 dB | 0 | 0 | 0 |
| +3 dB | 2,999 dB | 0 | 0 | 0 |
| 0 dB | -0,001 dB | 0 | 0 | 0 |
| -3 dB | -3,001 dB | 0 | 0 | 0 |
| -6 dB | -5,998 dB | 1 | 17 | 0,0001 |
| -9 dB | -9,001 dB | 104 | 183 | 0,0104 |
| -12 dB | -11,995 dB | 640 | 604 | 0,064 |

Les graphiques réels sont [teb_en_fonction_sb.png](../mesures/module2/teb_en_fonction_sb.png), [comparaison_sb_theorique_mesure.png](../mesures/module2/comparaison_sb_theorique_mesure.png), [comparaison_signaux_bruites.png](../mesures/module2/comparaison_signaux_bruites.png), [spectres_signaux_bruites.png](../mesures/module2/spectres_signaux_bruites.png) et [erreurs_par_sb.png](../mesures/module2/erreurs_par_sb.png).

Cette campagne exclut porteuse, 8N1, synchronisation physique et CRC; elle ne valide donc pas J3/J4/J5.

### 6.3 Boucles locales

G8 et Bell 103 ont tous deux reçu exactement `BONJOUR G8` dans les fichiers texte associés. Les CSV [resultats_boucle_audio.csv](../mesures/module2/resultats_boucle_audio.csv) enregistrent 100 bits reçus, 0 erreur et 0 ambigüité pour chaque profil.

Minimodem a aussi décodé le WAV local Bell 103 à 300 bauds. Cela confirme une interopérabilité locale, pas une compatibilité avec une référence officielle absente du dépôt.

### 6.4 Transmission acoustique historique

- Plusieurs échecs ont été associés à des microphones désactivés, des périphériques absents ou un routage incorrect.
- Le G8 officiel a présenté une faible énergie aux fréquences 7400/7600 Hz sur certains matériels.
- Le verrouillage du récepteur sur du bruit a provoqué des caractères faux et des erreurs de tramage.
- Une transmission Monitor locale a été réussie avant les essais air.
- Le profil expérimental `G8_acoustique` a été introduit; une réception ponctuelle de `BONJOUR G8` est documentée avec dix caractères corrects et zéro bit ambigu.
- La réception documentée avait une amplitude maximale de 0,181; elle ne doit pas être présentée comme une stabilité permanente.
- Les essais suivants ont été instables.
- Le profil officiel G8 a été restauré comme profil de référence et les trois profils ont été séparés.

Les assertions ponctuelles doivent être confirmées par WAV, conditions expérimentales et validation enseignant avant toute conclusion durable.

### 6.5 Problèmes audio et corrections

| Problème | Résultat |
|---|---|
| PulseAudio inaccessible | Expliqué comme isolation/absence de serveur local; à confirmer par environnement |
| PipeWire / `wait()` bloqué | Résolu dans `audio_io.py` par arrêt explicite après durée bornée |
| Microphone désactivé | Détection explicite du périphérique, mais aucune preuve universelle |
| Mauvaise conversion d'indices | Corrigée par conversion des indices numériques |
| Écrêtage | Détection persistante ajoutée; gain est refusé si écrêtage |
| Clic isolé | Interpolation dans le prétraitement |
| Stop 8N1/UTF-8 | Contrôles, reprise et exceptions ajoutés |
| Porteuse fausse | Préambule f1 puis start f0 obligatoires |
| Écho/réverbération | Test simulé ajouté; canal physique non caractérisé |
| Fin tronquée/faux caractères | Silence final distingué de troncature réelle |

Voir [MODULE2_ERREURS_ET_SOLUTIONS.md](./MODULE2_ERREURS_ET_SOLUTIONS.md) et [MODULE2_CORRECTION_ROBUSTESSE.md](./MODULE2_CORRECTION_ROBUSTESSE.md).

### 6.6 Validation académique

- **J3 :** implémentation logicielle à démontrer physiquement; non validé officiellement.
- **J4 :** démodulation/synchronisation testées localement; matériel officiel non validé.
- **J5 :** aucune mesure complète à 0,25 m/0,5 m/1 m disponible.
- **Fiche A2 :** à préparer, aucune preuve officielle trouvée.
- **Audacity :** recommandations présentes, captures officielles absentes.
- **Journal :** gabarit non rempli et non visé.

## 7. Module 3 — Fiabiliser, accélérer et valider

### 7.1 Phase 1 — ARQ stop-and-wait

`arq.py` implémente le stop-and-wait semi-duplex :

- Trame I : adresse, contrôle, longueur, données, CRC et fanions.
- N(S) : 0 ou 1, alterné après ACK valide.
- N(R) : prochain numéro attendu dans les ACK/NAK.
- ACK : supervision, longueur zéro, N(R).
- NAK : supervision avec bit spécifique et N(R).
- Timeout : 3 secondes simulées.
- Tentatives : 5 maximum.
- Doublon : ré-ACK sans recopie de la charge utile.
- Échec permanent : `RuntimeError("ARQ abandonné après 5 tentatives")`.

Scénarios déterministes vérifiés : canal parfait, perte I, perte ACK, corruption I, corruption ACK, NAK, mauvais ACK et abandon permanent.

Résultats documentés et testés :

- 49 octets acceptés après perte d'une trame.
- 2 octets acceptés après perte d'un ACK; retransmission, doublon ignoré, aucune duplication.
- Un doublon est ignoré par le récepteur.
- Après cinq tentatives permanentes, la transmission est abandonnée.

Ces résultats sont strictement simulés dans `CanalSimule`.

### 7.2 Phase 2 — Intégration ARQ/FSK

[canal_fsk.py](../canal_fsk.py) relie le corps HDLC à CPFSK :

- synchronisation provisoire `10` répétée 16 fois;
- modulation FSK de l'I;
- modulation FSK de l'ACK/NAK;
- démodulation puis extraction du flux HDLC;
- CRC/CRC ARQ repris par la couche ARQ.

La séquence alternée est provisoire et ne remplace pas une spécification officielle. Les erreurs déterministes sont injectées avant ou après modulation selon le canal; les erreurs AWGN sont produites après modulation.

### 7.3 Campagnes AWGN ARQ

Les deux campagnes appariées portent sur 144 octets, 20 essais par niveau, 140 transferts avec ARQ et 140 sans retransmission, graine 2026, profil G8.

| S/B | Avec ARQ | Sans retransmission | Gain | Retransmissions |
|---:|---:|---:|---:|---:|
| +6 dB | 20/20 | 20/20 | 0 point | 0 |
| +3 dB | 20/20 | 20/20 | 0 point | 0 |
| 0 dB | 20/20 | 20/20 | 0 point | 0 |
| -3 dB | 20/20 | 20/20 | 0 point | 0 |
| -6 dB | 20/20 | 13/20 | +35 points | 9 |
| -9 dB | 0/20 | 0/20 | 0 point | 80 |
| -12 dB | 0/20 | 0/20 | 0 point | 80 |

À -6 dB l'ARQ augmente le nombre de transferts réussis. Aux niveaux -9/-12 dB, les perturbations dépassent la capacité de compensation et les 20 essais sont abandonnés après cinq tentatives. Résultats dans [synthese_awgn.csv](../mesures/module3/simulation/synthese_awgn.csv).

### 7.4 Limites à auditer

- [ ] Calcul détaillé du TEB brut incluant insertions/suppressions.
- [ ] Audit du nombre réel de bits comparables.
- [ ] Rapport S/B réellement mesuré hors simulation.
- [ ] Indépendance des réalisations de bruit.
- [ ] Durées simulées : ils ne modélisent pas modulation/basculement/réponse physique.
- [ ] Débit utile réel après en-têtes et retransmissions.
- [ ] Chronologie complète des échanges physiques.
- [ ] Graphique dédié au taux d'abandon.
- [ ] Validation d'une séquence de synchronisation conforme au support.

### 7.5 Phase 3 — Transmission complète de fichiers

| Élément | État |
|---|---|
| Lecture binaire | IMPLÉMENTÉ |
| Compression | IMPLÉMENTÉ |
| En-tête source | IMPLÉMENTÉ |
| Découpage | IMPLÉMENTÉ |
| TLM-HDLC/CRC | IMPLÉMENTÉ |
| ARQ | IMPLÉMENTÉ en simulation |
| FSK | IMPLÉMENTÉ |
| Reconstruction | IMPLÉMENTÉ localement |
| Décompression | IMPLÉMENTÉ |
| SHA-256 | IMPLÉMENTÉ localement |
| Chaîne ARQ/audio fichier complet | NON INTÉGRÉE bout en bout |

Prévoir les tests TXT, CSV, PNG, ZIP, BIN, fichier vide, 1 Kio et 2 Kio.

### 7.6 Phase 4 — Communication physique

Non terminée : canal semi-duplex entre ordinateurs, ACK/NAK sonores, basculement émission/réception, temporisations réelles, retransmissions physiques, échos, câble et air.

### 7.7 Phase 5 — Caractérisation du canal

À mesurer : bande -3 dB, bande -10 dB, bruit blanc sur cinq secondes, signal sur cinq secondes, S/B réel, TEB à 25 cm/50 cm/1 m, débit utile et capacité de Shannon. Aucun résultat vérifiable n'est actuellement disponible pour ces exigences.

### 7.8 Phase 6 — Accélération optionnelle

Bell 202 à 1200 bauds, 4-FSK et comparaisons de débit/bande/TEB restent optionnelles. Elles ne doivent pas retarder les exigences obligatoires.

### 7.9 Phase 7 — Validation finale

J6/J7 exigent une démonstration ARQ puis un transfert par l'air d'un fichier de 2 Ko maximum, avec échange entre groupes/interopérabilité et comparaison SHA-256. Aucun jalon n'est déclaré validé faute de preuve officielle.

## 8. Registre général des erreurs et solutions

| Identifiant | Module | Message/observation | Cause confirmée ou probable | Solution | Preuve | Statut | Risque |
|---|---|---|---|---|---|---|---|
| E1 | Audio | PulseAudio inaccessible | Serveur audio isolé | Exécuter dans la session audio | Documentation | Résolu localement | Moyen |
| E2 | Audio | Microphone désactivé/signal nul | Mauvaise source/périphérique | Sélection explicite | `audio_io.py` | Partiellement résolu | Élevé |
| E3 | Audio | Périphériques introuvables | Aucun PortAudio/PipeWire exploité | Liste et diagnostics | `lister_peripheriques` | Résolu logiciel | Moyen |
| E4 | Audio | `sounddevice.wait()` bloqué | Backend ne signale pas fin | Arrêt explicite après durée | `audio_io.py` | Résolu | Faible |
| E5 | Audio | Écrêtage | Gain excessif | Détection persistante et volume limité | Tests audio | Résolu | Moyen |
| E6 | Audio | Clic plein échelle | Pic de périphérique | Interpolation isolée | `modem_fsk.py` | Résolu | Moyen |
| E7 | FSK | Porteuse absente | Mauvais verrouillage ou matériel | Préambule f1/start f0 | `recevoir.py` | Partiellement résolu | Élevé |
| E8 | 8N1 | Stop/UTF-8 invalide | Bits erronés/trame tronquée | Contrôle strict/reprise | Tests robustesse | Résolu logiciel | Moyen |
| E9 | FSK | Faux caractère en fin | Silence/résidu mal interprété | Silence final retiré | Tests réception robuste | Résolu | Moyen |
| E10 | Canal | G8 faible en air | Hautes fréquences peu robustes | Profil expérimental séparé | Essai documenté | À vérifier | Élevé |
| E11 | Canal | Échos/réverbérations | Canal réel non modélisé | Prétraitement futur; essais | Tests écho | Partiellement résolu | Élevé |
| E12 | ARQ | Mauvais compte de doublon/octets | Mélange statistiques émetteur/récepteur | Séparer les compteurs | `test_arq.py` | Résolu | Faible |
| E13 | ARQ | ARQ >5 tentatives | Absence de limite | Limite constante 5 | `test_abandon` | Résolu | Faible |
| E14 | Git | GitHub 403 | Droits distants | Vérifier authentification | — | À confirmer | Moyen |
| E15 | Documentation | Valeurs contradictoires | Rapports anciens non vérifiés | Audit direct des fichiers | Rapport actuel | Résolu | Faible |

## 9. Évolution des tests unitaires

| Étape | Nombre confirmé | Ajout principal | Statut |
|---|---:|---|---|
| Audit initial | 33 | Module 1 | Confirmé dans l'audit historique |
| Finalisation G8 | 39 | CRC, 48/49 octets, UTF-8, configuration/WAV/import | Confirmé |
| Module 2 AWGN | 56 | Mesures 10 000 bits et graphes | Confirmé par le document |
| Suite actuelle | 87 | 8 fichiers test; ARQ/FSK/audio robuste/finalisation | Confirmé aujourd'hui |
| Étapes 46,50,61,62,73,83,86 | À confirmer | Fonctionnalités non identifiées par des preuves versionnées | Historique non vérifiable |

Commande exécutée : `python -m unittest discover -s tests -v`

- Total : 87
- Réussis : 87
- Échecs : 0
- Ignorés : 0
- Durée : 34,861 s
- Date : 27 novembre 2026

Tests restant à ajouter : transferts bout en bout TXT/CSV/PNG/ZIP/BIN/vide/1 Kio/2 Kio, ACK/NAK réellement audio, perte/duplication physique, temps réels, bande passante, S/B mesuré, TEB à distance et validation intergroupes.

## 10. Inventaire des fichiers

### Arborescence réelle utile

```text
modem.G8/
├── config.py
├── source.py
├── crc.py
├── trame.py
├── modem_fsk.py
├── canal_fsk.py
├── arq.py
├── emettre.py
├── emmettre.py
├── recevoir.py
├── audio_io.py
├── diagnostic_audio.py
├── demo_arq.py
├── demo_arq_fsk.py
├── mesures_module1.py
├── mesures_module2.py
├── mesures_physiques.py
├── mesures_arq.py
├── synthese_module3.py
├── graphiques.py
├── graphiques_module2.py
├── graphiques_module3.py
├── main.py
├── tests/
├── docs/
├── donnees/
├── reception/
└── mesures/
```

| Chemin | Module | Rôle | Fonctions/classes principales | Statut |
|---|---|---|---|---|
| [config.py](../config.py) | Tous | Paramètres G8/profils | `profil`, constantes | Confirmé |
| [source.py](../source.py) | 1 | Entropie, compression, TLM1 | lecture, entropie, statistiques | Confirmé |
| [crc.py](../crc.py) | 1/3 | CRC-16 | `crc16_ccitt_false` | Confirmé |
| [trame.py](../trame.py) | 1/3 | Trames, stuffing, reconstruction | `construire_trame`, `encoder_trames`, `reconstruire` | Confirmé |
| [modem_fsk.py](../modem_fsk.py) | 2/3 | CPFSK/démodulation | `moduler`, `demoduler`, synchronisation | Confirmé |
| [arq.py](../arq.py) | 3 | Stop-and-wait | `EmetteurARQ`, `RecepteurARQ`, `CanalSimule` | Confirmé simulé |
| [canal_fsk.py](../canal_fsk.py) | 3 | ARQ/FSK | `CanalFSK` | Confirmé simulé |
| [audio_io.py](../audio_io.py) | 2 | Sounddevice/WAV | `jouer`, `enregistrer`, `statistiques` | Confirmé tests |
| [recevoir.py](../recevoir.py) | 2 | CLI réception | lecture, synchronisation, décodage | Confirmé fichiers locaux |
| [emettre.py](../emettre.py) | 2 | CLI émission | profils, WAV, lecture | Confirmé fichiers locaux |
| [diagnostic_audio.py](../diagnostic_audio.py) | 2 | Diagnostic WAV | niveaux, spectre, porteuse | Confirmé sur WAV |

Les anciens documents sont conservés; les caches `__pycache__`, `.venv` et fichiers générés sans intérêt documentaire sont exclus de cet inventaire.

## 11. Inventaire des mesures et preuves expérimentales

| ID | Module | Profil | Canal | Résultat | Preuve | Interprétation | Limites/Statut |
|---|---|---|---|---|---|---|---|
| M1 | 1 | G8 | Boucle locale | Trois fichiers reconstruits à l'identique | [resultats.txt](../mesures/resultats.txt) | SHA-256 identiques | Simulation locale; valide techniquement |
| M2 | 1 | G8 | Canal d'inversion | 0 altération acceptée | [erreurs.csv](../mesures/erreurs.csv) | CRC et structure rejettent les corruptions | Simulation numérique |
| M3 | 2 | G8/Bell | Boucle WAV | `BONJOUR G8` exact | [resultats_boucle_audio.csv](../mesures/module2/resultats_boucle_audio.csv) | Décodage numérique exact | Pas d'air/câble |
| M4 | 2 | G8 | AWGN 10k bits | TEB 0 à 0,064 | [resultats_teb.txt](../mesures/module2/bruit/resultats_teb.txt) | TEB augmente avec bruit | Synchronisation connue, pas physique |
| M5 | 2 | G8_acoustique | Air ponctuel | `BONJOUR G8`, 10 caractères | Documentation historique | Réception ponctuelle réussie | Instabilité observée; non officialisé |
| M6 | 2 | G8 | WAV physique reçu | FSK officiel non détectable | [MODULE2_CORRECTION_ROBUSTESSE.md](./MODULE2_CORRECTION_ROBUSTESSE.md) | Pas de porteuse fiable | Expérience physique à poursuivre |
| M7 | 3 | G8 | AWGN apparié | ARQ 20/20 jusqu'à -6 dB | [synthese_awgn.csv](../mesures/module3/simulation/synthese_awgn.csv) | ARQ améliore -6 dB | Abandon -9/-12 dB; simulé |

## 12. Tableau général de synthèse des performances

| Canal | Profil | Bauds | S/B mesuré | TEB | Débit utile | Shannon | Statut | Preuve |
|---|---|---:|---|---|---|---|---|---|
| AWGN | G8 | 300 | -12 à +6 dB | 0 à 0,064 | Non mesuré | Non calculable | Simulation | CSV/TXT/WAV |
| WAV Monitor | G8/Bell | 300 | Non mesuré | 0 localement | Non mesuré | Non calculable | Boucle locale | CSV |
| Câble jack | Tous | — | Non mesuré | Non mesuré | Non mesuré | Non calculable | À vérifier | Aucun WAV résultat |
| Air 0,25 m | G8/G8_acoustique | — | Non mesuré | Non mesuré | Non mesuré | Non calculable | À vérifier | Aucun essai complet |
| Air 0,5 m | G8/G8_acoustique | — | Non mesuré | Ponctuel non stable | Non mesuré | Non calculable | À vérifier | WAV historiques |
| Air 1 m | Tous | — | Non mesuré | Non mesuré | Non mesuré | Non calculable | Non mesuré | Aucun |

Formules :

- TEB = (bits erronés + pertes + insertions) / nombre de bits transmis.
- S/B = `10 log10(Ps/Pb)`.
- Débit utile = octets d'information correctement acceptés / durée réelle.
- Rendement = bits utiles / bits transmis.
- Capacité de Shannon : `C=B log2(1+S/N)` en bit/s.

## 13. Suivi des exigences du professeur

| Exigence | Module | Implémentation | Preuve | Statut technique | Validation officielle | Travail restant |
|---|---|---|---|---|---|---|
| J1 CRC | 1 | Calcul manuel | `0x29B1` | TERMINÉ | En attente | Visa enseignant |
| J2 boucle locale | 1 | Reconstruction/SHA | Trois fichiers | TERMINÉ | En attente | Matériel/visa |
| J3 émission FSK | 2 | Émetteur, WAV | WAV G8 | TERMINÉ logiciel | En attente | Démonstration officielle |
| J4 réception FSK | 2 | Démodulation | Boucles locales | TERMINÉ logiciel | En attente | Essai externe officiel |
| J5 canal physique | 2 | Outils audio | WAV historiques | PARTIELLEMENT | En attente | Câble/air/S/B/distance |
| J6 ARQ | 3 | Simulateur | Tests AWGN | TERMINÉ simulé | En attente | Démonstration réelle |
| J7 transfert fichier | 3 | Composants séparés | Boucle locale module 1 | BLOQUÉ | En attente | Chaîne complète + intergroupe |
| Fiche A1 | 1 | Gabarit | `annexe_A1.md` | À compléter | En attente | Réponses/visa |
| Fiche A2 | 2 | Gabarit absent | — | NON COMMENCÉ | En attente | Fiche/captures |
| Fiche A3 | 3 | Gabarit absent | — | NON COMMENCÉ | En attente | ARQ/canal |
| Journal | Tous | Gabarit | `journal_a_completer.md` | À compléter | En attente | Mesures/signatures |
| IA | Tous | Déclaration | `declaration_IA.md` | À vérifier | En attente | Compléter/viser |

## 14. Tableau de bord d'avancement

| Domaine/phase | Avancement technique | Expérimental | Documentaire | Académique |
|---|---|---|---|---|
| Module 1 | TERMINÉ | TERMINÉ en boucle locale | TERMINÉ | J1/J2 à valider |
| Module 2 phases 1-3 | TERMINÉ | Simulation/boucles terminées | TERMINÉ | J3/J4 à valider |
| Module 2 phase 4 | PARTIELLEMENT TERMINÉ | EN COURS | PARTIELLEMENT | J5 en attente |
| Module 3 phases 1-2 | TERMINÉ simulé | Simulation disponible | TERMINÉ | J6 non validé |
| Module 3 phases 3-7 | EN COURS/PARTIEL | NON COMMENCÉ | PARTIELLEMENT | J6/J7 en attente |
| Rapport | TERMINÉ initialement | À actualiser | TERMINÉ | À viser |

Aucun pourcentage global n'est attribué, car aucune liste de jalons pondérés vérifiés n'a été fournie par l'enseignant.

## 15. Liste détaillée du travail restant

### P0 — Obligatoire et bloquant

- [ ] Finaliser l'intégration lecture/compression/découpage/CRC/ARQ/FSK/reconstruction/décompression/SHA.
  - **Prérequis :** composants actuels stabilisés.
  - **Fichiers :** `main.py`, `arq.py`, `canal_fsk.py`, `source.py`, `trame.py`, `modem_fsk.py`, `recevoir.py`.
  - **Critère :** fichier égal à l'original pour TXT, CSV, PNG, ZIP, BIN, vide, 1 Kio et 2 Kio.
- [ ] Valider le canal ARQ audio semi-duplex entre deux ordinateurs.
  - **Critère :** ACK/NAK reçus, retransmissions limitées, aucun doublon accepté.
- [ ] Obtenir un transfert fiable par câble.
  - **Critère :** deux machines, SHA-256 égal, répétitions documentées.
- [ ] Obtenir un transfert fiable par air.
  - **Critère :** fichier reçu égal, environnement enregistré, J6/J7 visés.

### P1 — Mesures et conformité

- [ ] Auditer le TEB brut avec pertes/insertions et séquence officielle.
- [ ] Mesurer les bandes -3 dB et -10 dB.
- [ ] Enregistrer cinq secondes de bruit et cinq secondes de signal.
- [ ] Mesurer S/B réel et TEB à 25 cm, 50 cm et 1 m.
- [ ] Calculer débit utile et capacité de Shannon.
- [ ] Compléter fiches A1/A2/A3 et journaux visés.
- [ ] Compléter la déclaration d'usage de l'IA.

### P2 — Documentation et présentation

- [ ] Produire le rapport final académique et préserver cet historique.
- [ ] Ajouter les captures Audacity manquantes.
- [ ] Mettre à jour README avec les commandes confirmées.
- [ ] Préparer une présentation de 8 à 10 diapositives.
- [ ] Préparer démonstration et questions de défense.

### P3 — Optionnel

- [ ] Bell 202 à 1200 bauds sur câble.
- [ ] Modulation 4-FSK.
- [ ] Comparer débits, bandes et TEB.
- [ ] Améliorer synchronisation et robustesse audio.

## 16. Commandes générales du projet

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python crc.py
python trame.py donnees/texte.txt
python main.py environnement
python main.py crc
python main.py boucle donnees/texte.txt
python main.py mesures
python emettre.py "BONJOUR G8" --profil G8 --sortie mesures/module2/fsk_message_G8.wav
python recevoir.py mesures/module2/fsk_message_G8.wav --profil G8
python mesures_module2.py --bits 10000 --seed 2026
python graphiques_module2.py
python demo_arq.py
python demo_arq_fsk.py
python diagnostic_audio.py mesures/module2/physique/air/test_local_recu.wav --profil G8
python recevoir.py --liste-peripheriques
python emettre.py --liste-peripheriques
```

Toutes les commandes dépendantes du matériel exigent PortAudio/Sounddevice et un périphérique disponible. Elles ne doivent pas être présentées comme des succès physiques automatiques.

## 17. Registre des décisions techniques

| Décision | Contexte | Justification | Avantages | Limites/alternative |
|---|---|---|---|---|
| Python | Développement rapide académique | Lisibilité, tests, SciPy | Portable | Performance limitée pour temps réel |
| zlib | Compression standard | Réversible et disponible | Gain pour texte | Peut augmenter PNG/BIN |
| CRC-16/CCITT-FALSE | Protection locale | Conformité G8 | Détection simple | Ne corrige pas les erreurs |
| TLM-HDLC | Cadre de trames | Adresse/contrôle/longueur/stuffing | Structuration robuste | Convention et stuffing locaux |
| CPFSK | Canal acoustique | Phase continue | Compatibilité FSK | Faibles fréquences sensibles au matériel |
| Énergie I/Q | Démodulation | Indépendante de phase | Simple/robuste | Synchronisation encore critique |
| Trois profils | Conformité et expérimentation | Séparer officiel/acoustique/compatibilité | Évite les confusions | Interopérabilité à valider |
| Stop-and-wait | Fiabilité | Simple à démontrer | Doublons gérables | Temps de transfert important |
| Cinq tentatives | Limite ARQ | Évite boucle infinie | Abandon clair | Peut abandonner le fichier |
| SHA-256 | Validation finale | Empreinte standard | Comparaison fiable | Ne fournit pas correction |
| WAV bruts conservés | Audit | Preuve reproductible | Permet diagnostic | Gros fichiers/coordination |
| Gestion PipeWire explicite | Audio Linux | Évite blocage | Acquisition bornée | Dépend du backend/routage |

## 18. Risques et limitations

| Risque | Impact | Action correctrice | Vérification |
|---|---|---|---|
| Instabilité acoustique | Perte de caractère/trame | Répétitions, profil adapté, synchronisation robuste | Taux de succès sur plusieurs essais |
| Blocage audio | Processus suspendu | Durée bornée/arrêt explicite | Finir les commandes sous timeout |
| Atténuation hautes fréquences | G8 faible | Profil acoustique expérimentale | Mesure spectrale/S/B |
| Échos/réverbération | Décision erronée | Prétraitement, plus d'espace | Test réel à plusieurs distances |
| Synchronisation | Faux verrouillage/troncature | Préambule robuste/localisation fine | 100 caractères sans pertes |
| Temps de transfert | Démonstration trop lente | 300/1200 bauds, compression | Durée réelle mesurée |
| Cinq tentatives | Abandon | Canal plus robuste/timeout adapté | Scénarios permanents |
| Mesures incomplètes | Conformité incertaine | Exécuter campagne physique | CSV/WAV/conditions |
| Droits GitHub | Sauvegarde/partage | Vérifier authentification | Clone/push autorisé |
| Validation officielle | Mise en conformité incertaine | Réunion/visa enseignant | Signature/annotation réelle |

## 19. Règles d'actualisation et journal

À chaque phase : ajouter date, travail, fichiers, tests, mesures, erreurs, solutions, tâches terminées, tâches restantes et prochaine étape. Ne jamais effacer les anciennes preuves ou modifier les anciens CSV.

### Journal des mises à jour

| Date | Travail réalisé | Fichiers créés/modifiés | Résultats | Erreurs/solutions | Statut suivant |
|---|---|---|---|---|---|
| 27/11/2026 | Audit intégral des fichiers, Git, tests, docs, CSV/WAV/PNG | Création de [RAPPORT_EVOLUTION_PROJET.md](./RAPPORT_EVOLUTION_PROJET.md); lien ajouté au README | 87 tests réussis | Confusion entre simulations et essais physiques corrigée | Finaliser intégration fichiers/audio physique |

## 20. Reprendre le projet à partir de l'état actuel

- **Projet :** transmettre un fichier 2 Ko maximum par voie acoustique entre deux ordinateurs et vérifier SHA-256.
- **Paramètres :** G8 adresse `0x18`, 48 octets, f0/f1 `7400/7600 Hz`, 300 bauds, 48 kHz, CRC `0x1021/0xFFFF`, timeout 3 s, cinq tentatives.
- **Architecture :** source → compression → découpage → HDLC/CRC → ARQ → CPFSK → canal → démodulation → reconstruction → décompression → SHA-256.
- **Terminé :** module 1; émission/démodulation; 87 tests; AWGN; ARQ déterministe/FSK simulé.
- **Derniers résultats :** 87/87 tests; TEB 10k bits de 0 à 0,064; ARQ gains à -6 dB; boucles G8/Bell exactes.
- **Problèmes :** stabilité air, S/B physique absent, carte canal incomplète, ACK/NAK physiques absents, transfert fichier bout en bout non intégré.
- **Phase actuelle :** intégration module 3 puis essais physiques/revalidations officielles.
- **Priorités :** P0 transfert bout en bout, canal semi-duplex, câble/air, J6/J7.
- **Fichiers clés :** `config.py`, `source.py`, `trame.py`, `arq.py`, `modem_fsk.py`, `canal_fsk.py`, `audio_io.py`, `recevoir.py`, `emettre.py` et ce rapport.
- **Première commande :** `python -m unittest discover -s tests -v`.
- **Prochaine action concrète :** construire un petit transfert de fichier simulé bout en bout, puis intégrer un canal audio en boucle avec récepteur et ACK.

## 21. Conclusion

Le noyau numérique et les composants FSK/ARQ sont avancés et disposent de tests nombreux. Les mesures locales montrent que CRC, compression, reconstruction et boucles numériques sont fiables. Les résultats acoustiques ponctuels ne doivent pas être confondus avec une stabilité permanente. Le travail bloquant est désormais l'intégration bout en bout entre les deux ordinateurs, les mesures physiques réelles et la validation officielle J6/J7.
