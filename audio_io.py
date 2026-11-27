"""Entrées/sorties Sounddevice pour les essais physiques, sans DSP modem."""
from pathlib import Path
import time
import numpy as np
from scipy.io import wavfile
from config import FE

def _sd():
    try:
        import sounddevice
        return sounddevice
    except (ImportError, OSError) as exc:
        raise RuntimeError(f"Sounddevice/PortAudio indisponible : {exc}") from exc

def normaliser_peripherique(device):
    """Convertit un index CLI numérique en entier, sans altérer un nom."""
    if device is None: return None
    if isinstance(device, bool): raise ValueError("Identifiant de périphérique invalide")
    if isinstance(device, int):
        if device < 0: raise ValueError("Indice de périphérique négatif")
        return device
    if isinstance(device, str):
        valeur=device.strip()
        if not valeur: raise ValueError("Nom de périphérique vide")
        return int(valeur) if valeur.isdigit() else valeur
    raise ValueError("Périphérique : indice entier, nom ou None attendu")

def lister_peripheriques():
    """Retourne les périphériques PortAudio; aucun périphérique par défaut imposé."""
    return _sd().query_devices()

def formater_peripheriques():
    """Liste lisible : index, nom, canaux et fréquence par défaut."""
    lignes=[]
    for index,info in enumerate(lister_peripheriques()):
        lignes.append(f"{index:>3} | {info['name']} | entrée={info['max_input_channels']} | "
                      f"sortie={info['max_output_channels']} | Fe défaut={info['default_samplerate']:.0f} Hz")
    return "\n".join(lignes) or "Aucun périphérique PortAudio détecté."

def verifier_peripherique(device=None, entree=False, fe=FE):
    sd=_sd(); device=normaliser_peripherique(device); role="entrée" if entree else "sortie"
    if device is None:
        # Certains serveurs PipeWire exposent un défaut PortAudio à -1. Dans
        # ce cas, choisir explicitement leur source/sortie par défaut.
        cible = "default source" if entree else "default sink"
        for index, info in enumerate(sd.query_devices()):
            canaux = info.get("max_input_channels" if entree else "max_output_channels", 0)
            if canaux and info.get("name", "").strip().lower() == cible:
                device = index
                break
    if device is not None:
        try: info=sd.query_devices(device)
        except Exception as exc:
            choix=f"indice {device}" if isinstance(device,int) else repr(device)
            raise RuntimeError(f"Périphérique {role} introuvable ({choix}) : {exc}") from exc
        canaux=info.get("max_input_channels" if entree else "max_output_channels",0)
        if canaux < 1:
            raise RuntimeError(f"Périphérique {device!r} incompatible : aucun canal {role} disponible")
    try:
        if entree: sd.check_input_settings(device=device, channels=1, samplerate=fe)
        else: sd.check_output_settings(device=device, channels=1, samplerate=fe)
    except Exception as exc:
        raise RuntimeError(f"Périphérique {device!r} incompatible {fe} Hz mono en {role} : {exc}") from exc
    return device

def statistiques(signal):
    # Ne jamais convertir silencieusement NaN/Inf en valeurs audio : ce sont
    # des buffers/acquisitions invalides, pas du silence ni une saturation.
    with np.errstate(invalid="ignore", over="ignore"):
        x=np.asarray(signal,dtype=np.float64)
    if x.ndim != 1: raise ValueError("Signal mono requis")
    invalides=int(np.count_nonzero(~np.isfinite(x)))
    if invalides:
        raise ValueError(f"Acquisition invalide : {invalides}/{len(x)} échantillons non finis")
    maximum=float(np.max(np.abs(x))) if x.size else 0.0
    # Un pic isolé à pleine échelle (clic de périphérique, transitoire) ne
    # dégrade pas nécessairement une trame.  On ne qualifie d'écrêtage que
    # celui qui persiste sur au moins 0,1 % de la capture.
    echantillons_ecretes=int(np.count_nonzero(np.abs(x) >= .999))
    ecretage = maximum >= .999 and (
        len(x) <= 10 or echantillons_ecretes >= max(3, int(np.ceil(.001 * len(x))))
    )
    return {"echantillons":len(x),"amplitude_max":maximum,"ecretage":ecretage,
            "echantillons_ecretes":echantillons_ecretes}

def jouer(signal, fe=FE, device=None, volume=1.0):
    x=np.asarray(signal,dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all() or not 0 < volume <= 1:
        raise ValueError("Signal mono fini et volume dans ]0,1] requis")
    sortie=x*volume
    if statistiques(sortie)["ecretage"]: raise ValueError("Gain refusé : écrêtage de l'émission")
    device=verifier_peripherique(device,False,fe); sd=_sd()
    try:
        sd.play(sortie.astype(np.float32),fe,device=device)
        # PipeWire peut ne jamais notifier sd.wait(); borner la lecture à la
        # durée exacte du signal puis arrêter le flux explicitement.
        time.sleep(len(sortie) / fe)
        arreter = getattr(sd, "stop", None)
        if arreter is not None:
            arreter()
        else:
            sd.wait()
    except Exception as exc: raise RuntimeError(f"Erreur PortAudio en lecture : {exc}") from exc
    return statistiques(sortie)

def enregistrer(duree, fe=FE, device=None, chemin=None):
    if duree <= 0: raise ValueError("Durée positive requise")
    device=verifier_peripherique(device,True,fe); sd=_sd(); n=int(round(duree*fe))
    try:
        signal=sd.rec(n,samplerate=fe,channels=1,dtype="float32",device=device)
        # Certains flux PipeWire ne réveillent jamais sd.wait(). L'arrêt
        # explicite garantit que --duree reste bornée.
        time.sleep(duree)
        arreter = getattr(sd, "stop", None)
        if arreter is not None:
            arreter()
        else:  # Compatibilité avec les doubles de test et anciens backends.
            sd.wait()
    except Exception as exc: raise RuntimeError(f"Erreur PortAudio en acquisition : {exc}") from exc
    with np.errstate(invalid="ignore", over="ignore"):
        signal=np.asarray(signal,dtype=np.float32).reshape(-1)
    # Conserver un WAV de valeurs non finies serait inutilisable et masquerait
    # un défaut du périphérique. Refuser explicitement avant toute écriture.
    invalides=int(np.count_nonzero(~np.isfinite(signal)))
    if invalides:
        raise RuntimeError(
            f"Acquisition audio invalide : {invalides}/{len(signal)} échantillons NaN/Inf. "
            "Vérifier --device, le gain/la source PulseAudio et le routage microphone.")
    if chemin:
        chemin=Path(chemin); chemin.parent.mkdir(parents=True,exist_ok=True); wavfile.write(chemin,fe,signal)
    return signal, statistiques(signal)
