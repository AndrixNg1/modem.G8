# Résultats de l'exécution locale — Module 1, G8

Les résultats suivants sont issus de l'exécution effective du programme en boucle locale sur les fichiers de démonstration inclus. Les valeurs de la séance doivent être recalculées avec les fichiers éventuellement imposés par l'enseignant. Les visas officiels restent à obtenir.

## 1. Codage source
| Fichier | Taille (o) | H (bits/o) | Compressé (o) | Qc | zeta | Gc (%) |
|---|---:|---:|---:|---:|---:|---:|
| texte.txt | 2800 | 4,1214 | 138 | 20,2899 | 0,0493 | 95,07 |
| image.png | 12420 | 7,9792 | 12431 | 0,9991 | 1,0009 | -0,09 |
| aleatoire.bin | 4096 | 7,9533 | 4107 | 0,9973 | 1,0027 | -0,27 |

Le texte de démonstration répète un paragraphe, ce qui explique son gain élevé ; il n'est pas représentatif de tous les textes. Les octets du PNG et du fichier pseudo-aléatoire ont une entropie proche de 8. La surcharge zlib augmente légèrement leur taille. L'entropie est une mesure de distribution des octets, pas une prédiction exacte de la performance de zlib, qui exploite aussi les répétitions.

## 2. Rendements
| Format | Théorie (%) | Mesure (%) | Bits utiles/émis |
|---|---:|---:|---:|
| 8N1 | 80 | 80 | 384/480 |
| 8E2 | 66,67 | 66,67 | 384/576 |
| TLM-HDLC sans stuffing | 87,27 | 87,27 | 384/440 |
| TLM-HDLC avec stuffing | variable | 85,91 | 384/447 |

Pour la dernière ligne, le résultat dépend des bits. Le bloc de 48 octets utilisé a nécessité sept zéros insérés. Le rendement est calculé sur une trame pleine, hors en-tête de fichier.

## 3. Détection d'erreurs
| p | Essais | Altérées | Rejetées | CRC | Autres rejets | Altérées acceptées | Altérations théoriques / 1000 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10^-4 | 1000 | 43 | 43 | 38 | 5 | 0 | 43,66 |
| 10^-3 | 1000 | 370 | 370 | 283 | 87 | 0 | 360,21 |
| 10^-2 | 1000 | 990 | 990 | 395 | 595 | 0 | 988,75 |

Les résultats sont proches des valeurs théoriques 1-(1-p)^n, où n inclut ici le stuffing. Les écarts reflètent notamment le hasard d'échantillonnage. Aucune altération acceptée n'a été observée sur ces 3000 essais, sans que cela garantisse une détection parfaite pour toute erreur possible.

## 4. Validation technique préalable
Exécution le 25 novembre 2026 avec `/home/andrix-ng/anaconda3/envs/ia.labo2.0/bin/python`. J1 : CRC("123456789") = 0x29B1. J2 : SHA-256 identiques pour les trois fichiers ; le détail est dans mesures/resultats.txt et boucle_locale.csv. 33 tests automatiques réussis, dont les paramètres G8 et le découpage en blocs de 48 octets. J1/J2 officiels à faire valider en salle.

Les graphiques PNG et les CSV se trouvent dans mesures/. Pour refaire les graphiques après une nouvelle mesure : `python graphiques.py` (matplotlib installé).
