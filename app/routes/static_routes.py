from flask import Blueprint, render_template, redirect, url_for, session, current_app, send_from_directory, flash, request
from app.utils.helper import resource_path, validate_latlon

static_bp = Blueprint('static', __name__)

@static_bp.route('/')
def index():
    """ Home page -> redirect to map """
    if 'coordinates' not in session:
        session['coordinates'] = []

    if 'map_center' not in session:
        cfg = current_app.config
        session['map_center'] = {'lat': cfg.map_default['lat'], 'lon': cfg.map_default['lon']}

    return redirect(url_for('static.map_view'))

@static_bp.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(resource_path('static'), filename)


@static_bp.route('/map')
def map_view():
    ''' Renders the map view with stored coordinates and center '''
    cfg = current_app.config

    # Get coordinates and map center from session
    coords = session.get('coordinates', [])
    center = session.get('map_center', {'lat': cfg.map_default['lat'], 'lon': cfg.map_default['lon']})

    return render_template("map.html",
                           coordinates=[{"lat": c[0], "lon": c[1]} for c in coords],
                           map_center=center,
                           zoom=cfg.map_default['zoom'])


@static_bp.route('/search_location', methods=['POST'])
def search_location():
    ''' Handles location search and updates map center '''
    try:
        # Validate and extract latitude and longitude from form
        lat, lon = validate_latlon(request.form['latitude'], request.form['longitude'])

        # Update session with new map center
        session['map_center'] = {"lat": lat, "lon": lon}
        session.modified = True

        # Provide user feedback
        flash('Map centered on searched location.', 'success')
    except (ValueError, KeyError):
        flash('Invalid coordinates provided for search.', 'error')

    return redirect(url_for('static.map_view'))


