from flask import Blueprint, request, jsonify, redirect, url_for, session, flash
from app.controllers.coordinate_controller import CoordinateController
from app.utils.helper import _return_json

coordinate_bp = Blueprint("coordinate", __name__, url_prefix="/coordinates")


@coordinate_bp.route("/add", methods=["POST"])
def add_coordinate_route():
    # get lat lon from form
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    coordinates = session.get('coordinates', [])

    result = CoordinateController.add_coordinate(lat, lon, coordinates, request)

    if result["type"] == "error":
        return _return_json({"message" : result.get("message", "Error adding coordinate")}, result.get("status_code"))
    
    if result['type'] == "ajax":
        return _return_json(result.get("response", {}), result.get("status_code"))


    return redirect(url_for("pages.map_view"))


@coordinate_bp.route("/delete", methods=["POST"])
def delete_coordinate_route():
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    result = CoordinateController.delete_coordinate(lat, lon)

    if result['type'] == "error":
        flash(result.get("message", "Error deleting coordinate"), "error")

    flash(result.get("message"), result.get("type"))


    return redirect(url_for("pages.map_view"))


@coordinate_bp.route("/clear", methods=["POST"])
def clear_coordinates_route():
    result = CoordinateController.clear_all(request)

    if result['type'] == "ajax":
        return _return_json({"message" : result.get("message", "Cleared all coordinates")}, result.get("status_code"))

    flash(result.get("message"), result.get("type"))

    return redirect(url_for("pages.map_view"))


@coordinate_bp.route("/upload", methods=["POST"])
def upload_coordinates_route():
    if 'csv_file' not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("pages.map_view"))
    

    csv_file = request.files["csv_file"]

    result = CoordinateController.upload_coordinates(csv_file, request)


    flash(result.get("message"), result.get("type"))


    return redirect(url_for("pages.map_view"))

    
