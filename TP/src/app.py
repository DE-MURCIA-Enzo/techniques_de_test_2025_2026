"""API Flask pour le service de Triangulation."""
import uuid
from urllib.error import HTTPError
from urllib.request import urlopen

from flask import Flask, make_response

from PointSet import PointSet
from Triangulator import Triangulator

app = Flask(__name__)

@app.route("/triangulate/<point_set_id>", methods=["GET"])
def triangulate(point_set_id: str):
    """Endpoint API pour trianguler un ensemble de points."""
    try:
        uuid.UUID(point_set_id)
    except ValueError:
        return {"error": "Invalid UUID format"}, 400

    try:
        with urlopen("url") as response:
            point_set_bytes = response.read()

    except HTTPError as e:
        if e.code == 404:
            return {"error": "PointSet not found"}, 404
        else:
            return {"error": f"Upstream error: {e.reason}"}, 502
    except Exception as e:
         return {"error": f"Connection error: {str(e)}"}, 503

    try:
        ps = PointSet(point_set_bytes)
        triangulator = Triangulator(ps)
        triangles_obj = triangulator.triangulate()
        response_bytes = triangles_obj.to_bytes()

    except ValueError as e:
        return {"error": f"Processing error: {str(e)}"}, 500

    response = make_response(response_bytes)
    response.headers['Content-Type'] = 'application/octet-stream'
    return response