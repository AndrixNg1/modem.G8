"""CLI du transfert de fichier ARQ exclusivement sonore entre deux PC."""
from __future__ import annotations
import argparse, json, time
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from arq import EmetteurARQ, RecepteurARQ
from canal_audio_arq import CanalAudioARQ, ServeurAudioARQ
from config import PROFILS
from transfert_fichier import TAILLE_MAX, decoder_paquet, preparer_paquet

def envoyer(chemin, profil, protection, entree_audio, sortie_audio, timeout=3.):
    source=Path(chemin); original=source.read_bytes()
    paquet,_=preparer_paquet(source.name,original)
    # Convention transportée par le son : paquet TLM1 puis SHA-256 original.
    charge=paquet+sha256(original).digest()
    canal=CanalAudioARQ(profil,protection,entree_audio,sortie_audio,ecoute_ack=timeout)
    # Le pair est distant : cet objet ne sert qu'à l'API existante et à ses stats.
    emetteur=EmetteurARQ(canal,RecepteurARQ(),timeout=timeout)
    debut=time.monotonic()
    try: emetteur.transferer(charge)
    except RuntimeError:
        canal.journal.changer("ABANDON"); raise
    canal.journal.changer("TERMINE")
    return {"statut":"OK","fichier":source.name,"taille":len(original),"sha256":sha256(original).hexdigest(),
            "secondes":time.monotonic()-debut,"statistiques":asdict(emetteur.stats),
            "audio":{"bits_ambigus":canal.journal.bits_ambigus,"saturation":canal.journal.saturation,
                     "evenements":canal.journal.evenements}}

def recevoir(dossier, profil, protection, entree_audio, sortie_audio, fenetre=1., session=60., garde_fin=5.):
    serveur=ServeurAudioARQ(profil,protection,entree_audio,sortie_audio)
    fin=time.monotonic()+session; fin_final=None
    while time.monotonic() < (fin_final or fin):
        serveur.ecouter_une_fois(min(fenetre,max(.01,(fin_final or fin)-time.monotonic())))
        if serveur.acquisitions_invalides >= 3:
            raise RuntimeError("Trois acquisitions audio invalides consécutives : vérifier --entree-audio et PulseAudio")
        if serveur.termine and fin_final is None: fin_final=time.monotonic()+garde_fin
    if not serveur.termine: raise RuntimeError("Session terminée sans dernière trame valide")
    charge=bytes(serveur.recepteur.donnees)
    if len(charge)<32: raise ValueError("Fin de transfert reçue sans empreinte SHA-256")
    nom,contenu=decoder_paquet(charge[:-32]); attendu=charge[-32:]
    obtenu=sha256(contenu).digest()
    if obtenu != attendu: raise ValueError("SHA-256 reçu différent du fichier reconstruit")
    destination=Path(dossier)/nom
    if destination.exists(): raise FileExistsError(f"Fichier reçu existe déjà : {destination}")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as f: f.write(contenu)
    serveur.journal.changer("TERMINE")
    return {"statut":"OK","destination":str(destination),"taille":len(contenu),"sha256":obtenu.hex(),
            "statistiques":asdict(serveur.recepteur.stats),"audio":{"bits_ambigus":serveur.journal.bits_ambigus,
            "saturation":serveur.journal.saturation,"evenements":serveur.journal.evenements}}

def main():
    p=argparse.ArgumentParser(description="ARQ stop-and-wait exclusivement audio")
    sub=p.add_subparsers(dest='action',required=True)
    def commun(x):
        x.add_argument('--profil',choices=tuple(PROFILS),default='G8'); x.add_argument('--protection',choices=('off','basic','advanced'),default='basic')
        x.add_argument('--entree-audio'); x.add_argument('--sortie-audio')
    e=sub.add_parser('envoyer'); e.add_argument('fichier'); commun(e); e.add_argument('--timeout',type=float,default=3.)
    r=sub.add_parser('recevoir'); commun(r); r.add_argument('--dossier-reception',default='reception/audio'); r.add_argument('--fenetre',type=float,default=1.); r.add_argument('--session',type=float,default=60.); r.add_argument('--garde-fin',type=float,default=5.)
    a=p.parse_args()
    try:
        resultat=envoyer(a.fichier,a.profil,a.protection,a.entree_audio,a.sortie_audio,a.timeout) if a.action=='envoyer' else recevoir(a.dossier_reception,a.profil,a.protection,a.entree_audio,a.sortie_audio,a.fenetre,a.session,a.garde_fin)
    except (OSError,RuntimeError,ValueError,FileExistsError) as exc: p.error(str(exc))
    print(json.dumps(resultat,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__': main()
