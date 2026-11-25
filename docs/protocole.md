# Conventions du module 1

Base : Module1_Preparer_les_donnees.pdf, pages 5, 8–12 ; Annexes_TD_Modem_Acoustique.pdf, annexe E. Ce document précise les décisions locales non imposées par ces PDF.

## Trame TLM-HDLC

| Champ | Taille | Valeur |
|---|---:|---|
| Fanion | 1 octet | 0x7E |
| Adresse | 1 octet | 0x18 (G8) |
| Contrôle | 1 octet | bit 7 : 0 pour I, 1 pour supervision (convention) ; bit 6 : dernière ; bit 0 : séquence alternée, autres à 0 |
| Longueur | 1 octet | 0 à 48 |
| Données | 0 à 48 octets | En-tête ou bloc du fichier |
| CRC | 2 octets | CRC-16/CCITT-FALSE, calcul sur adresse, contrôle, longueur et données |
| Fanion | 1 octet | 0x7E |

Le CRC est écrit en big endian (octet de poids fort en premier, décision locale), puis chaque octet est sérialisé LSB first, y compris les octets du CRC. Les fanions ne sont pas soumis au stuffing. Le corps et le CRC sont soumis ensemble au stuffing. Après cinq 1 consécutifs, insérer 0 ; au décodage, retirer ce 0. Chaque trame conserve ses deux fanions (pas de mutualisation à l'émission). `construire_trame` renvoie les octets bruts ; `trame_vers_bits` applique le stuffing et produit les bits réellement émis. `extraire_trames` renvoie seulement les trames valides ; `analyser_flux` fournit aussi les motifs de rejet.

## En-tête TLM1 (convention locale)

| Champ | Taille |
|---|---:|
| Magic ASCII TLM1 | 4 octets |
| Indicateur de compression (0 brut / 1 zlib) | 1 octet |
| Taille originale (uint32, big endian) | 4 octets |
| Taille transmise (uint32, big endian) | 4 octets |
| Longueur du nom UTF-8 | 1 octet |
| Nom UTF-8 | 1 à 18 octets |

Total : 14 + longueur du nom, soit au plus 32 octets, qui tiennent dans les 48 octets disponibles pour G8. Le PDF indique 18 caractères, sans définir l'encodage : la convention existante de 18 octets UTF-8 est conservée (18 caractères ASCII ou moins si accents). Renommer une copie si besoin. Les deux tailles sont exprimées en octets. La première trame est toujours l'en-tête. La séquence commence à zéro sur l'en-tête, puis alterne ; le dernier bloc a le bit 6 à 1. Pour un fichier vide sans compression, la trame d'en-tête est aussi la dernière. On utilise zlib uniquement si le résultat est plus court ; la mesure de compression compare néanmoins toujours le résultat zlib à l'original.

## Mesures
Les rendements sont mesurés sur un bloc plein de 48 octets, hors en-tête de fichier. Les mesures d'erreur utilisent 1 000 trames pleines isolées pour chaque p, avec bits indépendamment inversés, fanions et stuffing inclus. Graine pseudo-aléatoire 2026. La probabilité théorique est la moyenne de 1-(1-p)^n, où n est la longueur réelle de chaque trame avec stuffing. Cette probabilité décrit une altération, pas nécessairement un rejet CRC. Une perte de fanion ou une structure invalide est comptée séparément du rejet CRC. Les trames altérées acceptées sont comptées distinctement. Aucune transmission physique n'est simulée ou revendiquée.

## Limites
Le module 1 travaille en mémoire sur des fichiers de taille raisonnable. Le flux représente une boucle locale complète, sans son. Les chemins absolus de réception sont générés sur chaque machine. Un fichier reçu de même nom est remplacé dans le dossier de réception. Les conventions devront être alignées sur le squelette de l'enseignant si celui-ci est fourni.
