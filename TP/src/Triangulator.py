"""Implémentation de l'algorithme de triangulation de Delaunay."""
from PointSet import PointSet
from Triangles import Triangles

TriangleIndices = tuple[int, int, int]
Point = tuple[float, float]


class Triangulator:
    """Implémente l'algorithme de triangulation de Delaunay (Bowyer-Watson)."""

    def __init__(self, point_set: PointSet):
        """Initialise le triangulateur."""
        self.point_set = point_set
        self._validate_min_points(point_set.points)
        self._validate_no_duplicates(point_set.points)

    @staticmethod
    def _validate_min_points(points: list[Point]) -> None:
        """Vérifie qu'il y a assez de points pour former un triangle."""
        if len(points) < 3:
            raise ValueError("need at least three points for triangulation")

    @staticmethod
    def _validate_no_duplicates(points: list[Point]) -> None:
        """Vérifie l'absence de points dupliqués (mêmes coordonnées x et y)."""
        seen: set[Point] = set()
        for x, y in points:
            key = (float(x), float(y))
            if key in seen:
                raise ValueError("duplicate points in point set")
            seen.add(key)

    def triangulate(self) -> Triangles:
        """Exécute l'algorithme de triangulation de Bowyer-Watson."""
        points = self.point_set.points
        n_points = len(points)

        # 1. Création du Super-Triangle
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        dx = max_x - min_x
        dy = max_y - min_y
        delta_max = max(dx, dy)
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        st_p1 = (mid_x - 20 * delta_max, mid_y - delta_max)
        st_p2 = (mid_x, mid_y + 20 * delta_max)
        st_p3 = (mid_x + 20 * delta_max, mid_y - delta_max)

        super_triangle_nodes = [st_p1, st_p2, st_p3]
        all_points = points + super_triangle_nodes
        triangulation: list[TriangleIndices] = [(n_points, n_points + 1, n_points + 2)]

        # 2. Algorithme incrémental
        for i, point in enumerate(points):
            bad_triangles = []

            for tri in triangulation:
                if self._is_point_in_circumcircle(point, tri, all_points):
                    bad_triangles.append(tri)

            polygon = []
            for tri in bad_triangles:
                edges = [
                    (tri[0], tri[1]),
                    (tri[1], tri[2]),
                    (tri[2], tri[0])
                ]
                for edge in edges:
                    sorted_edge = tuple(sorted(edge))
                    shared = False
                    for other_tri in bad_triangles:
                        if tri == other_tri:
                            continue
                        other_edges = [
                            tuple(sorted((other_tri[0], other_tri[1]))),
                            tuple(sorted((other_tri[1], other_tri[2]))),
                            tuple(sorted((other_tri[2], other_tri[0])))
                        ]
                        if sorted_edge in other_edges:
                            shared = True
                            break
                    if not shared:
                        polygon.append(edge)

            for tri in bad_triangles:
                triangulation.remove(tri)

            for edge in polygon:
                new_tri = (edge[0], edge[1], i)
                triangulation.append(new_tri)

        # 3. Nettoyage
        final_triangles = []
        for tri in triangulation:
            if not any(idx >= n_points for idx in tri):
                final_triangles.append(tri)

        return Triangles(pointset=self.point_set, triangles=final_triangles)

    def _is_point_in_circumcircle(
            self, p: Point,
            triangle: TriangleIndices,
            all_points: list[Point]
    ) -> bool:
        """Vérifie si un point p se trouve dans le cercle circonscrit d'un triangle."""
        p1 = all_points[triangle[0]]
        p2 = all_points[triangle[1]]
        p3 = all_points[triangle[2]]

        ax, ay = p1
        bx, by = p2
        cx, cy = p3

        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))

        if abs(d) < 1e-9:
            return False

        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) *
              (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) *
              (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d

        center = (ux, uy)
        r_sq = (center[0] - ax) ** 2 + (center[1] - ay) ** 2
        d_sq = (center[0] - p[0]) ** 2 + (center[1] - p[1]) ** 2

        return d_sq < r_sq - 1e-9