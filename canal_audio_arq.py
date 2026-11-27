"""Transport ARQ semi-duplex par audio, distinct du canal FSK simulé.

Chaque trame HDLC est modulée sur haut-parleur, puis le pair répond par une
trame de supervision dans sa propre fenêtre d'émission. Aucun réseau ni fichier
partagé ne participe à l'échange.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import time
import numpy as np
from arq import RecepteurARQ
from audio_io import enregistrer, jouer
from emettre import profils
from modem_fsk import demoduler, moduler, pretraiter_signal, synchroniser_porteuse
from trame import analyser_flux, trame_vers_bits
from canal_fsk import SYNC

ETATS = ("IDLE", "TRANSMISSION_I", "ATTENTE_ACK", "RECEPTION_I", "VALIDATION_CRC",
         "EMISSION_ACK", "EMISSION_NAK", "RETRANSMISSION", "TERMINE", "ABANDON")

@dataclass
class JournalAudio:
    etat: str = "IDLE"
    evenements: list = field(default_factory=list)
    bits_ambigus: int = 0
    saturation: bool = False
    temps_audio: float = 0.0
    def changer(self, etat, detail=""):
        if etat not in ETATS: raise ValueError("État audio ARQ inconnu")
        self.etat=etat; self.evenements.append((time.monotonic(), etat, detail))


def signal_trame(brute, profil="G8"):
    """Annonce f1 + synchronisation connue + flux HDLC brut + garde f1."""
    p=profils(profil)
    bits=[1]*round(p['annonce_secondes']*p['R']) + SYNC + trame_vers_bits(brute)
    bits += [1]*max(1,round(p['garde_fin_secondes']*p['R']))
    return moduler(bits,p['f0'],p['f1'],p['R'],p['fe'])


def decoder_capture(signal, profil="G8", protection="basic"):
    """Extrait une unique trame HDLC; retourne ``None`` sans candidat valide."""
    p=profils(profil); x=np.asarray(signal,dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all(): raise ValueError("Capture mono finie requise")
    if not np.any(np.abs(x)>1e-12): return None, {"ambigus":0,"raison":"silence"}
    y=pretraiter_signal(x,p['f0'],p['f1'],p['fe'],protection=protection,nom_profil=p['nom'])
    try:
        # Le premier 0 de SYNC est précédé du premier 1 de SYNC : remonter
        # d'une période pour démoduler la séquence complète sans alignement connu.
        start=synchroniser_porteuse(y,p['f0'],p['f1'],p['R'],p['fe'],
                                    min_porteuse_bits=max(1,round(.75*p['annonce_secondes']*p['R'])))
    except ValueError as exc: return None, {"ambigus":0,"raison":str(exc)}
    periode=p['fe']//p['R']; debut=max(0,start-periode)
    bits,ambigus,_,_=demoduler(y[debut:],p['f0'],p['f1'],p['R'],p['fe'],True)
    indices=[i for i in range(len(bits)-len(SYNC)+1) if bits[i:i+len(SYNC)]==SYNC]
    for i in indices:
        trames, erreurs=analyser_flux(bits[i+len(SYNC):])
        # La garde f1 après le fanion final produit des résidus hors trame;
        # elle protège l'arrêt audio et ne doit pas invalider un CRC déjà vérifié.
        erreurs_bloquantes=[e for e in erreurs if e != "Bits résiduels après le dernier fanion"]
        if len(trames)==1 and not erreurs_bloquantes:
            from trame import construire_trame
            t=trames[0]
            return construire_trame(t['adr'],t['ctrl'],t['donnees']), {"ambigus":sum(ambigus),"raison":"ok"}
    return None, {"ambigus":sum(ambigus),"raison":"sync/HDLC/CRC invalide"}


class CanalAudioARQ:
    """Côté émetteur : joue I puis écoute exclusivement la réponse ACK/NAK."""
    def __init__(self, profil="G8", protection="basic", entree_audio=None, sortie_audio=None,
                 ecoute_ack=3.0, bascule_s=.05, sauvegarde_wav=None):
        if protection not in {"off","basic","advanced"}: raise ValueError("Protection invalide")
        if ecoute_ack <= 0 or bascule_s < 0: raise ValueError("Délais audio invalides")
        self.profil=profil; self.protection=protection; self.entree_audio=entree_audio; self.sortie_audio=sortie_audio
        self.ecoute_ack=ecoute_ack; self.bascule_s=bascule_s; self.sauvegarde_wav=sauvegarde_wav
        self.temps=0.; self.ack_perdus=0; self.journal=JournalAudio(); self._contexte=None
    def definir_tentative(self, bloc, tentative): self._contexte=(bloc,tentative)
    def attendre(self, secondes): self.temps += secondes
    def echanger(self, trame, recepteur_inutilise=None):
        self.journal.changer("TRANSMISSION_I", f"trame={self._contexte}")
        emission=signal_trame(trame,self.profil); jouer(emission,profils(self.profil)['fe'],self.sortie_audio)
        self.temps += len(emission)/profils(self.profil)['fe']; time.sleep(self.bascule_s); self.temps += self.bascule_s
        self.journal.changer("ATTENTE_ACK")
        try:
            capture, stats=enregistrer(self.ecoute_ack,profils(self.profil)['fe'],self.entree_audio,self.sauvegarde_wav)
        except (RuntimeError, ValueError) as exc:
            self.journal.changer("IDLE", f"acquisition ACK invalide: {exc}")
            self.ack_perdus += 1
            return None
        self.temps += self.ecoute_ack; self.journal.saturation |= stats['ecretage']
        ack, info=decoder_capture(capture,self.profil,self.protection); self.journal.bits_ambigus += info['ambigus']
        if ack is None: self.ack_perdus += 1; return None
        return ack


class ServeurAudioARQ:
    """Côté récepteur : écoute une capture, valide, puis émet ACK ou NAK."""
    def __init__(self, profil="G8", protection="basic", entree_audio=None, sortie_audio=None, bascule_s=.05):
        self.profil=profil; self.protection=protection; self.entree_audio=entree_audio; self.sortie_audio=sortie_audio
        self.bascule_s=bascule_s; self.recepteur=RecepteurARQ(); self.journal=JournalAudio(); self.termine=False; self.acquisitions_invalides=0
    def traiter_capture(self, capture):
        self.journal.changer("RECEPTION_I")
        brute,info=decoder_capture(capture,self.profil,self.protection); self.journal.bits_ambigus += info['ambigus']
        if brute is None:
            # Un candidat synchronisé mais HDLC/CRC invalide mérite un NAK;
            # silence et absence de porteuse restent simplement IDLE.
            if info['raison'] == "sync/HDLC/CRC invalide":
                reponse=self.recepteur.recevoir(b"")
                self.journal.changer("EMISSION_NAK",info['raison'])
                time.sleep(self.bascule_s); jouer(signal_trame(reponse,self.profil),profils(self.profil)['fe'],self.sortie_audio)
                return reponse
            self.journal.changer("IDLE",info['raison']); return None
        self.journal.changer("VALIDATION_CRC")
        reponse=self.recepteur.recevoir(brute)
        self.journal.changer("EMISSION_ACK" if not (reponse[2]&0x20) else "EMISSION_NAK")
        time.sleep(self.bascule_s); jouer(signal_trame(reponse,self.profil),profils(self.profil)['fe'],self.sortie_audio)
        from arq import _analyse
        try: self.termine=bool(_analyse(brute)['ctrl'] & 0x40)
        except ValueError: pass
        return reponse
    def ecouter_une_fois(self, duree, chemin=None):
        try:
            capture,stats=enregistrer(duree,profils(self.profil)['fe'],self.entree_audio,chemin)
        except (RuntimeError, ValueError) as exc:
            self.acquisitions_invalides += 1
            self.journal.changer("IDLE", f"acquisition invalide: {exc}")
            return None
        self.journal.saturation |= stats['ecretage']; return self.traiter_capture(capture)
