"""Canal FSK local pour ARQ : HDLC binaire → CPFSK → démodulation → HDLC."""
import numpy as np
from emettre import profils
from modem_fsk import moduler, demoduler, ajouter_bruit, pretraiter_signal
from trame import trame_vers_bits, analyser_flux

SYNC = [1, 0] * 16  # convention provisoire documentée, hors données HDLC

class CanalFSK:
    def __init__(self, profil="G8", actions=(), sb_db=None, seed=2026, protection="off"):
        if protection not in {"off", "basic", "advanced"}:
            raise ValueError("protection attend off, basic ou advanced")
        self.p=profils(profil); self.actions=list(actions); self.sb_db=sb_db; self.seed=seed; self.protection=protection; self.temps=0.; self.evenements=[]
        self.bits_bruts_transmis = 0
        self.bits_bruts_errones = 0
        self.bits_bruts_perdus = 0
        self.bits_bruts_inseres = 0
        self.ack_perdus = 0
        self._contexte = None
    def definir_tentative(self, bloc, tentative):
        self._contexte = (bloc, tentative)
    def attendre(self, secondes):
        self.temps += secondes
    def _passer(self, brute, sens):
        action=self.actions.pop(0) if self.actions else "ok"
        self.dernier_evenement = action
        if action == "perte_" + sens:
            self.evenements.append(f"perte {sens}")
            if sens == 'ack': self.ack_perdus += 1
            return None
        # Altération déterministe après CRC, puis transport réel FSK.
        entree=brute
        if action == "corruption_" + sens:
            x=bytearray(brute); x[4 if len(x) > 7 else -3] ^= 1; entree=bytes(x)
            self.evenements.append(f"corruption {sens} transportée par FSK")
        bits=SYNC + trame_vers_bits(entree)
        signal=moduler(bits,self.p['f0'],self.p['f1'],self.p['R'],self.p['fe'])
        self.temps += len(signal)/self.p['fe']
        if self.sb_db is not None:
            if self._contexte is None:
                graine = self.seed
                self.seed += 1
            else:
                graine = int(np.random.SeedSequence([self.seed, *self._contexte, int(sens == 'ack')]).generate_state(1)[0])
            signal,_=ajouter_bruit(signal,self.sb_db,graine,True)
        if self.protection != "off":
            signal = pretraiter_signal(signal, self.p['f0'], self.p['f1'], self.p['fe'],
                                        protection=self.protection, nom_profil=self.p['nom'])
        recus=demoduler(signal,self.p['f0'],self.p['f1'],self.p['R'],self.p['fe'])
        # TEB avant CRC, sur toutes les transmissions effectivement modulées,
        # y compris les retransmissions et les acquittements. Alignement connu.
        self.bits_bruts_transmis += len(bits)
        self.bits_bruts_perdus += max(len(bits) - len(recus), 0)
        self.bits_bruts_inseres += max(len(recus) - len(bits), 0)
        self.bits_bruts_errones += sum(a != b for a, b in zip(bits, recus)) + abs(len(bits) - len(recus))
        trames, erreurs=analyser_flux(recus[len(SYNC):])
        if len(trames)!=1 or erreurs: return None
        # reconstruire la forme brute pour laisser ARQ refaire CRC/adresse.
        t=trames[0]; from trame import construire_trame
        return construire_trame(t['adr'],t['ctrl'],t['donnees'])
    def echanger(self, brute, recepteur):
        i=self._passer(brute,'i')
        if i is None: return None
        if self.dernier_evenement == "nak":
            from arq import trame_supervision
            self.evenements.append("NAK transporté par FSK")
            return self._passer(trame_supervision(recepteur.attendu, True),'ack')
        ack=recepteur.recevoir(i)
        return self._passer(ack,'ack')
