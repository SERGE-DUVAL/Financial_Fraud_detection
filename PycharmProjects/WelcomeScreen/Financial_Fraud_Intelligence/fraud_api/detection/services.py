"""Le modèle est chargé une seule fois, au premier appel, puis gardé en mémoire."""
import threading

from predicteur import ModeleFraude  # module partagé, à la racine du projet

_modele = None
_verrou = threading.Lock()


def modele():
    global _modele
    if _modele is None:
        with _verrou:
            if _modele is None:
                _modele = ModeleFraude()
    return _modele
