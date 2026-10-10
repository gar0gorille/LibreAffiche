"""Modèle SQLAlchemy/PostGIS d'une commune.

Un modèle décrit une table et ses contraintes. Il n'effectue pas de requête SQL
à lui seul (c'est le rôle de ``app.repositories.commune``).

IMPORTANT : ce fichier décrit une base *existante*. Pour changer une colonne,
il faut une migration Alembic, et pas seulement modifier le modèle.
"""

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Commune(Base):
    """Données administratives + emprise géographique d'une commune.

    Les identifiants sont des chaînes : les codes INSEE peuvent commencer
    par zéro et ne doivent pas être convertis en entiers.
    """

    __tablename__ = "communes"

    # Code INSEE de la commune : clé primaire référencée par panels.commune_code.
    code: Mapped[str] = mapped_column(String(5), primary_key=True)

    nom: Mapped[str] = mapped_column(Text, nullable=False)

    # Métadonnées optionnelles ; conserver leur type compatible avec l'import.
    departement: Mapped[str | None] = mapped_column(String(3), nullable=True)
    region: Mapped[str | None] = mapped_column(String(3), nullable=True)
    epci: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Géométrie PostGIS : MULTIPOLYGON en coordonnées WGS84 (SRID 4326).
    # L'index spatial GiST accélère notamment les recherches de commune
    # par point (ST_Covers / ST_Contains, selon le repository).
    # Ne pas transformer en géométrie Point ni changer le SRID côté modèle.
    geometry: Mapped[WKBElement] = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )
