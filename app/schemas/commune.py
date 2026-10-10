"""Schémas Pydantic liés aux communes.

Ces schémas définissent le format des réponses HTTP : ils ne réalisent
ni requête SQL ni recherche géographique.
"""

from pydantic import BaseModel


class CommuneResponse(BaseModel):
    """Commune trouvée à partir d'un point (longitude, latitude).

    Les codes INSEE restent des chaînes de caractères : certains commencent
    par zéro et certains codes comportent des lettres (ex. Corse).
    """

    commune_code: str
    commune_name: str
