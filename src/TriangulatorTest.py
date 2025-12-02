import struct
import random
import time

import pytest
from urllib.error import HTTPError
from urllib import request
from unittest.mock import Mock

import PointSet
import Triangles
import Triangulator
import app


def build_pointset_bytes(points):
    buf = bytearray()
    buf += struct.pack("<I", len(points))
    for x, y in points:
        buf += struct.pack("<ff", float(x), float(y))
    return bytes(buf)


def build_triangles_bytes(points, triangles):
    buf = bytearray(build_pointset_bytes(points))
    buf += struct.pack("<I", len(triangles))
    for i, j, k in triangles:
        buf += struct.pack("<III", i, j, k)
    return bytes(buf)


def _fake_http_error(code):
    """Retourne une fausse fonction urlopen qui lève un HTTPError avec code donné."""
    def _fake(_url, timeout=5):
        raise HTTPError(url=_url, code=code, msg=str(code), hdrs=None, fp=None)
    return _fake


def _fake_urlopen(return_val):
    """Retourne une fausse fonction urlopen qui renvoie un objet réponse avec read()."""
    fake_response = Mock()
    fake_response.read.return_value = return_val

    def _urlopen(_url, timeout=1):
        return fake_response

    return _urlopen


############
# FIXTURES #
############


@pytest.fixture
def valid_three_points():
    return [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]

@pytest.fixture
def valid_four_points():
    return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

@pytest.fixture
def valid_pointsset(valid_three_points):
    return PointSet(points=valid_three_points)


@pytest.fixture
def valid_pointset_bytes(valid_three_points):
    return build_pointset_bytes(valid_three_points)


@pytest.fixture
def triangulator():
    return Triangulator(point_set_id="123e4567-e89b-12d3-a456-426614174000")

@pytest.fixture
def client():
    with app.test_client() as c:
        yield c


##################
# TESTS POINTSET #
##################

def test_pointset_from_bytes_valid_three_points(valid_three_points, valid_pointset_bytes):
    ps = PointSet.from_bytes(valid_pointset_bytes)

    assert len(ps.points) == len(valid_three_points)
    for (x1, y1), (x2, y2) in zip(ps.points, valid_three_points):
        assert x1 == pytest.approx(x2)
        assert y1 == pytest.approx(y2)


def test_pointset_from_bytes_buffer_too_short():
    # buffer trop court pour contenir un point
    buf = b"\x01\x02\x03"
    with pytest.raises(ValueError):
        PointSet.from_bytes(buf)


###################
# TESTS TRIANGLES #
###################


def test_triangles_to_bytes_ok(valid_three_points, valid_pointset):
    triangle = [(0, 1, 2)]
    tris = Triangles(points=valid_pointset, triangles=triangle)
    triangles_bytes = tris.to_bytes()

    assert triangles_bytes == build_triangles_bytes(valid_three_points, triangle)

def test_triangles_indices_out_of_range(valid_pointset):
    invalid_triangle = [(0, 1, 3)]
    with pytest.raises(ValueError):
        Triangles(points_set=valid_pointset, triangles=invalid_triangle)

def test_triangles_same_indices(valid_three_points):
    same_indices = [(0, 0, 1)]
    with pytest.raises(ValueError):
        Triangles(points=valid_three_points, triangles=same_indices)

def test_triangles_same_triangles(valid_three_points):
    same_triangles = [(0, 1, 2), (0, 2, 1)]
    with pytest.raises(ValueError):
        Triangles(points=valid_three_points, triangles=same_triangles)


#######################
# TESTS TRIANGULATION #
#######################


def test_triangulate_three_points(valid_three_points):
    points_set = PointSet(valid_three_points)
    triangulator = Triangulator(point_set=points_set)
    triangle = triangulator.triangulate()

    assert len(triangle) == 1
    assert sorted(triangle) == sorted(valid_three_points)


def test_triangulate_square(valid_four_points):
    points_set = PointSet(valid_four_points)
    triangulator = Triangulator(point_set=points_set)
    triangles = triangulator.triangulate()

    assert len(triangles) == 2
    flat = [i for tri in triangulator for i in tri]
    assert all(0 <= i < len(valid_four_points) for i in flat)


def test_triangulate_less_than_three_points():
    with pytest.raises(ValueError):
        points_set = PointSet([])
        triangulator = Triangulator(point_set=points_set)
        triangulator.triangulate()
    with pytest.raises(ValueError):
        points_set = PointSet([(0.0, 0.0)])
        triangulator = Triangulator(point_set=points_set)
        triangulator.triangulate()
    with pytest.raises(ValueError):
        points_set = PointSet([(0.0, 0.0), (1.0, 0.0)])
        triangulator = Triangulator(point_set=points_set)
        triangulator.triangulate()


def test_triangulate_with_duplicate_points():
    points = [
        (0.0, 0.0),
        (1.0, 0.0), # doublon
        (1.0, 0.0), # doublon
        (0.0, 1.0),
    ]
    points_set = PointSet(points)
    triangulator = Triangulator(point_set=points_set)
    with pytest.raises(ValueError):
        triangulator.triangulate(points)


######################
# TESTS TRIANGULATOR #
######################


def test_triangulator_pointset_id_valid(triangulator):
    assert triangulator.point_set_id == "123e4567-e89b-12d3-a456-426614174000"


def test_pointset_id_is_not_uuid():
    with pytest.raises(AttributeError):
        Triangulator(point_set_id="test")
    with pytest.raises(AttributeError):
        Triangulator(point_set_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")


def test_fetch_pointset_happy_path(monkeypatch, triangulator, valid_pointset_bytes):
    monkeypatch.setattr(request, "urlopen", _fake_urlopen(valid_pointset_bytes))
    assert triangulator.fetch_pointset() == valid_pointset_bytes


def test_fetch_pointset_404(monkeypatch, triangulator):
    monkeypatch.setattr(request, "urlopen", _fake_http_error(404))
    with pytest.raises(FileNotFoundError):
        triangulator.fetch_pointset()


def test_fetch_pointset_400(monkeypatch, triangulator):
    monkeypatch.setattr(request, "urlopen", _fake_http_error(400))
    with pytest.raises(ValueError):
        triangulator.fetch_pointset()


def test_fetch_pointset_503(monkeypatch, triangulator):
    monkeypatch.setattr(request, "urlopen", _fake_http_error(503))
    with pytest.raises(RuntimeError):
        triangulator.fetch_pointset()


def test_fetch_invalid_pointset_too_short(monkeypatch, triangulator):
    # buffer trop court (< 4 bytes)
    invalid_data = b"\x01\x02\x03"
    monkeypatch.setattr(request, "urlopen", _fake_urlopen(invalid_data))
    with pytest.raises(ValueError):
        triangulator.fetch_pointset()


def test_load_pointset_integration(monkeypatch, triangulator, valid_three_points, valid_pointset_bytes):
    monkeypatch.setattr(request, "urlopen", _fake_urlopen(valid_pointset_bytes))

    ps = triangulator.load_pointset()
    assert isinstance(ps, PointSet)
    assert ps.points == pytest.approx(valid_three_points)


#############
# TESTS API #
#############


def test_api_triangulate_happy_path(monkeypatch, client, valid_three_points):
    triangles = [(0, 1, 2)]
    expected = build_triangles_bytes(valid_three_points, triangles)

    def fake_compute(self):
        return expected

    monkeypatch.setattr(Triangulator, "compute_triangles", fake_compute)

    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")

    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/octet-stream"
    assert resp.data == expected


def test_api_triangulate_invalid_uuid(client):
    resp = client.get("/triangulate/not-a-uuid")
    assert resp.status_code == 400


def test_api_triangulate_pointset_not_found(monkeypatch, client):
    def fake_compute(self):
        raise FileNotFoundError

    monkeypatch.setattr(Triangulator, "compute_triangles", fake_compute)

    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")
    assert resp.status_code == 404


def test_api_triangulate_invalid_pointset(monkeypatch, client):
    def fake_compute(self):
        raise ValueError("invalid pointset")

    monkeypatch.setattr(Triangulator, "compute_triangles_bytes", fake_compute)

    resp = client.get("/triangulate/123e4567-e89b-12d3-a456-426614174000")
    assert resp.status_code == 500


########################
# TESTS DE PERFORMANCE #
########################


@pytest.mark.perf
def test_perf_triangulate_large():
    points = [(float(i), float(i % 100)) for i in range(10_000)]
    point_set = PointSet(points=points)

    start = time.perf_counter()
    triangulation = Triangulator(point_set).triangulate()
    duration = time.perf_counter() - start

    assert duration < 10.0
    assert len(triangulation) > 0