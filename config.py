"""Configuration centralisée des profils du modem G8."""
GROUPE = "G8"
ADRESSE = 0x18
N = 48
FE = 48000
AMPLITUDE = 0.5
CRC_POLYNOME = 0x1021
CRC_INIT = 0xFFFF

G8 = {"nom": "G8", "f0": 7400, "f1": 7600, "R": 300, "fe": FE,
      "format": "8N1", "annonce_secondes": .3, "garde_fin_secondes": .05}
G8_ACOUSTIQUE = {"nom": "G8_acoustique", "f0": 1800, "f1": 3600, "R": 100,
                 "fe": FE, "format": "8N1", "annonce_secondes": .8,
                 "garde_fin_secondes": .05}
BELL103 = {"nom": "bell103", "f0": 1070, "f1": 1270, "R": 300, "fe": FE,
           "format": "8N1", "annonce_secondes": .3, "garde_fin_secondes": .05}
PROFILS = {"G8": G8, "G8_acoustique": G8_ACOUSTIQUE, "bell103": BELL103}

def profil(nom="G8"):
    try:
        return PROFILS[nom].copy()
    except KeyError as exc:
        raise ValueError("Profil attendu : G8, G8_acoustique ou bell103") from exc

# Compatibilité historique : G8 officiel.
F0, F1, R = G8["f0"], G8["f1"], G8["R"]
BIT_DURATION = 1 / R
SAMPLES_PER_BIT = FE // R
BANDWIDTH_THEORIQUE = 2 * (F1 - F0) + 2 * R
