from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, send_file
from app.controllers.prediction_controller import PredictionController
from app.utils.helper import _return_json

prediction_bp = Blueprint('predict', __name__, url_prefix="/predict")


@prediction_bp.route('/single', methods=['POST'])
def predict_single():
    model = current_app.model
    cfg = current_app.config["APP_CONFIG"]

    lat = request.form.get('lat')
    lon = request.form.get('lon')

    result = PredictionController.predict_single(lat, lon, model, cfg)

    if result.get("type") == "ajax":
        return _return_json(result.get("response", {}), result.get("status_code"))
    
    if result.get("type") == "error_coordinates":
        flash(result.get("message", "Invalid coordinates."), "error")
        return redirect(url_for("pages.map_view"))
    
    if result.get("type") == "error_response":
        flash(result['message'], "error")
        return render_template("prediction.html", lat=lat, lon=lon)
    
    render_info = result.get("response", {})
    

    return render_template(
        "prediction.html",
        show_sidebar=False,
        label=render_info['label'],
        confidence=render_info['confidence'],
        lat=render_info['lat'],
        lon=render_info['lon'],
        image_base64=render_info['image_base64']
    )

@prediction_bp.route('/batch', methods=['POST'])
def predict_batch():
    """Predict all coordinates stored in session"""
    coords = session.get("coordinates", [])

    cfg = current_app.config["APP_CONFIG"]
    model = current_app.model

    result = PredictionController.predict_batch(model,coords,cfg)

    if result.get("type") == "ajax":
        return _return_json(result.get("response", {}), result.get("status_code"))

    if result.get("type") == "error":
        flash(result.get("message", "Failed to run batch prediction."), "error")
        return redirect(url_for("pages.map_view"))
    
    try:
        predictions_results = result.get("response", {}).get("predictions", [])
    except Exception:
        flash("Failed to process prediction results.", "error")
        return redirect(url_for("pages.map_view"))

    # SUCCESS (normal)
    return render_template(
        "predict_all.html",
        show_sidebar=False,
        predictions=predictions_results
    )

@prediction_bp.route('/history', methods=['GET'])
def load_history():
    """Load predictions from file"""

    cfg = current_app.config['APP_CONFIG']

    result = PredictionController.load_history(cfg)

    # Error or warning
    if result.get("type") in ["error", "warning"]:
        flash(result["message"], result["type"])

    return render_template(
        'predictions.html',
        show_sidebar=False,
        predictions=result["response"].get("predictions", [])
    )

@prediction_bp.route('/clear', methods=['POST'])
def clear_history():
    """Clear all predictions from file"""
    cfg = current_app.config

    result = PredictionController.clear_history(cfg, request)

    flash(result.get("message"), result.get("type"))

    return redirect(url_for("predict.load_history"))

@prediction_bp.route('/download', methods=['GET'])
def download_history():
    """Download the predictions CSV file."""
    cfg = current_app.config["APP_CONFIG"]
    file_path = cfg.predictions_file

    result = PredictionController.download_history(file_path)

    if result.get("type") == "error":
        flash(result["message"], "error")
        return redirect(url_for("predict.load_history"))
    
    args = result.get("response", {})
    
    return send_file(
        args["file_path"],
        mimetype=args["mime_type"],
        download_name=args["download_name"],
        as_attachment=args["as_attachment"]
    )
