"""Configuration centralisée du module 1 — groupe G8."""
GROUPE = "G8"
ADRESSE = 0x18
N = 48
# Profil G8 acoustique : séparation large et symboles de 10 ms pour une
# transmission fiable par haut-parleur/microphone.
F0 = 1800
F1 = 3600
FE = 48000
R = 100
AMPLITUDE = 0.5
BIT_DURATION = 1 / R
SAMPLES_PER_BIT = FE // R
BANDWIDTH_THEORIQUE = 2 * (F1 - F0) + 2 * R
CRC_POLYNOME = 0x1021
CRC_INIT = 0xFFFF

# Réservé aux essais de compatibilité du module 2 : ne pas utiliser pour G8.
BELL103 = {"F0": 1070, "F1": 1270, "R": 300, "FORMAT": "8N1"}
