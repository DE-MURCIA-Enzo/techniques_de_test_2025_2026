"""Gestion des structures de triangles et validation."""
import struct

from PointSet import PointSet

Triangle = tuple[int, int, int]

class Triangles:
    """Gère un ensemble de triangles référençant un PointSet."""

    def __init__(self, pointset: PointSet, triangles: list[Triangle]):
        """Initialise l'objet Triangles et valide les données."""
        self.pointset = pointset
        self.triangles = triangles
        self._validate_triangles()

    def _validate_triangles(self):
        """Exécute toutes les validations sur la liste des triangles."""
        seen = set()
        for triangle in self.triangles:
            self._validate_indices_number(triangle)
            self._validate_indices_in_range(triangle, len(self.pointset.points))
            self._validate_distinct_vertices(triangle)
            self._validate_not_duplicate(triangle, seen)

    @staticmethod
    def _validate_indices_number(triangle: Triangle):
        """Vérifie qu'un triangle possède exactement 3 indices."""
        if not len(triangle) == 3:
            raise ValueError("a triangle don't have exactly 3 indices")

    @staticmethod
    def _validate_indices_in_range(triangle: Triangle, nb_points: int):
        """Vérifie que les indices du triangle existent dans le PointSet."""
        i, j, k = triangle
        if ((i < 0 or i >= nb_points) or
            (j < 0 or j >= nb_points) or
            (k < 0 or k >= nb_points)):
            raise ValueError("triangle indices out of range")

    @staticmethod
    def _validate_distinct_vertices(triangle: Triangle):
        """Vérifie qu'un triangle ne référence pas plusieurs fois le même point."""
        if len(set(triangle)) != 3:
            raise ValueError("a triangle must reference three distinct points")

    @staticmethod
    def _validate_not_duplicate(triangle: Triangle, seen: set):
        """Vérifie que le triangle n'est pas un doublon d'un triangle déjà traité."""
        i, j, k = triangle
        key = tuple(sorted((i, j, k)))
        if key in seen:
            raise ValueError("duplicate triangles")
        seen.add(key)

    def to_bytes(self) -> bytes:
        """Retourne la représentation binaire du set de triangles.

        Inclut le pointset complet suivi de la liste des triangles.
        """
        buf = bytearray(self.pointset.to_bytes())

        buf += struct.pack("<I", len(self.triangles))
        for i, j, k in self.triangles:
            buf += struct.pack("<III", i, j, k)

        return bytes(buf)