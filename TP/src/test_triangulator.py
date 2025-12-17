"""Tests unitaires et d'intégration pour le Triangulator."""
import struct
import time
from unittest.mock import MagicMock
from urllib.error import HTTPError

import pytest

import app
from PointSet import PointSet
from Triangles import Triangles
from Triangulator import Triangulator


def build_pointset_bytes(points):
    """Construit manuellement un buffer binaire pour un PointSet."""
    buf = bytearray()
    buf += struct.pack("<I", len(points))
    for x, y in points:
        buf += struct.pack("<ff", float(x), float(y))
    return bytes(buf)


def build_triangles_bytes(points, triangles):
    """Construit manuellement un buffer binaire pour un objet Triangles."""
    buf = bytearray(build_pointset_bytes(points))
    buf += struct.pack("<I", len(triangles))
    for i, j, k in triangles:
        buf += struct.pack("<III", i, j, k)
    return bytes(buf)


############
# FIXTURES #
############

@pytest.fixture
def valid_three_points():
    """Retourne une liste de 3 points formant un triangle rectangle."""
    return [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]

@pytest.fixture
def valid_four_points():
    """Retourne une liste de 4 points formant un carré."""
    return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


@pytest.fixture
def valid_pointset_bytes(valid_three_points):
    """Retourne la représentation binaire des 3 points valides."""
    return build_pointset_bytes(valid_three_points)


@pytest.fixture
def valid_pointset(valid_pointset_bytes):
    """Retourne une instance PointSet initialisée avec 3 points."""
    return PointSet(pointset_bytes=valid_pointset_bytes)


@pytest.fixture
def triangulator(valid_pointset):
    """Retourne une instance Triangulator prête à l'emploi."""
    return Triangulator(point_set=valid_pointset)


@pytest.fixture
def client():
    """Crée un client de test Flask pour simuler les requêtes HTTP."""
    with app.app.test_client() as c:
        yield c


##################
# TESTS POINTSET #
##################

def test_pointset_from_bytes_valid_three_points(
        valid_three_points, valid_pointset_bytes
):
    """Vérifie que PointSet désérialise correctement les données binaires."""
    ps = PointSet(valid_pointset_bytes)

    assert len(ps.points) == len(valid_three_points)
    for (x1, y1), (x2, y2) in zip(ps.points, valid_three_points, strict=True):
        assert x1 == pytest.approx(x2)
        assert y1 == pytest.approx(y2)


def test_pointset_from_bytes_buffer_too_short():
    """Vérifie que PointSet lève une erreur si le buffer est incomplet."""
    # buffer trop court pour contenir un point
    buf = b"\x01\x02\x03"
    with pytest.raises(ValueError):
        PointSet(buf)


###################
# TESTS TRIANGLES #
###################

def test_triangles_to_bytes_ok(valid_three_points, valid_pointset):
    """Vérifie que la méthode to_bytes génère le format binaire attendu."""
    triangle = [(0, 1, 2)]
    tris = Triangles(pointset=valid_pointset, triangles=triangle)
    triangles_bytes = tris.to_bytes()

    assert triangles_bytes == build_triangles_bytes(valid_three_points, triangle)

def test_triangles_indices_out_of_range(valid_pointset):
    """Vérifie le rejet d'indices de triangle hors limites."""
    invalid_triangle = [(0, 1, 3)] # indices valides: 0, 1, 2
    with pytest.raises(ValueError, match="triangle indices out of range"):
        Triangles(pointset=valid_pointset, triangles=invalid_triangle)

def test_triangles_same_indices(valid_pointset):
    """Vérifie le rejet d'un triangle référençant plusieurs fois le même point."""
    same_indices = [(0, 0, 1)]
    with pytest.raises(ValueError,
                       match="a triangle must reference three distinct points"):
        Triangles(pointset=valid_pointset, triangles=same_indices)

def test_triangles_same_triangles(valid_pointset):
    """Vérifie le rejet de triangles dupliqués (ex: (0,1,2) et (0,2,1))."""
    same_triangles = [(0, 1, 2), (0, 2, 1)]
    with pytest.raises(ValueError, match="duplicate triangles"):
        Triangles(pointset=valid_pointset, triangles=same_triangles)


def test_triangles_invalid_indices_number(valid_pointset):
    """Vérifie qu'un triangle doit avoir exactement 3 indices."""
    triangle_to_short = [(0, 1)]
    triangle_to_long = [(0, 1, 2, 3)]

    with pytest.raises(ValueError, match="a triangle don't have exactly 3 indices"):
        Triangles(pointset=valid_pointset, triangles=triangle_to_short)
    with pytest.raises(ValueError, match="a triangle don't have exactly 3 indices"):
        Triangles(pointset=valid_pointset, triangles=triangle_to_long)

#######################
# TESTS TRIANGULATION #
#######################


def test_triangulate_three_points(triangulator):
    """Vérifie la triangulation basique de 3 points (doit donner 1 triangle)."""
    result = triangulator.triangulate()

    assert len(result.triangles) == 1
    assert sorted(result.triangles[0]) == [0, 1, 2]


def test_triangulate_square(valid_four_points):
    """Vérifie la triangulation de 4 points (carré) qui doit donner 2 triangles."""
    valid_pointset_bytes = build_pointset_bytes(valid_four_points)
    points_set = PointSet(valid_pointset_bytes)
    triangulator = Triangulator(point_set=points_set)
    result = triangulator.triangulate()
    flat_indices = [idx for tri in result.triangles for idx in tri]

    assert len(result.triangles) == 2
    #Tous les indices doivent être dans la plage [0, 3]
    assert all(0 <= idx < len(valid_four_points) for idx in flat_indices)
    #Tous les points du carré doivent être utilisés
    assert set(flat_indices) == {0, 1, 2, 3}


def test_triangulate_less_than_three_points():
    """Vérifie que la triangulation échoue s'il y a moins de 3 points."""
    with pytest.raises(ValueError):
        pointset = PointSet(build_pointset_bytes([]))
        triangulator = Triangulator(point_set=pointset)
        triangulator.triangulate()

    with pytest.raises(ValueError):
        pointset = PointSet(build_pointset_bytes([(0.0, 0.0)]))
        triangulator = Triangulator(point_set=pointset)
        triangulator.triangulate()

    with pytest.raises(ValueError):
        pointset = PointSet(build_pointset_bytes([(0.0, 0.0), (1.0, 0.0)]))
        triangulator = Triangulator(point_set=pointset)
        triangulator.triangulate()


def test_triangulate_with_duplicate_points():
    """Vérifie que le Triangulator rejette un PointSet contenant des doublons."""
    points = [
        (0.0, 0.0),
        (1.0, 0.0), # doublon
        (1.0, 0.0), # doublon
        (0.0, 1.0),
    ]
    points_set_bytes = build_pointset_bytes(points)
    points_set = PointSet(points_set_bytes)

    with pytest.raises(ValueError, match="duplicate points in point set"):
        Triangulator(point_set=points_set)


#############
# TESTS API #
#############

def test_api_triangulate_happy_path(monkeypatch, client, valid_three_points):
    """Teste le flux nominal de l'API : réception ID -> fetch -> calcul -> réponse."""
    expected_response = build_triangles_bytes(valid_three_points, [(1, 0, 2)])
    fake_pointset_bytes = build_pointset_bytes(valid_three_points)

    mock_response = MagicMock()
    mock_response.read.return_value = fake_pointset_bytes
    mock_response.__enter__.return_value = mock_response

    def fake_urlopen(url, timeout=None):
        return mock_response

    monkeypatch.setattr(app, "urlopen", fake_urlopen)

    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")

    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/octet-stream"
    assert resp.data == expected_response


def test_api_error_500(monkeypatch, client):
    """Teste le retour 500 si le traitement interne (Triangulator/PointSet) échoue."""
    bad_bytes = b'bad_data'
    mock_response = MagicMock()
    mock_response.read.return_value = bad_bytes
    mock_response.__enter__.return_value = mock_response

    def fake_urlopen(url, timeout=None):
        return mock_response

    monkeypatch.setattr(app, "urlopen", fake_urlopen)
    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")

    assert resp.status_code == 500
    assert "Processing error" in resp.get_json()["error"]


def test_api_error_502(monkeypatch, client):
    """Teste le retour 502 si le service PointSetManager renvoie une erreur."""
    def fake_urlopen(url, timeout=None):
        raise HTTPError("", 503, "Service Unavailable", {}, None)

    monkeypatch.setattr(app, "urlopen", fake_urlopen)
    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")

    assert resp.status_code == 502
    assert resp.get_json() == {"error": "Upstream error: Service Unavailable"}


def test_api_error_404(monkeypatch, client):
    """Teste le retour 404 si le PointSetID n'est pas trouvé par le Manager."""
    def fake_urlopen(url):
        raise HTTPError("", 404, "", {}, None)

    monkeypatch.setattr(app, "urlopen", fake_urlopen)
    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")

    assert resp.status_code == 404
    assert resp.get_json() == {"error": "PointSet not found"}


def test_pointset_id_is_not_uuid(client):
    """Teste que l'API rejette (400) les IDs qui ne sont pas des UUID valides."""
    resp = client.get("/triangulate/test")
    assert resp.status_code == 400
    assert resp.get_json() == {'error': 'Invalid UUID format'}

    resp = client.get("/triangulate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    assert resp.status_code == 400
    assert resp.get_json() == {'error': 'Invalid UUID format'}


########################
# TESTS DE PERFORMANCE #
########################

@pytest.mark.perf
@pytest.mark.parametrize("n_points, max_time", [
    (100, 0.5),   # 100 points < 0.5s
    (500, 1),   # 500 points < 1s
    (1000, 3)   # 1000 points < 3s
])
def test_perf_scalability(n_points, max_time):
    """Vérifie la performance de la triangulation pour différentes charges."""
    points = [(float(i), float(i % 100)) for i in range(n_points)]
    point_set = PointSet(build_pointset_bytes(points))

    start = time.perf_counter()
    Triangulator(point_set).triangulate()
    duration = time.perf_counter() - start

    assert duration < max_time, \
        f"Trop lent pour {n_points} points : {duration:.4f}s (Max {max_time}s)"