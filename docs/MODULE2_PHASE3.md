# Module 2 — Phase 3 : AWGN et taux d'erreur binaire

## Protocole

La séquence officielle de 10 000 bits n'était pas présente dans le dépôt inspecté. `mesures_module2.py` génère donc `sequence_test_10000.txt` localement, avec la graine 2026, et emploie exactement cette même séquence pour tous les S/B. Ce n'est pas la séquence de l'enseignant.

Pour chaque valeur 6, 3, 0, -3, -6, -9 et -12 dB, le signal CPFSK G8 est modulé puis perturbé par un AWGN : `Ps=mean(s²)`, `Pb=Ps/10^(S/B_dB/10)`, `sigma=sqrt(Pb)`. Le S/B réel est recalculé après tirage : `10 log10(Ps/Pb)`. Les WAV sont float32; aucune saturation ou normalisation individuelle n'est appliquée.

La démodulation est volontairement à synchronisation connue, sur les bits bruts : ni porteuse, ni 8N1, ni CRC, ni ARQ ne sont inclus. `TEB=(erreurs de décision + différence de longueur)/bits transmis`; ainsi pertes ou insertions ne sont jamais masquées par une troncature au minimum des longueurs.

## Exécution

```bash
python mesures_module2.py --bits 10000 --seed 2026
python graphiques_module2.py
python -m unittest discover -s tests -v
```

Les fichiers et le tableau réel sont dans `mesures/module2/bruit/`. Les points à TEB nul restent à zéro dans le CSV; ils sont dessinés à une limite explicitement indiquée dans le graphique logarithmique, sans remplacer la mesure.

## Résultats obtenus

Exécution réelle : 10 000 bits, graine 2026, aucun écart de longueur, synchronisation connue.

| S/B demandé (dB) | S/B mesuré (dB) | Erreurs | Ambigus | TEB |
|---:|---:|---:|---:|---:|
| 6 | 6,000 | 0 | 0 | 0 |
| 3 | 2,999 | 0 | 0 | 0 |
| 0 | -0,001 | 0 | 0 | 0 |
| -3 | -3,001 | 0 | 0 | 0 |
| -6 | -5,998 | 1 | 17 | 0,0001 |
| -9 | -9,001 | 104 | 183 | 0,0104 |
| -12 | -11,995 | 640 | 604 | 0,0640 |

Les TEB nuls sont des observations sur 10 000 bits, non une preuve d'un TEB théorique nul. Les graphiques `teb_en_fonction_sb.png`, `comparaison_signaux_bruites.png`, `spectres_signaux_bruites.png`, `erreurs_par_sb.png` et `comparaison_sb_theorique_mesure.png` sont produits depuis ces CSV/WAV. La validation a exécuté 56 tests, tous réussis.

## Interprétation et limites

Le TEB augmente généralement lorsque le S/B diminue parce que le bruit perturbe les deux corrélations I/Q. Un S/B négatif peut encore fonctionner : les corrélateurs sélectionnent seulement l'énergie projetée aux deux fréquences FSK, plutôt que tout le bruit audio. La bande occupée théorique (800 Hz) ne correspond pas exactement à la bande effective de ces détecteurs sur des fenêtres de 160 échantillons.

Cette simulation AWGN idéale ne représente ni haut-parleur/microphone, ni réverbération, interférences, dérive d'horloge, filtrage matériel ou acquisition de porteuse. Elle ne valide aucun jalon officiel J3/J4/J5.
