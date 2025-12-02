from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, send_file
from app.controllers.prediction_controller import PredictionController

prediction_bp = Blueprint('predict', __name__, url_prefix="/predict")


@prediction_bp.route('/single', methods=['POST'])
def predict_single():
    model = current_app.model
    cfg = current_app.config

    lat = request.form.get('lat')
    lon = request.form.get('lon')

    result = PredictionController.predict_single(lat, lon, model, cfg)

    if result.get("type") == "ajax":
        return jsonify(result['response'])
    
    if result.get("type") == "error_coordinates":
        flash(result['message'], "error")
    
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

    cfg = current_app.config
    model = current_app.model

    result = PredictionController.predict_batch(model,coords,cfg)

    if result.get("type") == "error":
        flash(result["message"], "error")
        return redirect(url_for("static.map_view"))


    # ERROR (normal)
    if result.get("error"):
        flash(result["message"], "error")
        return redirect(url_for("static.map_view"))

    # SUCCESS (normal)
    return render_template(
        "predict_all.html",
        show_sidebar=False,
        predictions=result["predictions"]
    )

@prediction_bp.route('/history', methods=['GET'])
def load_history():
    """Load predictions from file"""

    cfg = current_app.config

    result = PredictionController.load_history(cfg)

    if result.get("type") == "error":
        flash(result["message"], "error")

    if result.get("type") == "warning":
        flash(result["message"], "warning")

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

    # Normal request
    if result.get("type") == "success":
        flash(result["message"], "success")
    
    if result.get("type") == "error":
        flash(result["message"], "error")

    return redirect(url_for("predict.load_history"))

@prediction_bp.route('/download', methods=['GET'])
def download_history():
    """Download the predictions CSV file."""
    cfg = current_app.config
    file_path = cfg.predictions_file

    result = PredictionController.download_history(file_path)
    if result.get("type") == "error":
        flash(result["message"], "error")
        return redirect(url_for("predict.load_history"))
    
    send_file_kwargs = result.get("response", {})
    
    return send_file(
        send_file_kwargs["file_path"],
        mimetype=send_file_kwargs["mime_type"],
        download_name=send_file_kwargs["download_name"],
        as_attachment=send_file_kwargs["as_attachment"]
    )
