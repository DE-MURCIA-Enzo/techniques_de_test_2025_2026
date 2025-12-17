"""Gestion des ensembles de points et de leur format binaire."""
import struct


class PointSet:
    """Représente un ensemble de points 2D avec capacités de sérialisation."""

    def __init__(self, pointset_bytes: bytes):
        """Initialise le PointSet à partir de sa représentation binaire."""
        self.points = self._build_from_bytes(pointset_bytes)

    @staticmethod
    def _build_from_bytes(data: bytes) -> list[tuple[float, float]]:
        """Décode les données binaires pour extraire la liste des points."""
        if len(data) < 4:
            raise ValueError("buffer too short to contain point count")

        (count,) = struct.unpack_from("<I", data, 0)
        offset = 4

        if len(data) < offset + count * 8:
            raise ValueError("buffer too short")

        points: list[tuple[float, float]] = []
        for _ in range(count):
            x, y = struct.unpack_from("<ff", data, offset)
            offset += 8
            points.append((x, y))

        return points

    def to_bytes(self) -> bytes:
        """Retourne la représentation binaire du PointSet."""
        buf = bytearray()
        buf += struct.pack("<I", len(self.points))
        for x, y in self.points:
            buf += struct.pack("<ff", x, y)
        return bytes(buf)