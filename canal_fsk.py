"""Canal FSK local pour ARQ : HDLC binaire → CPFSK → démodulation → HDLC."""
import numpy as np
from scipy.io import wavfile
from emettre import profils
from modem_fsk import moduler, demoduler, ajouter_bruit
from trame import trame_vers_bits, analyser_flux

SYNC = [1, 0] * 16  # convention provisoire documentée, hors données HDLC

class CanalFSK:
    def __init__(self, profil="G8", actions=(), sb_db=None, seed=2026):
        self.p=profils(profil); self.actions=list(actions); self.sb_db=sb_db; self.seed=seed; self.temps=0.; self.evenements=[]
    def _passer(self, brute, sens):
        action=self.actions.pop(0) if self.actions else "ok"
        self.dernier_evenement = action
        if action == "perte_" + sens: self.temps += 3.; self.evenements.append(f"perte {sens}"); return None
        # Altération déterministe après CRC, puis transport réel FSK.
        entree=brute
        if action == "corruption_" + sens:
            x=bytearray(brute); x[4 if len(x) > 7 else -3] ^= 1; entree=bytes(x)
            self.evenements.append(f"corruption {sens} transportée par FSK")
        bits=SYNC + trame_vers_bits(entree)
        signal=moduler(bits,self.p['f0'],self.p['f1'],self.p['R'],self.p['fe'])
        self.temps += len(signal)/self.p['fe']
        if self.sb_db is not None: signal,_=ajouter_bruit(signal,self.sb_db,self.seed,True); self.seed += 1
        recus=demoduler(signal,self.p['f0'],self.p['f1'],self.p['R'],self.p['fe'])
        trames, erreurs=analyser_flux(recus[len(SYNC):])
        if len(trames)!=1 or erreurs: return None
        # reconstruire la forme brute pour laisser ARQ refaire CRC/adresse.
        t=trames[0]; from trame import construire_trame
        return construire_trame(t['adr'],t['ctrl'],t['donnees'])
    def echanger(self, brute, recepteur):
        i=self._passer(brute,'i')
        if i is None: self.temps += 3.; return None
        if self.dernier_evenement == "nak":
            from arq import trame_supervision
            self.evenements.append("NAK transporté par FSK")
            return self._passer(trame_supervision(recepteur.attendu, True),'ack')
        ack=recepteur.recevoir(i)
        return self._passer(ack,'ack')
