# Module 2 — erreurs et solutions

| Erreur / contexte | Cause | Correction et vérification | Statut |
|---|---|---|---|
| PulseAudio inaccessible | Exécution isolée sans serveur audio | Exécuter avec le serveur audio de session | Résolu en environnement local |
| Microphone muet / signal nul | Source désactivée ou mauvais périphérique | Activation et sélection automatique d'une source disponible | Résolu lors de l'essai acoustique |
| `sounddevice.wait()` bloqué | Certains flux PipeWire ne signalent pas la fin | Arrêt explicite après `--duree` | Couvert par `audio_io.py` |
| Écrêtage | Gain micro/sortie excessif | Détection persistante, volume réduit | Résolu lors de l'essai G8_acoustique |
| Clic isolé | Impulsion pleine échelle dans la capture | Interpolation avant filtrage | Couvert par prétraitement |
| Porteuse/start introuvable | S/B insuffisant ou faux préambule | Préambule, synchronisation et erreur explicite | Détecté, non masqué |
| Stop 8N1 / UTF-8 invalide | Bits altérés ou trame tronquée | Contrôles de tramage, resynchronisation et exceptions | Couvert par tests |
| G8 officiel faible en air | 7400/7600 Hz à 300 bauds peu robuste sur ce matériel | Profil séparé `G8_acoustique`, sans prétendre à la conformité | Documenté |
| GitHub 403 | Autorisation distante non vérifiée | Réessayer avec les droits du dépôt | À confirmer |
