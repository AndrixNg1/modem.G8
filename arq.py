"""ARQ stop-and-wait simulé, bâti sur les trames TLM-HDLC existantes."""
from dataclasses import dataclass
from config import ADRESSE, N
from trame import construire_trame, analyser_corps, CTRL_SEQUENCE, CTRL_DERNIERE, CTRL_SUPERVISION

ARQ_TIMEOUT = 3.0
ARQ_MAX_ATTEMPTS = 5
CTRL_NAK = 0x20

def _corrompre(trame):
    x = bytearray(trame); x[-3] ^= 1; return bytes(x)

def _analyse(trame):
    if not isinstance(trame, (bytes, bytearray)) or len(trame) < 7 or trame[0] != 0x7E or trame[-1] != 0x7E:
        raise ValueError("Trame ARQ invalide")
    return analyser_corps(bytes(trame[1:-1]))

def trame_supervision(nr, nak=False, adr=ADRESSE):
    return construire_trame(adr, CTRL_SUPERVISION | (CTRL_NAK if nak else 0) | (nr & 1), b"")

@dataclass
class StatistiquesARQ:
    trames_originales: int = 0; tentatives: int = 0; retransmissions: int = 0
    ack: int = 0; nak: int = 0; corrompues: int = 0; doublons_ignores: int = 0
    delais: int = 0; octets_acceptes: int = 0; duree_simulee: float = 0.0
    statut: str = "EN_COURS"
    ack_emis: int = 0; ack_perdus: int = 0; nak_emis: int = 0; trames_acceptees: int = 0

class RecepteurARQ:
    def __init__(self, adresse=ADRESSE): self.adresse=adresse; self.attendu=0; self.donnees=bytearray(); self.stats=StatistiquesARQ()
    def recevoir(self, brute):
        try: t=_analyse(brute)
        except ValueError:
            self.stats.corrompues += 1
            self.stats.nak_emis += 1
            return trame_supervision(self.attendu, True, self.adresse)
        if t["adr"] != self.adresse or t["ctrl"] & CTRL_SUPERVISION:
            self.stats.nak_emis += 1
            return trame_supervision(self.attendu, True, self.adresse)
        ns=t["ctrl"] & CTRL_SEQUENCE
        if ns == self.attendu:
            self.donnees.extend(t["donnees"]); self.stats.octets_acceptes += len(t["donnees"]); self.stats.trames_acceptees += 1; self.attendu ^= 1
        else: self.stats.doublons_ignores += 1
        self.stats.ack_emis += 1
        return trame_supervision(self.attendu, False, self.adresse)

class CanalSimule:
    """Actions déterministes : ok, perte_i, corruption_i, perte_ack, corruption_ack, mauvais_ack, nak."""
    def __init__(self, actions=(), horloge=None):
        self.actions=list(actions); self.horloge=horloge or [0.0]
        self.ack_perdus = 0
    def attendre(self, secondes): self.horloge[0] += secondes
    def echanger(self, trame, recepteur):
        action=self.actions.pop(0) if self.actions else "ok"
        if action == "perte_i": return None
        entree=_corrompre(trame) if action == "corruption_i" else trame
        reponse=recepteur.recevoir(entree)
        if action == "nak": return trame_supervision(recepteur.attendu, True)
        if action == "perte_ack":
            self.ack_perdus += 1
            return None
        if action == "corruption_ack": return _corrompre(reponse)
        if action == "mauvais_ack": return trame_supervision((recepteur.attendu ^ 1), False)
        return reponse

class EmetteurARQ:
    def __init__(self, canal, recepteur, adresse=ADRESSE, timeout=ARQ_TIMEOUT, max_attempts=ARQ_MAX_ATTEMPTS):
        if timeout <= 0 or not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("Timeout positif et au moins une tentative requis")
        self.canal,self.recepteur,self.adresse,self.timeout,self.max_attempts=canal,recepteur,adresse,timeout,max_attempts; self.sequence=0; self.stats=StatistiquesARQ()
    def _bilan(self):
        for nom in ("octets_acceptes", "doublons_ignores", "trames_acceptees", "ack_emis", "nak_emis"):
            setattr(self.stats, nom, getattr(self.recepteur.stats, nom))
        self.stats.ack_perdus = getattr(self.canal, 'ack_perdus', 0)
        self.stats.duree_simulee = self.canal.temps if hasattr(self.canal, "temps") else self.canal.horloge[0]
    def transferer(self, donnees):
        blocs=[bytes(donnees)[i:i+N] for i in range(0,len(donnees),N)] or [b""]
        self.stats.trames_originales=len(blocs)
        for index, bloc in enumerate(blocs):
            ctrl=self.sequence | (CTRL_DERNIERE if index == len(blocs)-1 else 0); brute=construire_trame(self.adresse,ctrl,bloc)
            for tentative in range(self.max_attempts):
                self.stats.tentatives += 1; self.stats.retransmissions += tentative > 0
                if hasattr(self.canal, "definir_tentative"):
                    self.canal.definir_tentative(index, tentative)
                reponse=self.canal.echanger(brute,self.recepteur)
                if reponse is None:
                    self.stats.delais += 1
                    self.canal.attendre(self.timeout)
                    continue
                try: ack=_analyse(reponse)
                except ValueError:
                    self.stats.corrompues += 1
                    self.stats.delais += 1
                    self.canal.attendre(self.timeout)
                    continue
                if ack["adr"] != self.adresse or not ack["ctrl"] & CTRL_SUPERVISION:
                    self.stats.delais += 1
                    self.canal.attendre(self.timeout)
                    continue
                if ack["ctrl"] & CTRL_NAK: self.stats.nak += 1; continue
                if (ack["ctrl"] & 1) != (self.sequence ^ 1):
                    self.stats.delais += 1
                    self.canal.attendre(self.timeout)
                    continue
                self.stats.ack += 1; self.sequence ^= 1; break
            else:
                self.stats.statut="ECHEC"
                self._bilan()
                raise RuntimeError(f"ARQ abandonné après {self.max_attempts} tentatives")
        # Bilan de transfert : les données acceptées et doublons sont des
        # événements du récepteur, publiés ici sans les compter deux fois.
        self._bilan()
        self.stats.statut="OK"
        return bytes(self.recepteur.donnees)
