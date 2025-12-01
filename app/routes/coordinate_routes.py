from flask import Blueprint, request, jsonify, redirect, url_for, session, flash
from app.controllers.coordinate_controller import CoordinateController

coordinate_bp = Blueprint("coordinate", __name__, url_prefix="/coordinates")


@coordinate_bp.route("/add", methods=["POST"])
def add_coordinate_route():
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    coordinates = session.get('coordinates', [])

    result = CoordinateController.add_coordinate(lat, lon, coordinates, request)

    if result["type"] == "error":   # AJAX request
        return jsonify(result["message"]), result["status_code"]
    
    if result['type'] == "ajax":
        return jsonify(result["response"]), result["status_code"]    
    

    return redirect(url_for("map"))


@coordinate_bp.route("/delete", methods=["POST"])
def delete_coordinate_route():
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    result = CoordinateController.delete_coordinate(lat, lon)

    if result['type'] == "error":
        flash(result["message"], "error")

    flash(result['response']['message'], result['type'])

    return redirect(url_for("map"))


@coordinate_bp.route("/clear", methods=["POST"])
def clear_coordinates_route():
    result = CoordinateController.clear_all(request)

    if result['type'] == "ajax":
        return jsonify(result["response"]), result["status_code"]

    flash(result['message'], result['type'])

    return redirect(url_for("map"))


@coordinate_bp.route("/upload", methods=["POST"])
def upload_coordinates_route():
    if 'csv_file' not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("map.map_view"))
    

    file_name = request.files["csv_file"]
    result = CoordinateController.upload_coordinates(file_name, request)

    flash(result['message'], result['type'])

    return redirect(url_for("map"))

    
