"""Nom correct de la commande; `emmettre.py` reste le nom historique.

Une seule implémentation est maintenue dans le module historique afin que
`python emettre.py` et les anciennes commandes `python emmettre.py` restent
compatibles sans dupliquer le code.
"""
from emmettre import ANNONCE_SECONDES, encoder_message, profils, signal_message, signal_bits, ecrire_wav, main

__all__ = ("ANNONCE_SECONDES", "encoder_message", "profils", "signal_message", "signal_bits", "ecrire_wav", "main")

if __name__ == "__main__":
    main()
