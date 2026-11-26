# Protocole — conventions du module 1

G8 utilise adresse `0x18`, charge utile maximale 48 octets, CRC-16/CCITT-FALSE (`0x1021`, init. `0xFFFF`) et octets LSB-first. La trame est `0x7E | adresse | contrôle | longueur | données | CRC(2, big-endian) | 0x7E`. Le CRC couvre adresse à données. Les bits du corps, CRC inclus, reçoivent un zéro après cinq `1`; les fanions sont exclus.

Le contrôle est : bit 7 supervision, bit 6 dernière trame, bit 0 séquence alternée; les autres bits sont nuls. 8N1 est start, 8 données LSB-first, stop; 8E2 ajoute parité paire et deux stops.

L'en-tête local TLM1 est `TLM1 | compression(1) | taille originale uint32 BE | taille transmise uint32 BE | longueur du nom(1) | nom UTF-8`. Cette convention locale limite le nom à 18 octets et tient dans une charge G8. Les paramètres imposés/centralisés sont dans `config.py`; Bell 103 (1070/1270 Hz) est réservé aux futurs tests de compatibilité et ne remplace jamais G8.
